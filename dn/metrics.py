# -*- coding: utf-8 -*-
"""Fase 2 · métricas de Distribuição Numérica a partir da camada curada.

Definições (docs/mapeamento.md §5, config/config.yaml → regras):

  positivado         PDV com PESO_KG > 0 no mês
  cobertura_pdv      nº de PDVs positivados no mês
  base_ativa         nº de PDVs positivados em pelo menos um dos últimos N meses
                     (janela móvel fechada no mês; N = janela_base_ativa_meses);
                     só existe quando a janela está completa — antes fica nulo
  pct_cobertura (DN) cobertura_pdv ÷ base_ativa
  volume_t           soma de PESO_KG ÷ 1000 (todas as linhas, inclusive kg ≤ 0)
  kg_pdv             volume_t × 1000 ÷ cobertura_pdv
  receita_rs         soma de RECEITA (mesmas linhas do volume)
  rs_pdv             receita_rs ÷ cobertura_pdv

Níveis e contagem (rodada 5): no distribuidor o PDV conta em cada distribuidor;
em canal, segmento, supervisor e cluster o PDV conta uma vez dentro do nível.

Categoria: positivados na categoria ÷ base_ativa do nível (régua DN);
penetração = positivados na categoria ÷ positivados do nível (régua do protótipo).

Segmento do distribuidor: meses de histórico contados até o mês de referência,
inclusive; Base atual quando > segmento_novos_meses, senão Novos. Sem venda (02/10/2026, Douglas) quando o
distribuidor não teve kg > 0 em nenhum dos últimos segmento_sem_venda_meses meses até o de referência; vale antes
da maturidade (um Novo sem venda também é Sem venda). A contagem
sai da DATA_CADASTRO do de-para quando ela existe (C3, 09/09/2026); sem data,
cai no PRIMEIRO_MES com sell-out na Mtrix, que é censurado pelo início da série
— e só nesse caso HISTORICO_CENSURADO fica verdadeiro. O segmento é o do mês de
referência e vale para a série inteira.

Comparativos: vs mês anterior, vs média dos 3 meses anteriores (só com os 3
presentes), vs mesmo mês do ano anterior (pela DIM_CALENDARIO.ANO_MES_LY;
nulo se o mês não existe na série). Variação % para cobertura e volume,
pontos percentuais para o % de cobertura.
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

from . import manifesto
from .load import parquet
from .utils.config import CFG, PASTA_CURATED
from .utils.log import abortar, log

_R = CFG["regras"]
JANELA = int(_R["janela_base_ativa_meses"])
NOVOS_MESES = int(_R["segmento_novos_meses"])
SEM_VENDA_MESES = int(_R["segmento_sem_venda_meses"])            # 02/10/2026 (Douglas): 3
SEG_NOMES = dict(CFG["painel"]["rotulos"]["segmentos"])          # D6: rótulos vêm do config
SEGMENTOS = ("base_atual", "novos", "sem_venda")
assert set(SEG_NOMES) == {"todos", *SEGMENTOS}, "painel.rotulos.segmentos precisa de todos/base_atual/novos/sem_venda"


def slug(s: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(s).upper())


def _idx(am: str) -> int:
    return int(am[:4]) * 12 + int(am[5:7]) - 1


def meses_entre(a: str, b: str) -> int:
    """Meses de a até b, inclusive (a=b -> 1)."""
    return _idx(b) - _idx(a) + 1


# =============================================================================
# Etapa 1 · performance (P1/P2, 15/09/2026): chaves categoricas e tabelas compartilhadas
# =============================================================================
# As chaves da fato (mes, distribuidor, PDV, segmento, supervisor, categoria, cluster) viajam como CATEGORIA ORDENADA
# com as categorias em ordem lexicografica: `==`, `<=`, `isin`, `sort_values` e `groupby` dao o mesmo resultado do texto,
# mas a memoria cai pela metade e os agrupamentos usam os codigos inteiros. Os cubos que saem daqui voltam a texto
# (`_descat`), para que painel, validacao e curated vejam exatamente o que viam antes. O calculo pesado (positivados,
# base ativa, PDVs distintos) e feito UMA vez sobre a tabela de pares mes x distribuidor x PDV (x categoria) e
# derivado para os 14 cubos (`preparar_codigos`), em vez de 14 varreduras da fato.
CHAVES = ("ANO_MES", "DIST", "COD_PDV", "SEG", "SUP", "CAT", "CLUSTER")
MEDIDAS = ("PESO_KG", "RECEITA", "ATEND", "NF_MIN", "ATEND_CAT", "NF_MIN_CAT", "FREQ")   # FREQ: so a validacao (P5)
NIVEIS = {"canal": [], "segmento": ["SEG"], "supervisor": ["SEG", "SUP"], "cluster": ["SEG", "CLUSTER"],
          "supervisor_canal": ["SUP"], "cluster_canal": ["CLUSTER"], "distribuidor": ["DIST"]}


def _categorizar(s: pd.Series) -> pd.Series:
    """Texto -> categoria ordenada (categorias em ordem lexicografica; nulo continua nulo)."""
    if isinstance(s.dtype, pd.CategoricalDtype):
        return s if s.cat.ordered else s.cat.as_ordered()
    return s.astype("category").cat.as_ordered()


def _mapear_cat(s: pd.Series, mapa) -> pd.Series:
    """De-para aplicado pelas CATEGORIAS de uma coluna categorica (nunca linha a linha): devolve uma categoria ordenada.
    `mapa`: Series indexada pela chave ou dict; chave sem de-para vira nulo."""
    cats = s.cat.categories
    vals = pd.Series(cats, index=cats).map(mapa).astype(object)
    vals = vals.where(vals.notna(), None)
    alvo = pd.Categorical(vals.to_numpy(dtype=object)).as_ordered()
    codes = s.cat.codes.to_numpy()
    novo = np.where(codes >= 0, alvo.codes[np.maximum(codes, 0)], -1)
    return pd.Series(pd.Categorical.from_codes(novo, categories=alvo.categories, ordered=True), index=s.index)


def _descat(df: pd.DataFrame) -> pd.DataFrame:
    """Colunas categoricas de volta a texto (`string`): contrato de sempre dos cubos."""
    for col in df.columns:
        if isinstance(df[col].dtype, pd.CategoricalDtype):
            df[col] = df[col].astype("string")
    return df


def _codigos(s: pd.Series) -> np.ndarray:
    return s.cat.codes.to_numpy()


def _sem_nulos(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Linhas com chave nula (codigo -1) ficam fora do agrupamento, como no groupby de texto (dropna)."""
    for col in cols:
        if len(df) and int(df[col].min()) < 0:
            df = df[(df[cols] >= 0).all(axis=1)]
            break
    return df


def preparar_codigos(c: dict) -> dict:
    """Tabelas compartilhadas do calculo, a partir da fato categorica (`c["fato"]`):
      cats     categorias de cada chave (codigo -> texto)
      K        codigos das chaves + medidas (mesmas linhas da fato; as medidas nao sao copiadas)
      pares    pares mes x distribuidor x PDV com kg > 0 (com segmento, supervisor e cluster)
      pares_cat  idem x categoria
      base     base ativa por nivel: {tuple(G): DataFrame(G + ANO_MES + base_ativa)}, janela de JANELA meses
    Os codigos de ANO_MES coincidem com a posicao em c["meses"]."""
    f = c["fato"]
    for col in ("DIST", "COD_PDV"):   # ANO_MES fica com a serie inteira: um recorte (usuario) sem venda num mes mantem o codigo do mes
        f[col] = f[col].cat.remove_unused_categories()
    cats = {col: np.asarray(f[col].cat.categories, dtype=object) for col in CHAVES}
    if list(cats["ANO_MES"]) != list(c["meses"]):
        abortar(f"codigos de ANO_MES nao coincidem com a serie: {list(cats['ANO_MES'])[:3]}... x {list(c['meses'])[:3]}...")
    K = pd.DataFrame({col: f[col].cat.codes for col in CHAVES})
    for m in MEDIDAS:
        K[m] = f[m]
    pos = (f["PESO_KG"] > 0).to_numpy()
    pares_cat = K.loc[pos, list(CHAVES)].drop_duplicates(["ANO_MES", "DIST", "COD_PDV", "CAT"])
    pares = pares_cat.drop_duplicates(["ANO_MES", "DIST", "COD_PDV"])
    base = {}
    n_meses = len(c["meses"])
    M = pares["ANO_MES"].to_numpy()
    for nome, G in NIVEIS.items():
        base[tuple(G)] = []
    for i in range(JANELA - 1, n_meses):
        w = pares[(M >= i - JANELA + 1) & (M <= i)]
        for G in base:
            Gl = list(G)
            wg = _sem_nulos(w, Gl) if Gl else w
            if Gl:
                b = wg.drop_duplicates(Gl + ["COD_PDV"]).groupby(Gl, sort=True).size().rename("base_ativa").reset_index()
            else:
                b = pd.DataFrame({"base_ativa": [int(wg["COD_PDV"].nunique())]})
            b["ANO_MES"] = i
            base[G].append(b)
    for G in base:
        base[G] = pd.concat(base[G], ignore_index=True) if base[G] else pd.DataFrame(columns=list(G) + ["ANO_MES", "base_ativa"])
    c.update({"cats": cats, "K": K, "pares": pares, "pares_cat": pares_cat, "base": base})
    return c


def recortar_codigos(c: dict, c2: dict) -> dict:
    """Etapa 2b: as tabelas compartilhadas do mes fechado sao as do mes de referencia cortadas nos meses <= mes fechado
    (os codigos de ANO_MES sao posicoes na serie, entao o corte e por codigo; nada e recalculado)."""
    n2 = len(c2["meses"])
    if list(c["meses"][:n2]) != list(c2["meses"]):
        abortar("recortar_codigos: a serie do mes fechado nao e um prefixo da serie do mes de referencia")
    cats2 = dict(c["cats"]); cats2["ANO_MES"] = c["cats"]["ANO_MES"][:n2]
    c2["cats"] = cats2
    for k_ in ("K", "pares", "pares_cat"):
        c2[k_] = c[k_][c[k_]["ANO_MES"] < n2]
    c2["base"] = {G: b[b["ANO_MES"] < n2] for G, b in c["base"].items()}
    return c2


def _decodificar(df: pd.DataFrame, cats: dict, cols: list[str]) -> pd.DataFrame:
    """Codigos -> texto nas colunas de chave (dtype `string`, o contrato dos cubos)."""
    for col in cols:
        df[col] = pd.array(cats[col][df[col].to_numpy()], dtype="string")
    return df


# =============================================================================
# carga
# =============================================================================
def carregar(mes_ref: str | None = None) -> dict:
    # P1: so as colunas que o calculo usa (UNIDADES, ARQUIVO_ORIGEM, EXECUCAO_ID, PROCESSADO_EM ficam no Parquet) e as chaves
    # como categoria ordenada desde a leitura
    f = parquet.carregar("FATO_SELLOUT", colunas=["ANO_MES", "CNPJ_DISTRIBUIDOR", "COD_PDV", "COD_PRODUTO", "RECEITA", "PESO_KG", "FREQ"])
    for col in ("ANO_MES", "CNPJ_DISTRIBUIDOR", "COD_PDV", "COD_PRODUTO"):
        f[col] = _categorizar(f[col])
    dim_dist = parquet.carregar("DIM_DISTRIBUIDOR")
    dim_pdv = parquet.carregar("DIM_PDV")
    dim_prod = parquet.carregar("DIM_PRODUTO")
    dim_cal = parquet.carregar("DIM_CALENDARIO")
    meses = [str(m) for m in sorted(f["ANO_MES"].unique())]
    mes_ref = mes_ref or meses[-1]
    if mes_ref not in meses:
        abortar(f"mes de referencia {mes_ref} nao esta na serie ({meses[0]} a {meses[-1]})")
    meses = [m for m in meses if m <= mes_ref]
    if meses != list(f["ANO_MES"].cat.categories):
        f = f[f["ANO_MES"].isin(meses)]
        f["ANO_MES"] = f["ANO_MES"].cat.remove_unused_categories()

    # distribuidores do painel (rodada 7) e seus atributos
    d = dim_dist[dim_dist["NO_PAINEL"] & dim_dist["TEM_SELLOUT"]].copy()
    obs = d["PRIMEIRO_MES"].map(lambda p: meses_entre(p, mes_ref) if pd.notna(p) else None)
    if "DATA_CADASTRO" not in d.columns:
        d["DATA_CADASTRO"] = pd.NaT
    cad = d["DATA_CADASTRO"].map(lambda t: meses_entre(pd.Timestamp(t).strftime("%Y-%m"), mes_ref)
                                 if pd.notna(t) else None)
    # inteiro puro: o mapa sobre datas devolve float (NaT vira NaN) e o painel
    # imprimiria "37.0 meses"
    d["MESES_HISTORICO"] = cad.where(cad.notna(), obs).map(
        lambda v: int(v) if pd.notna(v) else None).astype(object)
    pos_ = f.loc[f["PESO_KG"].to_numpy() > 0, ["CNPJ_DISTRIBUIDOR", "ANO_MES"]].drop_duplicates()
    vendas = {str(k): set(map(str, g["ANO_MES"])) for k, g in pos_.groupby("CNPJ_DISTRIBUIDOR", observed=True)}
    d["SEGMENTO_ID"] = segmento_ids(d, mes_ref, meses, vendas)
    d["SEGMENTO"] = d["SEGMENTO_ID"].map(SEG_NOMES)
    sv = d.loc[d["SEGMENTO_ID"] == "sem_venda", "NOME_REDUZIDO"].tolist()
    log(f"segmento Sem venda (sem kg > 0 nos ultimos {SEM_VENDA_MESES} meses ate {mes_ref}): {len(sv)} distribuidor(es) {sv}", "ok")
    # so e censurado quem nao tem data de cadastro E comeca no 1o mes da serie
    d["HISTORICO_CENSURADO"] = cad.isna() & (d["PRIMEIRO_MES"] == meses[0])
    n_cad = int(cad.notna().sum())
    log(f"maturidade: {n_cad} distribuidor(es) pela data de cadastro · "
        f"{int(d['HISTORICO_CENSURADO'].sum())} ainda com historico censurado (C3)", "ok")
    d["SUP_ID"] = d["SUPERVISOR"].map(slug)
    d["DIST_ID"] = d["CNPJ_DISTRIBUIDOR"]

    # RN-58: a calibracao da frequencia usa TODAS as linhas do arquivo (todos os distribuidores, kg <= 0 inclusive), como o
    # total da Mtrix; so depois a fato e recortada aos distribuidores do painel
    calib = _calibracao_guardada(meses)
    if calib is None:
        calib = frequencia_calibrar(f)
        calib["curated_execucao"] = str((manifesto.gravado() or {}).get("execucao", ""))
    else:
        log(f"frequencia (RN-58): alfa de {len(calib)} meses reaproveitado de DN_FREQ_CALIBRACAO (mesma ingestao; "
            f"{calib['alfa'].min():.4f} a {calib['alfa'].max():.4f})", "ok")

    no_painel = f["CNPJ_DISTRIBUIDOR"].isin(set(d["CNPJ_DISTRIBUIDOR"])).to_numpy()
    n_fora = int((~no_painel).sum())
    f = f[no_painel]
    log(f"fato: {len(f):,} linhas de {d.shape[0]} distribuidores no painel; "
        f"{n_fora:,} linhas fora (distribuidores excluidos)", "ok")
    for col in ("CNPJ_DISTRIBUIDOR", "COD_PDV", "COD_PRODUTO"):
        f[col] = f[col].cat.remove_unused_categories()

    # P1: atributos do distribuidor, do produto e do PDV entram pelas categorias (de-para aplicado uma vez por chave, nao por linha)
    dd = d.drop_duplicates("CNPJ_DISTRIBUIDOR").set_index("CNPJ_DISTRIBUIDOR")
    f["SEG"] = _mapear_cat(f["CNPJ_DISTRIBUIDOR"], dd["SEGMENTO_ID"])
    f["SUP"] = _mapear_cat(f["CNPJ_DISTRIBUIDOR"], dd["SUP_ID"])
    f["CAT"] = _mapear_cat(f["COD_PRODUTO"], dim_prod.drop_duplicates("COD_PRODUTO").set_index("COD_PRODUTO")["CATEGORIA"])
    seg_pdv = dim_pdv.drop_duplicates("COD_PDV").set_index("COD_PDV")["SEGMENTO_MTRIX"].reindex(f["COD_PDV"].cat.categories)
    # de-para de clusters (C5) vem da camada curada (D2): DIM_CLUSTER vazia = sem de-para na ingestao
    clu = parquet.carregar("DIM_CLUSTER")
    if clu.empty:
        log("DIM_CLUSTER vazia (sem de-para de clusters na ingestao) — clusters = Segmento do PDV da Mtrix", "aviso")
        clu = None
    if clu is not None:
        mapa = clu.set_index("SEGMENTO_MTRIX")["CLUSTER"]
        sem = sorted(set(seg_pdv.dropna()) - set(mapa.index))
        if sem:
            log(f"{len(sem)} segmento(s) da Mtrix sem linha no de-para de clusters — mantidos com o proprio nome: {sem[:8]}", "aviso")
        seg_pdv = seg_pdv.map(lambda x: mapa.get(x, x))
    f["CLUSTER"] = _mapear_cat(f["COD_PDV"], seg_pdv)
    f = f.drop(columns=["COD_PRODUTO"]).rename(columns={"CNPJ_DISTRIBUIDOR": "DIST"})
    f = frequencia_alocar(f, calib)
    return {"fato": f, "dist": d, "pdv": dim_pdv, "prod": dim_prod, "cal": dim_cal,
            "meses": meses, "mes_ref": mes_ref, "freq_calib": calib, "vendas_dist": vendas}


def segmento_ids(d: pd.DataFrame, mes: str, meses: list[str], vendas: dict) -> np.ndarray:
    """Sem venda (sem kg > 0 nos ultimos SEM_VENDA_MESES meses ate `mes`) > Base atual (> NOVOS_MESES de historico) > Novos.
    `d` precisa de CNPJ_DISTRIBUIDOR e MESES_HISTORICO contados ate `mes`."""
    i = meses.index(mes)
    ult = set(meses[max(0, i - SEM_VENDA_MESES + 1): i + 1])
    sem = d["CNPJ_DISTRIBUIDOR"].astype(str).map(lambda c_: not (vendas.get(c_, set()) & ult)).to_numpy()
    return np.where(sem, "sem_venda", np.where(d["MESES_HISTORICO"] > NOVOS_MESES, "base_atual", "novos"))


# =============================================================================
# RN-58 · frequencia de compra (atendimentos = NFs) — Etapas 1 a 3 da frequencia, 13/09/2026
# =============================================================================
_FR = CFG["regras"].get("frequencia") or {}
_FR_REGRA = str(_FR.get("regra", "uniao_proporcional"))
if _FR_REGRA not in ("uniao_proporcional", "minimo"):
    abortar(f"regras.frequencia.regra '{_FR_REGRA}' nao implementada (uniao_proporcional | minimo)")


def _uniao(par: np.ndarray, fq: np.ndarray, mx: np.ndarray, alfa: float | np.ndarray) -> np.ndarray:
    """Uniao proporcional por grupo: D = alfa x maior frequencia do grupo; estimativa = D(1 − Π(1 − f/D)), nunca abaixo
    do maior valor e nunca acima da soma. Grupo de uma linha devolve exatamente a frequencia da linha."""
    D = np.asarray(alfa, dtype="float64") * mx
    r = np.minimum(fq / D[par], 1.0 - 1e-12)
    lg = np.bincount(par, np.log1p(-r), len(mx))
    return np.maximum(D * (1.0 - np.exp(lg)), mx)


def _grupos(df: pd.DataFrame, cols: list[str]) -> tuple[np.ndarray, int]:
    """Numero do grupo por linha, na ordem da 1a aparicao (como `ngroup(sort=False)`). P1: com chaves categoricas a chave
    composta e montada a partir dos codigos inteiros e fatorada de uma vez — mesma numeracao, sem agrupar texto."""
    if cols and all(isinstance(df[c_].dtype, pd.CategoricalDtype) for c_ in cols):
        chave = np.zeros(len(df), dtype=np.int64)
        for c_ in cols:
            chave = chave * (len(df[c_].cat.categories) + 1) + (df[c_].cat.codes.to_numpy().astype(np.int64) + 1)
        g = pd.factorize(chave, sort=False)[0]
    else:
        g = df.groupby(cols, sort=False, observed=True).ngroup().to_numpy()
    return g, int(g.max()) + 1 if len(g) else 0


def _max_soma(par: np.ndarray, n: int, fq: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    mx = np.zeros(n); np.maximum.at(mx, par, fq)
    return mx, np.bincount(par, fq, n)


def _calibracao_guardada(meses: list[str]) -> pd.DataFrame | None:
    """P2: o alfa de cada mes so depende do arquivo Mtrix daquele mes. O DN_FREQ_CALIBRACAO gravado por uma execucao sobre a
    MESMA ingestao (coluna `curated_execucao` = execucao do manifesto) e reaproveitado; qualquer mudanca nas bases reingere,
    muda a execucao do manifesto e a calibracao e refeita."""
    alvo = PASTA_CURATED / "DN_FREQ_CALIBRACAO.parquet"
    if not alvo.exists():
        return None
    try:
        k = pd.read_parquet(alvo)
    except Exception:
        return None
    exec_ = str((manifesto.gravado() or {}).get("execucao", ""))
    if not exec_ or "curated_execucao" not in k.columns or set(k["curated_execucao"].astype(str)) != {exec_}:
        return None
    if not set(meses) <= set(k["ANO_MES"].astype(str)):
        return None
    return k[k["ANO_MES"].astype(str).isin(meses)].reset_index(drop=True)


def frequencia_calibrar(f: pd.DataFrame) -> pd.DataFrame:
    """RN-58: alfa do mes tal que Σ estimativa dos pares distribuidor x PDV (todas as linhas do arquivo) = atendimentos da
    linha de total (freq_total x Cod. PDV distintos, conferido inteiro na ingestao). Nao calibra = aborta (decisao 6)."""
    V = CFG["validacao"]; tol = float(V["frequencia_tolerancia_total"]); amax = float(_FR.get("alfa_busca_max", 1000))
    gab = parquet.carregar("SELLOUT_GABARITO").set_index("ANO_MES")
    rows = []
    for mes, g in f.groupby("ANO_MES", sort=True, observed=True):
        if mes not in gab.index or pd.isna(gab.loc[mes, "atendimentos_total"]):
            abortar(f"frequencia (RN-58): {mes} sem atendimentos da linha de total na curated (SELLOUT_GABARITO) — nao calibra")
        K = float(gab.loc[mes, "atendimentos_total"])
        par, n = _grupos(g, ["CNPJ_DISTRIBUIDOR", "COD_PDV"])
        fq = g["FREQ"].to_numpy("float64")
        mx, sm = _max_soma(par, n, fq)
        tot = lambda a: float(_uniao(par, fq, mx, a).sum())
        lo, hi = 1.0, amax
        if mx.sum() > K + tol:
            abortar(f"frequencia (RN-58): {mes} — a soma do maior valor por par ({mx.sum():,.0f}) ja passa o total da Mtrix ({K:,.0f}); nenhum alfa fecha")
        if tot(hi) < K - tol:
            abortar(f"frequencia (RN-58): {mes} — mesmo com alfa {hi:g} a estimativa ({tot(hi):,.0f}) nao alcanca o total da Mtrix ({K:,.0f}); nenhum alfa fecha")
        for _ in range(60):
            mid = (lo + hi) / 2
            if tot(mid) < K:
                lo = mid
            else:
                hi = mid
        alfa = (lo + hi) / 2
        est = tot(alfa)
        if abs(est - K) > tol:
            abortar(f"frequencia (RN-58): {mes} — calibracao nao fechou: estimativa {est:,.3f} x total {K:,.0f} (tolerancia {tol:g})")
        rows.append({"ANO_MES": mes, "atendimentos_total": int(K), "pdvs_distintos": int(g["COD_PDV"].nunique()), "alfa": alfa,
                     "soma_max_pares": float(mx.sum()), "soma_linhas": float(sm.sum()), "soma_estimada": est, "erro_nfs": est - K,
                     "pares": n, "pares_uma_linha": int((np.bincount(par, minlength=n) == 1).sum())})
    out = pd.DataFrame(rows)
    log(f"frequencia (RN-58): alfa calibrado em {len(out)} meses ({out['alfa'].min():.4f} a {out['alfa'].max():.4f}); "
        f"maior erro {out['erro_nfs'].abs().max():.4f} NF · regra exibida: {_FR_REGRA}", "ok")
    return out


def frequencia_alocar(f: pd.DataFrame, calib: pd.DataFrame) -> pd.DataFrame:
    """RN-58: estimativa por par distribuidor x PDV e por par x categoria (linhas kg > 0, R8), gravada numa unica linha de
    cada grupo — assim qualquer soma por nivel (canal, segmento, supervisor, cluster, distribuidor, categoria) soma pares
    inteiros. NF_MIN = maior frequencia de SKU do grupo (minimo sem estimativa, decisao 1)."""
    for c_ in ("ATEND", "NF_MIN", "ATEND_CAT", "NF_MIN_CAT"):
        f[c_] = 0.0
    pos = (f["PESO_KG"] > 0).to_numpy()
    sub = f.loc[pos, ["ANO_MES", "DIST", "COD_PDV", "CAT", "FREQ"]]
    if not len(sub):
        return f
    alfa_mes = calib.set_index("ANO_MES")["alfa"]
    fq = sub["FREQ"].to_numpy("float64")
    idx = sub.index.to_numpy()
    for cols, c_est, c_min in ((["ANO_MES", "DIST", "COD_PDV"], "ATEND", "NF_MIN"),
                               (["ANO_MES", "DIST", "COD_PDV", "CAT"], "ATEND_CAT", "NF_MIN_CAT")):
        par, n = _grupos(sub, cols)
        mx, _ = _max_soma(par, n, fq)
        if isinstance(sub["ANO_MES"].dtype, pd.CategoricalDtype):   # P1: alfa pelo codigo do mes, nao linha a linha
            alfa_lin = alfa_mes.reindex(sub["ANO_MES"].cat.categories).to_numpy("float64")[sub["ANO_MES"].cat.codes.to_numpy()]
        else:
            alfa_lin = sub["ANO_MES"].map(alfa_mes).to_numpy("float64")
        alfa_g = np.zeros(n); alfa_g[par] = alfa_lin
        est = _uniao(par, fq, mx, alfa_g) if _FR_REGRA == "uniao_proporcional" else mx
        primeira = ~pd.Series(par).duplicated().to_numpy()
        f.loc[idx[primeira], c_est] = est[par[primeira]]
        f.loc[idx[primeira], c_min] = mx[par[primeira]]
    return f


# =============================================================================
# séries por nível
# =============================================================================
def serie_nivel(c: dict, G: list[str], cat: bool = False) -> pd.DataFrame:
    """Série mensal por grupo G (lista de colunas, pode ser vazia).

    Devolve ANO_MES × G [× CAT] com positivados, base_ativa (nulo sem janela
    completa; para categoria é a base do grupo SEM categoria), pct, volume_kg,
    kg_pdv, receita_rs, rs_pdv e, com cat=True, penetracao.

    P2 (Etapa 1): positivados e base ativa vem das tabelas de pares de `preparar_codigos` (calculadas uma vez para todos
    os niveis); as somas continuam sendo feitas nas linhas da fato (mesmas linhas, mesma ordem: mesmo resultado).
    """
    K, cats, base = c["K"], c["cats"], c["base"][tuple(G)]
    keys = ["ANO_MES"] + G
    pares = _sem_nulos(c["pares"], G)
    positivados = pares.drop_duplicates(keys + ["COD_PDV"]).groupby(keys, sort=True).size().rename("positivados")
    Kg = _sem_nulos(K, G)
    # somas kg, R$ e, RN-58, atendimentos estimados (ATEND) e minimo sem estimativa (NF_MIN), uma linha por par distribuidor
    # x PDV — as quatro somas numa unica passada pelas linhas (cada coluna somada na mesma ordem de sempre)
    if not cat:
        S = Kg.groupby(keys, sort=True)[["PESO_KG", "RECEITA", "ATEND", "NF_MIN"]].sum()
        S.columns = ["volume_kg", "receita_rs", "atendimentos", "atendimentos_min"]
        out = pd.concat([positivados, S], axis=1).reset_index()
        out = out.merge(base, on=keys, how="left")
        kc = keys
    else:
        kc = keys + ["CAT"]
        pc = _sem_nulos(c["pares_cat"], G + ["CAT"]).drop_duplicates(kc + ["COD_PDV"]).groupby(kc, sort=True).size().rename("positivados")
        S = _sem_nulos(Kg, ["CAT"]).groupby(kc, sort=True)[["PESO_KG", "RECEITA", "ATEND_CAT", "NF_MIN_CAT"]].sum()
        S.columns = ["volume_kg", "receita_rs", "atendimentos", "atendimentos_min"]
        out = pd.concat([pc, S], axis=1).reset_index()
        out = out.merge(base, on=keys, how="left")
        out = out.merge(positivados.rename("positivados_nivel").reset_index(), on=keys, how="left")
        out["penetracao"] = out["positivados"] / out["positivados_nivel"] * 100
    out["pct_cobertura"] = out["positivados"] / out["base_ativa"] * 100
    out["kg_pdv"] = out["volume_kg"] / out["positivados"].replace(0, np.nan)
    out["rs_pdv"] = out["receita_rs"] / out["positivados"].replace(0, np.nan)
    # RN-58: frequencia de compra = atendimentos estimados ÷ positivados; frequencia_min = minimo sem estimativa ÷ positivados
    out["frequencia"] = out["atendimentos"] / out["positivados"].replace(0, np.nan)
    out["frequencia_min"] = out["atendimentos_min"] / out["positivados"].replace(0, np.nan)
    out = out.sort_values(keys).reset_index(drop=True)
    return _decodificar(out, cats, kc)


def comparativos(s: pd.DataFrame, G: list[str], cal: pd.DataFrame) -> pd.DataFrame:
    """Acrescenta as variações vs mês anterior, média L3M e LY, por grupo."""
    s = s.sort_values(G + ["ANO_MES"]).copy()
    ly = cal.set_index("ANO_MES")["ANO_MES_LY"]
    s["ANO_MES_LY"] = s["ANO_MES"].map(ly)
    g = s.groupby(G) if G else None

    def shifted(col, k):
        return g[col].shift(k) if G else s[col].shift(k)

    for col, nome, pp in (("positivados", "cobertura", False), ("pct_cobertura", "pct_cobertura", True),
                          ("volume_kg", "volume", False), ("receita_rs", "receita", False),
                          ("frequencia", "frequencia", False)):   # RN-58: variacao % da frequencia de compra
        prev = shifted(col, 1)
        l3 = pd.concat([shifted(col, k) for k in (1, 2, 3)], axis=1)
        l3m = l3.mean(axis=1).where(l3.notna().all(axis=1))
        # LY por juncao com o proprio DataFrame (nunca por deslocamento de posicao)
        chave = G + ["ANO_MES"]
        ref = s[chave + [col]].rename(columns={"ANO_MES": "ANO_MES_LY", col: "_ly"})
        lyv = s[G + ["ANO_MES_LY"]].merge(ref, on=G + ["ANO_MES_LY"], how="left")["_ly"].values
        # a janela do mes anterior/L3M so vale se esses meses sao consecutivos na serie
        for suf, refv in (("mes_anterior", prev), ("l3m", l3m), ("ly", pd.Series(lyv, index=s.index))):
            if pp:
                s[f"{nome}_var_{suf}"] = s[col] - refv
            else:
                s[f"{nome}_var_{suf}"] = (s[col] / refv.replace(0, np.nan) - 1) * 100
    return s



def acumulados(s: pd.DataFrame, G: list[str], cal: pd.DataFrame, meses: list[str]) -> pd.DataFrame:
    """F5 (RN-25, A.10/D31): acumulado no ano CIVIL e no ano FISCAL por grupo x mes, calculado no pipeline.

    ytd_<persp>_volume_kg / receita_rs = soma dos meses do mesmo ano (civil: ANO; fiscal: ANO_FISCAL) ate o mes,
    SO quando todos os meses do periodo (do 1o mes do ano ate o mes) estao na serie; senao nulo — nunca zero.
    ytd_<persp>_n_meses = quantos meses o acumulado soma. LY por JUNCAO (mesmo mes do periodo, ano - 1), so se o
    periodo do ano anterior tambem esta completo; ytd_<persp>_<medida>_var_ly em %. Contagens de PDV nao se
    acumulam aqui (ver acum_ano)."""
    c = cal.set_index("ANO_MES")
    presentes = set(meses)
    s = s.sort_values(G + ["ANO_MES"]).reset_index(drop=True)
    for pref, ano_col, mes_col in (("civil", "ANO", "MES"), ("fiscal", "ANO_FISCAL", "MES_FISCAL")):
        completo = {}
        for m in meses:
            a, k = c.loc[m, ano_col], int(c.loc[m, mes_col])
            do_ano = c[(c[ano_col] == a) & (c[mes_col] <= k)].index
            completo[m] = len(do_ano) == k and all(x in presentes for x in do_ano)
        ka, km = f"_{pref}_ano", f"_{pref}_mes"
        s[ka] = s["ANO_MES"].map(c[ano_col]).astype("int64")
        s[km] = s["ANO_MES"].map(c[mes_col]).astype("int64")
        comp = s["ANO_MES"].map(completo).fillna(False).astype(bool)
        grp = G + [ka]
        s[f"ytd_{pref}_volume_kg"] = s.groupby(grp)["volume_kg"].cumsum().where(comp)
        s[f"ytd_{pref}_receita_rs"] = s.groupby(grp)["receita_rs"].cumsum().where(comp)
        s[f"ytd_{pref}_n_meses"] = s[km].where(comp)
        # RN-58 (decisao 5): frequencia acumulada = Σ atendimentos dos meses ÷ Σ positivados dos meses (mesma escala do mes)
        if "atendimentos" in s.columns:
            s[f"ytd_{pref}_frequencia"] = (s.groupby(grp)["atendimentos"].cumsum()
                                           / s.groupby(grp)["positivados"].cumsum().replace(0, np.nan)).where(comp)
        cols_ref = [f"ytd_{pref}_volume_kg", f"ytd_{pref}_receita_rs"] + ([f"ytd_{pref}_frequencia"] if "atendimentos" in s.columns else [])
        ref = s[G + [ka, km] + cols_ref].rename(
            columns={f"ytd_{pref}_volume_kg": "_vly", f"ytd_{pref}_receita_rs": "_rly", f"ytd_{pref}_frequencia": "_fly"}).copy()
        ref[ka] = ref[ka] + 1
        mm = s[G + [ka, km]].merge(ref, on=G + [ka, km], how="left")
        s[f"ytd_{pref}_volume_ly"] = mm["_vly"].values
        s[f"ytd_{pref}_receita_ly"] = mm["_rly"].values
        if "atendimentos" in s.columns:
            s[f"ytd_{pref}_frequencia_ly"] = mm["_fly"].values
            s[f"ytd_{pref}_frequencia_var_ly"] = (s[f"ytd_{pref}_frequencia"] / s[f"ytd_{pref}_frequencia_ly"].replace(0, np.nan) - 1) * 100
        for med, col in (("volume", f"ytd_{pref}_volume_kg"), ("receita", f"ytd_{pref}_receita_rs")):
            ly = s[f"ytd_{pref}_{med}_ly"].replace(0, np.nan)
            s[f"ytd_{pref}_{med}_var_ly"] = (s[col] / ly - 1) * 100
        s = s.drop(columns=[ka, km])
    return s


def acum_ano(c_: dict) -> pd.DataFrame:
    """F5 (RN-25, Q-a): uma linha por perspectiva (civil/fiscal) x ano presente na serie x nivel, com os PDVs
    DISTINTOS que compraram no periodo (cobertura do periodo — nao e soma de meses), kg, R$, n meses, se o periodo
    comeca no 1o mes do ano (completo) e se fecha no 12o (fechado). Niveis: canal, segmento, supervisor (com e sem
    segmento), distribuidor, categoria. Alimenta a tabela "Ano a ano" e a linha de acumulado da Visao geral.
    P2: PDVs distintos pela tabela de pares x categoria; somas nas linhas da fato (codigos), como antes."""
    cal, meses, K, pares, cats = c_["cal"], c_["meses"], c_["K"], c_["pares_cat"], c_["cats"]
    c = cal.set_index("ANO_MES")
    niveis = {"canal": [], "segmento": ["SEG"], "supervisor_canal": ["SUP"], "supervisor": ["SEG", "SUP"],
              "distribuidor": ["DIST"], "categoria": ["CAT"]}
    rows = []
    for persp, ano_col, mes_col in (("civil", "ANO", "MES"), ("fiscal", "ANO_FISCAL", "MES_FISCAL")):
        anos = sorted({int(c.loc[m, ano_col]) for m in meses})
        for a in anos:
            ms = [m for m in meses if int(c.loc[m, ano_col]) == a]
            completo = int(c.loc[ms[0], mes_col]) == 1
            fechado = int(c.loc[ms[-1], mes_col]) == 12
            idx = [meses.index(m) for m in ms]
            fm = K[K["ANO_MES"].isin(idx)]
            pm = pares[pares["ANO_MES"].isin(idx)]
            base = {"PERSPECTIVA": persp, "ANO_P": a, "n_meses": len(ms), "mes_de": ms[0], "mes_ate": ms[-1],
                    "completo": bool(completo), "fechado": bool(fechado)}
            for nivel, G in niveis.items():
                if not G:
                    rows.append(dict(base, NIVEL=nivel, K1="", K2="", pdvs_distintos=int(pm["COD_PDV"].nunique()),
                                     volume_kg=float(fm["PESO_KG"].sum()), receita_rs=float(fm["RECEITA"].sum())))
                    continue
                p = _sem_nulos(pm, G).drop_duplicates(G + ["COD_PDV"]).groupby(G, sort=True).size()
                vr = _sem_nulos(fm, G).groupby(G, sort=True)[["PESO_KG", "RECEITA"]].sum()
                v, r = vr["PESO_KG"], vr["RECEITA"]
                for key, n in p.items():
                    kk = key if isinstance(key, tuple) else (key,)
                    rows.append(dict(base, NIVEL=nivel, K1=str(cats[G[0]][kk[0]]), K2=str(cats[G[1]][kk[1]]) if len(kk) > 1 else "",
                                     pdvs_distintos=int(n), volume_kg=float(v.get(key, 0.0)), receita_rs=float(r.get(key, 0.0))))
    cols = ["PERSPECTIVA", "ANO_P", "NIVEL", "K1", "K2", "n_meses", "mes_de", "mes_ate", "completo", "fechado",
            "pdvs_distintos", "volume_kg", "receita_rs"]
    return pd.DataFrame(rows, columns=cols)


def acum_pdvs_mensal(c_: dict) -> pd.DataFrame:
    """Refino E4b (D24) / E5 (D25): PDVs DISTINTOS acumulados no ano ate cada mes (civil e fiscal), nos niveis canal, segmento,
    supervisor (com e sem segmento), distribuidor, cluster, categoria e as linhas por categoria das tabelas. Mesma regua de
    `acum_ano` (kg > 0; lojas distintas, nunca soma de meses): primeiro mes de compra de cada PDV no ano, no nivel, e soma
    acumulada desses primeiros meses. As colunas de texto viram codigos inteiros antes de agrupar (so desempenho; a conta e a
    mesma). Uma linha por nivel x chave x ANO_MES com as colunas de `acum_ano` (mes_ate = ANO_MES)."""
    # P2: parte da tabela de pares x categoria (mesmas chaves distintas da fato com kg > 0, na mesma ordem de 1a aparicao);
    # os codigos sao refatorados na ordem de aparicao, como antes, e ANO_MES ja e a posicao em `meses`
    cal, meses, P, cats = c_["cal"], c_["meses"], c_["pares_cat"], c_["cats"]
    if "pares_cat" not in c_:
        abortar("acum_pdvs_mensal: chame metrics.preparar_codigos(c) antes")
    c = cal.set_index("ANO_MES")
    cols = ["SEG", "SUP", "DIST", "CLUSTER", "CAT"]
    cod, uni = {}, {}
    for col in cols + ["COD_PDV"]:
        v_ = P[col].to_numpy()
        k_, u_ = pd.factorize(np.where(v_ >= 0, v_, np.nan).astype("float64"), use_na_sentinel=True)
        cod[col] = k_.astype(np.int64); uni[col] = np.asarray(cats[col][u_.astype(np.int64)], dtype=object)
    base = pd.DataFrame({**{c_c: cod[c_c] for c_c in cols + ["COD_PDV"]}, "M": P["ANO_MES"].to_numpy().astype(np.int64)})
    niveis = {"canal": [], "segmento": ["SEG"], "supervisor_canal": ["SUP"], "supervisor": ["SEG", "SUP"], "distribuidor": ["DIST"],
              "cluster_canal": ["CLUSTER"], "cluster": ["SEG", "CLUSTER"], "categoria": ["CAT"],
              "supervisor_canal_cat": ["SUP", "CAT"], "supervisor_cat": ["SEG", "SUP", "CAT"],
              "cluster_canal_cat": ["CLUSTER", "CAT"], "cluster_cat": ["SEG", "CLUSTER", "CAT"], "distribuidor_cat": ["DIST", "CAT"]}
    rows = []
    for persp, ano_col, mes_col in (("civil", "ANO", "MES"), ("fiscal", "ANO_FISCAL", "MES_FISCAL")):
        ano_m = np.array([int(c.loc[m, ano_col]) for m in meses], dtype=np.int64)
        meses_ano = {}
        for k, m in enumerate(meses):
            meses_ano.setdefault(int(ano_m[k]), []).append(k)
        pos_m = np.zeros(len(meses), dtype=np.int64); de_m = [""] * len(meses); comp_m = [False] * len(meses); fech_m = [False] * len(meses)
        for a_, ks in meses_ano.items():
            comp_ = int(c.loc[meses[ks[0]], mes_col]) == 1
            for j_, k in enumerate(ks):
                pos_m[k] = j_ + 1; de_m[k] = meses[ks[0]]; comp_m[k] = comp_; fech_m[k] = int(c.loc[meses[k], mes_col]) == 12
        b = base.assign(A=ano_m[base["M"].to_numpy()])
        prim = b.groupby(["A"] + cols + ["COD_PDV"], sort=False)["M"].min().reset_index()
        for nivel, G in niveis.items():
            sub = prim[(prim[G] >= 0).all(axis=1)] if G else prim   # chave nula (sem cluster, por exemplo) fica fora, como no groupby original
            pr = sub.groupby(["A"] + G + ["COD_PDV"], sort=False)["M"].min().reset_index()
            cont = pr.groupby(["A"] + G + ["M"], sort=False).size().rename("n").reset_index()
            chaves = cont[["A"] + G].drop_duplicates()
            grade = chaves.merge(pd.DataFrame({"M": np.arange(len(meses)), "A": ano_m}), on="A")
            grade = grade.merge(cont, on=["A"] + G + ["M"], how="left")
            grade["n"] = grade["n"].fillna(0).astype(np.int64)
            grade = grade.sort_values(["A"] + G + ["M"], kind="stable")
            grade["pdvs"] = grade.groupby(["A"] + G, sort=False)["n"].cumsum()
            mk = grade["M"].to_numpy()
            out = pd.DataFrame({"PERSPECTIVA": persp, "ANO_P": grade["A"].to_numpy().astype(int), "NIVEL": nivel,
                                "K1": uni[G[0]][grade[G[0]].to_numpy()].astype(str) if len(G) > 0 else "",
                                "K2": uni[G[1]][grade[G[1]].to_numpy()].astype(str) if len(G) > 1 else "",
                                "K3": uni[G[2]][grade[G[2]].to_numpy()].astype(str) if len(G) > 2 else "",
                                "ANO_MES": np.asarray(meses, dtype=object)[mk], "n_meses": pos_m[mk].astype(int),
                                "mes_de": np.asarray(de_m, dtype=object)[mk], "mes_ate": np.asarray(meses, dtype=object)[mk],
                                "completo": np.asarray(comp_m, dtype=bool)[mk], "fechado": np.asarray(fech_m, dtype=bool)[mk],
                                "pdvs_distintos": grade["pdvs"].to_numpy().astype(int)})
            rows.append(out)
    return pd.concat(rows, ignore_index=True)


# =============================================================================
# F6 · Penetração (RN-27..RN-31, RN-34..RN-36, RN-38, RN-45) — tudo no mês fechado
# =============================================================================
def mes_em_andamento(mes_ref: str) -> bool:
    """True quando o mes de referencia ainda esta correndo (a Mtrix trouxe so parte dele).
    `auto` (regras.mes_em_andamento) = o mes de referencia e o mesmo mes da ultima leitura
    das bases, pelo manifesto; `sim`/`nao` forcam. Decisao de 10/09/2026. (F6: movida de painel.py.)"""
    v = str(CFG["regras"].get("mes_em_andamento", "auto")).strip().lower()
    if v in ("sim", "true", "1"):
        return True
    if v in ("nao", "não", "false", "0"):
        return False
    d = manifesto.dados_atualizados_em()                     # dd/mm/aaaa
    return len(d) == 10 and f"{d[6:10]}-{d[3:5]}" == mes_ref


def mes_fechado(meses: list[str], mes_ref: str) -> str:
    """F6 (RN-27): competencia da Penetracao = ultimo mes fechado (o anterior quando mes_ref esta em andamento)."""
    if not mes_em_andamento(mes_ref):
        return mes_ref
    i = meses.index(mes_ref)
    if i == 0:
        abortar(f"{mes_ref} esta em andamento e nao ha mes fechado antes dele na serie (RN-27)")
    return meses[i - 1]


def _sum1(s):
    return s.sum(min_count=1)


def penetracao(c: dict, T: dict) -> dict:
    """Benchmark P75 por categoria (RN-30), lojas a positivar no grao distribuidor x categoria (RN-31) e por
    distribuidor x cluster x categoria (Q-b), kg/R$ por loja truncados no P99 (RN-34), fator observado por categoria
    (RN-34), potencial de entrada e em regime (RN-34/35), cores (RN-36), categorias por loja, niveis por SOMA dos
    distribuidores (RN-45) e medicao da mascara PDV x categoria (RN-38). Nada disso e recalculado no template."""
    import base64
    import gzip
    import json
    f, d, meses, mes_ref = c["fato"], c["dist"], c["meses"], c["mes_ref"]
    P = _R["penetracao"]; PO = _R["potencial"]; B = P["benchmark"]
    if str(B.get("tipo", "percentil")) != "percentil":
        abortar(f"regras.penetracao.benchmark.tipo '{B.get('tipo')}' nao implementado (so percentil)")
    pctl = float(B["valor"]); min_obs = int(B.get("minimo_observacoes") or 0)
    janela_f = int(PO["janela_fator_meses"]); min_lojas = int(PO["minimo_lojas_distribuidor"])
    p_out = float(PO["percentil_corte_outliers"])
    verde = float(P["cor_verde_pct"]); vermelho = float(P["cor_vermelho_pct"])
    foco = [str(x) for x in (P.get("categorias_foco") or [])]
    mp = mes_fechado(meses, mes_ref)
    i_mp = meses.index(mp)
    fm = f[f["ANO_MES"] == mp]
    cats = sorted(str(x) for x in fm["CAT"].dropna().unique())
    for x in foco:
        if x not in cats:
            abortar(f"regras.penetracao.categorias_foco: '{x}' nao existe em DIM_PRODUTO.CATEGORIA ({cats})")

    # Etapa 2 (Q1, aprovada 16/09/2026): num painel por usuario a REFERENCIA e a do canal inteiro — benchmark P75, cortes P99,
    # kg/R$ por loja do canal e fator observado vem de `c["pen_canal"]`, guardado pela execucao do canal; so o que e do
    # distribuidor (kg/loja por distribuidor, lojas, penetracao) e recalculado no recorte
    PC_ = c.get("pen_canal") if c.get("recorte") else None   # so o painel por usuario reaproveita; o canal (e a sua 2b) calcula
    jan_f = meses[max(0, i_mp - janela_f + 1): i_mp + 1]
    dc = T["DN_DISTRIBUIDOR_CAT_MES"]
    # ---- benchmark (RN-30): P75 da penetracao dos distribuidores com sell-out na categoria no mes fechado
    if PC_ is None:
        dcm = dc[(dc["ANO_MES"] == mp) & (dc["positivados"] > 0)]
        bench, n_dist_b = {}, {}
        for cat, g in dcm.groupby("CAT"):
            n_dist_b[str(cat)] = int(len(g))
            bench[str(cat)] = float(np.percentile(g["penetracao"].astype(float), pctl)) if len(g) >= max(min_obs, 1) else None
    else:
        bench, n_dist_b = PC_["bench"], PC_["n_dist_b"]

    # ---- kg/loja e R$/loja por distribuidor x categoria (compradores no mes fechado; media truncada no P99 da categoria)
    pk = fm.groupby(["DIST", "CAT", "COD_PDV"], as_index=False).agg(kg=("PESO_KG", "sum"), rs=("RECEITA", "sum"))
    pk = _descat(pk[pk["kg"] > 0])   # P1: chaves de volta a texto (os mapas por categoria abaixo esperam texto)
    if PC_ is None:
        corte_kg = pk.groupby("CAT")["kg"].quantile(p_out / 100)
        corte_rs = pk.groupby("CAT")["rs"].quantile(p_out / 100)
    else:
        corte_kg, corte_rs = PC_["corte_kg"], PC_["corte_rs"]
    pk["kg_ok"] = pk["kg"] <= pk["CAT"].map(corte_kg)
    pk["rs_ok"] = pk["rs"] <= pk["CAT"].map(corte_rs)
    if PC_ is None:
        canal_kg = pk[pk["kg_ok"]].groupby("CAT")["kg"].mean()
        canal_rs = pk[pk["rs_ok"]].groupby("CAT")["rs"].mean()
        canal_kg_simples = pk.groupby("CAT")["kg"].mean()
    else:
        canal_kg, canal_rs, canal_kg_simples = PC_["canal_kg"], PC_["canal_rs"], PC_["canal_kg_simples"]
    n_lojas = pk.groupby(["DIST", "CAT"]).size()
    d_kg = pk[pk["kg_ok"]].groupby(["DIST", "CAT"])["kg"].mean()
    d_rs = pk[pk["rs_ok"]].groupby(["DIST", "CAT"])["rs"].mean()

    # ---- fator observado por categoria (RN-34): lojas com a 1a compra da categoria na janela, ja ativas no canal antes
    if PC_ is None:
        pos_all = f[f["PESO_KG"] > 0]
        pcm = pos_all.groupby(["COD_PDV", "CAT", "ANO_MES"], as_index=False)["PESO_KG"].sum()
        first_cat = pcm.groupby(["COD_PDV", "CAT"])["ANO_MES"].min().rename("primeiro_cat").reset_index()
        first_canal = pcm.groupby("COD_PDV")["ANO_MES"].min().rename("primeiro_canal").reset_index()
        fc = first_cat.merge(first_canal, on="COD_PDV")
        novas = fc[fc["primeiro_cat"].isin(jan_f) & (fc["primeiro_canal"] < fc["primeiro_cat"])]
        kg1 = novas.merge(pcm, left_on=["COD_PDV", "CAT", "primeiro_cat"], right_on=["COD_PDV", "CAT", "ANO_MES"])
        kg_novas = kg1.groupby("CAT")["PESO_KG"].mean(); n_novas = kg1.groupby("CAT").size()
        kg_comp = pcm[pcm["ANO_MES"].isin(jan_f)].groupby("CAT")["PESO_KG"].mean()
        fator = {}
        for cat in cats:
            a, b_ = kg_novas.get(cat), kg_comp.get(cat)
            fator[cat] = float(a) / float(b_) if a is not None and b_ is not None and not pd.isna(a) and not pd.isna(b_) and b_ > 0 else None
            if fator[cat] is not None and fator[cat] > 1:
                log(f"fator observado de {cat} acima de 1 ({fator[cat]:.2f}): lojas novas compram mais que a media no 1o mes — mantido como observado", "aviso")
        c["pen_canal"] = {"bench": bench, "n_dist_b": n_dist_b, "corte_kg": corte_kg, "corte_rs": corte_rs, "canal_kg": canal_kg,
                          "canal_rs": canal_rs, "canal_kg_simples": canal_kg_simples, "fator": fator, "n_novas": n_novas,
                          "kg_novas": kg_novas, "kg_comp": kg_comp, "mes_fechado": mp}
    else:
        if PC_.get("mes_fechado") != mp:
            abortar(f"penetracao: referencia do canal e de {PC_.get('mes_fechado')}, recorte pede {mp}")
        fator, n_novas, kg_novas, kg_comp = PC_["fator"], PC_["n_novas"], PC_["kg_novas"], PC_["kg_comp"]

    BK = pd.DataFrame([{"CAT": cat, "foco": cat in foco, "benchmark": bench.get(cat), "n_dist": n_dist_b.get(cat, 0),
                        "fator": fator.get(cat), "n_lojas_novas": int(n_novas.get(cat, 0)),
                        "kg_novas_1o_mes": _f(kg_novas.get(cat)), "kg_compradores_janela": _f(kg_comp.get(cat)),
                        "kg_loja_canal": _f(canal_kg.get(cat)), "rs_loja_canal": _f(canal_rs.get(cat)),
                        "kg_loja_canal_simples": _f(canal_kg_simples.get(cat)),
                        "corte_kg_p": _f(corte_kg.get(cat)), "corte_rs_p": _f(corte_rs.get(cat))} for cat in cats])

    # ---- distribuidor x categoria (RN-31, RN-34, RN-35, RN-36): TODOS os distribuidores com venda no mes fechado;
    #      sem venda na categoria -> penetracao 0 (abaixo da referencia)
    dm = T["DN_DISTRIBUIDOR_MES"]
    dmm = dm[dm["ANO_MES"] == mp].set_index("DIST")["positivados"]
    seg_of = d.set_index("DIST_ID")["SEGMENTO_ID"].to_dict(); sup_of = d.set_index("DIST_ID")["SUP_ID"].to_dict()
    pen_d = dc[dc["ANO_MES"] == mp].set_index(["DIST", "CAT"])
    dists = [x for x in d["DIST_ID"] if x in dmm.index]

    def _cor(pct_b):
        if pct_b is None:
            return None
        return "verde" if pct_b >= verde else ("vermelho" if pct_b < vermelho else "neutro")

    def _linha(did, cat, pen, lojas, pos_niv, extra):
        b = bench.get(cat)
        nl = int(n_lojas.get((did, cat), 0))
        kg_l, rs_l = d_kg.get((did, cat)), d_rs.get((did, cat))
        media_canal = nl < min_lojas or kg_l is None or pd.isna(kg_l)
        if media_canal:
            kg_l, rs_l = canal_kg.get(cat), canal_rs.get(cat)
        kg_l, rs_l = _f(kg_l), _f(rs_l)
        gap = None if b is None else max(0.0, b - pen)
        a_pos = None if gap is None else gap * pos_niv / 100
        fa = fator.get(cat)
        reg_t = None if a_pos is None or kg_l is None else a_pos * kg_l / 1000
        reg_rs = None if a_pos is None or rs_l is None else a_pos * rs_l
        pot_t = None if reg_t is None or fa is None else reg_t * fa
        pot_rs = None if reg_rs is None or fa is None else reg_rs * fa
        pct_b = None if not b else pen / b * 100
        return dict(extra, DIST=did, CAT=cat, SEG=seg_of.get(did), SUP=sup_of.get(did), positivados_nivel=int(pos_niv), lojas=int(lojas),
                    penetracao=float(pen), benchmark=b, pct_bench=pct_b, cor=_cor(pct_b), gap=gap, a_positivar=a_pos,
                    n_lojas_kg=nl, media_canal=bool(media_canal), kg_loja=kg_l, rs_loja=rs_l, fator=fa,
                    potencial_t=pot_t, potencial_rs=pot_rs, regime_t=reg_t, regime_rs=reg_rs)

    rows = []
    for did in dists:
        pos_niv = int(dmm[did])
        for cat in cats:
            r0 = pen_d.loc[(did, cat)] if (did, cat) in pen_d.index else None
            pen = float(r0["penetracao"]) if r0 is not None else 0.0
            lojas = int(r0["positivados"]) if r0 is not None else 0
            rows.append(_linha(did, cat, pen, lojas, pos_niv, {}))
    DC = pd.DataFrame(rows)

    # ---- distribuidor x cluster x categoria (Q-b): mesma regua, no grao do cluster; kg/loja do distribuidor x categoria
    pos_m = fm[fm["PESO_KG"] > 0]
    dcl = pos_m.groupby(["DIST", "CLUSTER"])["COD_PDV"].nunique()
    dclc = pos_m.groupby(["DIST", "CLUSTER", "CAT"])["COD_PDV"].nunique()
    rows = []
    for (did, cl), pos_dc in dcl.items():
        if did not in dmm.index:
            continue
        for cat in cats:
            lojas = int(dclc.get((did, cl, cat), 0))
            rows.append(_linha(did, cat, lojas / pos_dc * 100 if pos_dc else 0.0, lojas, int(pos_dc), {"CLUSTER": str(cl)}))
    DCL = pd.DataFrame(rows)
    DCL["positivados_nivel"] = DCL["positivados_nivel"].astype(int)

    # ---- niveis: penetracao do nivel (cubo) + somas dos distribuidores (RN-31/RN-45: agregacao no grao, nunca gap do nivel)
    niveis = {"canal": ([], T["DN_CANAL_CAT_MES"], DC), "segmento": (["SEG"], T["DN_SEGMENTO_CAT_MES"], DC),
              "supervisor_canal": (["SUP"], T["DN_SUPERVISOR_CANAL_CAT_MES"], DC), "supervisor": (["SEG", "SUP"], T["DN_SUPERVISOR_CAT_MES"], DC),
              "cluster_canal": (["CLUSTER"], T["DN_CLUSTER_CANAL_CAT_MES"], DCL), "cluster": (["SEG", "CLUSTER"], T["DN_CLUSTER_CAT_MES"], DCL),
              "distribuidor": (["DIST"], T["DN_DISTRIBUIDOR_CAT_MES"], DC)}
    partes = []
    for nivel, (G, cubo, grao) in niveis.items():
        cm = cubo[cubo["ANO_MES"] == mp][G + ["CAT", "positivados", "positivados_nivel", "penetracao", "pct_cobertura", "volume_kg", "receita_rs"]].copy()
        cm = cm.rename(columns={"positivados": "lojas"})
        ag = grao.groupby(G + ["CAT"]).agg(a_positivar=("a_positivar", _sum1), potencial_t=("potencial_t", _sum1), potencial_rs=("potencial_rs", _sum1),
                                           regime_t=("regime_t", _sum1), regime_rs=("regime_rs", _sum1), n_dist=("DIST", "nunique"),
                                           n_media_canal=("media_canal", "sum")).reset_index()
        m = cm.merge(ag, on=G + ["CAT"], how="outer")
        # nivel sem venda na categoria: penetracao 0 (a soma dos distribuidores continua valendo)
        for col, val in (("lojas", 0), ("penetracao", 0.0)):
            m[col] = m[col].fillna(val)
        if G:
            tot_tab = {("SEG",): T["DN_SEGMENTO_MES"], ("SUP",): T["DN_SUPERVISOR_CANAL_MES"], ("SEG", "SUP"): T["DN_SUPERVISOR_MES"],
                       ("CLUSTER",): T["DN_CLUSTER_CANAL_MES"], ("SEG", "CLUSTER"): T["DN_CLUSTER_MES"], ("DIST",): T["DN_DISTRIBUIDOR_MES"]}[tuple(G)]
            tt = tot_tab[tot_tab["ANO_MES"] == mp].set_index(G)["positivados"]
            keys = list(zip(*[m[g] for g in G]))
            pn = pd.Series([tt.get(k if len(G) > 1 else k[0]) for k in keys], index=m.index, dtype="float")
            m["positivados_nivel"] = m["positivados_nivel"].fillna(pn)
        else:
            tot = T["DN_CANAL_MES"]; m["positivados_nivel"] = m["positivados_nivel"].fillna(int(tot[tot["ANO_MES"] == mp]["positivados"].iloc[0]))
        m["benchmark"] = m["CAT"].map(bench)
        m["pct_bench"] = np.where(m["benchmark"].astype(float) > 0, m["penetracao"] / m["benchmark"].astype(float) * 100, np.nan)
        m["cor"] = [_cor(None if pd.isna(x) else float(x)) for x in m["pct_bench"]]
        m["fator"] = m["CAT"].map(fator)
        m["kg_loja"] = np.where(m["lojas"] > 0, m["volume_kg"] / m["lojas"].replace(0, np.nan), np.nan)
        m["rs_loja"] = np.where(m["lojas"] > 0, m["receita_rs"] / m["lojas"].replace(0, np.nan), np.nan)
        if nivel == "distribuidor":
            # F10 (D-A, aprovada em 11/09/2026): no distribuidor a coluna mostra o kg/R$ por loja USADO no potencial (media truncada
            # no P99 ou media do canal abaixo do minimo de lojas, RN-34); nos niveis acima segue a media simples do nivel (volume ÷ lojas),
            # rotulada "media do nivel" no painel — o potencial desses niveis e a soma dos distribuidores
            usado = grao.assign(_d=grao["DIST"].astype(str), _c=grao["CAT"].astype(str)).set_index(["_d", "_c"])
            ix = pd.MultiIndex.from_arrays([m["DIST"].astype(str), m["CAT"].astype(str)])
            m["kg_loja"] = pd.to_numeric(usado["kg_loja"], errors="coerce").reindex(ix).to_numpy(dtype=float)
            m["rs_loja"] = pd.to_numeric(usado["rs_loja"], errors="coerce").reindex(ix).to_numpy(dtype=float)
        m["NIVEL"] = nivel
        m["K1"] = m[G[0]].astype(str) if G else ""
        m["K2"] = m[G[1]].astype(str) if len(G) > 1 else ""
        partes.append(m.drop(columns=[g for g in G]))
    NC = pd.concat(partes, ignore_index=True)
    NC["CAT"] = NC["CAT"].astype(str)
    NC = NC[["NIVEL", "K1", "K2", "CAT", "lojas", "positivados_nivel", "penetracao", "pct_cobertura", "benchmark", "pct_bench", "cor",
             "a_positivar", "kg_loja", "rs_loja", "fator", "potencial_t", "potencial_rs", "regime_t", "regime_rs", "n_dist", "n_media_canal"]]

    # ---- F7 (RN-32, RN-33): ativacao e recorrencia por nivel x categoria, na janela que termina no mes fechado
    AR = _ativacao_recorrencia(c, mp)
    jan_ar, jan_ar_ly = AR.attrs["janela"], AR.attrs["janela_ly"]
    NC = NC.merge(AR, on=["NIVEL", "K1", "K2", "CAT"], how="left")
    # categoria sem comprador na janela no nivel: a ativar = base inteira, recorrencia indefinida
    if NC["base_elegivel"].isna().any():
        base_by = AR.drop_duplicates(["NIVEL", "K1", "K2"]).set_index(["NIVEL", "K1", "K2"])["base_elegivel"]
        falt = NC["base_elegivel"].isna()
        NC.loc[falt, "base_elegivel"] = [base_by.get((a, b_, c_)) for a, b_, c_ in zip(NC.loc[falt, "NIVEL"], NC.loc[falt, "K1"], NC.loc[falt, "K2"])]
        for col in ("compradores_janela", "compradores_mes", "sem_compra_mes"):
            NC.loc[falt, col] = 0
        NC.loc[falt, "a_ativar"] = NC.loc[falt, "base_elegivel"]
        NC.loc[falt, "pct_compradores"] = 0.0; NC.loc[falt, "pct_a_ativar"] = 100.0
    # ---- por nivel: categorias por loja (PDV conta uma vez no nivel), somas das foco e das 10, maior oportunidade (foco)
    def _cpl(G):
        if G:
            return pos_m.groupby(G + ["COD_PDV"])["CAT"].nunique().groupby(G).mean()
        return float(pos_m.groupby("COD_PDV")["CAT"].nunique().mean())
    rows = []
    for nivel, (G, cubo, grao) in niveis.items():
        cpl = _cpl(G)
        sub = NC[NC["NIVEL"] == nivel]
        for (k1, k2), g in sub.groupby(["K1", "K2"]):
            key = tuple(x for x in (k1, k2) if x != "")
            if G == ["SEG", "SUP"] or G == ["SEG", "CLUSTER"]:
                cp = cpl.get(key)
            elif G:
                cp = cpl.get(key[0])
            else:
                cp = cpl
            gf = g[g["CAT"].isin(foco)]
            best = gf.sort_values("potencial_t", ascending=False).iloc[0] if len(gf) and gf["potencial_t"].notna().any() else None
            rows.append({"NIVEL": nivel, "K1": k1, "K2": k2, "positivados": int(g["positivados_nivel"].max()),
                         "categorias_por_loja": _f(cp), "n_categorias": len(cats),
                         "a_pos_foco": _f(_sum1(gf["a_positivar"])), "pot_foco_t": _f(_sum1(gf["potencial_t"])), "pot_foco_rs": _f(_sum1(gf["potencial_rs"])),
                         "reg_foco_t": _f(_sum1(gf["regime_t"])), "reg_foco_rs": _f(_sum1(gf["regime_rs"])),
                         "a_pos_total": _f(_sum1(g["a_positivar"])), "pot_total_t": _f(_sum1(g["potencial_t"])), "pot_total_rs": _f(_sum1(g["potencial_rs"])),
                         # F7: positivacoes a ativar (janela) e sem compra no mes (recorrencia), somadas nas foco e nas 10
                         "a_ativar_foco": _f(_sum1(gf["a_ativar"])), "sem_compra_foco": _f(_sum1(gf["sem_compra_mes"])),
                         "a_ativar_total": _f(_sum1(g["a_ativar"])), "sem_compra_total": _f(_sum1(g["sem_compra_mes"])),
                         "base_elegivel": _f(g["base_elegivel"].max()),
                         "reg_total_t": _f(_sum1(g["regime_t"])), "reg_total_rs": _f(_sum1(g["regime_rs"])),
                         "maior_cat": None if best is None else str(best["CAT"]), "maior_pen": None if best is None else _f(best["penetracao"]),
                         "maior_bench": None if best is None else _f(best["benchmark"]), "maior_pot_t": None if best is None else _f(best["potencial_t"]),
                         "maior_pot_rs": None if best is None else _f(best["potencial_rs"])})
    NL = pd.DataFrame(rows)

    # ---- mascara PDV x categoria (RN-38): medir (bits = comprou a categoria na janela da base ativa), sem embutir
    PC = CFG["painel"].get("pdv_categoria") or {}
    pb = T["DN_PDV_BASE_ATIVA"][["DIST", "COD_PDV"]]
    i_ref = meses.index(mes_ref)
    jan = meses[max(0, i_ref - JANELA + 1): i_ref + 1]
    fj = f[(f["PESO_KG"] > 0) & f["ANO_MES"].isin(jan)][["DIST", "COD_PDV", "CAT"]].drop_duplicates()
    ci = {cat: k for k, cat in enumerate(cats)}
    fj = fj[fj["CAT"].isin(ci)].copy()
    fj["v"] = fj["CAT"].astype(object).map(ci).map(lambda k: 1 << int(k))   # P1: .astype(object) — CAT e categoria
    mk = fj.groupby(["DIST", "COD_PDV"])["v"].sum().rename("mascara").reset_index()
    # F7 (RN-38, Q-c): bits 10..19 = comprou a categoria no mes de referencia; flag "novo na janela" (PRIMEIRO_MES, A.6)
    fmr = f[(f["PESO_KG"] > 0) & (f["ANO_MES"] == mes_ref)][["DIST", "COD_PDV", "CAT"]].drop_duplicates()
    fmr = fmr[fmr["CAT"].isin(ci)].copy()
    fmr["v"] = fmr["CAT"].astype(object).map(ci).map(lambda k: 1 << (int(k) + len(cats)))
    mm_ = fmr.groupby(["DIST", "COD_PDV"])["v"].sum().rename("mascara_mes").reset_index()
    MASK = pb.merge(mk, on=["DIST", "COD_PDV"], how="left").merge(mm_, on=["DIST", "COD_PDV"], how="left")
    MASK["mascara_janela"] = MASK["mascara"].fillna(0).astype("int64")
    MASK["mascara"] = (MASK["mascara"].fillna(0).astype("int64") + MASK["mascara_mes"].fillna(0).astype("int64")).astype("int64")
    MASK = MASK.drop(columns=["mascara_mes"])
    prim = c["pdv"].set_index("COD_PDV")["PRIMEIRO_MES"] if "PRIMEIRO_MES" in c["pdv"].columns else None
    MASK["novo"] = MASK["COD_PDV"].map(prim).isin(jan).astype(bool) if prim is not None else False
    raw = json.dumps(MASK["mascara"].tolist(), separators=(",", ":")).encode("utf-8")
    b64 = base64.b64encode(gzip.compress(raw, compresslevel=9))
    lim = float(PC.get("limite_mb", 1))
    META = pd.DataFrame([{"mes_fechado": mp, "mes_referencia": mes_ref, "n_categorias": len(cats), "categorias": ",".join(cats),
                          "mascara_bits": 2 * len(cats), "janela_ativacao": f"{jan_ar[0]} a {jan_ar[-1]}", "janela_ativacao_ly": (f"{jan_ar_ly[0]} a {jan_ar_ly[-1]}" if jan_ar_ly else ""),
                          "percentil": pctl, "minimo_observacoes": min_obs, "janela_fator_meses": janela_f, "janela_fator": f"{jan_f[0]} a {jan_f[-1]}",
                          "minimo_lojas": min_lojas, "p_outliers": p_out, "verde": verde, "vermelho": vermelho, "foco": ",".join(foco),
                          "mascara_pares": int(len(MASK)), "mascara_bytes_json": int(len(raw)), "mascara_bytes_b64": int(len(b64)),
                          "mascara_mb": len(b64) / 1024 / 1024, "mascara_limite_mb": lim, "mascara_config": str(PC.get("embutir_mascara", "medir")),
                          "mascara_cabe": bool(len(b64) / 1024 / 1024 <= lim)}])
    log(f"penetracao ({mp}): benchmark P{pctl:g} em {len(cats)} categorias · {len(DC):,} linhas distribuidor x categoria · "
        f"{len(DCL):,} distribuidor x cluster x categoria · {len(NC):,} nivel x categoria · {len(NL)} niveis", "ok")
    log("fator observado (" + f"{jan_f[0]} a {jan_f[-1]}" + "): " + " · ".join(f"{cat} {fator[cat]*100:.0f}% ({int(n_novas.get(cat, 0))} lojas novas)" if fator.get(cat) is not None else f"{cat} —" for cat in cats), "ok")
    log(f"mascara PDV x categoria (RN-38): {len(MASK):,} pares · {2*len(cats)} bits (janela | mes) · {len(raw)/1024:.0f} KB json · {len(b64)/1024:.0f} KB gzip+base64 = "
        f"{len(b64)/1024/1024:.2f} MB (limite {lim:g} MB; config {PC.get('embutir_mascara', 'medir')})", "ok")
    ac = NC[NC["NIVEL"] == "canal"].set_index("CAT")
    log("ativacao/recorrencia (" + f"{jan_ar[0]} a {jan_ar[-1]}" + "): " + " · ".join(
        f"{cat} a ativar {int(ac.loc[cat, 'a_ativar']):,} · recorrencia {ac.loc[cat, 'recorrencia']:.0f}%" for cat in foco if cat in ac.index)
        + (f" · LY {jan_ar_ly[0]} a {jan_ar_ly[-1]}" if jan_ar_ly else " · sem janela LY na serie"), "ok")
    return {k_: _descat(v_) for k_, v_ in {"DN_PEN_BENCHMARK": BK, "DN_PEN_DIST_CAT": DC, "DN_PEN_DIST_CLUSTER_CAT": DCL,
                                            "DN_PEN_NIVEL_CAT": NC, "DN_PEN_NIVEL": NL, "DN_PEN_META": META,
                                            "DN_PDV_CAT_MASCARA": MASK}.items()}



def _ativacao_recorrencia(c: dict, mp: str) -> pd.DataFrame:
    """F7 (RN-32, RN-33, RN-41): por nivel x categoria, na janela de JANELA meses que termina no mes fechado:
    base elegivel (= base ativa do nivel: PDVs com kg > 0 em >= 1 mes da janela), compradores da categoria na janela,
    a ativar = base − compradores, compradores no mes, recorrencia mensal = mes ÷ janela, sem compra no mes, distribuicao
    de frequencia (meses com compra da categoria, 1..JANELA) e media, recorrencia no mesmo mes LY quando a janela LY existe.
    PDV conta uma vez no nivel (canal, segmento, supervisor, cluster); no distribuidor conta o par.
    P3 (Etapa 1): parte da tabela de pares mes x distribuidor x PDV x categoria (codigos), nao das linhas da fato; a
    distribuicao de frequencia sai de uma contagem de valores em vez de seis agregacoes por grupo. Mesmos numeros."""
    meses, cal, cats = c["meses"], c["cal"], c["cats"]
    i = meses.index(mp)
    jan = meses[max(0, i - JANELA + 1): i + 1]
    ly_am = cal.set_index("ANO_MES")["ANO_MES_LY"].get(mp)
    jan_ly = None
    if ly_am is not None and not pd.isna(ly_am) and ly_am in meses:
        j = meses.index(ly_am); cand = meses[max(0, j - JANELA + 1): j + 1]
        if len(cand) == JANELA:
            jan_ly = cand
    niveis = {"canal": ["CANAL"], "segmento": ["SEG"], "supervisor_canal": ["SUP"], "supervisor": ["SEG", "SUP"],
              "cluster_canal": ["CLUSTER"], "cluster": ["SEG", "CLUSTER"], "distribuidor": ["DIST"]}
    pos = c["pares_cat"].assign(CANAL=0)

    def _bloco(janela, mes, sufixo):
        fj = pos[pos["ANO_MES"].isin([meses.index(m_) for m_ in janela])]
        mes_i = meses.index(mes)
        partes = []
        for nivel, G in niveis.items():
            fg = _sem_nulos(fj, [g_ for g_ in G if g_ != "CANAL"])
            base = fg[G + ["COD_PDV"]].drop_duplicates().groupby(G, sort=True).size().rename("base_elegivel")
            pcm = _sem_nulos(fg[G + ["COD_PDV", "CAT", "ANO_MES"]], ["CAT"]).drop_duplicates()   # PDV conta uma vez no nivel
            comp_j = pcm[G + ["COD_PDV", "CAT"]].drop_duplicates().groupby(G + ["CAT"], sort=True).size().rename("compradores_janela")
            comp_m = pcm[pcm["ANO_MES"] == mes_i][G + ["COD_PDV", "CAT"]].drop_duplicates().groupby(G + ["CAT"], sort=True).size().rename("compradores_mes")
            fq = pcm.groupby(G + ["COD_PDV", "CAT"], sort=True).size().rename("n").reset_index()
            gq = fq.groupby(G + ["CAT"], sort=True)["n"]
            dist = gq.mean().rename("meses_medios").to_frame()
            vc = gq.value_counts().unstack(fill_value=0)
            for k in range(1, JANELA + 1):
                dist[f"freq_{k}"] = vc[k].astype(int).reindex(dist.index).to_numpy() if k in vc.columns else 0
            m = pd.concat([comp_j, comp_m, dist], axis=1).reset_index()
            m = m.merge(base.reset_index(), on=G, how="left")
            m["NIVEL"] = nivel
            m["K1"] = "" if nivel == "canal" else cats[G[0]][m[G[0]].to_numpy()].astype(str)
            m["K2"] = cats[G[1]][m[G[1]].to_numpy()].astype(str) if len(G) > 1 else ""
            m["CAT"] = cats["CAT"][m["CAT"].to_numpy()]
            partes.append(m.drop(columns=G))
        out = pd.concat(partes, ignore_index=True)
        out["CAT"] = out["CAT"].astype(str)
        out["compradores_mes"] = out["compradores_mes"].fillna(0).astype(int)
        out["compradores_janela"] = out["compradores_janela"].astype(int)
        out["a_ativar"] = out["base_elegivel"] - out["compradores_janela"]
        out["pct_compradores"] = out["compradores_janela"] / out["base_elegivel"] * 100
        out["pct_a_ativar"] = out["a_ativar"] / out["base_elegivel"] * 100
        out["recorrencia"] = out["compradores_mes"] / out["compradores_janela"].replace(0, np.nan) * 100
        out["sem_compra_mes"] = out["compradores_janela"] - out["compradores_mes"]
        if sufixo:
            out = out[["NIVEL", "K1", "K2", "CAT", "recorrencia"]].rename(columns={"recorrencia": "recorrencia" + sufixo})
        return out

    A = _bloco(jan, mp, "")
    if jan_ly is not None:
        A = A.merge(_bloco(jan_ly, ly_am, "_ly"), on=["NIVEL", "K1", "K2", "CAT"], how="left")
    else:
        A["recorrencia_ly"] = np.nan
    A.attrs["janela"] = jan; A.attrs["janela_ly"] = jan_ly
    return A

def _f(v):
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    return float(v)

def pdvs_base_ativa(f: pd.DataFrame, meses: list[str], mes_ref: str) -> pd.DataFrame:
    """Um registro por distribuidor × PDV da base ativa do mês de referência
    (positivado em algum mês da janela), com a leitura de oportunidade:
    positivou no mês? no mês anterior? quantos meses na janela? último mês e
    kg do último mês? kg na janela? E, desde a F1 (RN-06), o R$ do sell-through
    nas mesmas linhas: rs_mes, rs_ultimo_mes, rs_janela."""
    i = meses.index(mes_ref)
    if i < JANELA - 1:
        abortar(f"o mes de referencia {mes_ref} nao tem janela de {JANELA} meses completa")
    jan = meses[i - JANELA + 1:i + 1]
    pos = f[(f["PESO_KG"] > 0) & f["ANO_MES"].isin(jan)]
    # F1 (RN-06): o R$ (sell-through) e somado nas MESMAS linhas do kg (kg > 0), por par e mes
    m = pos.groupby(["DIST", "COD_PDV", "ANO_MES"])[["PESO_KG", "RECEITA"]].sum().reset_index()
    g = m.groupby(["DIST", "COD_PDV"])
    out = g.agg(meses_positivado_janela=("ANO_MES", "nunique"), ultimo_mes_compra=("ANO_MES", "max"),
                kg_janela=("PESO_KG", "sum"), rs_janela=("RECEITA", "sum")).reset_index()
    ult = m.merge(out[["DIST", "COD_PDV", "ultimo_mes_compra"]], on=["DIST", "COD_PDV"])
    ult = (ult[ult["ANO_MES"] == ult["ultimo_mes_compra"]][["DIST", "COD_PDV", "PESO_KG", "RECEITA"]]
           .rename(columns={"PESO_KG": "kg_ultimo_mes", "RECEITA": "rs_ultimo_mes"}))
    out = out.merge(ult, on=["DIST", "COD_PDV"], how="left")
    atual = (m[m["ANO_MES"] == mes_ref][["DIST", "COD_PDV", "PESO_KG", "RECEITA"]]
             .rename(columns={"PESO_KG": "kg_mes", "RECEITA": "rs_mes"}))
    out = out.merge(atual, on=["DIST", "COD_PDV"], how="left")
    # 22/09/2026 (Douglas): o minimo de atendimentos por PDV no mes (RN-58, decisao 2, coluna nf_min_mes) saiu do blob; NF_MIN segue nos cubos
    out["positivado_mes"] = out["kg_mes"].notna()
    ant = set(map(tuple, m.loc[m["ANO_MES"] == meses[i - 1], ["DIST", "COD_PDV"]].values)) if i >= 1 else set()
    out["positivado_mes_anterior"] = [(a, b) in ant for a, b in zip(out["DIST"], out["COD_PDV"])]
    ly_m = f"{int(mes_ref[:4]) - 1}-{mes_ref[5:7]}"
    if ly_m in meses:
        ly_pos = f[(f["PESO_KG"] > 0) & (f["ANO_MES"] == ly_m)][["DIST", "COD_PDV"]].drop_duplicates()
        lys = set(map(tuple, ly_pos.values))
        out["positivado_mesmo_mes_ly"] = [(a, b) in lys for a, b in zip(out["DIST"], out["COD_PDV"])]
    else:
        out["positivado_mesmo_mes_ly"] = None
    out["ANO_MES"] = mes_ref
    return _descat(out)


# =============================================================================
# cálculo completo
# =============================================================================
# =============================================================================
# RTM · aderência ao direcionamento
# =============================================================================
# Cliente que era atendido pela Dori e passou a ser atendido por um distribuidor.
# A régua (decisão de 09/09/2026): aderiu quem comprou DO DESTINO do de-para.
# Comprar de outro distribuidor é vazamento, medido à parte e nunca somado.
#
# O universo é a BASE RTM inteira (DIM_RTM), não a fato: cliente que nunca
# comprou de ninguém não existe na fato e é exatamente o caso que interessa.
#
# Destino sem nenhum CNPJ entre os distribuidores do painel entra como SEM
# COBERTURA e fica fora do denominador: não se sabe se comprou, e chamar isso
# de "não comprou" seria afirmar o que o dado não diz.
def rtm_aderencia(c: dict) -> dict:
    """Aderencia RTM (Fase 4): destino resolvido por CNPJ quando a base traz, senao por nome;
    tres motivos de 'destino nao mensuravel'; estado de cada cliente em cada mes (DN_RTM_CLIENTE_MES)
    com quem o atendeu; ativacao em duas reguas (historico completo e a partir da migracao)."""
    f, d, meses, mes_ref = c["fato"], c["dist"], c["meses"], c["mes_ref"]
    base = parquet.carregar("DIM_RTM").drop_duplicates("COD_PDV").copy()     # D2: da curated, nunca do Excel
    dim_all = parquet.carregar("DIM_DISTRIBUIDOR")
    corte = str(CFG["regras"]["rtm"]["data_migracao"])[:7]                   # AAAA-MM
    nome_por_cnpj = dict(zip(dim_all["CNPJ_DISTRIBUIDOR"], dim_all["NOME_REDUZIDO"]))

    # ---- destino: por codigo do distribuidor (13/09/2026, decisao 8b), por CNPJ (quando existe) ou por nome
    base["DESTINO"] = base["DISTRIBUIDOR_RTM"]
    base["DESTINO_POR_CHAVE"] = True
    base["FILIAL_DESTINO"] = pd.Series(pd.NA, index=base.index, dtype="string")   # 02/10/2026: CNPJ da filial apontada pela chave
    if str(CFG["regras"].get("rtm_destino_chave", "nome")) == "codigo":
        # Cod. Cliente [Distribuidor] -> filial no de-para -> nome reduzido do de-para; "do destino" segue valendo para qualquer
        # filial desse nome (RN-52). Sem codigo ou codigo fora do de-para = destino sem cadastro (nao mensuravel), mesmo que o nome case.
        if "COD_CLIENTE_DISTRIBUIDOR_RTM" not in base.columns:
            abortar("regras.rtm_destino_chave = codigo, mas a base RTM nao traz 'Cód. Cliente [Distribuidor]'")
        cod2nome = dim_all.dropna(subset=["COD_CLIENTE"]).drop_duplicates("COD_CLIENTE").set_index("COD_CLIENTE")["NOME_REDUZIDO"]
        nome_cod = base["COD_CLIENTE_DISTRIBUIDOR_RTM"].map(cod2nome)
        dif = nome_cod.notna() & base["DISTRIBUIDOR_RTM"].notna() & (nome_cod != base["DISTRIBUIDOR_RTM"])
        if dif.any() and not c.get("recorte"):   # Etapa 2: aviso do canal, nao repetido em cada usuario
            ex = base.loc[dif, ["DISTRIBUIDOR_RTM"]].assign(DE_PARA=nome_cod[dif]).drop_duplicates().head(5).values.tolist()
            log(f"RTM: {int(dif.sum())} cliente(s) com nome do destino na planilha diferente do nome reduzido do código no de-para "
                f"(vale o código): {ex}", "aviso")
        base["DESTINO"] = nome_cod.where(nome_cod.notna(), base["DISTRIBUIDOR_RTM"])
        base["DESTINO_POR_CHAVE"] = nome_cod.notna()
        # 02/10/2026 (Douglas): a filial do codigo define o supervisor do destino; codigo repetido no de-para seria desempate
        cods = dim_all.dropna(subset=["COD_CLIENTE"])
        rep = sorted(set(cods.loc[cods["COD_CLIENTE"].duplicated(), "COD_CLIENTE"]) & set(base["COD_CLIENTE_DISTRIBUIDOR_RTM"].dropna()))
        if rep:
            abortar(f"RTM: Cód. Cliente [Distribuidor] com mais de uma filial no de-para (filial do destino ambigua): {rep[:10]}")
        base["FILIAL_DESTINO"] = base["COD_CLIENTE_DISTRIBUIDOR_RTM"].map(cods.drop_duplicates("COD_CLIENTE").set_index("COD_CLIENTE")["CNPJ_DISTRIBUIDOR"]).astype("string")
        log(f"RTM: destino pelo código do distribuidor em {int(nome_cod.notna().sum())} cliente(s); "
            f"{int(nome_cod.isna().sum())} sem código ou com código fora do de-para (destino sem cadastro)", "ok")
    if "CNPJ_DESTINO" in base.columns and base["CNPJ_DESTINO"].notna().any():
        m = base["CNPJ_DESTINO"].map(nome_por_cnpj)
        base.loc[m.notna(), "DESTINO"] = m[m.notna()]
        base.loc[m.notna(), "DESTINO_POR_CHAVE"] = True
        base.loc[m.notna(), "FILIAL_DESTINO"] = base.loc[m.notna(), "CNPJ_DESTINO"].astype("string")
        ruim = base["CNPJ_DESTINO"].notna() & m.isna()
        log(f"RTM: destino resolvido por CNPJ em {int(m.notna().sum())} cliente(s); "
            f"{int(ruim.sum())} CNPJ(s) de destino fora do de-para (ficam pelo nome)", "aviso" if ruim.any() else "ok")

    # ---- cobertura e motivo (P2): painel = tem hierarquia E sell-out; as tres causas de nao mensuravel
    cnpjs = d.groupby("NOME_REDUZIDO")["CNPJ_DISTRIBUIDOR"].apply(lambda s_: set(s_)).to_dict()
    nomes_depara = set(dim_all["NOME_REDUZIDO"].dropna())
    nomes_no_painel = set(dim_all.loc[dim_all["NO_PAINEL"], "NOME_REDUZIDO"].dropna())

    def motivo(nome):
        if nome in cnpjs:
            return None
        if nome not in nomes_depara:
            return "sem_cadastro"
        if nome not in nomes_no_painel:
            return "fora_do_painel"
        return "sem_sellout"

    if c.get("recorte"):
        # Etapa 2 (Q2, aprovada 16/09/2026): no painel de um usuario entram so os clientes cujo destino, pela chave, e um
        # distribuidor do recorte; os sem destino cadastrado ficam so no painel do canal
        # 02/10/2026: pela FILIAL do codigo (antes: pelo nome do grupo, que trazia clientes de filiais de outro supervisor)
        base = base[base["DESTINO_POR_CHAVE"].astype(bool) & base["FILIAL_DESTINO"].isin(set(d["CNPJ_DISTRIBUIDOR"].astype(str)))].copy()
    base["MOTIVO"] = base["DESTINO"].map(motivo)
    base.loc[~base["DESTINO_POR_CHAVE"].astype(bool), "MOTIVO"] = "sem_cadastro"   # decisao 8b: sem chave = sem cadastro
    base["COBERTO"] = base["MOTIVO"].isna()
    # D18 revista (13/09/2026) e 02/10/2026 (Douglas): supervisor do destino = supervisor da FILIAL apontada pelo codigo,
    # nao do grupo de filiais com o mesmo nome reduzido (a CHUA passou a ter filiais de dois supervisores). "Atendeu certo"
    # continua valendo para qualquer filial do nome (RN-52). Cliente coberto sem filial no painel aborta: nada e inferido.
    sup_filial = dict(zip(d["CNPJ_DISTRIBUIDOR"].astype(str), d["SUP_ID"]))
    base["SUP_DESTINO"] = base["FILIAL_DESTINO"].map(sup_filial).where(base["COBERTO"])
    sem_sup = base["COBERTO"] & base["SUP_DESTINO"].isna()
    if sem_sup.any():
        ex = base.loc[sem_sup, ["COD_PDV", "DESTINO", "FILIAL_DESTINO"]].head(5).values.tolist()
        abortar(f"RTM (RN-44): {int(sem_sup.sum())} cliente(s) com destino mensuravel cuja filial do codigo nao esta no painel "
                f"— supervisor do destino indefinido: {ex}")
    nm = base[~base["COBERTO"]].groupby(["DESTINO", "MOTIVO"]).size()
    if len(nm):
        log("RTM: destinos nao mensuraveis — " + " · ".join(f"{k[0]} ({k[1]}: {v})" for k, v in nm.items()), "aviso")

    # ---- compras dos clientes RTM, por mes x cliente x distribuidor
    alvo = set(base["COD_PDV"])
    compras = (f[f["COD_PDV"].isin(alvo)].groupby(["ANO_MES", "COD_PDV", "DIST"], observed=True)[["PESO_KG", "RECEITA"]]
                .sum().reset_index())
    destino_de = dict(zip(base["COD_PDV"], base["DESTINO"]))
    compras["CERTO"] = [d_ in cnpjs.get(destino_de.get(p_, ""), ()) for p_, d_ in zip(compras["COD_PDV"], compras["DIST"])]
    compras["ROT"] = [f"{nome_por_cnpj.get(x, x)} ({x})" for x in compras["DIST"]]
    for col, base_col, cond in (("kg_certo", "PESO_KG", True), ("kg_outro", "PESO_KG", False),
                                ("rs_certo", "RECEITA", True), ("rs_outro", "RECEITA", False)):
        compras[col] = compras[base_col].where(compras["CERTO"] == cond, 0.0)
    compras["_certo_rot"] = compras["ROT"].where(compras["CERTO"], None)
    compras["_outro_rot"] = [(f"{r}={kg:.1f}" if not c_ else None) for r, kg, c_ in zip(compras["ROT"], compras["PESO_KG"], compras["CERTO"])]
    mc = (compras.groupby(["ANO_MES", "COD_PDV"], observed=True)
                 .agg(certo=("CERTO", "max"), outro=("CERTO", lambda s_: bool((~s_).any())),
                      kg_certo=("kg_certo", "sum"), kg_outro=("kg_outro", "sum"),
                      rs_certo=("rs_certo", "sum"), rs_outro=("rs_outro", "sum"),
                      ATENDEU_CERTO=("_certo_rot", lambda s_: "; ".join(sorted(x for x in s_ if isinstance(x, str) and x))),
                      OUTROS=("_outro_rot", lambda s_: "; ".join(sorted(x for x in s_ if isinstance(x, str) and x))))
                 .reset_index())
    mc["certo"] = mc["certo"].astype(bool)
    mc["outro"] = mc["outro"].astype(bool)

    # ---- grade cliente x mes (DN_RTM_CLIENTE_MES)
    grade = pd.MultiIndex.from_product([meses, sorted(alvo)], names=["ANO_MES", "COD_PDV"]).to_frame(index=False)
    grade = grade.merge(mc, on=["ANO_MES", "COD_PDV"], how="left")
    for col in ("kg_certo", "kg_outro", "rs_certo", "rs_outro"):
        grade[col] = grade[col].fillna(0.0)
    grade["certo"] = grade["certo"].fillna(False).astype(bool)
    grade["outro"] = grade["outro"].fillna(False).astype(bool)
    grade["ATENDEU_CERTO"] = grade["ATENDEU_CERTO"].fillna("")
    grade["OUTROS"] = grade["OUTROS"].fillna("")
    coberto_de = dict(zip(base["COD_PDV"], base["COBERTO"]))
    grade["COBERTO"] = grade["COD_PDV"].map(coberto_de).astype(bool)
    grade["ESTADO"] = np.select([~grade["COBERTO"], grade["certo"], grade["outro"]],
                                ["nao_mensuravel", "certo", "so_outro"], default="sem_compra")
    grade = grade.sort_values(["COD_PDV", "ANO_MES"]).reset_index(drop=True)
    comprou = grade["certo"] | grade["outro"]
    grade["ULTIMO_MES_COMPRA"] = grade["ANO_MES"].where(comprou)
    grade["ULTIMO_MES_COMPRA"] = grade.groupby("COD_PDV")["ULTIMO_MES_COMPRA"].ffill()

    # ---- ativacao: historico completo (1o mes certo da serie) e a partir da migracao (1o mes certo >= corte)
    certo_m = grade[grade["certo"]]
    ativ_h = certo_m.groupby("COD_PDV")["ANO_MES"].min().rename("MES_ATIVACAO_HIST")
    ativ_m = certo_m[certo_m["ANO_MES"] >= corte].groupby("COD_PDV")["ANO_MES"].min().rename("MES_ATIVACAO_MIG")
    # dtype "string" explicito: sem ativacao nenhuma (caso da regua de migracao hoje) o map devolveria float64 so de NaN
    base["MES_ATIVACAO_HIST"] = base["COD_PDV"].map(ativ_h).astype("string")
    base["MES_ATIVACAO_MIG"] = base["COD_PDV"].map(ativ_m).astype("string")
    base["ATIVADO_HIST"] = base["MES_ATIVACAO_HIST"].notna()
    base["ATIVADO_MIG"] = base["MES_ATIVACAO_MIG"].notna()
    base["ATIVADO"] = base["ATIVADO_HIST"]                                   # compatibilidade (regua historica)
    base["MES_ATIVACAO"] = base["MES_ATIVACAO_HIST"]

    cob_set = set(base.loc[base["COBERTO"], "COD_PDV"])
    n_cob, n_sem = len(cob_set), int((~base["COBERTO"]).sum())

    # ---- serie mensal do canal (so mensuraveis) com ativados acumulados nas duas reguas; D18 revista: a mesma serie por
    #      supervisor do destino (DN_RTM_SUP_MES) — os mensuraveis de cada supervisor somam o canal
    def _serie_rtm(clientes: set, extra: dict) -> list[dict]:
        n_c = len(clientes); bb = base[base["COD_PDV"].isin(clientes)]
        out_l = []
        for m in meses:
            gm = grade[(grade["ANO_MES"] == m) & grade["COD_PDV"].isin(clientes)]
            certo = int(gm["certo"].sum()); outro = int((gm["outro"] & ~gm["certo"]).sum())
            ah = int((bb["MES_ATIVACAO_HIST"] <= m).fillna(False).sum())
            am = int((bb["MES_ATIVACAO_MIG"] <= m).fillna(False).sum()) if m >= corte else 0
            out_l.append({**extra, "ANO_MES": m, "base_rtm": n_c, "certo": certo, "so_outro": outro,
                          "sem_compra": n_c - certo - outro, "nao_mensuravel": n_sem,
                          "pct_aderencia": certo / n_c * 100 if n_c else None,
                          "kg_certo": float(gm["kg_certo"].sum()), "kg_outro": float(gm["kg_outro"].sum()),
                          "rs_certo": float(gm["rs_certo"].sum()), "rs_outro": float(gm["rs_outro"].sum()),
                          "ativados_hist": ah, "ativados_parados_hist": max(ah - certo, 0),
                          "ativados_mig": am, "ativados_parados_mig": max(am - certo, 0) if m >= corte else 0,
                          "desde_migracao": m >= corte})
        return out_l
    serie = pd.DataFrame(_serie_rtm(cob_set, {}))
    sup_linhas = []
    for sup_id, gsup in base[base["COBERTO"]].groupby("SUP_DESTINO"):
        sup_linhas += _serie_rtm(set(gsup["COD_PDV"]), {"SUP": sup_id})
    serie_sup = pd.DataFrame(sup_linhas)

    # ---- por cliente no mes de referencia
    mref = grade[grade["ANO_MES"] == mes_ref].set_index("COD_PDV")
    for col in ("certo", "outro"):
        base[col] = base["COD_PDV"].map(mref[col]).fillna(False).astype(bool)
    base["so_outro"] = base["outro"] & ~base["certo"]
    for col in ("kg_certo", "kg_outro", "rs_certo", "rs_outro"):
        base[col] = base["COD_PDV"].map(mref[col]).fillna(0.0)
    for col in ("ATENDEU_CERTO", "OUTROS", "ULTIMO_MES_COMPRA", "ESTADO"):
        base[col] = base["COD_PDV"].map(mref[col])
    nome_pdv = c["pdv"].set_index("COD_PDV")["NOME_PDV"]
    base["NOME_MTRIX"] = base["COD_PDV"].map(nome_pdv)

    # ---- por destino
    dest = (base.groupby(["DESTINO", "COBERTO"], dropna=False)
                .agg(clientes=("COD_PDV", "size"), certo=("certo", "sum"), so_outro=("so_outro", "sum"),
                     ativados=("ATIVADO_HIST", "sum"), ativados_mig=("ATIVADO_MIG", "sum"),
                     kg_certo=("kg_certo", "sum"), kg_outro=("kg_outro", "sum"),
                     rs_certo=("rs_certo", "sum"), rs_outro=("rs_outro", "sum"),
                     MOTIVO=("MOTIVO", "first"))
                .reset_index())
    dest["sem_compra"] = dest["clientes"] - dest["certo"] - dest["so_outro"]
    dest["pct_aderencia"] = np.where(dest["COBERTO"], dest["certo"] / dest["clientes"] * 100, np.nan)
    dest.loc[~dest["COBERTO"], ["certo", "so_outro", "sem_compra", "ativados", "ativados_mig",
                                "kg_certo", "kg_outro", "rs_certo", "rs_outro"]] = np.nan
    dest = dest.sort_values(["COBERTO", "clientes"], ascending=[False, False]).reset_index(drop=True)

    r = serie[serie["ANO_MES"] == mes_ref].iloc[0]
    log(f"RTM {mes_ref}: {n_cob} cliente(s) mensuraveis · {int(r['certo'])} compraram do destino "
        f"({float(r['pct_aderencia'] or 0):.1f}%) · {int(r['so_outro'])} so de outro · {int(r['sem_compra'])} de ninguem · "
        f"{n_sem} com destino nao mensuravel", "ok")
    log(f"RTM ativacao: {int(base['ATIVADO_HIST'].sum())} (historico) · {int(base['ATIVADO_MIG'].sum())} "
        f"(desde {corte}) de {len(base)} cliente(s) · grade cliente x mes: {len(grade):,} linhas", "ok")
    return {k_: _descat(v_) for k_, v_ in {"DN_RTM_MES": serie, "DN_RTM_DESTINO": dest, "DN_RTM_CLIENTE": base,
                                            "DN_RTM_CLIENTE_MES": grade, "DN_RTM_SUP_MES": serie_sup}.items()}


def carteira(c: dict, pb: pd.DataFrame) -> pd.DataFrame:
    """RN-56 · classifica cada linha da planilha ponderada pela regra de CNPJ (Q2–Q5) e grava o relatorio das linhas fora.

    Entra a linha cujo distribuidor esta no de-para e no painel, cujo PDV existe na Mtrix (e nao e CNPJ de distribuidor) e
    para o qual esse distribuidor vendeu (kg > 0) em algum mes da serie. Razao social diferente da Mtrix e so aviso. Linha
    fora da regra NAO aborta: vai para o log e para `quality/carteira_pdv.md` com o numero da linha do Excel e o motivo."""
    import re as _re
    import unicodedata as _ud
    from .utils.config import PASTA_CURATED, PASTA_QUALITY
    cols = ["LINHA", "CLUSTER", "CNPJ_DISTRIBUIDOR", "DISTRIBUIDOR_PLANILHA", "COD_PDV", "RAZAO_PLANILHA", "NOME_MTRIX", "VALIDA", "MOTIVO",
            "AVISO_NOME", "SIM_NOME", "MESES_COMPRA", "ULTIMO_MES", "NA_BASE_ATIVA"]
    arq = PASTA_CURATED / "DIM_PDV_PONDERADA.parquet"
    P = pd.read_parquet(arq) if arq.exists() else None
    if P is None or not len(P):
        return pd.DataFrame(columns=cols)
    R = _R.get("carteira") or {}
    validos = [str(x).upper() for x in (R.get("clusters_validos") or ["DESTAQUE", "PRIME"])]
    exige = bool(R.get("exige_compra_na_serie", True)); lim = float(R.get("nome_aviso_minimo", 0.5))
    ign = {str(x).upper() for x in (R.get("nome_palavras_ignoradas") or [])}
    def _s(v):
        return "" if v is None or (not isinstance(v, str) and pd.isna(v)) else str(v)
    def _toks(v):
        t = _ud.normalize("NFKD", _s(v)).encode("ascii", "ignore").decode().upper()
        return {w for w in _re.sub(r"[^A-Z0-9 ]", " ", t).split() if w not in ign and len(w) > 1}
    depara = set(pd.read_parquet(PASTA_CURATED / "DIM_DISTRIBUIDOR.parquet", columns=["CNPJ_DISTRIBUIDOR"])["CNPJ_DISTRIBUIDOR"].astype(str))
    painel = set(c["dist"]["CNPJ_DISTRIBUIDOR"].astype(str))
    pdv = c["pdv"][["COD_PDV", "NOME_PDV"]].copy(); pdv["COD_PDV"] = pdv["COD_PDV"].astype(str)
    nome_pdv = pdv.drop_duplicates("COD_PDV").set_index("COD_PDV")["NOME_PDV"]
    f = c["fato"]; alvo = set(P["COD_PDV"].dropna().astype(str))
    g = f[(f["PESO_KG"] > 0) & f["COD_PDV"].isin(alvo)][["DIST", "COD_PDV", "ANO_MES"]].astype(str)
    comp = {k: (int(v["nunique"]), str(v["max"])) for k, v in g.groupby(["DIST", "COD_PDV"])["ANO_MES"].agg(["nunique", "max"]).iterrows()}
    ativos = set(zip(pb["DIST"].astype(str), pb["COD_PDV"].astype(str)))
    cd_s = P["CNPJ_DISTRIBUIDOR"].map(_s); cp_s = P["COD_PDV"].map(_s); cl_s = P["CLUSTER"].map(_s).str.upper()
    rep = (cd_s + "|" + cp_s).duplicated(keep=False) & (cd_s != "") & (cp_s != "")
    dois = pd.Series(False, index=P.index)
    for _, gi in P.assign(_p=cp_s, _c=cl_s)[cp_s != ""].groupby("_p"):
        if gi["_c"].nunique() > 1:
            dois.loc[gi.index] = True
    out = []
    for i in P.index:
        cd, cp, cl = cd_s[i], cp_s[i], cl_s[i]; mot = []
        if cl not in validos: mot.append(f"cluster '{cl or 'vazio'}' fora de {', '.join(validos)}")
        if not cd: mot.append("sem CNPJ do distribuidor")
        elif cd not in depara: mot.append("distribuidor fora do de-para")
        elif cd not in painel: mot.append("distribuidor fora do painel")
        if not cp: mot.append("sem CNPJ do PDV")
        elif cp in depara: mot.append("CNPJ do PDV é de distribuidor")
        elif cp not in nome_pdv.index: mot.append("PDV não existe na Mtrix")
        elif exige and (cd, cp) not in comp: mot.append("esse distribuidor nunca vendeu para esse PDV na série")
        if rep[i]: mot.append("par repetido na planilha")
        if dois[i]: mot.append("PDV em dois clusters")
        nm = _s(nome_pdv.get(cp)) if cp in nome_pdv.index else ""
        A, B = _toks(P.at[i, "RAZAO_SOCIAL"]), _toks(nm)
        sim = (len(A & B) / len(A | B)) if nm and (A | B) else None
        mc = comp.get((cd, cp))
        out.append({"LINHA": int(P.at[i, "LINHA"]), "CLUSTER": cl, "CNPJ_DISTRIBUIDOR": cd, "DISTRIBUIDOR_PLANILHA": _s(P.at[i, "DISTRIBUIDOR"]),
                    "COD_PDV": cp, "RAZAO_PLANILHA": _s(P.at[i, "RAZAO_SOCIAL"]), "NOME_MTRIX": nm, "VALIDA": not mot, "MOTIVO": "; ".join(mot),
                    "AVISO_NOME": bool(not mot and sim is not None and sim < lim), "SIM_NOME": sim,
                    "MESES_COMPRA": None if mc is None else mc[0], "ULTIMO_MES": None if mc is None else mc[1],
                    "NA_BASE_ATIVA": bool(not mot and (cd, cp) in ativos)})
    K = pd.DataFrame(out, columns=cols)
    K["MESES_COMPRA"] = K["MESES_COMPRA"].astype("Int64"); K["SIM_NOME"] = K["SIM_NOME"].astype(float)
    V = K[K["VALIDA"]]
    log(f"carteira (RN-56): {len(K)} linha(s) · {len(V)} válida(s) (" + ", ".join(f"{k} {v}" for k, v in V["CLUSTER"].value_counts().items())
        + f"; {int(V['NA_BASE_ATIVA'].sum())} na base ativa de {c['mes_ref']}) · {len(K) - len(V)} fora da regra", "ok")
    if c.get("recorte"):   # Etapa 2 (Q5): no recorte, linhas de outros distribuidores sao "fora do painel" por definicao; sem aviso nem relatorio
        return K
    fora = K[~K["VALIDA"]]
    if len(fora):
        ex = fora.assign(M=fora["MOTIVO"].str.split("; ")).explode("M")
        partes = [f"{m} ({len(gm)}): linhas {', '.join(str(x) for x in gm['LINHA'].head(12))}{' …' if len(gm) > 12 else ''}" for m, gm in ex.groupby("M")]
        log("carteira: linhas fora da regra (não abortam; detalhe em quality/carteira_pdv.md) — " + " · ".join(partes), "aviso")
    avn = K[K["AVISO_NOME"]]
    if len(avn):
        log("carteira: razão social diferente da Mtrix, só aviso — " + "; ".join(f"linha {r.LINHA} '{r.RAZAO_PLANILHA}' × Mtrix '{r.NOME_MTRIX}'" for r in avn.itertuples()), "aviso")
    PASTA_QUALITY.mkdir(parents=True, exist_ok=True)
    L_ = ["# Carteira de PDVs ponderados · linhas da planilha (RN-56)", "",
          f"Mês de referência {c['mes_ref']} · {len(K)} linhas · {len(V)} válidas · {len(fora)} fora da regra · {len(avn)} com aviso de nome.", "",
          "Regra: distribuidor no de-para e no painel · PDV existe na Mtrix e não é CNPJ de distribuidor · o distribuidor vendeu para o PDV "
          "em algum mês da série. Linha fora da regra não entra no painel e não trava a execução.", "",
          "| Linha | Cluster | Situação | Motivo / aviso | Razão social (planilha) | Nome na Mtrix | CNPJ distribuidor | CNPJ PDV | Meses com compra | Última compra |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for r in K.sort_values(["VALIDA", "LINHA"]).itertuples():
        sit = "fora" if not r.VALIDA else ("válida" if r.NA_BASE_ATIVA else "válida, fora da base ativa")
        mot = r.MOTIVO or (f"nome diferente ({r.SIM_NOME:.0%})" if r.AVISO_NOME else "")
        L_.append(f"| {r.LINHA} | {r.CLUSTER} | {sit} | {mot} | {r.RAZAO_PLANILHA} | {r.NOME_MTRIX} | {r.CNPJ_DISTRIBUIDOR} | {r.COD_PDV} | "
                  f"{'' if pd.isna(r.MESES_COMPRA) else int(r.MESES_COMPRA)} | {r.ULTIMO_MES or ''} |")
    (PASTA_QUALITY / "carteira_pdv.md").write_text("\n".join(L_) + "\n", encoding="utf-8")
    return K


def calcular(c: dict) -> dict:
    f, cal, meses, mes_ref = c["fato"], c["cal"], c["meses"], c["mes_ref"]
    log(f"mes de referencia {mes_ref} · serie {meses[0]} a {meses[-1]} ({len(meses)} meses) · janela {JANELA} meses")
    out: dict[str, pd.DataFrame] = {}
    preparar_codigos(c)   # P2: pares e base ativa calculados uma vez para todos os niveis
    log(f"pares mes x distribuidor x PDV: {len(c['pares']):,} · x categoria: {len(c['pares_cat']):,} · base ativa de {len(NIVEIS)} niveis", "ok")
    for nome, G in NIVEIS.items():
        s = acumulados(comparativos(serie_nivel(c, G), G, cal), G, cal, meses)   # F5 (RN-25): + ytd civil/fiscal
        out[f"DN_{nome.upper()}_MES"] = s
        log(f"DN_{nome.upper()}_MES: {len(s):,} linhas", "ok")
    # F4 (RN-37, A.13/D20): categoria tambem por supervisor e por cluster — com segmento (tabela da aba
    # "Clusters e supervisores") e no canal (Visao geral filtrada por supervisor; Penetracao na F6)
    for nome, G in (("canal", []), ("segmento", ["SEG"]), ("distribuidor", ["DIST"]),
                    ("supervisor", ["SEG", "SUP"]), ("supervisor_canal", ["SUP"]),
                    ("cluster", ["SEG", "CLUSTER"]), ("cluster_canal", ["CLUSTER"])):
        s = acumulados(comparativos(serie_nivel(c, G, cat=True), G + ["CAT"], cal), G + ["CAT"], cal, meses)
        out[f"DN_{nome.upper()}_CAT_MES"] = s
        log(f"DN_{nome.upper()}_CAT_MES: {len(s):,} linhas", "ok")
    # F5 (RN-25, Q-a): ano a ano — PDVs distintos do periodo, kg e R$ por perspectiva x ano x nivel
    out["DN_ACUM_ANO"] = acum_ano(c)
    log(f"DN_ACUM_ANO: {len(out['DN_ACUM_ANO']):,} linhas (civil + fiscal x anos da serie x niveis)", "ok")
    out.update(rtm_aderencia(c))
    out["DN_PDV_BASE_ATIVA"] = pdvs_base_ativa(f, meses, mes_ref)
    out["DN_PDV_CARTEIRA"] = carteira(c, out["DN_PDV_BASE_ATIVA"])   # RN-56
    log(f"DN_PDV_BASE_ATIVA ({mes_ref}): {len(out['DN_PDV_BASE_ATIVA']):,} pares distribuidor x PDV", "ok")
    out.update(penetracao(c, out))   # F6: benchmark, lojas a positivar, potencial, mascara (mes fechado)
    out["DN_FREQ_CALIBRACAO"] = c["freq_calib"]   # RN-58: alfa do mes e o fechamento com o total da Mtrix
    for nome in out:
        out[nome] = _descat(out[nome])   # P1: os cubos saem em texto, como sempre
    return out
