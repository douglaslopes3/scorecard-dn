# -*- coding: utf-8 -*-
"""Monta o JSON do painel no contrato de `template/data-inventory.json` a partir
das tabelas DN_* da Fase 2. Valores brutos (números); a formatação é de
`render.formatar`. Campos além do inventário (novos na Fase 2) entram com o
mesmo padrão snake_case e ficam disponíveis para a Fase 3 do template.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from . import manifesto, memoria, resumos
from .metrics import JANELA, NOVOS_MESES, SEGMENTOS, SEG_NOMES, SEM_VENDA_MESES, mes_em_andamento, slug
from .transform.calendario import MES_ABREV
from .utils import log as L
from .utils.config import CFG

_P = CFG["painel"]
_ROT = _P["rotulos"]
_EST = dict(_ROT["estados_rtm"])
assert set(_EST) == {"certo", "so_outro", "sem_compra", "nao_mensuravel"}, "painel.rotulos.estados_rtm incompleto"

MET = ["base_ativa", "cobertura_pdv", "pct_cobertura", "volume_t", "kg_pdv", "receita_rs", "rs_pdv", "frequencia"]
VARS = [f"{m}_var_{c}" for m in ("cobertura", "pct_cobertura", "volume", "receita", "frequencia")
        for c in ("mes_anterior", "l3m", "ly")]

# 10/09/2026: a serie EXIBIDA pode ser menor que a calculada (painel.serie_meses_exibidos).
# O calculo, os cards, a base ativa e o LY seguem com TODOS os meses da Mtrix; so as listas
# de serie do painel sao cortadas nos ultimos N meses. null/0 = mostra a serie inteira.
# 13/09/2026 (RN-59, decisao 6 da Etapa 1): com painel.periodo.ativo a serie INTEIRA vai embutida e o seletor "Periodo" do
# navegador escolhe os pontos desenhados; serie_meses_exibidos passa a ser a janela padrao ("Ultimos N meses").
_SERIE_CFG = _P.get("serie_meses_exibidos")
SERIE_EXIBIDA = None if _SERIE_CFG in (None, "", 0) else int(_SERIE_CFG)
_PER = _P.get("periodo") or {}
PERIODO_ATIVO = bool(_PER.get("ativo", False))
JANELA_ARQ = int(_P.get("janela_arquivo_meses") or 0)   # Refino E6: janela movel do arquivo (0 = serie inteira)


def _cortar(serie: list) -> list:
    """Ultimos N meses da serie, quando painel.serie_meses_exibidos esta definido (com o seletor de periodo: a serie inteira)."""
    if PERIODO_ATIVO:
        return serie[-JANELA_ARQ:] if JANELA_ARQ and len(serie) > JANELA_ARQ else serie   # Refino E6: janela movel do arquivo
    if SERIE_EXIBIDA is None or len(serie) <= SERIE_EXIBIDA:
        return serie
    return serie[-SERIE_EXIBIDA:]


# RN-59 (decisao 4 da Etapa 2): serie embutida compacta — chaves curtas, numeros sem aspas, campo nulo omitido. O navegador le
# campo ausente como nulo (dnNum). A ordem das chaves e a mesma do bloco que o template montava campo a campo.
_SERIE_JS = (("m", "mes"), ("ba", "base_ativa"), ("pos", "cobertura_pdv"), ("pba", "cobertura_base_atual"), ("pn", "cobertura_novos"), ("psv", "cobertura_sem_venda"),
             ("pct", "pct_cobertura"), ("ly", "cobertura_ly"), ("vol", "volume_t"), ("rs", "receita_rs"), ("vly", "volume_ly"),
             ("rly", "receita_ly"), ("cv1", "cobertura_var_mes_anterior"), ("cv3", "cobertura_var_l3m"), ("cvy", "cobertura_var_ly"),
             ("pv1", "pct_cobertura_var_mes_anterior"), ("pv3", "pct_cobertura_var_l3m"), ("pvy", "pct_cobertura_var_ly"),
             ("vv1", "volume_var_mes_anterior"), ("vv3", "volume_var_l3m"), ("vvy", "volume_var_ly"),
             ("rv1", "receita_var_mes_anterior"), ("rv3", "receita_var_l3m"), ("rvy", "receita_var_ly"),
             ("ac", "acum_civil_t"), ("acr", "acum_civil_rs"), ("af", "acum_fiscal_t"), ("afr", "acum_fiscal_rs"),
             ("acv", "acum_civil_var_t"), ("acrv", "acum_civil_var_rs"), ("afv", "acum_fiscal_var_t"), ("afrv", "acum_fiscal_var_rs"),
             ("fr", "frequencia"))


def _serie_js(serie: list[dict]) -> str:
    partes = []
    for p in serie:
        campos = []
        for curta, longa in _SERIE_JS:
            v = p.get(longa)
            if v is None or (isinstance(v, float) and v != v):
                continue
            if isinstance(v, float) and v.is_integer():
                v = int(v)
            campos.append(f"{curta}:{json.dumps(v, ensure_ascii=False)}")
        partes.append("{" + ",".join(campos) + "}")
    return ("[" + ",".join(partes) + "]").replace("</", "<\\/")


# F6: mes_em_andamento vive em dn/metrics.py (a Penetracao precisa dela para achar o mes fechado, RN-27)


DIFS = ("cobertura_dif_mes_anterior", "volume_dif_mes_anterior", "receita_dif_mes_anterior")


def _mes_ant(am: str) -> str:
    t = int(am[:4]) * 12 + int(am[5:7]) - 2
    return f"{t // 12:04d}-{t % 12 + 1:02d}"


def _difs(g, mes_ref: str) -> dict:
    """Refino E3 (D7, "O que aconteceu no mes"): diferenca absoluta vs o mes anterior, no cubo da propria linha (mes - mes anterior):
    PDVs positivados, volume em t e valor em R$. Sem linha no mes ou no mes anterior = nulo (nunca zero)."""
    ant = _mes_ant(mes_ref)
    a = g[g["ANO_MES"] == mes_ref]; b = g[g["ANO_MES"] == ant]
    if a.empty or b.empty:
        return {k: None for k in DIFS}
    return _difs_linhas(a.iloc[0], b.iloc[0])


def _difs_linhas(a, b) -> dict:
    def d(col, k=1.0):
        x, y = _n(a.get(col)), _n(b.get(col))
        return None if x is None or y is None else (float(x) - float(y)) / k
    pos = d("positivados")
    return {"cobertura_dif_mes_anterior": None if pos is None else int(round(pos)),
            "volume_dif_mes_anterior": d("volume_kg", 1000.0), "receita_dif_mes_anterior": d("receita_rs")}


# ---- Etapa 1 · performance (P4, 15/09/2026): indices dos cubos, construidos uma vez por cubo e reaproveitados nos 25 meses
# montados. `montar` deixa de filtrar o DataFrame item a item (mascara por entidade, por mes, por categoria) e passa a
# consultar dicionarios {chave: {ANO_MES: linha}}. As linhas sao as mesmas (to_dict); nenhum numero e recalculado.
_IX: dict = {}


def _indice(df: pd.DataFrame, chaves: list[str]) -> tuple[dict, dict]:
    """({chave: {ANO_MES: linha}}, {entidade: [categorias na ordem do cubo]}); chave = valor unico ou tupla na ordem de `chaves`.
    Cache pela identidade do DataFrame (o cubo nao muda entre os meses montados; a referencia guardada impede a reutilizacao do id)."""
    k = (id(df), tuple(chaves))
    hit = _IX.get(k)
    if hit is not None and hit[0] is df:
        return hit[1], hit[2]
    por_chave: dict = {}
    por_ent: dict = {}
    n = len(chaves)
    for row in df.to_dict("records"):
        key = row[chaves[0]] if n == 1 else tuple(row[c_] for c_ in chaves)
        meses_ = por_chave.get(key)
        if meses_ is None:
            por_chave[key] = meses_ = {}
            if n > 1 and chaves[-1] == "CAT":
                por_ent.setdefault(key[:-1], []).append(key[-1])
        meses_[row["ANO_MES"]] = row
    if por_ent:
        for e_ in por_ent:
            por_ent[e_] = sorted(por_ent[e_])   # dentro de um mes o cubo esta em ordem de categoria
    _IX[k] = (df, por_chave, por_ent)
    return por_chave, por_ent


def _difs_ix(linhas: dict | None, mes_ref: str) -> dict:
    """`_difs` sobre o indice: linhas = {ANO_MES: linha} da entidade."""
    a = linhas.get(mes_ref) if linhas else None
    b = linhas.get(_mes_ant(mes_ref)) if linhas else None
    if a is None or b is None:
        return {k: None for k in DIFS}
    return _difs_linhas(a, b)


def _cats_ix(dc, chaves: list[str], ent: tuple, mes_ref: str, com_penetracao: bool) -> list[dict]:
    if dc is None or not len(dc):
        return []
    ix, por_ent = _indice(dc, chaves)
    out = []
    for cat in por_ent.get(ent, ()):
        linhas = ix[ent + (cat,)]
        r = linhas.get(mes_ref)
        if r is None:
            continue
        d = {"id": slug(str(cat)), "nome": str(cat).title(), **_metricas(r)}
        if com_penetracao:
            d["penetracao"] = _n(r.get("penetracao"))
        d.update(_difs_ix(linhas, mes_ref))   # Refino E3
        out.append(d)
    out.sort(key=lambda x: -(x["cobertura_pdv"] or 0))
    return out


def _cats_por(dc, col: str, val, mes_ref: str, seg: str | None = None) -> list[dict]:
    """F4 (RN-37): linhas por categoria de um cluster ou supervisor no mes de referencia (cubo com ou sem SEG)."""
    if dc is None or not len(dc):
        return []
    com_seg = seg is not None and "SEG" in dc.columns
    return _cats_ix(dc, [col] + (["SEG"] if com_seg else []) + ["CAT"], (val, seg) if com_seg else (val,), mes_ref, True)


def _cats_dist(dc, did, mes_ref: str) -> list[dict]:
    """Linhas do distribuidor por categoria no mes de referencia (10/09/2026).
    Sem serie: a tabela recorta o mes e o drill segue na serie total do distribuidor.
    Regua igual a da Visao geral: positivados na categoria / base ativa do nivel."""
    return _cats_ix(dc, ["DIST", "CAT"], (did,), mes_ref, False)


def _n(v):
    if v is None or (isinstance(v, float) and np.isnan(v)) or v is pd.NA:
        return None
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return None if np.isnan(v) else float(v)
    return v


def _txt(v):
    return None if v is None or (not isinstance(v, str) and pd.isna(v)) else str(v)


def _txt_(v):
    """F6: texto ou None (aceita NaN)."""
    return None if v is None or (not isinstance(v, str) and pd.isna(v)) else str(v)


def _metricas(r) -> dict:
    """Linha de DN_*_MES -> dicionário de métricas do contrato."""
    d = {
        "base_ativa": _n(r.get("base_ativa")),
        "cobertura_pdv": _n(r.get("positivados")),
        "pct_cobertura": _n(r.get("pct_cobertura")),
        "volume_t": None if _n(r.get("volume_kg")) is None else r["volume_kg"] / 1000,
        "kg_pdv": _n(r.get("kg_pdv")),
        "receita_rs": _n(r.get("receita_rs")),
        "rs_pdv": _n(r.get("rs_pdv")),
        # RN-58: frequencia de compra (estimada, calibrada no total Mtrix) e o minimo sem estimativa, com as parcelas
        "frequencia": _n(r.get("frequencia")),
        "atendimentos": _n(r.get("atendimentos")),
        "frequencia_min": _n(r.get("frequencia_min")),
        "atendimentos_min": _n(r.get("atendimentos_min")),
    }
    # F1 (A.5): cards mostram o valor em R$ milhoes com 1 decimal; a tabela usa receita_rs inteiro
    d["receita_mi"] = None if d["receita_rs"] is None else d["receita_rs"] / 1e6
    for v in VARS:
        d[v] = _n(r.get(v))
    # oportunidade: PDVs da base ativa que nao positivaram no mes (aritmetica sobre os dois campos)
    d["sem_compra_mes"] = None if d["base_ativa"] is None or d["cobertura_pdv"] is None else int(d["base_ativa"] - d["cobertura_pdv"])
    # F5 (RN-25): acumulados no ano civil e no ano fiscal ate o mes (nulos quando o periodo nao esta completo na serie)
    for pref in ("civil", "fiscal"):
        v = _n(r.get(f"ytd_{pref}_volume_kg")); rs_ = _n(r.get(f"ytd_{pref}_receita_rs"))
        d[f"acum_{pref}_t"] = None if v is None else v / 1000
        d[f"acum_{pref}_rs"] = rs_
        d[f"acum_{pref}_mi"] = None if rs_ is None else rs_ / 1e6
        n_ = _n(r.get(f"ytd_{pref}_n_meses")); d[f"acum_{pref}_n"] = None if n_ is None else int(n_)
        vly = _n(r.get(f"ytd_{pref}_volume_ly")); d[f"acum_{pref}_ly_t"] = None if vly is None else vly / 1000
        d[f"acum_{pref}_ly_rs"] = _n(r.get(f"ytd_{pref}_receita_ly"))
        d[f"acum_{pref}_var_t"] = _n(r.get(f"ytd_{pref}_volume_var_ly"))
        d[f"acum_{pref}_var_rs"] = _n(r.get(f"ytd_{pref}_receita_var_ly"))
        # RN-58 (decisao 5): frequencia acumulada = Σ atendimentos ÷ Σ positivados dos meses do periodo, e Δ% vs ano anterior
        d[f"acum_{pref}_freq"] = _n(r.get(f"ytd_{pref}_frequencia"))
        d[f"acum_{pref}_var_freq"] = _n(r.get(f"ytd_{pref}_frequencia_var_ly"))
    return d


def blob_pdvs(pb: pd.DataFrame, nome_dist: pd.Series, mascara: dict | None = None) -> dict:
    """Lista COMPLETA da base ativa em JSON compacto, gzip + base64, para a busca no
    HTML (o mesmo padrao gzip+base64 do painel gerencial). Colunas posicionais:
    0 cnpj, 1 nome, 2 idx distribuidor, 3 idx cluster, 4 uf, 5 cidade, 6 bairro,
    7 kg mes, 8 positivado mes, 9 positivado mes anterior, 10 meses na janela,
    11 ultimo mes (rotulo), 12 kg ultimo mes, 13 kg janela, 14 rtm,
    15 R$ mes, 16 R$ ultimo mes, 17 R$ janela (F1, RN-06: inteiros, mesmas linhas do kg),
    F7 (RN-38, quando `mascara` vem preenchida): 18 mascara PDV x categoria (bits 0..n-1 = comprou a categoria na
    janela; bits n..2n-1 = comprou no mes; ordem das categorias em `cats`), 19 novo na janela (PRIMEIRO_MES, A.6)."""
    import base64
    import gzip
    import json
    dists = sorted(set(nome_dist.dropna()))
    i_d = {d: i for i, d in enumerate(dists)}
    clusters = sorted(set(pb["SEGMENTO_MTRIX"].fillna("").astype(str)) | {""})
    i_c = {c: i for i, c in enumerate(clusters)}
    def _s(v) -> str:
        return "" if v is None or (not isinstance(v, str) and pd.isna(v)) else str(v)
    com_mascara = mascara is not None
    # 22/09/2026 (Douglas): a coluna nf_min (RN-58, decisao 2) saiu do blob e da tabela de PDVs
    rows = []
    for r in pb.itertuples(index=False):
        rows.append([str(r.COD_PDV), _s(r.NOME_PDV), i_d[r.nome_dist], i_c[_s(r.SEGMENTO_MTRIX)],
                     _s(r.UF), _s(r.CIDADE), _s(r.BAIRRO),
                     None if pd.isna(r.kg_mes) else round(float(r.kg_mes), 1), int(bool(r.positivado_mes)),
                     int(bool(r.positivado_mes_anterior)), int(r.meses_positivado_janela), str(r.ultimo_rot),
                     None if pd.isna(r.kg_ultimo_mes) else round(float(r.kg_ultimo_mes), 1),
                     None if pd.isna(r.kg_janela) else round(float(r.kg_janela), 1), int(bool(r.ORIGEM_RTM)),
                     None if pd.isna(r.rs_mes) else int(round(float(r.rs_mes))),
                     None if pd.isna(r.rs_ultimo_mes) else int(round(float(r.rs_ultimo_mes))),
                     None if pd.isna(r.rs_janela) else int(round(float(r.rs_janela)))]
                    + ([int(r.mascara), int(bool(r.novo))] if com_mascara else []))
    carga = {"cols": ["cnpj", "nome", "dist", "cluster", "uf", "cidade", "bairro", "kg_mes", "pos_mes", "pos_ant",
                      "meses_janela", "ultimo_mes", "kg_ultimo", "kg_janela", "rtm", "rs_mes", "rs_ultimo", "rs_janela"]
                     + (["mascara", "novo"] if com_mascara else []),
             "dists": dists, "clusters": clusters, "rows": rows}
    if com_mascara:
        carga["cats"] = list(mascara["cats"]); carga["cats_nomes"] = list(mascara["cats_nomes"]); carga["bits"] = int(mascara["bits"])
    raw = json.dumps(carga, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    b64 = base64.b64encode(gzip.compress(raw, compresslevel=9)).decode("ascii")
    return {"z": "gzip+base64", "n": len(rows), "bytes_json": len(raw), "bytes_b64": len(b64), "b64": b64}


def combinar_pdv_blobs(itens: list[tuple[str, dict]]) -> dict:
    """Refino E4a (D22): uma lista de PDVs para os meses do arquivo (mes parcial e mes fechado). Cada par distribuidor x PDV
    aparece uma vez com as colunas fixas (cadastro) e, por mes, as colunas do mes ou nulo quando o par nao esta na base ativa
    daquele mes. As listas de cada mes continuam sendo montadas por `blob_pdvs`; aqui so se juntam, sem conta."""
    import base64
    import gzip
    fixas = ["cnpj", "nome", "dist", "cluster", "uf", "cidade", "bairro", "rtm"]
    dec = [(mid, json.loads(gzip.decompress(base64.b64decode(b["b64"])))) for mid, b in itens]
    cols = dec[0][1]["cols"]
    for mid, d in dec:
        if d["cols"] != cols:
            L.abortar(f"lista de PDVs de {mid} com colunas diferentes ({d['cols']} x {cols})")
    i_fix = [cols.index(c) for c in fixas]; i_mes = [i for i in range(len(cols)) if i not in i_fix]
    dists = sorted({n for _, d in dec for n in d["dists"]}); clusters = sorted({n for _, d in dec for n in d["clusters"]})
    i_d = {n: i for i, n in enumerate(dists)}; i_c = {n: i for i, n in enumerate(clusters)}
    pares: dict[tuple, list] = {}
    for k_mes, (mid, d) in enumerate(dec):
        for r in d["rows"]:
            nome_d = d["dists"][r[2]]
            chave = (str(r[0]), nome_d)
            if chave not in pares:
                fx = [r[i] for i in i_fix]
                fx[fixas.index("dist")] = i_d[nome_d]; fx[fixas.index("cluster")] = i_c[d["clusters"][r[3]]]
                pares[chave] = fx + [None] * len(dec)
            pares[chave][len(fixas) + k_mes] = [r[i] for i in i_mes]
    base = dec[0][1]
    carga = {"formato": "combinado", "meses": [mid for mid, _ in dec], "cols": cols, "cols_fixas": fixas,
             "cols_mes": [cols[i] for i in i_mes], "dists": dists, "clusters": clusters, "rows": list(pares.values())}
    for k in ("cats", "cats_nomes", "bits"):
        if k in base:
            carga[k] = base[k]
    raw = json.dumps(carga, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    b64 = base64.b64encode(gzip.compress(raw, compresslevel=9)).decode("ascii")
    return {"z": "gzip+base64", "n": len(pares), "bytes_json": len(raw), "bytes_b64": len(b64), "b64": b64}


def _spark(serie: list[dict], meses_exib: list[str]) -> dict:
    """F3 (RN-46): os pontos da serie exibida, em t e em R$, ALINHADOS aos meses exibidos (F4: serie curta — nivel sem
    venda em algum mes — recebe nulo naquele mes, para a mini-linha e a evolucao por categoria nao deslocarem)."""
    by = {p["mes"]: p for p in serie}
    return {"spark_t": [by[m].get("volume_t") if m in by else None for m in meses_exib],
            "spark_rs": [by[m].get("receita_rs") if m in by else None for m in meses_exib]}


def _r(v, dec: int):
    """Arredonda numero cru da serie (F2): t 3 casas, R$ inteiro, % e p.p. 2 casas; None passa."""
    if v is None:
        return None
    return int(round(v)) if dec == 0 else round(float(v), dec)


def _serie(df: pd.DataFrame, rot: dict, stack: pd.DataFrame | None = None) -> list[dict]:
    """df filtrado a um grupo, uma linha por ANO_MES. `stack` (opcional): DataFrame
    ANO_MES x {base_atual, novos, sem_venda} com positivados por segmento."""
    out = []
    linhas = list(df.sort_values("ANO_MES").itertuples())
    por_mes = {r_.ANO_MES: r_ for r_ in linhas}   # P4: LY por consulta direta, nao por mascara a cada ponto
    for r in linhas:
        it = {"mes": rot[r.ANO_MES], "base_ativa": _n(r.base_ativa), "cobertura_pdv": _n(r.positivados)}
        if stack is not None:
            s = stack.loc[r.ANO_MES] if r.ANO_MES in stack.index else None
            it["cobertura_base_atual"] = None if s is None else _n(s.get("base_atual"))
            it["cobertura_novos"] = None if s is None else _n(s.get("novos"))
            it["cobertura_sem_venda"] = None if s is None else _n(s.get("sem_venda"))   # 02/10/2026
        it["pct_cobertura"] = _r(_n(r.pct_cobertura), 2)
        # LY por juncao no proprio grupo (RN-22: mes sem par fica nulo, nunca zero)
        def _ly(col):
            if pd.isna(r.ANO_MES_LY):
                return None
            q = por_mes.get(r.ANO_MES_LY)
            return None if q is None else _n(getattr(q, col))
        it["cobertura_ly"] = _ly("positivados")
        it["volume_t"] = _r(None if _n(r.volume_kg) is None else r.volume_kg / 1000, 3)
        it["receita_rs"] = _r(_n(getattr(r, "receita_rs", None)), 0)
        # F2 (RN-47): LY da medida e os comparativos ja calculados na curated, por ponto (o JS nao recalcula mais)
        vly = _ly("volume_kg")
        it["volume_ly"] = _r(None if vly is None else vly / 1000, 3)
        it["receita_ly"] = _r(_ly("receita_rs"), 0)
        for v in VARS:
            it[v] = _r(_n(getattr(r, v, None)), 2)
        # F5 (RN-25): acumulado civil/fiscal ate o mes, LY do acumulado e Δ (nulos sem periodo completo / sem par)
        for pref in ("civil", "fiscal"):
            va = _n(getattr(r, f"ytd_{pref}_volume_kg", None))
            it[f"acum_{pref}_t"] = _r(None if va is None else va / 1000, 3)
            it[f"acum_{pref}_rs"] = _r(_n(getattr(r, f"ytd_{pref}_receita_rs", None)), 0)
            n_ = _n(getattr(r, f"ytd_{pref}_n_meses", None)); it[f"acum_{pref}_n"] = None if n_ is None else int(n_)
            vly = _n(getattr(r, f"ytd_{pref}_volume_ly", None))
            it[f"acum_{pref}_ly_t"] = _r(None if vly is None else vly / 1000, 3)
            it[f"acum_{pref}_ly_rs"] = _r(_n(getattr(r, f"ytd_{pref}_receita_ly", None)), 0)
            it[f"acum_{pref}_var_t"] = _r(_n(getattr(r, f"ytd_{pref}_volume_var_ly", None)), 2)
            it[f"acum_{pref}_var_rs"] = _r(_n(getattr(r, f"ytd_{pref}_receita_var_ly", None)), 2)
        # RN-58 (decisao 3): nas series vai so o valor da frequencia (LY e variacoes ficam nos cards e tabelas)
        it["frequencia"] = _r(_n(getattr(r, "frequencia", None)), 3)
        out.append(it)
    return _cortar(out)


def _stack(seg_df: pd.DataFrame, extra_key: dict | None = None) -> pd.DataFrame:
    d = seg_df
    for k, v in (extra_key or {}).items():
        d = d[d[k] == v]
    return d.pivot_table(index="ANO_MES", columns="SEG", values="positivados", aggfunc="sum")



def _rot_atendeu(txt) -> str:
    """'NOME (CNPJ)=12.3; NOME2 (CNPJ)=4.0' -> 'NOME (CNPJ) 12 kg; NOME2 (CNPJ) 4 kg' (texto de exibicao)."""
    if txt is None or (not isinstance(txt, str)) or not txt:
        return ""
    partes = []
    for p_ in txt.split("; "):
        if "=" in p_:
            n, kg = p_.rsplit("=", 1)
            try:
                partes.append(f"{n} {float(kg):,.0f} kg".replace(",", "."))
            except ValueError:
                partes.append(p_)
        else:
            partes.append(p_)
    return "; ".join(partes)


def blob_rtm(grade: pd.DataFrame, cli: pd.DataFrame, meses: list[str], rot_of, corte: str, sup: pd.Series,
             pdv: pd.DataFrame) -> dict:
    """Cliente x mes da base RTM em JSON posicional, gzip + base64: e o que alimenta os drills.
    linhas: [i_cliente, i_mes, i_estado, kg_certo, kg_outro, atendeu_certo, outros, i_ultimo_mes, rs_certo, rs_outro]
    (rs_* desde a F1, RN-55: R$ inteiros, no fim para nao mover os indices ja usados pelo JS)
    clientes: [cnpj, cod_antigo, razao, origem_razao(0 mtrix/1 bandeira), destino, supervisor, uf, cidade,
               coberto, motivo, i_ativ_hist, i_ativ_mig]"""
    import base64
    import gzip
    import json
    i_m = {m: k for k, m in enumerate(meses)}
    estados = ["certo", "so_outro", "sem_compra", "nao_mensuravel"]
    i_e = {e: k for k, e in enumerate(estados)}

    def _s(v) -> str:
        return "" if v is None or (not isinstance(v, str) and pd.isna(v)) else str(v)

    def _im(v):
        return None if v is None or (not isinstance(v, str) and pd.isna(v)) or v not in i_m else i_m[v]

    clientes, i_c = [], {}
    for r in cli.itertuples():
        i_c[r.COD_PDV] = len(clientes)
        nome_mtrix = _s(getattr(r, "NOME_MTRIX", None))
        clientes.append([str(r.COD_PDV), _s(r.COD_CLIENTE_ANTIGO), nome_mtrix or _s(r.BANDEIRA_ANTIGA), 0 if nome_mtrix else 1,
                         _s(r.DESTINO), _s(sup.get(r.DESTINO)), _s(pdv["UF"].get(r.COD_PDV)), _s(pdv["CIDADE"].get(r.COD_PDV)),
                         int(bool(r.COBERTO)), _s(r.MOTIVO), _im(r.MES_ATIVACAO_HIST), _im(r.MES_ATIVACAO_MIG)])
    rows = []
    for r in grade.itertuples(index=False):
        rows.append([i_c[r.COD_PDV], i_m[r.ANO_MES], i_e[r.ESTADO], round(float(r.kg_certo), 1), round(float(r.kg_outro), 1),
                     _s(r.ATENDEU_CERTO), _rot_atendeu(r.OUTROS), _im(r.ULTIMO_MES_COMPRA),
                     int(round(float(r.rs_certo))), int(round(float(r.rs_outro)))])
    corte_idx = next((k for k, m in enumerate(meses) if m >= corte), None)
    carga = {"meses": [rot_of(m) for m in meses], "meses_am": meses, "estados": estados, "corte_idx": corte_idx,
             "cols": ["i_cliente", "i_mes", "i_estado", "kg_certo", "kg_outro", "atendeu_certo", "outros", "i_ultimo_mes", "rs_certo", "rs_outro"],
             "clientes": clientes, "linhas": rows}
    raw = json.dumps(carga, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    b64 = base64.b64encode(gzip.compress(raw, compresslevel=9)).decode("ascii")
    return {"z": "gzip+base64", "n": len(rows), "n_clientes": len(clientes), "bytes_json": len(raw), "bytes_b64": len(b64), "b64": b64}


def _rtm(T: dict, rot: dict, rot_of, c: dict) -> dict:
    """Bloco RTM do painel (Fase 4): indicadores do mes nas duas reguas de ativacao, serie,
    destinos (com motivo), clientes (com quem atendeu e ultima compra), corte temporal e blob
    cliente x mes para os drills. O denominador da aderencia sao os clientes com destino
    mensuravel; os demais entram so no total, com o motivo."""
    if "DN_RTM_MES" not in T:
        return {}
    ser, dest, cli, grade = T["DN_RTM_MES"], T["DN_RTM_DESTINO"], T["DN_RTM_CLIENTE"], T["DN_RTM_CLIENTE_MES"]
    meses, mes_ref = c["meses"], c["mes_ref"]
    u = ser.iloc[-1]
    sup = c["dist"].drop_duplicates("NOME_REDUZIDO").set_index("NOME_REDUZIDO")["SUPERVISOR"]
    pdv = c["pdv"].set_index("COD_PDV")
    R = CFG["regras"]["rtm"]
    corte = str(R["data_migracao"])[:7]
    tem_meses = any(m >= corte for m in meses)
    padrao = str(R.get("visao_padrao", "auto"))
    visao_padrao = ("migracao" if tem_meses else "historico") if padrao == "auto" else ("migracao" if padrao == "a_partir_da_migracao" else "historico")
    MOT = dict(_ROT["rtm_motivos"])

    def _situacao(est, r) -> str:
        rot_est = _EST[est]
        if est == "certo" and _txt(r.ATENDEU_CERTO):
            return f"{rot_est} · {r.ATENDEU_CERTO}"
        if est == "so_outro" and _txt(r.OUTROS):
            return f"{rot_est} · {_rot_atendeu(r.OUTROS)}"
        if est == "nao_mensuravel":
            return f"{rot_est} · {MOT.get(r.MOTIVO, r.MOTIVO)}"
        return rot_est

    clientes = []
    for r in cli.itertuples():
        est = str(r.ESTADO) if isinstance(r.ESTADO, str) else ("nao_mensuravel" if not bool(r.COBERTO) else "sem_compra")
        nome_mtrix = _txt(getattr(r, "NOME_MTRIX", None))
        clientes.append({
            "cnpj": str(r.COD_PDV), "nome": nome_mtrix or _txt(getattr(r, "BANDEIRA_ANTIGA", None)),
            "nome_origem": "mtrix" if nome_mtrix else "bandeira",
            "cod_antigo": _txt(getattr(r, "COD_CLIENTE_ANTIGO", None)),
            "destino": _txt(r.DESTINO), "supervisor": _txt(sup.get(r.DESTINO)),
            "uf": _txt(pdv["UF"].get(r.COD_PDV)), "cidade": _txt(pdv["CIDADE"].get(r.COD_PDV)),
            "estado": est, "estado_rotulo": _EST[est], "situacao": _situacao(est, r),
            "motivo": _txt(r.MOTIVO), "motivo_rotulo": MOT.get(r.MOTIVO) if _txt(r.MOTIVO) else None,
            "atendeu": _txt(r.ATENDEU_CERTO) if est == "certo" else (_rot_atendeu(r.OUTROS) if est == "so_outro" else None),
            "ultimo_mes_compra": rot_of(r.ULTIMO_MES_COMPRA) if _txt(r.ULTIMO_MES_COMPRA) else None,
            "ativado": bool(r.ATIVADO_HIST), "mes_ativacao": rot_of(r.MES_ATIVACAO_HIST) if bool(r.ATIVADO_HIST) else None,
            "ativado_mig": bool(r.ATIVADO_MIG), "mes_ativacao_mig": rot_of(r.MES_ATIVACAO_MIG) if bool(r.ATIVADO_MIG) else None,
            "kg_certo": _n(r.kg_certo), "kg_outro": _n(r.kg_outro),
            "receita_rs": _n(r.rs_certo), "receita_outro_rs": _n(r.rs_outro),
        })
    ordem = {"sem_compra": 0, "so_outro": 1, "certo": 2, "nao_mensuravel": 3}
    clientes.sort(key=lambda x: (ordem[x["estado"]], x["destino"] or "", x["nome"] or ""))

    destinos = []
    for r in dest.itertuples():
        destinos.append({
            "nome": _txt(r.DESTINO), "coberto": bool(r.COBERTO), "clientes": int(r.clientes),
            "motivo": _txt(r.MOTIVO), "motivo_rotulo": MOT.get(r.MOTIVO) if _txt(r.MOTIVO) else None,
            "certo": _n(r.certo), "so_outro": _n(r.so_outro), "sem_compra": _n(r.sem_compra),
            "ativados": _n(r.ativados), "ativados_mig": _n(r.ativados_mig), "pct_aderencia": _n(r.pct_aderencia),
            "kg_certo": _n(r.kg_certo), "kg_outro": _n(r.kg_outro),
            "receita_rs": _n(r.rs_certo), "receita_outro_rs": _n(r.rs_outro),
            "supervisor": _txt(sup.get(r.DESTINO)),
            # F9 (RN-48, regra R4): % dos clientes do destino sem compra no mes (so destinos mensuraveis)
            "pct_sem_compra": (float(r.sem_compra) / float(r.clientes) * 100) if bool(r.COBERTO) and int(r.clientes) else None,
        })

    serie = _cortar([{"mes": rot.get(r.ANO_MES, r.ANO_MES), "i_mes": k, "desde_migracao": bool(r.desde_migracao),
              "certo": int(r.certo), "so_outro": int(r.so_outro),
              "sem_compra": int(r.sem_compra), "pct_aderencia": _n(r.pct_aderencia),
              "kg_certo": _n(r.kg_certo), "kg_outro": _n(r.kg_outro),
              "ativados_hist": int(r.ativados_hist), "ativados_mig": int(r.ativados_mig),
              "receita_rs": _n(r.rs_certo), "receita_outro_rs": _n(r.rs_outro)} for k, r in enumerate(ser.itertuples())])

    motivos_n = cli.loc[~cli["COBERTO"], "MOTIVO"].value_counts().to_dict()
    motivos = [{"id": k, "rotulo": MOT.get(k, k), "n": int(motivos_n.get(k, 0))} for k in MOT]

    # ---- D18 revista (13/09/2026, RN-44): recorte por supervisor do destino. Cada linha de destino/cliente leva o sup_id; a serie
    #      e os indicadores do mes por supervisor vem de DN_RTM_SUP_MES (pipeline). Linhas do canal levam sup_id "__all__".
    sup_id_nome = c["dist"].drop_duplicates("NOME_REDUZIDO").set_index("NOME_REDUZIDO")["SUP_ID"]
    for x in destinos:
        x["sup_id"] = _txt(sup_id_nome.get(x["nome"])) if x["coberto"] else ""
    for x in clientes:
        x["sup_id"] = _txt(sup_id_nome.get(x["destino"])) if x["estado"] != "nao_mensuravel" else ""
    for x in serie:
        x["sup_id"] = "__all__"
    SS = T.get("DN_RTM_SUP_MES")
    por_sup, serie_sup = [], []
    if SS is not None and len(SS):
        for su, g in SS.groupby("SUP"):
            g = g.sort_values("ANO_MES")
            serie_sup += _cortar([{"mes": rot.get(r.ANO_MES, r.ANO_MES), "i_mes": k, "desde_migracao": bool(r.desde_migracao), "sup_id": str(su),
                                   "certo": int(r.certo), "so_outro": int(r.so_outro), "sem_compra": int(r.sem_compra), "pct_aderencia": _n(r.pct_aderencia),
                                   "kg_certo": _n(r.kg_certo), "kg_outro": _n(r.kg_outro), "ativados_hist": int(r.ativados_hist), "ativados_mig": int(r.ativados_mig),
                                   "receita_rs": _n(r.rs_certo), "receita_outro_rs": _n(r.rs_outro)} for k, r in enumerate(g.itertuples())])
            ur = g[g["ANO_MES"] == mes_ref]
            if len(ur):
                ur = ur.iloc[0]
                por_sup.append({"sup_id": str(su), "rastreaveis": int(ur["base_rtm"]), "certo": int(ur["certo"]), "so_outro": int(ur["so_outro"]),
                                "sem_compra": int(ur["sem_compra"]), "pct_aderencia": _n(ur["pct_aderencia"]),
                                "ativados": int(ur["ativados_hist"]), "ativados_parados": int(ur["ativados_parados_hist"]),
                                "ativados_mig": int(ur["ativados_mig"]), "ativados_parados_mig": int(ur["ativados_parados_mig"]),
                                "pct_vazamento_rs": _n(100 * ur["rs_outro"] / (ur["rs_certo"] + ur["rs_outro"])) if (ur["rs_certo"] + ur["rs_outro"]) else None})

    return {
        "base_total": int(len(cli)),
        "rastreaveis": int(u["base_rtm"]),
        "nao_mensuravel": int(u["nao_mensuravel"]),
        "rotulo_nao_mensuravel": _EST["nao_mensuravel"],
        "definicao_nao_mensuravel": str(CFG["painel"]["textos"]["rtm_nao_mensuravel"]),
        "motivos": motivos,
        "corte": {"data_migracao": str(R["data_migracao"]), "mes": corte, "rotulo_mes": rot_of(corte),
                  "tem_meses": tem_meses, "visao_padrao": visao_padrao,
                  "n_meses_desde_corte": int(sum(1 for m in meses if m >= corte))},
        "kpi": {"certo": int(u["certo"]), "so_outro": int(u["so_outro"]), "sem_compra": int(u["sem_compra"]),
                "pct_aderencia": _n(u["pct_aderencia"]),
                "ativados": int(u["ativados_hist"]), "ativados_parados": int(u["ativados_parados_hist"]),
                "ativados_mig": int(u["ativados_mig"]), "ativados_parados_mig": int(u["ativados_parados_mig"]),
                "kg_certo": _n(u["kg_certo"]), "kg_outro": _n(u["kg_outro"]),
                "receita_rs": _n(u["rs_certo"]), "receita_outro_rs": _n(u["rs_outro"]),
                "pct_vazamento_rs": _n(100 * u["rs_outro"] / (u["rs_certo"] + u["rs_outro"]))
                if (u["rs_certo"] + u["rs_outro"]) else None},
        "serie": serie, "serie_sup": serie_sup, "destinos": destinos, "clientes": clientes,
        "por_supervisor_json": json.dumps(por_sup, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/"),
        "n_supervisores": len(por_sup),
        "sup_nota": str((_P.get("textos") or {}).get("rtm_sup_nota", "{n} clientes com destino sem cadastro não têm supervisor e não aparecem neste recorte")).format(n=int(u["nao_mensuravel"])),
        "sup_vazio": str((_P.get("textos") or {}).get("rtm_sup_vazio", "sem clientes RTM com destino deste supervisor")),
        "rotulos_json": json.dumps({"estados": _EST, "motivos": MOT}, ensure_ascii=False).replace("</", "<\\/"),
        "blob": blob_rtm(grade, cli, meses, rot_of, corte, sup, pdv),
    }


def _carteira(K, dist_nome: dict, rot_of) -> dict:
    """RN-56 · JSON da carteira para o navegador: pares validos que estao na lista de PDVs, contagens por cluster e os validos
    que sairam da base ativa (a nota os cita em vez de sumir calado). Rotulos, padrao e textos vem de `painel.pdv_carteira`."""
    PC = CFG["painel"].get("pdv_carteira") or {}
    base = {"padrao": str(PC.get("padrao", "destaque")), "rotulo": str(PC.get("rotulo", "Carteira")),
            "opcoes": [[str(a), str(b)] for a, b in (PC.get("opcoes") or [])], "textos": dict(PC.get("textos") or {})}
    if K is None or not len(K) or not PC.get("ativo", True):
        carga = dict(base, ativo=False, pares={}, contagem={}, fora_base={}, total=0, validos=0)
        return {"ativo": False, "json": json.dumps(carga, ensure_ascii=False, separators=(",", ":")), "texto_definicoes": "", "n_validos": 0, "n_linhas": 0}
    V = K[K["VALIDA"].astype(bool)]
    pares = {f"{dist_nome.get(r.CNPJ_DISTRIBUIDOR, '')}|{r.COD_PDV}": str(r.CLUSTER).lower() for r in V[V["NA_BASE_ATIVA"].astype(bool)].itertuples()}
    cont = {}
    for cl, g in K.groupby(K["CLUSTER"].fillna("").astype(str).str.lower()):
        if cl:
            gv = g[g["VALIDA"].astype(bool)]
            cont[cl] = {"total": int(len(g)), "validos": int(len(gv)), "fora": int(len(g) - len(gv)), "na_base": int(gv["NA_BASE_ATIVA"].astype(bool).sum())}
    fb = {}
    for r in V[~V["NA_BASE_ATIVA"].astype(bool)].itertuples():
        um = str(r.ULTIMO_MES) if isinstance(r.ULTIMO_MES, str) and r.ULTIMO_MES else ""
        fb.setdefault(str(r.CLUSTER).lower(), []).append(f"{r.NOME_MTRIX or r.RAZAO_PLANILHA} ({dist_nome.get(r.CNPJ_DISTRIBUIDOR, r.CNPJ_DISTRIBUIDOR)}"
                                                         + (f", última compra {rot_of(um)}" if um else "") + ")")
    carga = dict(base, ativo=True, pares=pares, contagem=cont, fora_base=fb, total=int(len(K)), validos=int(len(V)))
    return {"ativo": True, "json": json.dumps(carga, ensure_ascii=False, separators=(",", ":")).replace("</", "<" + chr(92) + "/"),
            "texto_definicoes": str(base["textos"].get("definicoes", "")), "n_validos": int(len(V)), "n_linhas": int(len(K))}


def _rtm_mes(T: dict, c: dict, rot_of) -> dict:
    """Refino E4b (D24): o RTM de um mes do historico a partir das tabelas RTM da serie inteira (sem refazer o calculo): cards
    (DN_RTM_MES), recorte por supervisor do destino (DN_RTM_SUP_MES) e destinos no mes (grade cliente x mes + ativacao ate o mes).
    Os clientes do mes sao montados no navegador a partir da lista cliente x mes ja embutida (busca, sem conta)."""
    if "DN_RTM_MES" not in T:
        return {}
    m = c["mes_ref"]; meses = c["meses"]
    ser, SS, cli, grade = T["DN_RTM_MES"], T.get("DN_RTM_SUP_MES"), T["DN_RTM_CLIENTE"], T["DN_RTM_CLIENTE_MES"]
    u = ser[ser["ANO_MES"] == m].iloc[0]
    R = CFG["regras"]["rtm"]; corte = str(R["data_migracao"])[:7]
    tem_meses = any(x >= corte for x in meses)
    padrao = str(R.get("visao_padrao", "auto"))
    visao_padrao = ("migracao" if tem_meses else "historico") if padrao == "auto" else ("migracao" if padrao == "a_partir_da_migracao" else "historico")
    MOT = dict(_ROT["rtm_motivos"])
    sup = c["dist"].drop_duplicates("NOME_REDUZIDO").set_index("NOME_REDUZIDO")["SUPERVISOR"]
    sup_id_nome = c["dist"].drop_duplicates("NOME_REDUZIDO").set_index("NOME_REDUZIDO")["SUP_ID"]
    gm = grade[grade["ANO_MES"] == m].set_index("COD_PDV")
    b = cli[["COD_PDV", "DESTINO", "COBERTO", "MOTIVO", "MES_ATIVACAO_HIST", "MES_ATIVACAO_MIG"]].copy()
    b["certo"] = b["COD_PDV"].map(gm["certo"]).fillna(False).astype(bool)
    b["so_outro"] = b["COD_PDV"].map(gm["outro"]).fillna(False).astype(bool) & ~b["certo"]
    for col in ("kg_certo", "kg_outro", "rs_certo", "rs_outro"):
        b[col] = b["COD_PDV"].map(gm[col]).fillna(0.0)
    b["ativ_h"] = (b["MES_ATIVACAO_HIST"] <= m).fillna(False).astype(bool)
    b["ativ_m"] = ((b["MES_ATIVACAO_MIG"] <= m).fillna(False) & (m >= corte)).astype(bool)
    dest = (b.groupby(["DESTINO", "COBERTO"], dropna=False)
             .agg(clientes=("COD_PDV", "size"), certo=("certo", "sum"), so_outro=("so_outro", "sum"), ativados=("ativ_h", "sum"),
                  ativados_mig=("ativ_m", "sum"), kg_certo=("kg_certo", "sum"), kg_outro=("kg_outro", "sum"),
                  rs_certo=("rs_certo", "sum"), rs_outro=("rs_outro", "sum"), MOTIVO=("MOTIVO", "first")).reset_index())
    dest["sem_compra"] = dest["clientes"] - dest["certo"] - dest["so_outro"]
    dest["pct_aderencia"] = np.where(dest["COBERTO"], dest["certo"] / dest["clientes"] * 100, np.nan)
    dest.loc[~dest["COBERTO"], ["certo", "so_outro", "sem_compra", "ativados", "ativados_mig", "kg_certo", "kg_outro", "rs_certo", "rs_outro"]] = np.nan
    dest = dest.sort_values(["COBERTO", "clientes"], ascending=[False, False]).reset_index(drop=True)
    destinos = []
    for r in dest.itertuples():
        destinos.append({
            "nome": _txt(r.DESTINO), "coberto": bool(r.COBERTO), "clientes": int(r.clientes),
            "motivo": _txt(r.MOTIVO), "motivo_rotulo": MOT.get(r.MOTIVO) if _txt(r.MOTIVO) else None,
            "certo": _n(r.certo), "so_outro": _n(r.so_outro), "sem_compra": _n(r.sem_compra),
            "ativados": _n(r.ativados), "ativados_mig": _n(r.ativados_mig), "pct_aderencia": _n(r.pct_aderencia),
            "kg_certo": _n(r.kg_certo), "kg_outro": _n(r.kg_outro), "receita_rs": _n(r.rs_certo), "receita_outro_rs": _n(r.rs_outro),
            "supervisor": _txt(sup.get(r.DESTINO)),
            "pct_sem_compra": (float(r.sem_compra) / float(r.clientes) * 100) if bool(r.COBERTO) and int(r.clientes) else None,
            "sup_id": _txt(sup_id_nome.get(r.DESTINO)) if bool(r.COBERTO) else ""})
    por_sup = []
    if SS is not None and len(SS):
        for su, g in SS.groupby("SUP"):
            ur = g[g["ANO_MES"] == m]
            if len(ur):
                ur = ur.iloc[0]
                por_sup.append({"sup_id": str(su), "rastreaveis": int(ur["base_rtm"]), "certo": int(ur["certo"]), "so_outro": int(ur["so_outro"]),
                                "sem_compra": int(ur["sem_compra"]), "pct_aderencia": _n(ur["pct_aderencia"]),
                                "ativados": int(ur["ativados_hist"]), "ativados_parados": int(ur["ativados_parados_hist"]),
                                "ativados_mig": int(ur["ativados_mig"]), "ativados_parados_mig": int(ur["ativados_parados_mig"]),
                                "pct_vazamento_rs": _n(100 * ur["rs_outro"] / (ur["rs_certo"] + ur["rs_outro"])) if (ur["rs_certo"] + ur["rs_outro"]) else None})
    return {
        "base_total": int(len(cli)), "rastreaveis": int(u["base_rtm"]), "nao_mensuravel": int(u["nao_mensuravel"]),
        "corte": {"data_migracao": str(R["data_migracao"]), "mes": corte, "rotulo_mes": rot_of(corte), "tem_meses": tem_meses,
                  "visao_padrao": visao_padrao, "n_meses_desde_corte": int(sum(1 for x in meses if x >= corte))},
        "kpi": {"certo": int(u["certo"]), "so_outro": int(u["so_outro"]), "sem_compra": int(u["sem_compra"]), "pct_aderencia": _n(u["pct_aderencia"]),
                "ativados": int(u["ativados_hist"]), "ativados_parados": int(u["ativados_parados_hist"]),
                "ativados_mig": int(u["ativados_mig"]), "ativados_parados_mig": int(u["ativados_parados_mig"]),
                "kg_certo": _n(u["kg_certo"]), "kg_outro": _n(u["kg_outro"]), "receita_rs": _n(u["rs_certo"]), "receita_outro_rs": _n(u["rs_outro"]),
                "pct_vazamento_rs": _n(100 * u["rs_outro"] / (u["rs_certo"] + u["rs_outro"])) if (u["rs_certo"] + u["rs_outro"]) else None},
        "serie": [], "serie_sup": [], "destinos": destinos, "clientes": [],
        "por_supervisor_json": json.dumps(por_sup, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")}


def rtm_clientes_da_lista(blob: dict, mes: str) -> list[dict]:
    """Refino E4b: espelho em Python do que o navegador faz para montar os clientes RTM de um mes a partir da lista cliente x mes
    (validacao: no mes de referencia e no mes fechado tem de dar a tabela do pipeline). So busca, sem conta."""
    import base64
    import gzip
    d = json.loads(gzip.decompress(base64.b64decode(blob["b64"])))
    if mes not in d["meses_am"]:
        return []
    im = d["meses_am"].index(mes); est = d["estados"]; MOT = dict(_ROT["rtm_motivos"])
    out = []
    for l in d["linhas"]:
        if l[1] != im:
            continue
        cl = d["clientes"][l[0]]; e = est[l[2]]
        sit = _EST[e]
        if e == "certo" and l[5]:
            sit = f"{sit} · {l[5]}"
        elif e == "so_outro" and l[6]:
            sit = f"{sit} · {l[6]}"
        elif e == "nao_mensuravel":
            sit = f"{sit} · {MOT.get(cl[9], cl[9])}"
        ah = cl[10] is not None and cl[10] <= im
        am = cl[11] is not None and cl[11] <= im
        out.append({"cnpj": cl[0], "nome": cl[2] or None, "nome_origem": "bandeira" if cl[3] else "mtrix", "destino": cl[4] or None,
                    "supervisor": cl[5] or None, "uf": cl[6] or None, "cidade": cl[7] or None, "estado": e, "situacao": sit,
                    "ultimo_mes_compra": d["meses"][l[7]] if l[7] is not None else None,
                    "ativado": ah, "mes_ativacao": d["meses"][cl[10]] if ah else None,
                    "ativado_mig": am, "mes_ativacao_mig": d["meses"][cl[11]] if am else None,
                    "kg_certo": l[3], "kg_outro": l[4], "receita_rs": l[8], "receita_outro_rs": l[9]})
    ordem = {"sem_compra": 0, "so_outro": 1, "certo": 2, "nao_mensuravel": 3}
    out.sort(key=lambda x: (ordem[x["estado"]], x["destino"] or "", x["nome"] or ""))
    return out


def montar(c: dict, T: dict, leve: bool = False) -> dict:
    """`leve` (Refino E4b): mes do historico do arquivo — so o que muda com o mes (cards, tabelas, acumulado, RTM do mes),
    sem series, Penetracao, lista de PDVs, carteira, resumos e memoria."""
    meses, mes_ref, cal, dist = c["meses"], c["mes_ref"], c["cal"], c["dist"]
    rot = cal.set_index("ANO_MES")["ROTULO"].to_dict()
    i = meses.index(mes_ref)
    meses_exib = _cortar([rot[m] for m in meses])   # F3/F4: eixo comum das mini-linhas e da evolucao por categoria

    def rot_of(am: str) -> str:
        if am in rot:
            return rot[am]
        y, m = int(am[:4]), int(am[5:7])
        return f"{MES_ABREV[m-1]}/{str(y)[2:]}"

    def mes_menos(am: str, k: int) -> str:
        t = int(am[:4]) * 12 + int(am[5:7]) - 1 - k
        return f"{t // 12:04d}-{t % 12 + 1:02d}"

    em_andamento = mes_em_andamento(mes_ref)
    aviso_andamento = ""
    if em_andamento:
        aviso_andamento = str(_P.get("textos", {}).get("mes_em_andamento", "")).format(
            mes=rot_of(mes_ref), data=manifesto.dados_atualizados_em())

    J = {
        "periodo": {
            "mes_atual": rot_of(mes_ref),
            "mes_anterior": rot_of(mes_menos(mes_ref, 1)),
            "mesmo_mes_ano_anterior": rot_of(mes_menos(mes_ref, 12)),
            "janela_l3m": f"{rot_of(mes_menos(mes_ref, 3))} a {rot_of(mes_menos(mes_ref, 1))}",
            "janela_base_ativa": f"{rot_of(meses[max(0, i - c['janela'] + 1)])} a {rot_of(mes_ref)}",
            # D7: os textos do painel leem estes campos em vez de trazer o numero fixo
            "janela_meses": int(c["janela"]),
            "segmento_novos_meses": int(NOVOS_MESES),
            "n_meses_serie": int(len(_cortar(list(meses)))),
            # 10/09/2026: mes parcial entra no painel, mas etiquetado
            "mes_em_andamento": em_andamento,
            "aviso_mes_em_andamento": aviso_andamento,
        },
        "canal": {"nome": str(c.get("recorte_nome") or _ROT["canal"])},   # Etapa 2: no painel por usuario, o rotulo do recorte
    }

    # ---- série do canal, empilhada por segmento
    canal = T["DN_CANAL_MES"]
    seg = T["DN_SEGMENTO_MES"]
    if not leve:
        J["dn"] = {"serie": _serie(canal, rot, _stack(seg))}
        J["dn"]["serie_js"] = _serie_js(J["dn"]["serie"])   # RN-59: serie compacta embutida

    # ---- categorias (canal)
    cc = T["DN_CANAL_CAT_MES"]
    sc = T["DN_SEGMENTO_CAT_MES"]
    canal_ix = canal.set_index("ANO_MES")
    cats = []
    for cat, g in cc.groupby("CAT"):
        r = g[g["ANO_MES"] == mes_ref]
        if r.empty:
            continue
        r = r.iloc[0]
        d = {"id": slug(cat), "nome": str(cat).title(), **_metricas(r), "penetracao": _n(r.get("penetracao"))}
        if not leve:
            d["serie"] = _serie(g, rot, _stack(sc, {"CAT": cat}))
            d["serie_js"] = _serie_js(d["serie"])
        # F3 (RN-46): participacao da categoria na medida do canal, no mes e vs mesmo mes LY (p.p.), em t e em R$
        for col, suf in (("volume_kg", "vol"), ("receita_rs", "rs")):
            tot = float(canal_ix.loc[mes_ref, col]) if mes_ref in canal_ix.index else 0.0
            part = None if not tot else float(r[col]) / tot * 100
            d[f"participacao_{suf}"] = _r(part, 2)
            ly_am = canal_ix.loc[mes_ref, "ANO_MES_LY"] if mes_ref in canal_ix.index else None
            part_ly = None
            if ly_am is not None and not pd.isna(ly_am) and ly_am in canal_ix.index:
                gl = g[g["ANO_MES"] == ly_am]
                tot_ly = float(canal_ix.loc[ly_am, col])
                if len(gl) and tot_ly:
                    part_ly = float(gl.iloc[0][col]) / tot_ly * 100
            d[f"participacao_var_ly_{suf}"] = _r(None if part is None or part_ly is None else part - part_ly, 2)
        cats.append(d)
    cats.sort(key=lambda x: -(x["cobertura_pdv"] or 0))
    J["categorias"] = cats

    # ---- segmentos: todos / base_atual / novos
    sup_nome = dist.drop_duplicates("SUP_ID").set_index("SUP_ID")["SUPERVISOR"].to_dict()
    segs = []
    for sid in ("todos",) + SEGMENTOS:
        if sid == "todos":
            kpi_df, cl_df, su_df = canal, T["DN_CLUSTER_CANAL_MES"], T["DN_SUPERVISOR_CANAL_MES"]
        else:
            kpi_df = seg[seg["SEG"] == sid]
            cl_df = T["DN_CLUSTER_MES"][T["DN_CLUSTER_MES"]["SEG"] == sid]
            su_df = T["DN_SUPERVISOR_MES"][T["DN_SUPERVISOR_MES"]["SEG"] == sid]
        r = kpi_df[kpi_df["ANO_MES"] == mes_ref]
        kpi = _metricas(r.iloc[0]) if len(r) else {k: None for k in MET + VARS}
        clusters = []
        cl_cat = T.get("DN_CLUSTER_CANAL_CAT_MES") if sid == "todos" else T.get("DN_CLUSTER_CAT_MES")
        su_cat = T.get("DN_SUPERVISOR_CANAL_CAT_MES") if sid == "todos" else T.get("DN_SUPERVISOR_CAT_MES")
        for cl, g in cl_df.groupby("CLUSTER"):
            rr = g[g["ANO_MES"] == mes_ref]
            if len(rr):
                clusters.append({"id": slug(str(cl)), "nome": str(cl), **_metricas(rr.iloc[0]),
                                 "serie_js": "" if leve else _serie_js(_serie(g, rot)),   # Refino E3 (5b): grafico em janela ao clicar no cluster
                                 "categorias": _cats_por(cl_cat, "CLUSTER", cl, mes_ref, None if sid == "todos" else sid)})
        clusters.sort(key=lambda x: -(x["cobertura_pdv"] or 0))
        sups = []
        ix_su = _indice(T["DN_SUPERVISOR_CANAL_MES"] if sid == "todos" else T["DN_SUPERVISOR_MES"],
                        ["SUP"] if sid == "todos" else ["SEG", "SUP"])[0]   # P4
        for su, g in su_df.groupby("SUP"):
            rr = g[g["ANO_MES"] == mes_ref]
            if len(rr):
                ser = [] if leve else _serie(g, rot)
                sups.append({"id": str(su), "nome": sup_nome.get(su, str(su)), **_metricas(rr.iloc[0]),
                             **_difs_ix(ix_su.get(su if sid == "todos" else (sid, su)), mes_ref),
                             "serie": ser, "serie_js": _serie_js(ser),
                             "categorias": _cats_por(su_cat, "SUP", su, mes_ref, None if sid == "todos" else sid)})
        sups.sort(key=lambda x: (x["pct_cobertura"] is None, x["pct_cobertura"] or 0))
        n_dist = int((dist["SEGMENTO_ID"] == sid).sum()) if sid != "todos" else int(len(dist))
        # Refino E3 (4a): serie do canal no segmento e do segmento por categoria, para o grafico mes a mes seguir o filtro Segmento
        seg_js, seg_cats = "", []
        if sid != "todos" and not leve:
            seg_js = _serie_js(_serie(kpi_df, rot))
            for cat_, gsc in sc[sc["SEG"] == sid].groupby("CAT"):
                seg_cats.append({"id": slug(str(cat_)), "serie_js": _serie_js(_serie(gsc, rot))})
        segs.append({"id": sid, "nome": SEG_NOMES[sid], "n_distribuidores": n_dist,
                     "kpi": kpi, "clusters": clusters, "supervisores": sups, "serie_js": seg_js, "categorias_serie": seg_cats})
    J["segmentos"] = segs

    # ---- distribuidores
    dd = T["DN_DISTRIBUIDOR_MES"]
    attrs = dist.set_index("DIST_ID")
    dists = []
    for did, g in dd.groupby("DIST"):
        rr = g[g["ANO_MES"] == mes_ref]
        if not len(rr):
            continue
        a = attrs.loc[did]
        dists.append({
            "id": slug(did), "cnpj": str(did), "nome": str(a["DISTRIBUIDOR_MTRIX"]),
            "nome_reduzido": str(a["NOME_REDUZIDO"]), "status": str(a["STATUS"]),
            "supervisor": str(a["SUPERVISOR"]), "supervisor_id": str(a["SUP_ID"]),
            "segmento_id": str(a["SEGMENTO_ID"]), "segmento": str(a["SEGMENTO"]),
            "meses_historico": _n(a["MESES_HISTORICO"]), "historico_censurado": bool(a["HISTORICO_CENSURADO"]),
            "primeiro_mes": rot_of(a["PRIMEIRO_MES"]),
            **_metricas(rr.iloc[0]), **_difs_ix(_indice(dd, ["DIST"])[0].get(did), mes_ref), "serie": [] if leve else _serie(g, rot),
            "categorias": _cats_dist(T.get("DN_DISTRIBUIDOR_CAT_MES"), did, mes_ref),
        })
        dists[-1]["serie_js"] = _serie_js(dists[-1]["serie"])   # RN-59
    dists.sort(key=lambda x: (x["pct_cobertura"] is None, x["pct_cobertura"] or 0))
    J["distribuidores"] = dists

    # ---- F4 (RN-44): lista global de supervisores (select da barra), tabela supervisor x categoria da Visao geral,
    #      series supervisor x categoria (t e R$) para a evolucao por categoria, aviso da hierarquia (RN-15)
    n_por_sup = dist.groupby("SUP_ID").size().to_dict()
    J["supervisores_lista"] = sorted([{"id": str(k), "nome": str(v), "n_distribuidores": int(n_por_sup.get(k, 0))}
                                      for k, v in sup_nome.items()], key=lambda x: x["nome"])
    sc_canal = T.get("DN_SUPERVISOR_CANAL_CAT_MES")
    su_tot = T["DN_SUPERVISOR_CANAL_MES"].set_index(["SUP", "ANO_MES"])
    cats_sup, evo_sup = [], {}
    if sc_canal is not None and len(sc_canal):
        for (su, cat), g in sc_canal.groupby(["SUP", "CAT"]):
            r = g[g["ANO_MES"] == mes_ref]
            if not leve:
                ser = _serie(g, rot)
                sp = _spark(ser, meses_exib)
                evo_sup.setdefault(str(su), {})[slug(str(cat))] = {"t": sp["spark_t"], "rs": sp["spark_rs"]}
            if r.empty:
                continue
            r = r.iloc[0]
            d = {"id": slug(str(cat)), "nome": str(cat).title(), "sup_id": str(su), **_metricas(r), "penetracao": _n(r.get("penetracao"))}
            for col, suf in (("volume_kg", "vol"), ("receita_rs", "rs")):
                tot = float(su_tot.loc[(su, mes_ref), col]) if (su, mes_ref) in su_tot.index else 0.0
                part = None if not tot else float(r[col]) / tot * 100
                d[f"participacao_{suf}"] = _r(part, 2)
                ly_am = canal_ix.loc[mes_ref, "ANO_MES_LY"] if mes_ref in canal_ix.index else None
                part_ly = None
                if ly_am is not None and not pd.isna(ly_am) and (su, ly_am) in su_tot.index:
                    gl = g[g["ANO_MES"] == ly_am]; tot_ly = float(su_tot.loc[(su, ly_am), col])
                    if len(gl) and tot_ly:
                        part_ly = float(gl.iloc[0][col]) / tot_ly * 100
                d[f"participacao_var_ly_{suf}"] = _r(None if part is None or part_ly is None else part - part_ly, 2)
            cats_sup.append(d)
    cats_sup.sort(key=lambda x: (x["sup_id"], -(x["cobertura_pdv"] or 0)))
    J["categorias_sup"] = cats_sup
    J["evo_sup_json"] = json.dumps(evo_sup, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    H = CFG["regras"].get("hierarquia") or {}
    J["hierarquia"] = {"aviso": str(H.get("aviso", "hierarquia vigente em {data}, aplicada a toda a série")).format(data=manifesto.dados_atualizados_em()),
                       "rotulo_sup_todos": str(_P["rotulos"].get("supervisor_todos", "Todos os supervisores"))}

    # ---- F5 (RN-23/24/25, A.10): PDVs distintos do periodo (Q-a) no canal, segmentos, supervisores e distribuidores;
    #      bloco `calendario` (perspectiva padrao, rotulos, faixas de ano do eixo) (a tabela "Ano a ano" saiu no refino E1)
    A = T["DN_ACUM_ANO"]; calx = cal.set_index("ANO_MES")
    CALC = CFG["calendario"]; TX = _P.get("textos") or {}
    ano_ref = {"civil": int(calx.loc[mes_ref, "ANO"]), "fiscal": int(calx.loc[mes_ref, "ANO_FISCAL"])}
    ANO_COL = {"civil": "ANO", "fiscal": "ANO_FISCAL"}
    def _curto(persp, a):
        tpl = str(CALC.get("rotulo_civil_curto", "{ano}") if persp == "civil" else CALC.get("rotulo_fiscal_curto", "FY{aa}"))
        return tpl.format(ano=a, aa=str(a)[2:])
    A_ly = T.get("DN_ACUM_ANO_LY")   # Refino E5: acumulado do mesmo mes do ano anterior (PDVs distintos do periodo LY)
    def _ix_acum(AA):
        """P4: {(perspectiva, ano, nivel, K1, K2, K3): pdvs_distintos} das linhas completas; a 1a linha de cada chave vale (iloc[0])."""
        if AA is None or not len(AA):
            return None
        tem_k3 = "K3" in AA.columns
        d_ = {}
        for row in AA[AA["completo"].astype(bool)].itertuples(index=False):
            key = (row.PERSPECTIVA, int(row.ANO_P), row.NIVEL, row.K1, row.K2, row.K3 if tem_k3 else "")
            if key not in d_:
                d_[key] = int(row.pdvs_distintos)
        return d_, tem_k3
    IXA, IXA_ly = _ix_acum(A), _ix_acum(A_ly)
    def _pdvs(persp, nivel, k1="", k2="", k3="", AA=None):
        ix_ = IXA if (AA is None or AA is A) else IXA_ly
        if ix_ is None:
            return None
        ano_ = ano_ref[persp] - (0 if (AA is None or AA is A) else 1)
        return ix_[0].get((persp, ano_, nivel, k1, k2, k3 if ix_[1] else ""))
    def _acum_ext(d, nivel, k1="", k2="", k3=""):
        """Refino E5: PDVs distintos do periodo, Δ% e diferenca vs o mesmo periodo do ano anterior; diferenca da medida acumulada."""
        for persp in ("civil", "fiscal"):
            pd_ = _pdvs(persp, nivel, k1, k2, k3)
            ly_ = _pdvs(persp, nivel, k1, k2, k3, AA=A_ly) if A_ly is not None else None
            d[f"acum_{persp}_pdvs"] = pd_
            d[f"acum_{persp}_var_pdvs"] = None if pd_ is None or not ly_ else (pd_ / ly_ - 1) * 100
            d[f"acum_{persp}_dif_pdvs"] = None if pd_ is None or ly_ is None else pd_ - ly_
            for med in ("t", "rs"):
                v_, l_ = d.get(f"acum_{persp}_{med}"), d.get(f"acum_{persp}_ly_{med}")
                d[f"acum_{persp}_dif_{med}"] = None if v_ is None or l_ is None else v_ - l_
    cat_raw = {slug(str(x)): str(x) for x in T["DN_CANAL_CAT_MES"]["CAT"].unique()}
    for sg in J["segmentos"]:
        todos_ = sg["id"] == "todos"
        if todos_:
            _acum_ext(sg["kpi"], "canal")
        else:
            _acum_ext(sg["kpi"], "segmento", sg["id"])
        for su in sg["supervisores"]:
            _acum_ext(su, "supervisor_canal", su["id"]) if todos_ else _acum_ext(su, "supervisor", sg["id"], su["id"])
            for cx in su.get("categorias") or []:
                _acum_ext(cx, "supervisor_canal_cat", su["id"], cat_raw.get(cx["id"], cx["id"])) if todos_ else _acum_ext(cx, "supervisor_cat", sg["id"], su["id"], cat_raw.get(cx["id"], cx["id"]))
        for cl_ in sg["clusters"]:
            _acum_ext(cl_, "cluster_canal", cl_["nome"]) if todos_ else _acum_ext(cl_, "cluster", sg["id"], cl_["nome"])
            for cx in cl_.get("categorias") or []:
                _acum_ext(cx, "cluster_canal_cat", cl_["nome"], cat_raw.get(cx["id"], cx["id"])) if todos_ else _acum_ext(cx, "cluster_cat", sg["id"], cl_["nome"], cat_raw.get(cx["id"], cx["id"]))
    for dd_ in J["distribuidores"]:
        _acum_ext(dd_, "distribuidor", dd_["cnpj"])
        for cx in dd_.get("categorias") or []:
            _acum_ext(cx, "distribuidor_cat", dd_["cnpj"], cat_raw.get(cx["id"], cx["id"]))
    for cx in J["categorias"]:
        _acum_ext(cx, "categoria", cat_raw.get(cx["id"], cx["id"]))
    for cx in J["categorias_sup"]:
        _acum_ext(cx, "supervisor_canal_cat", cx["sup_id"], cat_raw.get(cx["id"], cx["id"]))
    persp_padrao = str(CALC.get("perspectiva_padrao", "fiscal")).strip().lower()
    assert persp_padrao in ("civil", "fiscal"), f"calendario.perspectiva_padrao '{persp_padrao}' (esperado civil | fiscal)"
    def _bloco(persp):
        a = ano_ref[persp]
        sel_ = A[(A["PERSPECTIVA"] == persp) & (A["ANO_P"] == a) & (A["NIVEL"] == "canal")]
        if len(sel_):
            row = sel_.iloc[0]
        else:
            # Etapa 2: recorte (usuario) sem nenhuma venda ate este mes — o bloco do calendario sai da DIM_CALENDARIO, nao do acumulado
            ms_ = [m for m in meses if int(calx.loc[m, ANO_COL[persp]]) == a]
            mcol_ = "MES" if persp == "civil" else "MES_FISCAL"
            row = {"mes_de": ms_[0], "mes_ate": ms_[-1], "n_meses": len(ms_), "completo": int(calx.loc[ms_[0], mcol_]) == 1}
        longo = str(CALC.get("rotulo_civil_longo", "Ano {ano} ({inicio}–{fim})") if persp == "civil" else CALC.get("rotulo_fiscal_longo", "Ano fiscal {ano} ({inicio}–{fim})"))
        return {"ano": str(a), "rotulo_curto": _curto(persp, a), "rotulo_anterior_curto": _curto(persp, a - 1),
                "rotulo_longo": longo.format(ano=a, aa=str(a)[2:], inicio=rot_of(row["mes_de"]), fim=rot_of(row["mes_ate"])),
                "periodo": f"{rot_of(row['mes_de'])} a {rot_of(row['mes_ate'])}", "n_meses": int(row["n_meses"]),
                "completo": bool(row["completo"]),
                # faixas do eixo: "rotulo do mes:rotulo do ano" para todos os meses da serie (o JS agrupa os consecutivos;
                # separador ':' porque '=' e escapado pelo renderizador em {{ }})
                "faixas": ",".join(f"{rot[m]}:{_curto(persp, int(calx.loc[m, ANO_COL[persp]]))}" for m in meses)}
    J["calendario"] = {"padrao": persp_padrao,
                       "rotulo_fiscal": str(_ROT.get("cal_fiscal", "Ano fiscal")), "rotulo_civil": str(_ROT.get("cal_civil", "Ano civil")),
                       "rotulo_acum": str(_ROT.get("acum_ano", "Acumulado no ano")), "rotulo_acum_col": str(_ROT.get("acum_col", "Acum. no ano")),
                       "texto_sem_par": str(TX.get("sem_par_anual", "sem par na série (Mtrix a partir de {mes})")).format(mes=rot_of(meses[0])),
                       "civil": _bloco("civil"), "fiscal": _bloco("fiscal")}

    if leve:   # Refino E4b: mes do historico
        J["rtm"] = _rtm_mes(T, c, rot_of)
        J["carteira"] = {"ativo": False, "json": "{}"}
        J["meta_execucao"] = {"mes_referencia": mes_ref}
        return J
    # ---- F6 (RN-27..RN-36, RN-38, RN-45): aba Penetracao — tudo vem das tabelas DN_PEN_* (mes fechado); o template so exibe
    PM = T["DN_PEN_META"].iloc[0]; mp = str(PM["mes_fechado"])
    PR = CFG["regras"]["penetracao"]; POT = CFG["regras"]["potencial"]
    foco_ids = [slug(str(x)) for x in (PR.get("categorias_foco") or [])]
    cat_nome = {slug(str(k)): str(k).title() for k in T["DN_PEN_BENCHMARK"]["CAT"]}
    n_cats = int(len(T["DN_PEN_BENCHMARK"]))
    def _ptx(k, padrao):
        return str(TX.get(k, padrao))
    comp = (_ptx("pen_competencia", "Competência: {mes} (último mês fechado)") if mp == mes_ref
            else _ptx("pen_competencia_parcial", "Competência: {mes} — último mês fechado; {mes_ref} está em andamento e não entra")).format(mes=rot_of(mp), mes_ref=rot_of(mes_ref))
    jan_f = str(PM["janela_fator"]); jan_f_rot = " a ".join(rot_of(x) for x in jan_f.split(" a "))
    J["penetracao"] = {
        "competencia": rot_of(mp), "mes_fechado": mp, "usa_mes_anterior": mp != mes_ref, "texto_competencia": comp,
        "referencia": _ptx("pen_referencia", "referência: P{p} dos distribuidores na categoria, {mes}").format(p=f"{float(PM['percentil']):g}", mes=rot_of(mp)),
        "aviso": str(POT.get("aviso", "oportunidade calculada, não previsão")),
        "rotulo_entrada": str(POT.get("rotulo_entrada", "Potencial de entrada")), "rotulo_regime": str(POT.get("rotulo_regime", "Potencial em regime")),
        "verde": float(PM["verde"]), "vermelho": float(PM["vermelho"]), "percentil": float(PM["percentil"]),
        "foco_ids": ",".join(foco_ids), "foco_nomes": ", ".join(cat_nome.get(x, x) for x in foco_ids), "n_foco": len(foco_ids), "n_categorias": n_cats,
        "janela_fator": jan_f_rot, "minimo_lojas": int(PM["minimo_lojas"]), "p_outliers": float(PM["p_outliers"]),
        "texto_fator_indisponivel": _ptx("pen_fator_indisponivel", "fator indisponível: nenhuma loja fez a primeira compra da categoria na janela {janela}").format(janela=jan_f_rot),
        "texto_censura": _ptx("pen_censura", "a primeira compra da categoria é observada desde {mes}").format(mes=rot_of(meses[0])),
        "texto_media_canal": _ptx("pen_media_canal", "média do canal (< {n} lojas compradoras)").format(n=int(PM["minimo_lojas"])),
        "texto_acima": _ptx("pen_acima_referencia", "acima da referência"),
        "rotulo_todas": str(_ROT.get("pen_todas", "Todas as 10 categorias")),
        # F10 (D-A): kg/R$ por loja — no distribuidor e o valor usado no potencial; acima, a media simples do nivel; legenda de soma
        "sub_loja_usado": str(_ROT.get("pen_loja_usado", "usado no potencial")), "sub_loja_nivel": str(_ROT.get("pen_loja_nivel", "média do nível")),
        "texto_soma": _ptx("pen_soma", "soma de {n} distribuidores do nível"),
        # F7 (RN-32, RN-33, RN-38)
        "janela_ativacao": " a ".join(rot_of(x) for x in str(PM["janela_ativacao"]).split(" a ")),
        "janela_ativacao_ly": (" a ".join(rot_of(x) for x in str(PM["janela_ativacao_ly"]).split(" a ")) if str(PM["janela_ativacao_ly"]) else ""),
        "janela_meses": int(JANELA), "mascara_embutida": str((CFG["painel"].get("pdv_categoria") or {}).get("embutir_mascara", "medir")).strip().lower() in ("sim", "true", "1"),
        # 16/09/2026 (Douglas): o select "Situação" da tabela de PDVs fica so com Todos · Sem compra · Positivados · Clientes RTM;
        # as opcoes por categoria (a ativar / na janela sem compra / no mes / positivados sem a categoria) so com a chave ligada
        "situacoes_por_categoria": bool(_P.get("pdv_situacoes_por_categoria", True)),
        "mascara_bits": int(PM["mascara_bits"]),
        "rotulo_ativar": str(_ROT.get("pen_ativar", "A ativar (janela)")), "rotulo_sem_compra": str(_ROT.get("pen_sem_compra", "Sem compra no mês")),
        "rotulo_novo": str(_ROT.get("pdv_novo", "Novo na janela")),
        "sit_ativar": str(_ROT.get("pdv_sit_ativar", "A ativar em {cat}")), "sit_sem_mes": str(_ROT.get("pdv_sit_sem_mes", "Compram {cat} na janela, sem compra no mês")),
        "sit_mes": str(_ROT.get("pdv_sit_mes", "Compram {cat} no mês")),
        "sit_pos_sem": str(_ROT.get("pdv_sit_pos_sem", "Positivados no mês sem {cat}")),   # F8; desde o refino E1 mora aqui (a Matriz saiu)
        "texto_janela": _ptx("pen_janela", "janela {janela}: os {n} meses que terminam no mês fechado").format(janela=" a ".join(rot_of(x) for x in str(PM["janela_ativacao"]).split(" a ")), n=int(JANELA)),
        "texto_ativacao": _ptx("pen_ativacao_nota", "Ativação = ampliar quem compra a categoria: base elegível é a base ativa do nível (não existe cadastro de PDVs elegíveis); a ativar = base ativa − PDVs que compraram a categoria em pelo menos um mês da janela. Não confundir com \"lojas a positivar\" (gap do mês contra a referência)."),
        "texto_recorrencia": _ptx("pen_recorrencia_nota", "Recorrência mensal = PDVs que compraram a categoria no mês ÷ PDVs que a compraram na janela; \"sem compra no mês\" é a oportunidade de recorrência. Frequência = meses com compra da categoria na janela."),
        "mascara_mb": float(PM["mascara_mb"]), "mascara_limite_mb": float(PM["mascara_limite_mb"]), "mascara_cabe": bool(PM["mascara_cabe"]),
        "benchmarks": [{"id": slug(str(r.CAT)), "nome": cat_nome[slug(str(r.CAT))], "foco": bool(r.foco), "benchmark": _n(r.benchmark), "n_dist": int(r.n_dist),
                        "fator_pct": None if _n(r.fator) is None else float(r.fator) * 100, "n_lojas_novas": int(r.n_lojas_novas),
                        "kg_loja_canal": _n(r.kg_loja_canal), "rs_loja_canal": _n(r.rs_loja_canal)} for r in T["DN_PEN_BENCHMARK"].itertuples()],
    }
    # nomes por nivel
    dist_nome = dist.set_index("DIST_ID")["DISTRIBUIDOR_MTRIX"].to_dict()
    seg_of_dist = dist.set_index("DIST_ID")["SEGMENTO_ID"].to_dict(); sup_of_dist = dist.set_index("DIST_ID")["SUP_ID"].to_dict()
    def _nome(nivel, k1, k2):
        if nivel == "canal": return str(c.get("recorte_nome") or _ROT["canal"])
        if nivel == "segmento": return SEG_NOMES.get(k1, k1)
        if nivel == "supervisor_canal": return sup_nome.get(k1, k1)
        if nivel == "supervisor": return sup_nome.get(k2, k2)
        if nivel == "cluster_canal": return k1
        if nivel == "cluster": return k2
        return str(dist_nome.get(k1, k1))
    def _chaves(nivel, k1, k2):
        """(seg_id, sup_id, cluster, dist_id, dist_nome) do recorte que a linha representa."""
        seg = "todos"; sup = ""; cl = ""; did = ""
        if nivel == "segmento": seg = k1
        elif nivel == "supervisor_canal": sup = k1
        elif nivel == "supervisor": seg, sup = k1, k2
        elif nivel == "cluster_canal": cl = k1
        elif nivel == "cluster": seg, cl = k1, k2
        elif nivel == "distribuidor": did = k1; seg = seg_of_dist.get(k1, ""); sup = sup_of_dist.get(k1, "")   # atributos do distribuidor (filtros)
        return seg, sup, cl, did
    NC = T["DN_PEN_NIVEL_CAT"]; DCp = T["DN_PEN_DIST_CAT"].set_index(["DIST", "CAT"])
    pen_nivel_cat = []
    for r in NC.itertuples():
        seg, sup, cl, did = _chaves(r.NIVEL, r.K1, r.K2)
        cid = slug(str(r.CAT))
        media_canal = bool(DCp.loc[(r.K1, r.CAT), "media_canal"]) if r.NIVEL == "distribuidor" and (r.K1, r.CAT) in DCp.index else None
        pen_nivel_cat.append({"nivel": r.NIVEL, "seg_id": seg, "sup_id": sup, "cluster": cl, "dist_nome": dist_nome.get(did, "") if did else "",
                              "cat_id": cid, "categoria": cat_nome.get(cid, str(r.CAT).title()), "foco": cid in foco_ids,
                              "lojas": _n(r.lojas), "penetracao": _n(r.penetracao), "pct_cobertura": _n(r.pct_cobertura),
                              "benchmark": _n(r.benchmark), "pct_bench": _n(r.pct_bench), "cor": _txt_(r.cor),
                              "a_positivar": _n(r.a_positivar), "kg_loja": _n(r.kg_loja), "rs_loja": _n(r.rs_loja),
                              "fator_pct": None if _n(r.fator) is None else float(r.fator) * 100,
                              "potencial_t": _n(r.potencial_t), "potencial_rs": _n(r.potencial_rs), "regime_t": _n(r.regime_t), "regime_rs": _n(r.regime_rs),
                              "media_canal": media_canal, "n_media_canal": _n(r.n_media_canal),
                              "n_dist": _n(r.n_dist),   # F10 (RN-49, D-A): distribuidores somados no nivel (conta de soma da memoria)
                              "positivados_nivel": _n(r.positivados_nivel),   # F8: positivados do nivel (conta da penetracao)
                              # F7 (RN-32, RN-33)
                              "base_elegivel": _n(r.base_elegivel), "compradores_janela": _n(r.compradores_janela), "pct_compradores": _n(r.pct_compradores),
                              "a_ativar": _n(r.a_ativar), "pct_a_ativar": _n(r.pct_a_ativar), "compradores_mes": _n(r.compradores_mes),
                              "recorrencia": _n(r.recorrencia), "sem_compra_mes": _n(r.sem_compra_mes), "meses_medios": _n(r.meses_medios),
                              "pct_sem_compra_mes": (float(r.sem_compra_mes) / float(r.compradores_janela) * 100) if _n(r.compradores_janela) else None,   # F9 (N3)
                              "recorrencia_ly": _n(r.recorrencia_ly),
                              # distribuicao de frequencia (1..JANELA meses) compactada num texto "n1|n2|...|nJ" (o JS so exibe)
                              "freq": "|".join("" if _n(getattr(r, f"freq_{k}", None)) is None else str(int(getattr(r, f"freq_{k}"))) for k in range(1, int(JANELA) + 1))})
    J["pen_nivel_cat"] = pen_nivel_cat
    NL = T["DN_PEN_NIVEL"]; pen_nivel = []
    for r in NL.itertuples():
        seg, sup, cl, did = _chaves(r.NIVEL, r.K1, r.K2)
        mc = None if r.maior_cat is None or (not isinstance(r.maior_cat, str) and pd.isna(r.maior_cat)) else slug(str(r.maior_cat))
        pen_nivel.append({"nivel": r.NIVEL, "nome": _nome(r.NIVEL, r.K1, r.K2),
                          "seg_id": seg, "sup_id": sup, "cluster": cl, "dist_nome": dist_nome.get(did, "") if did else "",
                          "positivados": _n(r.positivados), "categorias_por_loja": _n(r.categorias_por_loja), "n_categorias": int(r.n_categorias),
                          "a_pos_foco": _n(r.a_pos_foco), "pot_foco_t": _n(r.pot_foco_t), "pot_foco_rs": _n(r.pot_foco_rs), "reg_foco_t": _n(r.reg_foco_t), "reg_foco_rs": _n(r.reg_foco_rs),
                          "a_pos_total": _n(r.a_pos_total), "pot_total_t": _n(r.pot_total_t), "pot_total_rs": _n(r.pot_total_rs), "reg_total_t": _n(r.reg_total_t), "reg_total_rs": _n(r.reg_total_rs),
                          "maior_cat_id": mc, "maior_cat": cat_nome.get(mc, "") if mc else None, "maior_pen": _n(r.maior_pen), "maior_bench": _n(r.maior_bench),
                          "maior_pot_t": _n(r.maior_pot_t), "maior_pot_rs": _n(r.maior_pot_rs),
                          "base_elegivel": _n(r.base_elegivel), "a_ativar_foco": _n(r.a_ativar_foco), "sem_compra_foco": _n(r.sem_compra_foco),
                          "a_ativar_total": _n(r.a_ativar_total), "sem_compra_total": _n(r.sem_compra_total)})
    J["pen_nivel"] = pen_nivel
    # supervisores e clusters: uma linha por nivel com as foco em colunas fixas (f1..fN) e os totais
    by_nc = {}
    for x in pen_nivel_cat:
        by_nc.setdefault((x["nivel"], x["seg_id"], x["sup_id"], x["cluster"]), {})[x["cat_id"]] = x
    def _pivot(niveis_seg, nivel_canal):
        out = []
        for x in pen_nivel:
            if x["nivel"] not in (niveis_seg, nivel_canal):
                continue
            row = {"segmento_id": x["seg_id"], "id": x["sup_id"] or x["cluster"], "nome": x["nome"], "positivados": x["positivados"],
                   "categorias_por_loja": x["categorias_por_loja"], "a_pos_foco": x["a_pos_foco"], "pot_foco_t": x["pot_foco_t"], "pot_foco_rs": x["pot_foco_rs"],
                   "a_pos_total": x["a_pos_total"], "pot_total_t": x["pot_total_t"], "pot_total_rs": x["pot_total_rs"]}
            cats_ = by_nc.get((x["nivel"], x["seg_id"], x["sup_id"], x["cluster"]), {})
            for k, cid in enumerate(foco_ids, start=1):
                c_ = cats_.get(cid) or {}
                row[f"pen_f{k}"] = c_.get("penetracao"); row[f"pb_f{k}"] = c_.get("pct_bench"); row[f"cor_f{k}"] = c_.get("cor"); row[f"apos_f{k}"] = c_.get("a_positivar")
            out.append(row)
        out.sort(key=lambda z: (z["segmento_id"] != "todos", z["segmento_id"], -(z["pot_foco_t"] or 0)))
        return out
    J["pen_supervisores"] = _pivot("supervisor", "supervisor_canal")
    J["pen_clusters"] = _pivot("cluster", "cluster_canal")
    # F7: as linhas de cluster ficam so no pivot (pen_clusters); o nivel ativo da aba nunca e cluster (sem filtro de cluster)
    J["pen_nivel_cat"] = [x for x in pen_nivel_cat if x["nivel"] not in ("cluster", "cluster_canal")]

    # ---- PDVs da base ativa: lista completa embutida (blob); a tabela e montada pelo componente (Fase 3)
    pb_full = T["DN_PDV_BASE_ATIVA"].merge(
        c["pdv"][["COD_PDV", "NOME_PDV", "UF", "CIDADE", "BAIRRO", "SEGMENTO_MTRIX", "ORIGEM_RTM", "TIPO_CHAVE_PDV"]],
        on="COD_PDV", how="left")
    pb_full["nome_dist"] = pb_full["DIST"].map(attrs["DISTRIBUIDOR_MTRIX"])
    pb_full["ultimo_rot"] = pb_full["ultimo_mes_compra"].map(rot_of)
    pb_full = pb_full.sort_values(["nome_dist", "kg_janela"], ascending=[True, False])
    # F7 (RN-38, Q-c): mascara PDV x categoria (janela | mes) e flag "novo" embutidas no blob quando o config manda e cabe no limite
    PCm = CFG["painel"].get("pdv_categoria") or {}
    embutir = str(PCm.get("embutir_mascara", "medir")).strip().lower() in ("sim", "true", "1")
    PMm = T["DN_PEN_META"].iloc[0]
    if embutir and not bool(PMm["mascara_cabe"]):
        L.abortar(f"painel.pdv_categoria.embutir_mascara = sim, mas a mascara mede {float(PMm['mascara_mb']):.2f} MB > limite {float(PMm['mascara_limite_mb']):g} MB (RN-38: volta a decisao)")
    masc = None
    if embutir:
        MK = T["DN_PDV_CAT_MASCARA"][["DIST", "COD_PDV", "mascara", "novo"]]
        pb_full = pb_full.merge(MK, on=["DIST", "COD_PDV"], how="left")
        pb_full["mascara"] = pb_full["mascara"].fillna(0).astype("int64"); pb_full["novo"] = pb_full["novo"].fillna(False).astype(bool)
        cats_m = str(PMm["categorias"]).split(",")
        masc = {"cats": [slug(x) for x in cats_m], "cats_nomes": [str(x).title() for x in cats_m], "bits": int(PMm["mascara_bits"])}
    J["pdv_blob"] = blob_pdvs(pb_full, pb_full["nome_dist"], masc)
    J["pdv_blob"]["mascara_embutida"] = bool(embutir)
    # ---- RN-56: carteira de PDVs ponderados — pares validos na base ativa (chave = nome do distribuidor no blob | PDV) e nota
    J["carteira"] = _carteira(T.get("DN_PDV_CARTEIRA"), dist_nome, rot_of)
    # F1 (RN-06, Q-c): pares positivados sem R$ no mes e linhas da serie com kg > 0 e R$ = 0 (nota em Definicoes)
    pares_kg_sem_rs = int(((pb_full["kg_mes"] > 0) & (pb_full["rs_mes"].fillna(0) == 0)).sum())
    ff = c["fato"]
    linhas_kg_sem_rs = int(((ff["PESO_KG"] > 0) & (ff["RECEITA"] == 0)).sum())
    # ---- RTM: aderencia ao direcionamento (clientes que sairam da Dori para o distribuidor)
    J["rtm"] = _rtm(T, rot, rot_of, c)

    # ---- metrica (F1, RN-43): padrao, rotulos dos chips e definicao do Valor vem do config (regras.metrica, painel.rotulos)
    M = CFG["regras"].get("metrica") or {}
    J["metrica"] = {"padrao": str(M.get("padrao", "t")),
                    "rotulo_t": str(_P["rotulos"].get("metrica_t", "Volume · t")),
                    "rotulo_rs": str(_P["rotulos"].get("metrica_rs", "Valor · R$")),
                    "valor_nome": str(M.get("valor_nome", "Valor do sell-through (R$)")),
                    "valor_definicao": str(M.get("valor_definicao", ""))}

    # ---- graficos (F2, RN-47/RN-22): chave padrao, rotulo do chip de PDVs e texto "sem LY" vem do config
    G = _P.get("graficos") or {}
    J["graficos"] = {"chave_padrao": str(G.get("chave_padrao", "pdv")),
                     "rotulo_pdv": str(_P["rotulos"].get("graf_pdv", "PDVs positivados")),
                     # F3 (RN-46, RN-19): evolucao por categoria — Top N, rotulo de "outras", foco (ids = slug da categoria)
                     "categorias_top_n": int(G.get("categorias_top_n", 5)),
                     "categorias_outras_rotulo": str(G.get("categorias_outras_rotulo", "Outras categorias")),
                     "categorias_foco": ",".join(slug(str(c)) for c in ((CFG["regras"].get("penetracao") or {}).get("categorias_foco") or [])),
                     "rotulo_evo_todas": str(_P["rotulos"].get("evo_todas", "todas")),
                     "rotulo_evo_foco": str(_P["rotulos"].get("evo_foco", "só as foco")),
                     "rotulo_evo_total": str(_P["rotulos"].get("evo_total", "Total do canal")),
                     "meses": ",".join(_cortar([rot[m] for m in meses])),   # F3: rótulos dos meses exibidos (mini-linhas)
                     "texto_sem_ly": str((_P.get("textos") or {}).get("sem_ly", "sem LY na série (Mtrix a partir de {mes})")).format(mes=rot_of(meses[0])),
                     "rotulo_freq": str(_P["rotulos"].get("graf_freq", "Frequência"))}   # RN-58 (decisao 3): terceira chave do grafico

    # ---- RN-59: seletor de periodo (serie inteira embutida; o navegador escolhe os pontos) ----
    J["periodo_sel"] = {"ativo": PERIODO_ATIVO, "padrao_n": int(SERIE_EXIBIDA or len(meses)), "n_total": int(len(meses)),
                        "rotulo": str(_PER.get("rotulo", "Período")),
                        "rotulo_ultimos": str(_PER.get("rotulo_ultimos", "Últimos {n} meses")).format(n=int(SERIE_EXIBIDA or len(meses))),
                        "rotulo_tudo": str(_PER.get("rotulo_tudo", "Série completa")) + f" ({rot_of(meses[0])}–{rot_of(meses[-1])})",
                        "nota": str(_PER.get("nota", ""))}

    # ---- RN-58: frequencia de compra — calibracao do mes de referencia e textos (Definicoes, nota da estimativa) ----
    FC = T["DN_FREQ_CALIBRACAO"].set_index("ANO_MES")
    fr_txt = (_P.get("textos") or {})
    J["frequencia"] = {"rotulo": str(_P["rotulos"].get("frequencia", "Frequência de compra")),
                       "rotulo_col": str(_P["rotulos"].get("frequencia_col", "Freq. compra")),
                       "nota": str(fr_txt.get("frequencia_nota", "estimativa calibrada no total Mtrix")),
                       "definicao": str(fr_txt.get("frequencia_definicao", "")),
                       "regra": str((CFG["regras"].get("frequencia") or {}).get("regra", "uniao_proporcional")),
                       # textos prontos (4 casas; o inventario formata no maximo 2)
                       "alfa_mes": (f"{float(FC.loc[mes_ref, 'alfa']):.4f}".replace(".", ",") if mes_ref in FC.index else "—"),
                       "atendimentos_mtrix": (f"{int(FC.loc[mes_ref, 'atendimentos_total']):,}".replace(",", ".") if mes_ref in FC.index else "—"),
                       "alfa_min": f"{float(FC['alfa'].min()):.4f}".replace(".", ","), "alfa_max": f"{float(FC['alfa'].max()):.4f}".replace(".", ","),
                       "n_meses": int(len(FC))}

    # ---- abas (Fase 2): ordem, rotulo e filtros aplicaveis vem do config
    abas = list(_P["abas"])
    padrao = str(_P["aba_padrao"])
    assert padrao in {a["id"] for a in abas}, f"painel.aba_padrao '{padrao}' nao esta em painel.abas"
    J["abas"] = [{"id": str(a["id"]), "rotulo": str(a["rotulo"]),
                  "filtros": ",".join(a.get("filtros") or []), "padrao": a["id"] == padrao,
                  "oculta": bool(a.get("oculta", False))} for a in abas]   # Estabilizacao A3 (14/09/2026): aba fora da navegacao
    # ---- Refino E6: Definicoes em tabelas por tema (textos do config, com os parametros do config)
    subst = {"{janela}": str(int(c["janela"])), "{novos}": str(int(NOVOS_MESES)), "{sem_venda}": str(int(SEM_VENDA_MESES)), "{janela_arq}": str(JANELA_ARQ or len(meses)),
             "{p}": str(int((CFG["regras"].get("penetracao") or {}).get("benchmark", {}).get("valor", 75)))}
    def _sub(t):
        t = str(t or "")
        for k_, v_ in subst.items():
            t = t.replace(k_, v_)
        return t
    J["definicoes"] = [{"tema": str(g["tema"]), "itens": [{"indicador": _sub(it[0]), "formula": _sub(it[1]), "obs": _sub(it[2] if len(it) > 2 else "")}
                                                          for it in g.get("itens") or []]} for g in (_P.get("definicoes") or [])]
    # ---- Refino E5: seletor de periodo unificado (Mes, Acumulado do ano, Ano) — rotulos do config
    J["periodo_modo"] = {k: str(_ROT.get("per_" + k, v)) for k, v in (
        ("rotulo", "Período"), ("mes", "Mês"), ("acum", "Acumulado do ano"), ("ano", "Ano"), ("serie_completa", "Série completa"),
        ("card_pdvs", "PDVs distintos no período"), ("card_vol", "Volume acumulado"), ("card_rs", "Valor acumulado"),
        ("card_freq", "Frequência de compra acumulada (estimativa)"), ("mr_titulo", "O que aconteceu no período"), ("ate", "até"),
        ("doze", "12 meses até"), ("acumulado", "Acumulado"), ("ano_em_curso", "{ano} · em curso"))}   # A5 (14/09/2026)
    # ---- Refino E3 (D7): bloco "O que aconteceu no mes" (tamanho da lista e rotulos do config)
    MR = _P.get("mes_ranking") or {}
    J["mes_ranking"] = {"n": int(MR.get("n", 5)), "titulo": str(_ROT.get("mr_titulo", "O que aconteceu no mês")),
                        "quedas": str(_ROT.get("mr_quedas", "Maiores quedas")), "altas": str(_ROT.get("mr_altas", "Maiores altas")),
                        "nivel_sup": str(_ROT.get("mr_nivel_sup", "Supervisor")), "nivel_dist": str(_ROT.get("mr_nivel_dist", "Distribuidor")),
                        "regua_pdv": str(_ROT.get("mr_regua_pdv", "PDVs positivados")), "sem_compra": str(_ROT.get("mr_sem_compra", "sem compra")),
                        "ver_por": str(_ROT.get("ver_por", "Ver por")), "vp_cluster": str(_ROT.get("vp_cluster", "Cluster")),
                        "vazio": str(_ROT.get("mr_vazio", "sem variação neste recorte"))}
    # ---- Refino E2 (D10-D13): rotulos da barra lateral, da linha de filtros ativos, Limpar e Voltar
    J["lateral"] = {"titulo": str(_ROT.get("lateral_titulo", "Filtros")), "recolher": str(_ROT.get("lateral_recolher", "Recolher filtros")),
                    "expandir": str(_ROT.get("lateral_expandir", "Expandir filtros")), "limpar": str(_ROT.get("lateral_limpar", "Limpar filtros")),
                    "voltar": str(_ROT.get("lateral_voltar", "Voltar")), "parcial": str(_ROT.get("lateral_parcial", "parcial")),
                    "categoria_todas": str(_ROT.get("categoria_todas", "Todas as categorias")),
                    "mes": str(_ROT.get("lateral_mes", "Mês")), "carregando": str(_ROT.get("carregando", "carregando os dados do painel…")),
                    "pdv_mes_nota": str(_ROT.get("pdv_mes_nota", "Lista de PDVs de {mes}"))}
    # ---- F9 (RN-48): KPIs crus por segmento para o motor de resumos do navegador; distribuidores sem venda (mes em andamento);
    #      regras do config e o esperado avaliado no recorte do canal (o navegador confere a si mesmo)
    KPIS = ["base_ativa", "cobertura_pdv", "pct_cobertura", "pct_cobertura_var_mes_anterior", "pct_cobertura_var_ly",
            "cobertura_var_mes_anterior", "volume_t", "receita_rs", "sem_compra_mes"]
    J["kpi_json"] = json.dumps({s["id"]: {k: s["kpi"].get(k) for k in KPIS} for s in J["segmentos"]}, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    todos_d = dist[dist["NO_PAINEL"] & dist["TEM_SELLOUT"]] if "NO_PAINEL" in dist.columns else dist
    com_venda = {d_["cnpj"] for d_ in J["distribuidores"]}
    sem_venda = sorted(str(n_) for i_, n_ in zip(todos_d["DIST_ID"], todos_d["DISTRIBUIDOR_MTRIX"]) if i_ not in com_venda) if em_andamento else []
    achados = resumos.lint_textos()
    if achados:
        L.abortar("painel.resumos: termos vetados nos textos das regras (RN-48): " + "; ".join(achados))
    esperado = resumos.avaliar(J, pb_full, foco_ids, sem_venda, met="t")
    J["resumos"] = {"ativo": bool((CFG["painel"].get("resumos") or {}).get("ativo", False)), "n_regras": len(esperado),
                    "regras_json": resumos.regras_json(),
                    "esperado_json": json.dumps(esperado, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/"),
                    "titulo": str(TX.get("resumo_titulo", "Resumo do recorte")), "sem_dado": str(TX.get("resumo_sem_dado", "sem dado suficiente para {indicador} no recorte")),
                    "sem_ly": str(TX.get("resumo_sem_ly", "sem LY na série")), "atencao": str(TX.get("resumo_atencao", "atenção")),
                    "nota": str(TX.get("resumo_nota", "")), "sem_venda": ", ".join(sem_venda)}
    J["meta_execucao"] = {"mes_referencia": mes_ref, "meses_serie": _cortar([rot[m] for m in meses]),
                          "pdvs_base_ativa_total": int(len(T["DN_PDV_BASE_ATIVA"])),
                          "pares_kg_sem_rs": pares_kg_sem_rs, "linhas_kg_sem_rs": linhas_kg_sem_rs,
                          "gerado_em": L.INICIO.strftime("%d/%m/%Y %H:%M"), "execucao_id": L.EXECUCAO_ID,
                          "dados_atualizados_em": manifesto.dados_atualizados_em()}
    # ---- F10 (RN-49): memoria de calculo por numero — fichas do config, esperado no recorte do canal, extrato das RN
    achados_m = memoria.lint_textos()
    if achados_m:
        L.abortar("painel.memoria: termos vetados nos textos das fichas (RN-48/RN-49): " + "; ".join(achados_m))
    J["memoria"] = memoria.bloco(J)
    return J
