# -*- coding: utf-8 -*-
"""Orquestrador do Scorecard DN — as seis etapas do `run_dn.py` (D1 da reforma, 09/09/2026).

    0 verificar   config, bases e manifesto (decide se a ingestão precisa rodar)
    1 ingerir     raw (bases/) -> staging (cache) -> curated (Parquet)      [pulada se nada mudou]
    2 calcular    métricas DN_* a partir da curated
    3 renderizar  JSON do painel + HTML (Handlebars mínimo validado byte a byte)
    4 validar     placeholders, tamanho, totais, RTM, manifesto, blob
    5 publicar    copia o HTML para a pasta de publicação (Painéis Comerciais/DN)

Qualquer falha aborta com mensagem clara e exit 1; nada é publicado com validação
pendente. Ao final grava `data/dn/logs/resumo_<execução>.json`.
"""
from __future__ import annotations

import base64
import gzip
import hashlib
import json
import os
import re
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

from . import manifesto, metrics, painel, qualidade, render
from . import resumos as resumos_mod
from . import tabelas as tabelas_mod
from .extract import cadastros, sellout
from .load import parquet
from .transform import calendario, dimensoes, fato as fato_mod
from .utils import log as L
from .utils.config import CFG, PASTA_CURATED, PASTA_LOGS, PASTA_PAINEL, caminho, preparar_pastas
from .utils.log import abortar, log


# ============================================================ 0 · verificar
def verificar(forcar: bool) -> dict:
    L.etapa_inicio("0 · verificar")
    F = CFG["fontes"]
    problemas: list[str] = []
    pasta = caminho(F["sellout"]["pasta"])
    if not pasta.exists():
        problemas.append(f"fontes.sellout.pasta nao existe: {pasta}")
    for chave in ("produtos", "distribuidores", "rtm"):
        a = caminho(F[chave]["arquivo"])
        if not a.exists():
            problemas.append(f"fontes.{chave}.arquivo nao existe: {a}")
    log(f"hierarquia vigente: {cadastros.arquivo_hierarquia().name}")   # 02/10/2026: a de data mais recente; aborta se fora do padrao
    clu = F.get("clusters")
    if clu and not caminho(clu["arquivo"]).exists():
        log(f"fontes.clusters.arquivo ausente ({caminho(clu['arquivo']).name}) — clusters = segmentos da Mtrix", "aviso")
    for chave in ("janela_base_ativa_meses", "segmento_novos_meses"):
        if int(CFG["regras"][chave]) <= 0:
            problemas.append(f"regras.{chave} precisa ser > 0")
    pub = CFG.get("publicacao") or {}
    if not pub.get("pasta") or not pub.get("arquivo"):
        problemas.append("publicacao.pasta e publicacao.arquivo sao obrigatorios")
    if problemas:
        abortar("config invalido:\n  " + "\n  ".join(problemas) + "\n  (config/config.yaml)")
    bases = manifesto.bases_declaradas()
    log(f"config ok · {len(bases)} arquivo(s) de base declarados e presentes")
    diff = manifesto.comparar()
    curated_ok = (PASTA_CURATED / "DIM_RTM.parquet").exists() and (PASTA_CURATED / "FATO_SELLOUT").exists()
    if not curated_ok:
        diff["precisa_ingerir"] = True
        diff["motivo"] = "camada curated incompleta (DIM_RTM/FATO_SELLOUT ausentes)"
    if forcar:
        diff["precisa_ingerir"] = True
        diff["motivo"] = "--forcar"
    for k in ("novos", "alterados", "removidos"):
        for a in diff.get(k, []):
            log(f"base {k[:-1] if k != 'novos' else 'nova'}: {a}")
    log(f"ingestao {'NECESSARIA' if diff['precisa_ingerir'] else 'desnecessaria'}: {diff['motivo']}", "ok")
    L.etapa_fim("ok", precisa_ingerir=diff["precisa_ingerir"], motivo=diff["motivo"])
    return diff


# ============================================================== 1 · ingerir
def ingerir() -> dict:
    L.etapa_inicio("1 · ingerir (raw -> staging -> curated)")
    produtos = cadastros.ler_produtos()
    depara = cadastros.ler_distribuidores()
    hier = cadastros.ler_hierarquia()
    rtm = cadastros.ler_rtm()
    clu = cadastros.ler_clusters()
    if clu is None:
        clu = pd.DataFrame({"SEGMENTO_MTRIX": pd.Series(dtype="string"), "CLUSTER": pd.Series(dtype="string")})
    pon = cadastros.ler_pdv_ponderada()      # RN-56 (opcional): carteira de PDVs ponderados
    if pon is None:
        pon = pd.DataFrame({"LINHA": pd.Series(dtype="int64"), **{c_: pd.Series(dtype="string") for c_ in
                            ("CNPJ_DISTRIBUIDOR", "DISTRIBUIDOR", "COD_PDV", "RAZAO_SOCIAL", "CLUSTER")}})

    bruto, pdv_attrs, dist_fato, meta = sellout.ler()
    meta["rtm_total"] = int(len(rtm))
    log(f"{len(bruto):,} linhas em {len(meta['arquivos'])} arquivo(s); "
        f"{bruto['ANO_MES'].nunique()} meses ({bruto['ANO_MES'].min()} a {bruto['ANO_MES'].max()})")

    f = fato_mod.construir(bruto)
    del bruto
    fato_mod.conferir_grao(f)
    dim_cal = calendario.construir(sorted(f["ANO_MES"].unique()))
    dim_dist = dimensoes.dim_distribuidor(depara, hier, dist_fato)
    dim_pdv = dimensoes.dim_pdv(pdv_attrs, rtm)
    dim_prod = dimensoes.dim_produto(f["COD_PRODUTO"], produtos)

    fato_mod.conferir_integridade(f, dim_pdv, dim_dist, dim_prod, dim_cal)
    avisos = fato_mod.reconciliar_origem(f, meta)

    f["ANO"] = f["ANO_MES"].str.slice(0, 4)
    parquet.salvar_particionado(f, "FATO_SELLOUT", "ANO")
    parquet.salvar(dim_pdv, "DIM_PDV")
    parquet.salvar(dim_dist, "DIM_DISTRIBUIDOR")
    # F4 (RN-16, A.13/D20): retrato datado da hierarquia a cada ingestao, para construir historico de supervisor
    if (CFG["regras"].get("hierarquia") or {}).get("arquivar_retrato_mensal", False):
        hist = PASTA_CURATED / "historico"
        hist.mkdir(parents=True, exist_ok=True)
        alvo_h = hist / f"DIM_DISTRIBUIDOR_{L.INICIO.strftime('%Y-%m-%d')}.parquet"
        dim_dist.to_parquet(alvo_h, index=False)
        log(f"retrato da hierarquia: {len(dim_dist)} distribuidores -> historico/{alvo_h.name}", "ok")
    parquet.salvar(dim_prod, "DIM_PRODUTO")
    parquet.salvar(dim_cal, "DIM_CALENDARIO")
    parquet.salvar(rtm, "DIM_RTM")            # D2: RTM e clusters agora vivem na curated
    parquet.salvar(clu, "DIM_CLUSTER")
    parquet.salvar(pon, "DIM_PDV_PONDERADA")
    # RN-58: linha de total de cada arquivo na curated (a calibracao da frequencia le daqui, nunca do Excel)
    gab_rows = [{"ARQUIVO": a, "ANO_MES": (meta["meses_por_arquivo"].get(a) or [None])[0], **{k: g.get(k) for k in
                 ("receita", "unidades", "peso_kg", "pdvs_positivados", "total_skus", "freq_total", "atendimentos_total", "pdvs_distintos")}}
                for a, g in meta["gabaritos"].items()]
    parquet.salvar(pd.DataFrame(gab_rows), "SELLOUT_GABARITO")

    avisos = L.avisos() + [a for a in avisos if a not in L.avisos()]
    resumo = qualidade.gerar(f.drop(columns=["ANO"]), dim_pdv, dim_dist, dim_prod, dim_cal, meta, avisos)
    resumo["gerado_em"] = L.INICIO.strftime("%d/%m/%Y %H:%M")
    (PASTA_CURATED / "resumo.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=1), encoding="utf-8")

    gab = meta["gabaritos"]
    totais = {k: float(sum((g.get(k) or 0.0) for g in gab.values())) for k in ("receita", "unidades", "peso_kg")}
    manifesto.gravar(L.EXECUCAO_ID, {"linhas_fato": int(len(f)), "totais_gabarito": totais,
                                     "arquivos_com_gabarito": len(gab), "arquivos": meta["arquivos"]})
    L.etapa_fim("ok", linhas_fato=int(len(f)), pdvs=int(len(dim_pdv)),
                distribuidores_painel=int(dim_dist["NO_PAINEL"].sum()), avisos=len(avisos))
    return resumo


# ============================================================= 2 · calcular
def calcular(mes_ref: str | None) -> tuple[dict, dict]:
    L.etapa_inicio("2 · calcular (metricas DN)")
    c = metrics.carregar(mes_ref)
    c["janela"] = metrics.JANELA
    T = metrics.calcular(c)
    for nome, df in T.items():
        parquet.salvar(df, nome)
    L.etapa_fim("ok", mes_referencia=c["mes_ref"], meses=len(c["meses"]))
    return c, T


def calcular_fechado(c: dict, T: dict) -> tuple[dict | None, dict | None]:
    """Refino E4a (D2): com o mes de referencia em andamento, o arquivo leva tambem o ultimo mes fechado. Os cubos mensais sao os
    mesmos (ja trazem todos os meses); so o que depende do mes de referencia e refeito para o mes fechado: base ativa dos PDVs,
    carteira, mascara PDV x categoria (via Penetracao, cuja competencia ja e o mes fechado) e o RTM. Nada disso e gravado na
    curated (a curated segue sendo a do mes de referencia)."""
    if not metrics.mes_em_andamento(c["mes_ref"]):
        return None, None
    L.etapa_inicio("2b · mes fechado para o arquivo com mes em andamento")
    c2, T2 = fechado(c, T)
    L.etapa_fim("ok", mes_fechado=c2["mes_ref"])
    return c2, T2


def fechado(c: dict, T: dict) -> tuple[dict, dict]:
    """Corpo da etapa 2b, sem o registro de etapa (Etapa 2: reaproveitado por usuario)."""
    mp = metrics.mes_fechado(c["meses"], c["mes_ref"])
    c2 = dict(c); c2["mes_ref"] = mp; c2["meses"] = [m for m in c["meses"] if m <= mp]
    c2["fato"] = c["fato"][c["fato"]["ANO_MES"] <= mp]
    metrics.recortar_codigos(c, c2)   # P3: pares, base ativa e codigos cortados no mes fechado (sem recalcular)
    # maturidade e historico do distribuidor contados ate o mes fechado (a divisao em segmentos dos cubos segue a do mes de
    # referencia; se algum distribuidor mudar de segmento entre os dois meses, fica o aviso)
    d2 = c["dist"].copy()
    obs2 = d2["PRIMEIRO_MES"].map(lambda p_: metrics.meses_entre(p_, mp) if pd.notna(p_) else None)
    cad2 = d2["DATA_CADASTRO"].map(lambda t_: metrics.meses_entre(pd.Timestamp(t_).strftime("%Y-%m"), mp) if pd.notna(t_) else None)
    d2["MESES_HISTORICO"] = cad2.where(cad2.notna(), obs2).map(lambda v_: int(v_) if pd.notna(v_) else None).astype(object)
    seg2 = metrics.segmento_ids(d2, mp, c["meses"], c["vendas_dist"])   # 02/10/2026: + Sem venda
    muda = d2.loc[seg2 != d2["SEGMENTO_ID"].values, "DISTRIBUIDOR_MTRIX"].tolist()
    if muda:
        log(f"{len(muda)} distribuidor(es) com segmento diferente em {mp} e em {c['mes_ref']}; o arquivo usa o segmento de {c['mes_ref']}: {muda[:6]}", "aviso")
    c2["dist"] = d2
    T2 = dict(T)
    # (E5: os PDVs distintos do periodo do mes fechado vem de metrics.acum_pdvs_mensal, na renderizacao)
    T2.update(metrics.rtm_aderencia(c2))
    T2["DN_PDV_BASE_ATIVA"] = metrics.pdvs_base_ativa(c2["fato"], c2["meses"], mp)
    T2["DN_PDV_CARTEIRA"] = metrics.carteira(c2, T2["DN_PDV_BASE_ATIVA"])
    pen = metrics.penetracao(c2, T2)
    T2["DN_PDV_CAT_MASCARA"] = pen["DN_PDV_CAT_MASCARA"]; T2["DN_PEN_META"] = pen["DN_PEN_META"]
    if not c.get("recorte"):
        metrics.carteira(c, T["DN_PDV_BASE_ATIVA"])   # o relatorio quality/carteira_pdv.md volta a ser o do mes de referencia
    return c2, T2


# =========================================================== 3 · renderizar
def renderizar(c: dict, T: dict, regerar_exemplo: bool, c2: dict | None = None, T2: dict | None = None) -> tuple[dict, dict, Path, str]:
    L.etapa_inicio("3 · renderizar (JSON + HTML)")
    J, JF, html = gerar(c, T, c2, T2, prova_template=not regerar_exemplo)
    PASTA_PAINEL.mkdir(parents=True, exist_ok=True)
    (PASTA_PAINEL / "painel_dn.json").write_text(json.dumps(JF, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"JSON: {len(J['distribuidores'])} distribuidores · {len(J['categorias'])} categorias · "
        f"{J['meta_execucao']['pdvs_base_ativa_total']:,} pares na base ativa (blob) · "
        f"RTM {J['rtm'].get('base_total', 0)} clientes · tabelas embutidas: "
        + ", ".join(f"{k} {len(v):,}" for k, v in tabelas_mod.tabelas(JF).items()), "ok")
    if regerar_exemplo:
        alvo = render.regerar_exemplo(J)
        log(f"exemplo do template regerado a partir de {c['mes_ref']} -> {alvo.name} (D8)", "ok")
        if not render.validar_renderer():
            abortar("o renderizador Python NAO reproduz o exemplo recem-gerado (template/Scorecard_DN_base.html)")
        log("renderizador validado contra template/Scorecard_DN_base.html (byte a byte)", "ok")
        html = render.render(render.template(), JF)
    alvo = PASTA_PAINEL / f"Scorecard_DN_{c['mes_ref']}.html"
    alvo.write_text(html, encoding="utf-8")
    log(f"painel -> {alvo} ({len(html.encode('utf-8')) / 1024 / 1024:.1f} MB)", "ok")
    L.etapa_fim("ok", html=str(alvo), tamanho_mb=round(len(html.encode("utf-8")) / 1024 / 1024, 2))
    return J, JF, alvo, html


def gerar(c: dict, T: dict, c2: dict | None = None, T2: dict | None = None, prova_template: bool = True) -> tuple[dict, dict, str]:
    """JSON (cru e formatado) e HTML do painel, sem gravar nada (Etapa 2: reaproveitado por usuario)."""
    AM = metrics.acum_pdvs_mensal(c)   # Refino E4b/E5: PDVs distintos acumulados de todos os meses e niveis (P2: pela tabela de pares)
    def _com_acum(TT, m_):
        """T do mes: acumulado ate o mes e o do mesmo mes do ano anterior (PDVs distintos do periodo e LY)."""
        TT = dict(TT); TT["DN_ACUM_ANO"] = AM[AM["ANO_MES"] == m_]
        TT["DN_ACUM_ANO_LY"] = AM[AM["ANO_MES"] == f"{int(m_[:4]) - 1}{m_[4:]}"]
        return TT
    J = painel.montar(c, _com_acum(T, c["mes_ref"]))
    inv = render.inventario()
    J2 = painel.montar(c2, _com_acum(T2, c2["mes_ref"])) if c2 is not None else None   # Refino E4a: mes fechado
    blobs = [(c["mes_ref"], J["pdv_blob"])] + ([(c2["mes_ref"], J2["pdv_blob"])] if J2 is not None else [])
    J["pdv_blob_comb"] = painel.combinar_pdv_blobs(blobs)
    J["meses_arquivo"] = ",".join(m for m, _ in blobs)
    JF2 = render.formatar(J2, "", inv) if J2 is not None else None
    if JF2 is not None:
        JF2["tabelas_json"] = tabelas_mod.gerar(JF2)
    # Refino E4b (D24): os demais meses da serie, montados a partir dos mesmos cubos (montar leve), do mais recente ao mais antigo
    import time as _tm
    t0_ = _tm.time()
    feitos = {c["mes_ref"]} | ({c2["mes_ref"]} if c2 is not None else set())
    JF_hist, J_hist = [], {}
    janela_ = c["meses"][-painel.JANELA_ARQ:] if painel.JANELA_ARQ else c["meses"]   # Refino E6: janela movel do arquivo
    for m_ in sorted((x for x in janela_ if x not in feitos), reverse=True):
        cm_ = dict(c); cm_["mes_ref"] = m_; cm_["meses"] = [x for x in c["meses"] if x <= m_]
        dm_ = c["dist"].copy()
        obs_ = dm_["PRIMEIRO_MES"].map(lambda p_: metrics.meses_entre(p_, m_) if pd.notna(p_) else None)
        cad_ = dm_["DATA_CADASTRO"].map(lambda t_: metrics.meses_entre(pd.Timestamp(t_).strftime("%Y-%m"), m_) if pd.notna(t_) else None)
        dm_["MESES_HISTORICO"] = cad_.where(cad_.notna(), obs_).map(lambda v_: int(v_) if pd.notna(v_) and v_ >= 0 else None).astype(object)
        cm_["dist"] = dm_
        Tm_ = _com_acum(T, m_)
        Jm_ = painel.montar(cm_, Tm_, leve=True)
        J_hist[m_] = Jm_
        JF_hist.append(render.formatar(Jm_, "", inv))
    log(f"historico: {len(JF_hist)} mes(es) montados a partir dos cubos em {_tm.time() - t0_:.1f} s", "ok")
    c["_AM"] = AM; c["_J_hist"] = J_hist; c["_com_acum"] = _com_acum
    extras_ = ([JF2] if JF2 is not None else []) + JF_hist
    JF = render.preparar(render.formatar(J, "", inv), extras_ or None)
    c["_J2"] = J2; c["_JF2"] = JF2; c["_c2"] = c2; c["_T2"] = T2; c["_JF"] = JF
    fora = render.fora_do_inventario()
    if fora:
        log(f"{len(fora)} campo(s) do JSON fora de template/data-inventory.json (passam sem formato): "
            f"{fora[:10]}", "aviso")
    if prova_template and not c.get("recorte"):
        if not render.validar_renderer():
            abortar("o renderizador Python NAO reproduz o exemplo do template (template/Scorecard_DN_base.html).\n"
                    "  Mexeu no template? Rode `python run_dn.py --regerar-exemplo` uma vez.")
        log("renderizador validado contra template/Scorecard_DN_base.html (byte a byte)", "ok")
    html = render.render(render.template(), JF)
    return J, JF, html


# ============================================================== 4 · validar
def _md5(p: Path) -> str:
    h = hashlib.md5()
    with open(p, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def validar(c: dict, T: dict, J: dict, html: str, alvo: Path) -> dict:
    L.etapa_inicio("4 · validar")
    erros: list[str] = []
    checks: dict[str, str] = {}

    def ok(nome: str, cond: bool, detalhe: str) -> None:
        checks[nome] = ("ok" if cond else "FALHOU") + " · " + detalhe
        log(f"{nome:<34} {detalhe}", "ok" if cond else "erro")
        if not cond:
            erros.append(f"{nome}: {detalhe}")

    # placeholders e tamanho
    n_ph = html.count("{{")
    ok("placeholders", n_ph == 0, f"{n_ph} '{{{{' no HTML")
    mb = len(html.encode("utf-8")) / 1024 / 1024
    lim = float(CFG["validacao"]["html_max_mb"])
    ok("tamanho do HTML", mb <= lim, f"{mb:.1f} MB (limite {lim:g} MB)")

    # card do canal x recalculo independente na fato do painel
    f, meses, mes_ref, jan = c["fato"], c["meses"], c["mes_ref"], c["janela"]
    # P5 (Etapa 1): recalculos pesados sobre as MESMAS linhas da fato em codigos inteiros (c["K"]: uma linha por linha da fato;
    # ANO_MES = posicao em `meses`). E a fato, nao os cubos: a independencia da conferencia continua a mesma.
    K_ = c["K"]; i_mes = {m_: k_ for k_, m_ in enumerate(meses)}
    posK = K_.loc[K_["PESO_KG"] > 0, ["ANO_MES", "COD_PDV"]]
    pos = f[(f["PESO_KG"] > 0) & (f["ANO_MES"] == mes_ref)]["COD_PDV"].nunique()
    i = meses.index(mes_ref)
    janela = meses[max(0, i - jan + 1):i + 1]
    base = f[(f["PESO_KG"] > 0) & f["ANO_MES"].isin(janela)]["COD_PDV"].nunique() if len(janela) == jan else None
    kg = float(f[f["ANO_MES"] == mes_ref]["PESO_KG"].sum())
    k = J["segmentos"][0]["kpi"]
    ok("card canal · positivados", int(k["cobertura_pdv"]) == int(pos), f"{k['cobertura_pdv']:,} = {pos:,}")
    ok("card canal · base ativa", (k["base_ativa"] is None and base is None) or int(k["base_ativa"]) == int(base or 0),
       f"{k['base_ativa']} = {base}")
    ok("card canal · volume", abs(float(k["volume_t"]) * 1000 - kg) < 0.5, f"{k['volume_t']:,.1f} t = {kg / 1000:,.1f} t")
    # F1 (RN-06): valor do sell-through do card = recalculo independente na fato (todas as linhas do mes, com sinal)
    rs = float(f[f["ANO_MES"] == mes_ref]["RECEITA"].sum())
    tol_rs = float(CFG["validacao"]["tolerancia_receita_reais"])
    ok("card canal · valor (R$)", k["receita_rs"] is not None and abs(float(k["receita_rs"]) - rs) <= tol_rs,
       f"R$ {float(k['receita_rs'] or 0):,.2f} = R$ {rs:,.2f}")
    n_dist_esperado = int((c["dist"]["NO_PAINEL"] & c["dist"]["TEM_SELLOUT"]).sum())
    n_dist = len(J["distribuidores"])
    if J["periodo"].get("mes_em_andamento"):
        # 10/09/2026: mes ainda correndo — distribuidor sem venda ate agora nao e erro; o painel
        # so nao pode ter MAIS distribuidores do que a curated. Os que faltam vao para o log.
        ok("distribuidores no painel (mes em andamento)", n_dist <= n_dist_esperado,
           f"{n_dist} de {n_dist_esperado} com venda em {mes_ref}")
        faltam = sorted(set(c["dist"].loc[c["dist"]["NO_PAINEL"] & c["dist"]["TEM_SELLOUT"], "DIST_ID"])
                        - {d["cnpj"] for d in J["distribuidores"]})
        if faltam:
            nomes = c["dist"].set_index("DIST_ID")["DISTRIBUIDOR_MTRIX"]
            log(f"{len(faltam)} distribuidor(es) ainda sem venda em {mes_ref}: "
                + " · ".join(str(nomes.get(x, x)) for x in faltam[:8])
                + (" ..." if len(faltam) > 8 else ""), "aviso")
    else:
        # 02/10/2026: com o segmento Sem venda, distribuidor do painel sem linha no mes fica fora da tabela do mes (o historico
        # dele segue nos cubos). A tabela tem de ter exatamente os que tem linha na fato no mes; os demais tem de ser Sem venda.
        com_linha = set(f.loc[f["ANO_MES"] == mes_ref, "DIST"].astype(str))
        no_json = {d["cnpj"] for d in J["distribuidores"]}
        fora = c["dist"][~c["dist"]["DIST_ID"].astype(str).isin(com_linha)]
        ok("distribuidores no painel", no_json == com_linha and (fora["SEGMENTO_ID"] == "sem_venda").all(),
           f"{n_dist} com linha em {mes_ref} = {len(com_linha)} · {len(fora)} sem linha no mes, todos Sem venda "
           f"(de {n_dist_esperado} do painel)")

    # RTM: os estados somam a base
    r = J["rtm"]
    dim_rtm = parquet.carregar("DIM_RTM")
    soma = int(r["kpi"]["certo"]) + int(r["kpi"]["so_outro"]) + int(r["kpi"]["sem_compra"])
    ok("RTM · estados = rastreaveis", soma == int(r["rastreaveis"]), f"{soma} = {r['rastreaveis']}")
    ok("RTM · mensuraveis + nao mensuraveis", int(r["rastreaveis"]) + int(r["nao_mensuravel"]) == int(r["base_total"]),
       f"{r['rastreaveis']} + {r['nao_mensuravel']} = {r['base_total']}")
    ok("RTM · motivos somam", sum(m["n"] for m in r["motivos"]) == int(r["nao_mensuravel"]),
       " + ".join(f"{m['n']} {m['id']}" for m in r["motivos"]) + f" = {r['nao_mensuravel']}")
    # grade cliente x mes (drills) fecha com a serie em todos os meses
    grade, ser = T["DN_RTM_CLIENTE_MES"], T["DN_RTM_MES"]
    cont = grade.groupby(["ANO_MES", "ESTADO"]).size().unstack(fill_value=0)
    dif = []
    for rr in ser.itertuples():
        for est, col in (("certo", "certo"), ("so_outro", "so_outro"), ("sem_compra", "sem_compra"), ("nao_mensuravel", "nao_mensuravel")):
            if int(cont.loc[rr.ANO_MES].get(est, 0)) != int(getattr(rr, col)):
                dif.append(f"{rr.ANO_MES}/{est}: grade {int(cont.loc[rr.ANO_MES].get(est, 0))} x serie {int(getattr(rr, col))}")
    ok("RTM · grade cliente x mes = serie", not dif, f"{len(ser)} meses x 4 estados conferidos" if not dif else "; ".join(dif[:4]))
    kg_g = grade.groupby("ANO_MES")["kg_certo"].sum()
    dkg = float((kg_g - ser.set_index("ANO_MES")["kg_certo"]).abs().max())
    ok("RTM · kg no destino (grade = serie)", dkg < 0.01, f"maior diferenca {dkg:.4f} kg")
    rs_g = grade.groupby("ANO_MES")["rs_certo"].sum()                      # F1 (RN-55)
    drs = float((rs_g - ser.set_index("ANO_MES")["rs_certo"]).abs().max())
    ok("RTM · R$ no destino (grade = serie)", drs < 0.01, f"maior diferenca R$ {drs:.4f}")
    ok("RTM · grade = clientes x meses", len(grade) == len(dim_rtm) * len(c["meses"]), f"{len(grade):,} = {len(dim_rtm)} x {len(c['meses'])}")
    rb = J["rtm"]["blob"]
    db = json.loads(gzip.decompress(base64.b64decode(rb["b64"])).decode("utf-8"))
    ok("RTM · blob descompacta", len(db["linhas"]) == len(grade) and len(db["clientes"]) == len(dim_rtm),
       f"{len(db['linhas']):,} linhas · {len(db['clientes'])} clientes · {rb['bytes_b64'] / 1024:,.0f} KB em base64")
    ok("RTM · base = DIM_RTM", int(r["base_total"]) == int(dim_rtm["COD_PDV"].nunique()),
       f"{r['base_total']} = {dim_rtm['COD_PDV'].nunique()}")

    # fato completa x totais dos gabaritos da Mtrix (guardados no manifesto pela ingestao)
    m = manifesto.gravado() or {}
    tot = m.get("totais_gabarito")
    if tot and m.get("arquivos_com_gabarito") == len(m.get("arquivos", [])):
        ff = parquet.carregar("FATO_SELLOUT", colunas=["PESO_KG"])   # P1: so a coluna conferida
        dif = abs(float(ff["PESO_KG"].sum()) - float(tot["peso_kg"]))
        ok("fato x total Mtrix (kg)", dif <= float(CFG["validacao"]["tolerancia_peso_kg"]) * len(m["arquivos"]),
           f"{ff['PESO_KG'].sum():,.1f} kg x {tot['peso_kg']:,.1f} kg (dif {dif:,.2f})")
        ok("fato · linhas = manifesto", int(len(ff)) == int(m.get("linhas_fato", -1)), f"{len(ff):,} = {m.get('linhas_fato')}")
    else:
        log("fato x total Mtrix: sem gabarito completo no manifesto — checagem nao executada", "aviso")

    # nenhuma base mais nova que a curated
    diff = manifesto.comparar()
    ok("bases x curated (manifesto)", not diff["precisa_ingerir"], diff["motivo"])

    # blob de PDVs descompacta e tem o tamanho declarado
    blob = J["pdv_blob"]
    d = json.loads(gzip.decompress(base64.b64decode(blob["b64"])).decode("utf-8"))
    ok("blob de PDVs", len(d["rows"]) == int(J["meta_execucao"]["pdvs_base_ativa_total"]) == int(blob["n"]),
       f"{len(d['rows']):,} pares descompactados = {J['meta_execucao']['pdvs_base_ativa_total']:,}")
    # F1 (RN-06): R$ do mes no blob = curated (arredondamento por par) = recalculo na fato (linhas com kg > 0 do mes)
    i_rs = d["cols"].index("rs_mes")
    rs_blob = float(sum(r[i_rs] or 0 for r in d["rows"]))
    n_rs = sum(1 for r in d["rows"] if r[i_rs] is not None)
    rs_cur = float(T["DN_PDV_BASE_ATIVA"]["rs_mes"].fillna(0).sum())
    rs_fato = float(f[(f["ANO_MES"] == mes_ref) & (f["PESO_KG"] > 0)]["RECEITA"].sum())
    ok("blob de PDVs · R$ do mes", abs(rs_cur - rs_fato) <= tol_rs and abs(rs_blob - rs_cur) <= 0.5 * n_rs + 1,
       f"blob R$ {rs_blob:,.0f} ~ curated R$ {rs_cur:,.2f} = fato R$ {rs_fato:,.2f} ({n_rs:,} pares com R$)")

    # F7 (RN-38): mascara PDV x categoria embutida no blob = curated (bits) e dentro do limite
    if "mascara" in d["cols"]:
        i_m = d["cols"].index("mascara"); i_n = d["cols"].index("novo"); i_c = d["cols"].index("cnpj"); i_d = d["cols"].index("dist")
        MKv = T["DN_PDV_CAT_MASCARA"]; nome_dist_v = c["dist"].set_index("DIST_ID")["DISTRIBUIDOR_MTRIX"].to_dict()
        MKv = MKv.assign(nome_dist=MKv["DIST"].map(nome_dist_v)).set_index(["nome_dist", "COD_PDV"])
        difs = 0; n_novo = 0; bits_ok = True
        for r_ in d["rows"][:5000]:
            k_ = (d["dists"][r_[i_d]], str(r_[i_c]))
            if k_ not in MKv.index or int(MKv.loc[k_, "mascara"]) != int(r_[i_m]) or int(bool(MKv.loc[k_, "novo"])) != int(r_[i_n]): difs += 1
            if r_[i_m] >= (1 << int(d["bits"])): bits_ok = False
            n_novo += int(r_[i_n])
        ok("mascara · embutida = curated", difs == 0 and bits_ok and len(d["cats"]) * 2 == int(d["bits"]) and float(J["penetracao"]["mascara_mb"]) <= float(J["penetracao"]["mascara_limite_mb"]),
           f"5.000 pares conferidos (mascara e 'novo') · {int(d['bits'])} bits · {len(d['cats'])} categorias · {float(J['penetracao']['mascara_mb']):.2f} MB ≤ {float(J['penetracao']['mascara_limite_mb']):g} MB" if difs == 0 else f"{difs} pares divergentes")
    else:
        ok("mascara · embutida = curated", not J["penetracao"]["mascara_embutida"], "mascara nao embutida (config medir)")
    # abas (Fase 2): template e config falam a mesma lingua e nenhuma secao ficou fora de aba
    tpl = render.template()
    ids_tpl = re.findall(r'<template id="tpl-aba-([a-z0-9_]+)">', tpl)
    ids_cfg = [str(a["id"]) for a in CFG["painel"]["abas"]]
    ok("abas · template = config", ids_tpl == ids_cfg, f"template {ids_tpl} · config {ids_cfg}")
    fora = 0
    tpl_sem_dialog = re.sub(r"<dialog.*?</dialog>", "", tpl, flags=re.S)   # o titulo do modal de drill nao e secao
    for m in re.finditer(r"<h3[ >]", tpl_sem_dialog):
        antes = tpl_sem_dialog[:m.start()]
        fora += antes.count("<template id=") == antes.count("</template>")
    ok("abas · toda secao dentro de uma aba", fora == 0, f"{fora} secao(oes) <h3> fora de <template>")
    vazias = [i for i in ids_tpl if len(re.search(r'<template id="tpl-aba-' + i + r'">(.*?)</template>', tpl, re.S).group(1).strip()) < 200]
    ok("abas · nenhuma vazia", not vazias, f"vazias: {vazias}" if vazias else f"{len(ids_tpl)} abas com conteudo")
    n_btn = len(re.findall(r'<button type="button" role="tab"', html))
    ok("abas · botoes no HTML", n_btn == len(ids_cfg), f"{n_btn} botoes role=tab = {len(ids_cfg)} abas")
    # Estabilizacao A3 (14/09/2026): abas com `oculta: true` no config existem no HTML com o botao `hidden` (fora da navegacao)
    oc_cfg = sorted(str(a["id"]) for a in CFG["painel"]["abas"] if a.get("oculta"))
    oc_html = sorted(re.findall(r'role="tab" class="tab" id="tab-([a-z0-9_]+)"[^>]* hidden aria-controls=', html))
    tpl_oc = all(f'<template id="tpl-aba-{i}">' in tpl for i in oc_cfg)
    ok("abas · ocultas = config", oc_html == oc_cfg and tpl_oc, f"ocultas no HTML {oc_html} · config {oc_cfg} · templates mantidos: {tpl_oc}")
    # Refino E2 (D10-D13): barra lateral com os filtros, linha de filtros ativos, Limpar e Voltar; categoria em lista com todas as categorias
    m_cat = re.search(r'<select[^>]*id="fsel-cat"[^>]*>(.*?)</select>', html, flags=re.S)
    n_cat = (len(m_cat.group(1).split("<option")) - 1) if m_cat else -1
    frows = re.findall(r'<div class="fbrow" data-f="([a-z]+)"', html)
    lat_ok = ('id="dnside"' in html and 'id="dnativos"' in html and 'id="dnlimpar"' in html and 'id="dnvoltar"' in html
              and n_cat == len(J["categorias"]) + 1 and frows == ["periodo", "mes", "calendario", "segmento", "supervisor", "distribuidor", "categoria", "metrica"])
    ok("lateral · filtros, ativos, limpar e voltar no HTML", lat_ok,
       f"lateral com {len(frows)} filtros na ordem {' > '.join(frows)} · categoria: {n_cat} opcoes = {len(J['categorias'])} + Todas · linha de ativos, Limpar e Voltar presentes")
    # F2 (RN-47, RN-22): LY da serie = valor do mes correspondente (ou nulo sem par); Δ do JSON = curated = recalculo
    rot2am = dict(zip(c["cal"]["ROTULO"], c["cal"]["ANO_MES"]))
    _am2rot = dict(zip(c["cal"]["ANO_MES"], c["cal"]["ROTULO"]))
    def rot2am_inv(am): return _am2rot.get(am, am)
    def _chk_serie(serie, tab, nome):
        t = tab.set_index("ANO_MES"); difs = []
        for p in serie:
            am = rot2am.get(p["mes"])
            if am is None or am not in t.index:
                difs.append(f"{nome} {p['mes']}: mes fora da curated"); continue
            ly = t.loc[am, "ANO_MES_LY"]
            if ly is None or pd.isna(ly) or ly not in t.index:
                if any(p.get(k) is not None for k in ("cobertura_ly", "volume_ly", "receita_ly")):
                    difs.append(f"{nome} {p['mes']}: sem par LY mas com valor")
                continue
            q = t.loc[ly]
            if int(p["cobertura_ly"] or 0) != int(q["positivados"]) or abs(float(p["volume_ly"] or 0) - float(q["volume_kg"]) / 1000) > 0.001 \
               or abs(float(p["receita_ly"] or 0) - float(q["receita_rs"])) > 1.0:
                difs.append(f"{nome} {p['mes']}: LY {p['cobertura_ly']}/{p['volume_ly']}/{p['receita_ly']} x {int(q['positivados'])}/{q['volume_kg']/1000:.3f}/{q['receita_rs']:.0f}")
        return difs
    difs = _chk_serie(J["dn"]["serie"], T["DN_CANAL_MES"], "canal")
    for dd_ in J["distribuidores"][:5]:
        difs += _chk_serie(dd_["serie"], T["DN_DISTRIBUIDOR_MES"][T["DN_DISTRIBUIDOR_MES"]["DIST"] == dd_["cnpj"]], dd_["nome"][:20])
    ok("serie · LY = mes correspondente", not difs, f"canal + 5 distribuidores conferidos ({len(J['dn']['serie'])} pontos no canal)" if not difs else "; ".join(difs[:3]))
    tcm = T["DN_CANAL_MES"].set_index("ANO_MES"); difs = []
    vars_ = [f"{m}_var_{k}" for m in ("cobertura", "pct_cobertura", "volume", "receita") for k in ("mes_anterior", "l3m", "ly")]
    for p in J["dn"]["serie"]:
        am = rot2am.get(p["mes"]); q = tcm.loc[am]
        for v in vars_:
            a, b = p.get(v), q.get(v)
            if (a is None) != (b is None or pd.isna(b)) or (a is not None and abs(float(a) - float(b)) > 0.011):
                difs.append(f"{p['mes']} {v}: json {a} x curated {b}")
        # recalculo independente de dois deles a partir dos valores crus da curated
        i = list(tcm.index).index(am)
        if i > 0 and p.get("cobertura_var_mes_anterior") is not None:
            rec = (float(q["positivados"]) / float(tcm.iloc[i - 1]["positivados"]) - 1) * 100
            if abs(rec - float(p["cobertura_var_mes_anterior"])) > 0.011: difs.append(f"{p['mes']} cobertura vs mes ant: {p['cobertura_var_mes_anterior']} x {rec:.2f}")
        ly = q["ANO_MES_LY"]
        if ly is not None and not pd.isna(ly) and ly in tcm.index and p.get("volume_var_ly") is not None:
            rec = (float(q["volume_kg"]) / float(tcm.loc[ly, "volume_kg"]) - 1) * 100
            if abs(rec - float(p["volume_var_ly"])) > 0.011: difs.append(f"{p['mes']} volume vs LY: {p['volume_var_ly']} x {rec:.2f}")
    ok("serie · Δ do JSON = curated = recalculo", not difs, f"{len(vars_)} comparativos x {len(J['dn']['serie'])} meses do canal" if not difs else "; ".join(difs[:3]))
    # F5 (RN-25): serie sem buraco de mes; acumulados = soma da serie; periodo incompleto = nulo; LY por juncao;
    # ano a ano (DN_ACUM_ANO) = cubos + recalculo dos PDVs distintos na fato
    def _mes_mais(am, k):
        t_ = int(am[:4]) * 12 + int(am[5:7]) - 1 + k
        return f"{t_ // 12:04d}-{t_ % 12 + 1:02d}"
    todos, m_ = [], meses[0]
    while m_ <= meses[-1]:
        todos.append(m_); m_ = _mes_mais(m_, 1)
    buracos = [m for m in todos if m not in meses]
    ok("serie · sem buraco de mes", not buracos, f"{len(meses)} meses consecutivos de {meses[0]} a {meses[-1]}" if not buracos else f"faltam {buracos[:6]} (RN-25: aborta, nunca zera)")
    calx = c["cal"].set_index("ANO_MES")
    PERSP = (("civil", "ANO", "MES"), ("fiscal", "ANO_FISCAL", "MES_FISCAL"))
    def _periodo(am, ano_col, mes_col):
        a, k = calx.loc[am, ano_col], int(calx.loc[am, mes_col])
        return [m for m in meses if calx.loc[m, ano_col] == a and int(calx.loc[m, mes_col]) <= k], k
    difs, n_chk = [], 0
    def _chk_acum(tab, nome):
        nonlocal n_chk
        t = tab.set_index("ANO_MES")
        for pref, ano_col, mes_col in PERSP:
            for am in t.index:
                periodo, k = _periodo(am, ano_col, mes_col)
                v = t.loc[am, f"ytd_{pref}_volume_kg"]
                if len(periodo) != k:
                    if not pd.isna(v): difs.append(f"{nome} {am} {pref}: periodo incompleto com acumulado {v}")
                    continue
                sub = t[t.index.isin(periodo)]
                esp_v, esp_r = float(sub["volume_kg"].sum()), float(sub["receita_rs"].sum())
                if pd.isna(v) or abs(float(v) - esp_v) > 0.01 or abs(float(t.loc[am, f"ytd_{pref}_receita_rs"]) - esp_r) > 1.0:
                    difs.append(f"{nome} {am} {pref}: {v} x {esp_v:.1f}")
                if int(t.loc[am, f"ytd_{pref}_n_meses"]) != k: difs.append(f"{nome} {am} {pref}: n_meses {t.loc[am, f'ytd_{pref}_n_meses']} x {k}")
                n_chk += 1
    _chk_acum(T["DN_CANAL_MES"], "canal")
    for sg_ in metrics.SEGMENTOS: _chk_acum(T["DN_SEGMENTO_MES"][T["DN_SEGMENTO_MES"]["SEG"] == sg_], "seg " + sg_)
    for dd_ in J["distribuidores"][:5]: _chk_acum(T["DN_DISTRIBUIDOR_MES"][T["DN_DISTRIBUIDOR_MES"]["DIST"] == dd_["cnpj"]], dd_["nome"][:20])
    ok("acumulados · soma da serie", not difs, f"{n_chk} acumulados recalculados (canal, {len(metrics.SEGMENTOS)} segmentos, 5 distribuidores · civil e fiscal)" if not difs else "; ".join(difs[:3]))
    tcan = T["DN_CANAL_MES"].set_index("ANO_MES"); det, difs = [], []
    for pref, ano_col, mes_col in PERSP:
        esp = [am for am in tcan.index if len(_periodo(am, ano_col, mes_col)[0]) == int(calx.loc[am, mes_col])]
        tem = [am for am in tcan.index if not pd.isna(tcan.loc[am, f"ytd_{pref}_volume_kg"])]
        if esp != tem: difs.append(f"{pref}: esperado {esp} x com acumulado {tem}")
        nul = [am for am in tcan.index if am not in esp]
        det.append(f"{pref} {len(esp)} com acumulado ({rot2am_inv(esp[0])} a {rot2am_inv(esp[-1])})" + (f" · {len(nul)} nulo(s) ({', '.join(rot2am_inv(x) for x in nul[:3])})" if nul else "") if esp else f"{pref}: nenhum")
    ok("acumulados · periodo incompleto = nulo", not difs, "canal: " + " · ".join(det) if not difs else "; ".join(difs[:2]))
    difs, pares_ly = [], 0
    for pref, ano_col, mes_col in PERSP:
        for am in tcan.index:
            a, k = calx.loc[am, ano_col], int(calx.loc[am, mes_col])
            par = [m for m in tcan.index if calx.loc[m, ano_col] == a - 1 and int(calx.loc[m, mes_col]) == k]
            ly = tcan.loc[am, f"ytd_{pref}_volume_ly"]
            esp = tcan.loc[par[0], f"ytd_{pref}_volume_kg"] if par else None
            if esp is None or pd.isna(esp):
                if not pd.isna(ly): difs.append(f"{am} {pref}: sem par mas com LY {ly}")
                continue
            pares_ly += 1
            var = tcan.loc[am, f"ytd_{pref}_volume_var_ly"]
            if pd.isna(ly) or abs(float(ly) - float(esp)) > 0.01 or abs(float(var) - (float(tcan.loc[am, f"ytd_{pref}_volume_kg"]) / float(esp) - 1) * 100) > 0.011:
                difs.append(f"{am} {pref}: LY {ly} x {esp}")
    ok("acumulados · LY por juncao", not difs, f"canal: {pares_ly} par(es) de acumulado com o ano anterior completo (Mtrix a partir de {rot2am_inv(meses[0])})" if not difs else "; ".join(difs[:3]))
    A_ = T["DN_ACUM_ANO"]; difs, n_aa = [], 0
    for r_ in A_[A_["NIVEL"] == "canal"].itertuples():
        col_a = "ANO" if r_.PERSPECTIVA == "civil" else "ANO_FISCAL"
        ms = [m for m in meses if int(calx.loc[m, col_a]) == int(r_.ANO_P)]
        sub = T["DN_CANAL_MES"][T["DN_CANAL_MES"]["ANO_MES"].isin(ms)]
        rec = int(posK.loc[posK["ANO_MES"].isin([i_mes[m] for m in ms]), "COD_PDV"].nunique())   # P5
        if abs(float(r_.volume_kg) - float(sub["volume_kg"].sum())) > 0.01 or abs(float(r_.receita_rs) - float(sub["receita_rs"].sum())) > 1.0 or int(r_.n_meses) != len(ms):
            difs.append(f"{r_.PERSPECTIVA} {r_.ANO_P}: kg/R$/n meses")
        if not (int(sub["positivados"].max()) <= int(r_.pdvs_distintos) <= int(sub["positivados"].sum())) or int(r_.pdvs_distintos) != rec:
            difs.append(f"{r_.PERSPECTIVA} {r_.ANO_P}: PDVs distintos {r_.pdvs_distintos} x recalculo {rec}")
        n_aa += 1
    ok("acumulados · ano a ano = cubos + fato", not difs, f"{n_aa} ano(s) x perspectiva no canal: kg e R$ = soma dos meses, PDVs distintos = recalculo na fato" if not difs else "; ".join(difs[:3]))
    # F5 (RN-23/RN-24): faixas de ano do eixo = DIM_CALENDARIO (rotulos curtos do config); chips do toggle no HTML
    difs = []
    for persp, ano_col in (("civil", "ANO"), ("fiscal", "ANO_FISCAL")):
        tplc = str(CFG["calendario"].get("rotulo_civil_curto", "{ano}") if persp == "civil" else CFG["calendario"].get("rotulo_fiscal_curto", "FY{aa}"))
        fx = dict(p.split(":") for p in J["calendario"][persp]["faixas"].split(","))
        if len(fx) != len(meses): difs.append(f"{persp}: {len(fx)} faixas x {len(meses)} meses")
        for am in meses:
            a = int(calx.loc[am, ano_col]); esp = tplc.format(ano=a, aa=str(a)[2:])
            if fx.get(rot2am_inv(am)) != esp: difs.append(f"{persp} {rot2am_inv(am)}: {fx.get(rot2am_inv(am))} x {esp}")
    ok("calendario · faixas = DIM_CALENDARIO", not difs, f"{len(meses)} meses x civil/fiscal · mes de referencia em {J['calendario']['fiscal']['rotulo_longo']} / {J['calendario']['civil']['rotulo_longo']}" if not difs else "; ".join(difs[:3]))
    n_cal = len(re.findall(r'data-cal="(civil|fiscal)"', html))
    ok("calendario · chips no HTML", n_cal == 2 and J["calendario"]["padrao"] == str(CFG["calendario"].get("perspectiva_padrao", "fiscal")),
       f"{n_cal} chips (civil, fiscal) · padrao {J['calendario']['padrao']} = config")
    # F6 (RN-27..RN-36, RN-45): competencia, benchmark, a positivar, potencial, kg/loja, fator, categorias por loja, mascara
    PM = T["DN_PEN_META"].iloc[0]; mp = str(PM["mes_fechado"])
    esp_mp = mes_ref if not J["periodo"].get("mes_em_andamento") else meses[meses.index(mes_ref) - 1]
    ok("penetracao · competencia = ultimo mes fechado", mp == esp_mp, f"{rot2am_inv(mp)}" + (" (mes de referencia em andamento: usa o anterior)" if mp != mes_ref else " = mes de referencia (fechado)"))
    BK = T["DN_PEN_BENCHMARK"].set_index("CAT"); pctl = float(CFG["regras"]["penetracao"]["benchmark"]["valor"]); difs = []
    dcx = T["DN_DISTRIBUIDOR_CAT_MES"]; dcx = dcx[(dcx["ANO_MES"] == mp) & (dcx["positivados"] > 0)]
    for cat, g in dcx.groupby("CAT"):
        rec = float(np.percentile(g["penetracao"].astype(float), pctl)); b = BK.loc[str(cat), "benchmark"]
        if b is None or pd.isna(b) or abs(float(b) - rec) > 1e-6: difs.append(f"{cat}: {b} x {rec:.3f}")
    ok("benchmark · P75 = recalculo", not difs, f"{len(BK)} categorias · P{pctl:g} da penetracao dos distribuidores com venda na categoria em {rot2am_inv(mp)}" if not difs else "; ".join(difs[:3]))
    NC = T["DN_PEN_NIVEL_CAT"]
    nun = NC.groupby("CAT")["benchmark"].nunique(dropna=True)
    ok("benchmark · fixo por categoria", bool((nun <= 1).all()), f"{len(NC):,} linhas nivel x categoria com o mesmo benchmark por categoria (RN-45)")
    DCt = T["DN_PEN_DIST_CAT"]; DCLt = T["DN_PEN_DIST_CLUSTER_CAT"]; difs = []; n_ap = 0
    for r_ in NC.itertuples():
        if r_.NIVEL == "canal": src = DCt
        elif r_.NIVEL == "segmento": src = DCt[DCt["SEG"] == r_.K1]
        elif r_.NIVEL == "supervisor_canal": src = DCt[DCt["SUP"] == r_.K1]
        elif r_.NIVEL == "supervisor": src = DCt[(DCt["SEG"] == r_.K1) & (DCt["SUP"] == r_.K2)]
        elif r_.NIVEL == "cluster_canal": src = DCLt[DCLt["CLUSTER"] == r_.K1]
        elif r_.NIVEL == "cluster": src = DCLt[(DCLt["SEG"] == r_.K1) & (DCLt["CLUSTER"] == r_.K2)]
        else: src = DCt[DCt["DIST"] == r_.K1]
        s = src[src["CAT"] == r_.CAT]
        for col in ("a_positivar", "potencial_t", "regime_t", "potencial_rs"):
            esp = s[col].sum(min_count=1); v = getattr(r_, col)
            if (pd.isna(esp) != pd.isna(v)) or (not pd.isna(esp) and abs(float(esp) - float(v)) > 1e-6): difs.append(f"{r_.NIVEL} {r_.K1} {r_.K2} {r_.CAT} {col}: {v} x {esp}")
        n_ap += 1
    ok("a positivar · niveis = Σ distribuidores", not difs, f"{n_ap:,} linhas (canal, segmentos, supervisores, clusters, distribuidores) = soma do grao distribuidor x categoria" if not difs else "; ".join(difs[:3]))
    difs = []; dmx = T["DN_DISTRIBUIDOR_MES"]; dmx = dmx[dmx["ANO_MES"] == mp].set_index("DIST")["positivados"]
    dall = T["DN_DISTRIBUIDOR_CAT_MES"]; dall = dall[dall["ANO_MES"] == mp].set_index(["DIST", "CAT"])["penetracao"]
    canal_nc = NC[NC["NIVEL"] == "canal"].set_index("CAT")
    for cat in BK.index:
        b = BK.loc[cat, "benchmark"]
        if b is None or pd.isna(b): continue
        rec = sum(max(0.0, float(b) - float(dall.get((did, cat), 0.0))) * int(pos) / 100 for did, pos in dmx.items())
        v = canal_nc.loc[cat, "a_positivar"]
        if abs(float(v) - rec) > 1e-6: difs.append(f"{cat}: {v:.1f} x {rec:.1f}")
    ok("a positivar · canal = recalculo", not difs, "Σ por distribuidor abaixo do P75 de (P75 − penetracao) × positivados: " + " · ".join(f"{c_} {int(round(canal_nc.loc[c_, 'a_positivar']))}" for c_ in [x for x in BK[BK['foco']].index]) if not difs else "; ".join(difs[:3]))
    difs = []
    for r_ in DCt.itertuples():
        if r_.a_positivar is None or pd.isna(r_.a_positivar): continue
        reg = r_.a_positivar * r_.kg_loja / 1000 if not pd.isna(r_.kg_loja) else None
        pot = None if reg is None or r_.fator is None or pd.isna(r_.fator) else reg * r_.fator
        for nome_, esp, v in (("regime_t", reg, r_.regime_t), ("potencial_t", pot, r_.potencial_t)):
            if (esp is None) != (v is None or pd.isna(v)) or (esp is not None and abs(esp - float(v)) > 1e-9): difs.append(f"{r_.DIST} {r_.CAT} {nome_}: {v} x {esp}")
    ok("potencial · = a positivar × kg/loja × fator", not difs, f"{len(DCt):,} linhas distribuidor x categoria conferidas (entrada = regime × fator; sem fator → nulo)" if not difs else "; ".join(difs[:3]))
    min_l = int(CFG["regras"]["potencial"]["minimo_lojas_distribuidor"]); difs = []
    trunc_ok = bool((BK["kg_loja_canal"] <= BK["kg_loja_canal_simples"] + 1e-9).all())
    for r_ in DCt.itertuples():
        if r_.n_lojas_kg < min_l and not r_.media_canal: difs.append(f"{r_.DIST} {r_.CAT}: {r_.n_lojas_kg} lojas sem media do canal")
        if r_.media_canal and not pd.isna(r_.kg_loja) and abs(float(r_.kg_loja) - float(BK.loc[r_.CAT, "kg_loja_canal"])) > 1e-9: difs.append(f"{r_.DIST} {r_.CAT}: media do canal divergente")
    ok("kg/loja · truncado P99 e minimo de lojas", trunc_ok and not difs, f"media truncada ≤ media simples nas {len(BK)} categorias · {int(DCt['media_canal'].sum()):,} de {len(DCt):,} linhas com < {min_l} lojas usam a media do canal" if trunc_ok and not difs else ("truncada > simples; " if not trunc_ok else "") + "; ".join(difs[:3]))
    difs = [f"{cat}: fator {r_['fator']} com {r_['n_lojas_novas']} lojas novas" for cat, r_ in BK.iterrows() if (r_["fator"] is None or pd.isna(r_["fator"])) != (int(r_["n_lojas_novas"]) == 0) or (r_["fator"] is not None and not pd.isna(r_["fator"]) and float(r_["fator"]) <= 0)]
    ok("fator · observado > 0 ou nulo sem lojas novas", not difs, "janela " + str(PM["janela_fator"]) + ": " + " · ".join(f"{c_} {float(BK.loc[c_, 'fator'])*100:.0f}%" for c_ in BK[BK["foco"]].index if not pd.isna(BK.loc[c_, "fator"])) if not difs else "; ".join(difs[:3]))
    NL = T["DN_PEN_NIVEL"]; fpos = f[(f["PESO_KG"] > 0) & (f["ANO_MES"] == mp)]
    rec_cpl = float(fpos.groupby("COD_PDV")["CAT"].nunique().mean()); v_cpl = float(NL[NL["NIVEL"] == "canal"]["categorias_por_loja"].iloc[0])
    ok("categorias por loja · recalculo na fato", abs(rec_cpl - v_cpl) < 1e-9, f"canal {v_cpl:.2f} de {int(NL['n_categorias'].iloc[0])} em {rot2am_inv(mp)} = recalculo {rec_cpl:.2f}")
    ok("mascara PDV x categoria · medicao registrada", int(PM["mascara_pares"]) == int(len(T["DN_PDV_BASE_ATIVA"])) and int(PM["mascara_bytes_b64"]) > 0,
       f"{int(PM['mascara_pares']):,} pares = base ativa · {float(PM['mascara_mb']):.2f} MB em gzip+base64 (limite {float(PM['mascara_limite_mb']):g} MB) · " + ("cabe" if bool(PM["mascara_cabe"]) else "NAO cabe") + f" · config {PM['mascara_config']}: nao embutida")
    # F7 (RN-32, RN-33, RN-41): ativacao e recorrencia — identidades, recalculo na fato, mascara, LY
    NCx = T["DN_PEN_NIVEL_CAT"]; difs = []
    for r_ in NCx.itertuples():
        if abs(float(r_.a_ativar) - (float(r_.base_elegivel) - float(r_.compradores_janela))) > 1e-9: difs.append(f"{r_.NIVEL} {r_.K1} {r_.CAT}: a ativar")
        if r_.NIVEL != "distribuidor" and int(r_.compradores_mes) != int(r_.lojas): difs.append(f"{r_.NIVEL} {r_.K1} {r_.K2} {r_.CAT}: compradores no mes {r_.compradores_mes} x lojas {r_.lojas}")
    for nivel, cubo, G in (("canal", T["DN_CANAL_CAT_MES"], []), ("segmento", T["DN_SEGMENTO_CAT_MES"], ["SEG"])):
        cm_ = cubo[cubo["ANO_MES"] == mp]
        for r_ in NCx[NCx["NIVEL"] == nivel].itertuples():
            q = cm_[(cm_["CAT"] == r_.CAT) & ((cm_["SEG"] == r_.K1) if G else True)]
            if len(q) and not pd.isna(q.iloc[0]["base_ativa"]) and int(q.iloc[0]["base_ativa"]) != int(r_.base_elegivel): difs.append(f"{nivel} {r_.K1} {r_.CAT}: base elegivel {r_.base_elegivel} x base ativa {q.iloc[0]['base_ativa']}")
    ok("ativacao · a ativar = base elegivel − compradores", not difs, f"{len(NCx):,} linhas; base elegivel = base ativa do nivel (canal e segmentos); compradores no mes = lojas" if not difs else "; ".join(difs[:3]))
    jan_v = str(PM["janela_ativacao"]).split(" a "); i0, i1 = meses.index(jan_v[0]), meses.index(jan_v[1]); jan_ms = meses[i0:i1 + 1]
    fjv = f[(f["PESO_KG"] > 0) & f["ANO_MES"].isin(jan_ms)]
    base_rec = int(fjv["COD_PDV"].nunique()); difs = []
    canal_x = NCx[NCx["NIVEL"] == "canal"].set_index("CAT")
    for cat in [x for x in BK[BK["foco"]].index][:2]:
        cj = int(fjv[fjv["CAT"] == cat]["COD_PDV"].nunique()); cmm = int(fjv[(fjv["CAT"] == cat) & (fjv["ANO_MES"] == mp)]["COD_PDV"].nunique())
        r_ = canal_x.loc[cat]
        if int(r_["compradores_janela"]) != cj or int(r_["a_ativar"]) != base_rec - cj or int(r_["compradores_mes"]) != cmm: difs.append(f"{cat}: {r_['compradores_janela']}/{r_['a_ativar']}/{r_['compradores_mes']} x {cj}/{base_rec - cj}/{cmm}")
    ok("ativacao · canal = recalculo na fato", not difs and int(canal_x["base_elegivel"].iloc[0]) == base_rec, f"base elegivel {base_rec:,} PDVs distintos na janela {rot2am_inv(jan_ms[0])} a {rot2am_inv(jan_ms[-1])}; compradores, a ativar e no mes conferidos em 2 categorias foco" if not difs else "; ".join(difs[:3]))
    MK = T["DN_PDV_CAT_MASCARA"]; cats_m = str(PM["categorias"]).split(","); difs = []; n_chk = 0
    if mp == mes_ref:
        mv = np.asarray(MK["mascara"].tolist(), dtype=np.int64)
        for did in list(MK["DIST"].drop_duplicates())[:5]:
            sel = (MK["DIST"] == did).to_numpy(dtype=bool)
            for k, cat in enumerate(cats_m[:4]):
                comp = int(((mv[sel] >> k) & 1).sum()); a_at = int(sel.sum()) - comp
                comp_m = int(((mv[sel] >> (k + len(cats_m))) & 1).sum())
                r_ = NCx[(NCx["NIVEL"] == "distribuidor") & (NCx["K1"] == did) & (NCx["CAT"] == cat)]
                if len(r_) and (int(r_.iloc[0]["a_ativar"]) != a_at or int(r_.iloc[0]["compradores_mes"]) != comp_m): difs.append(f"{did[:8]} {cat}: {r_.iloc[0]['a_ativar']}/{r_.iloc[0]['compradores_mes']} x mascara {a_at}/{comp_m}")
                n_chk += 1
        ok("ativacao · distribuidor = pares da mascara", not difs, f"{n_chk} pares distribuidor x categoria: a ativar e compradores no mes = bits da mascara ({int(PM['mascara_bits'])} bits)" if not difs else "; ".join(difs[:3]))
    else:
        ok("ativacao · distribuidor = pares da mascara", True, f"nao comparavel: mascara na base ativa de {rot2am_inv(mes_ref)} (em andamento), contagens no mes fechado {rot2am_inv(mp)}")
    difs = []
    for r_ in NCx.itertuples():
        cj_ = int(r_.compradores_janela)
        esp = None if cj_ == 0 else int(r_.compradores_mes) / cj_ * 100
        v = r_.recorrencia
        if (esp is None) != (v is None or pd.isna(v)) or (esp is not None and abs(float(v) - esp) > 1e-9): difs.append(f"{r_.NIVEL} {r_.K1} {r_.CAT}: recorrencia {v} x {esp}")
        if int(r_.sem_compra_mes) != cj_ - int(r_.compradores_mes): difs.append(f"{r_.NIVEL} {r_.K1} {r_.CAT}: sem compra no mes")
    ok("recorrencia · = compradores no mes ÷ janela", not difs, f"{len(NCx):,} linhas; canal: " + " · ".join(f"{c_} {float(canal_x.loc[c_, 'recorrencia']):.1f}%" for c_ in BK[BK["foco"]].index) if not difs else "; ".join(difs[:3]))
    fcols = [c_ for c_ in NCx.columns if c_.startswith("freq_")]; difs = []
    for r_ in NCx.itertuples():
        cj_ = int(r_.compradores_janela)
        if cj_ == 0: continue
        s_ = sum(int(getattr(r_, c_)) for c_ in fcols); mm_ = float(r_.meses_medios)
        if s_ != cj_ or not (1 - 1e-9 <= mm_ <= len(fcols) + 1e-9): difs.append(f"{r_.NIVEL} {r_.K1} {r_.CAT}: freq {s_} x {cj_} · media {mm_:.2f}")
    ok("recorrencia · distribuicao de frequencia soma os compradores", not difs, f"{len(fcols)} faixas (1 a {len(fcols)} meses) x {len(NCx):,} linhas · canal: " + " · ".join(f"{c_} {float(canal_x.loc[c_, 'meses_medios']):.2f} meses" for c_ in BK[BK["foco"]].index) if not difs else "; ".join(difs[:3]))
    tem_ly = bool(str(PM["janela_ativacao_ly"]))
    n_ly = int(NCx["recorrencia_ly"].notna().sum())
    ok("recorrencia · LY nulo sem par", (n_ly == 0) if not tem_ly else n_ly > 0, (f"sem janela LY na serie (Mtrix a partir de {rot2am_inv(meses[0])}): {n_ly} valores" if not tem_ly else f"janela LY {PM['janela_ativacao_ly']}: {n_ly:,} linhas com recorrencia LY"))
    # F9 (RN-48): resumos — regras do config avaliadas em Python no recorte do canal = recalculo independente na curated (uma por aba),
    # ids das regras e esperado no HTML, textos sem termos vetados
    # Refino E1 (D18): resumos desligados no config pulam as validacoes (codigo mantido)
    if J["resumos"]["ativo"]:
        ESP = {e["id"]: e for e in json.loads(J["resumos"]["esperado_json"].replace("<\\/", "</"))}
        def _val(idr, campo):
            e = ESP.get(idr); return None if e is None or e.get("sem_dado") else e["valores"].get(campo)
        def _perto(a, b, tol=1e-6):
            return a is not None and b is not None and abs(float(a) - float(b)) <= tol
        nome_d = c["dist"].set_index("DIST_ID")["DISTRIBUIDOR_MTRIX"].to_dict()
        checks_rs = []
        # V2: Δ absoluto de PDVs por distribuidor (DN_DISTRIBUIDOR_MES)
        dmm_ = T["DN_DISTRIBUIDOR_MES"]; ant_ = meses[meses.index(mes_ref) - 1]
        pv = dmm_.pivot_table(index="DIST", columns="ANO_MES", values="positivados")
        pv = pv[[m for m in (mes_ref, ant_) if m in pv.columns]].dropna(); dlt = (pv[mes_ref] - pv[ant_]).sort_values()
        checks_rs.append(("visao", "V2", _perto(_val("V2", "min_d_dn"), dlt.iloc[0]) and _perto(_val("V2", "max_d_dn"), dlt.iloc[-1]) and _val("V2", "min_nome") == nome_d.get(dlt.index[0]),
                          f"V2 {nome_d.get(dlt.index[0])} {int(dlt.iloc[0]):+d} / {nome_d.get(dlt.index[-1])} {int(dlt.iloc[-1]):+d}"))
        # E1: Δ t por categoria (DN_CANAL_CAT_MES)
        ccm_ = T["DN_CANAL_CAT_MES"]; pv = ccm_.pivot_table(index="CAT", columns="ANO_MES", values="volume_kg")[[mes_ref, ant_]].dropna(); dl = ((pv[mes_ref] - pv[ant_]) / 1000).sort_values()
        checks_rs.append(("evolucao", "E1", _perto(_val("E1", "min_d_dm"), dl.iloc[0], 0.002) and _perto(_val("E1", "max_d_dm"), dl.iloc[-1], 0.002), f"E1 {dl.index[0]} {dl.iloc[0]:+.1f} t / {dl.index[-1]} {dl.iloc[-1]:+.1f} t"))
        # C1: Δ p.p. por cluster (DN_CLUSTER_CANAL_MES)
        clm_ = T["DN_CLUSTER_CANAL_MES"]; q_ = clm_[clm_["ANO_MES"] == mes_ref].dropna(subset=["pct_cobertura_var_mes_anterior"]).sort_values("pct_cobertura_var_mes_anterior")
        checks_rs.append(("clusters", "C1", _perto(_val("C1", "min_valor_pp"), q_.iloc[0]["pct_cobertura_var_mes_anterior"], 0.006) and _val("C1", "min_nome") == str(q_.iloc[0]["CLUSTER"]), f"C1 {q_.iloc[0]['CLUSTER']} {q_.iloc[0]['pct_cobertura_var_mes_anterior']:+.2f} p.p."))
        # D1: Δ% cobertura por distribuidor, com o piso de base do config (F10, Q6: PDVs do distribuidor no mes de comparacao)
        regs_rs_ = {r_["id"]: r_ for r_ in ((CFG["painel"].get("resumos") or {}).get("regras") or [])}
        pis_ = regs_rs_.get("D1", {}).get("piso") or {}
        base_ant_ = dmm_[dmm_["ANO_MES"] == ant_].set_index("DIST")["positivados"]
        q_ = dmm_[dmm_["ANO_MES"] == mes_ref].dropna(subset=["cobertura_var_mes_anterior"])
        if pis_:
            q_ = q_[q_["DIST"].map(base_ant_).fillna(-1) >= float(pis_["min"])]
        q_ = q_.sort_values("cobertura_var_mes_anterior")
        checks_rs.append(("distribuidores", "D1", _perto(_val("D1", "min_valor_pct"), q_.iloc[0]["cobertura_var_mes_anterior"], 0.006) and _val("D1", "min_nome") == nome_d.get(q_.iloc[0]["DIST"])
                          and _perto(_val("D1", "max_valor_pct"), q_.iloc[-1]["cobertura_var_mes_anterior"], 0.006) and _val("D1", "max_nome") == nome_d.get(q_.iloc[-1]["DIST"]),
                          f"D1 {nome_d.get(q_.iloc[0]['DIST'])} {q_.iloc[0]['cobertura_var_mes_anterior']:+.1f}% / {nome_d.get(q_.iloc[-1]['DIST'])} {q_.iloc[-1]['cobertura_var_mes_anterior']:+.1f}%"
                          + (f" (piso ≥ {float(pis_['min']):g} PDVs em {ant_}: {len(q_)} distribuidores)" if pis_ else "")))
        # P2: concentracao no blob (DN_PDV_BASE_ATIVA)
        kgv = np.sort(T["DN_PDV_BASE_ATIVA"]["kg_mes"].fillna(0).astype(float).values)[::-1]; k10 = max(1, int(len(kgv) * 0.10))
        checks_rs.append(("pdv", "P2", _perto(_val("P2", "pct10_pct"), kgv[:k10].sum() / kgv.sum() * 100, 1e-6) and int(_val("P2", "n_pares_n") or 0) == len(kgv), f"P2 10% maiores = {kgv[:k10].sum() / kgv.sum() * 100:.1f}%"))
        # R4: destino com maior % sem compra (DN_RTM_DESTINO, mensuraveis)
        rd_ = T["DN_RTM_DESTINO"]; rd_ = rd_[rd_["COBERTO"] == True].copy(); rd_["p"] = rd_["sem_compra"] / rd_["clientes"] * 100
        pis4_ = regs_rs_.get("R4", {}).get("piso") or {}   # F10 (Q7): piso de clientes no destino
        if pis4_:
            rd_ = rd_[rd_[str(pis4_.get("campo", "clientes"))] >= float(pis4_["min"])]
        q_ = rd_.sort_values(["p", "clientes"])
        checks_rs.append(("rtm", "R4", _perto(_val("R4", "valor_pct"), q_.iloc[-1]["p"]) and _val("R4", "nome") == str(q_.iloc[-1]["DESTINO"]),
                          f"R4 {q_.iloc[-1]['DESTINO']} {q_.iloc[-1]['p']:.1f}%" + (f" (piso ≥ {float(pis4_['min']):g} clientes: {len(rd_)} destinos)" if pis4_ else "")))
        # N1/N3: canal (DN_PEN_NIVEL_CAT)
        nc_ = T["DN_PEN_NIVEL_CAT"]; cn_ = nc_[nc_["NIVEL"] == "canal"]
        a1 = cn_.sort_values("a_positivar").iloc[-1]; cn2 = cn_.assign(p=cn_["sem_compra_mes"] / cn_["compradores_janela"] * 100).sort_values("sem_compra_mes"); a3 = cn2.iloc[-1]
        checks_rs.append(("penetracao", "N1/N3", _perto(_val("N1", "valor_n"), a1["a_positivar"]) and _val("N1", "nome") == str(a1["CAT"]).title() and _perto(_val("N3", "valor_n"), a3["sem_compra_mes"]) and _perto(_val("N3", "pct_pct"), a3["p"]) and _val("N3", "nome") == str(a3["CAT"]).title(),
                          f"N1 {str(a1['CAT']).title()} {int(a1['a_positivar'])} · N3 {str(a3['CAT']).title()} {int(a3['sem_compra_mes'])} ({a3['p']:.1f}%)"))
        for aba_, idr, cond, det in checks_rs:
            ok(f"resumos · {aba_} = curated", bool(cond), det if cond else f"{det} x JSON {ESP.get(idr.split('/')[0], {}).get('valores')}")
        regs_cfg = (CFG["painel"].get("resumos") or {}).get("regras") or []
        ids_html = all(f'"id":"{r_["id"]}"' in html for r_ in regs_cfg)
        n_esp = len(ESP); n_sem = sum(1 for e in ESP.values() if e.get("sem_dado")); n_at = sum(1 for e in ESP.values() if e.get("atencao"))
        ok("resumos · regras do config no HTML", ids_html and 'var DN_RS=' in html and J["resumos"]["ativo"],
           f"{len(regs_cfg)} regras no config · {n_esp} avaliadas no recorte do canal ({n_at} em atencao, {n_sem} sem dado) · ids e esperado no HTML")
        ok("resumos · textos sem termos vetados", not resumos_mod.lint_textos(), f"{len((CFG['painel'].get('resumos') or {}).get('termos_vetados') or [])} termos vetados conferidos em {len(regs_cfg)} textos")
    # F10 (RN-49): memoria de calculo — fichas do config no HTML, aritmetica sobre os dados crus do painel e a curated (D-A inclusa),
    # parcelas no inventario, RN citadas vigentes, fontes = config, ligacoes presentes no template, textos sem termos vetados, modal
    # Refino E1 (D18): memoria desligada no config pula as validacoes (codigo mantido)
    if (J.get("memoria") or {}).get("ativo"):
        import gzip as _gz, base64 as _b64, re as _re
        from . import memoria as memoria_mod
        FM = memoria_mod.fichas(); MB = J.get("memoria") or {}
        ok("memoria · fichas do config no HTML", bool(MB.get("ativo")) and 'id="dados-memoria"' in html and all(f'"id":"{f_["id"]}","rn":' in html for f_ in FM) and '"esperado":{' in html,
           f"{len(FM)} fichas · {MB.get('n_rn', 0)} RN no extrato · esperado do recorte do canal embutido")
        difs = []; n_chk = 0
        for s_ in J["segmentos"]:
            for f_ in FM:
                if any(str(l_).startswith("card:") for l_ in f_.get("liga") or []):
                    for met_ in ("t", "rs"):
                        n_chk += len(memoria_mod.checks(f_, met_)); difs += memoria_mod.confere_linha(f_, s_["kpi"], met_)
        pen_f = [f_ for f_ in FM if any(str(l_).startswith(("pen:", "col:pen_")) for l_ in f_.get("liga") or [])]
        for x_ in J["pen_nivel_cat"]:
            for f_ in pen_f:
                for met_ in ("t", "rs"):
                    if not memoria_mod.agregada(f_, x_):
                        n_chk += len(memoria_mod.checks(f_, met_))
                    difs += memoria_mod.confere_linha(f_, x_, met_)
        rtm_m = memoria_mod.rtm_linha(J, cru=True)
        for f_ in FM:
            if "rtm:aderencia" in (f_.get("liga") or []):
                n_chk += len(memoria_mod.checks(f_)); difs += memoria_mod.confere_linha(f_, rtm_m)
        fdn_ = next(f_ for f_ in FM if f_["id"] == "dn_distribuidor"); n_cubos = 0
        for tab_ in ("DN_CLUSTER_CANAL_MES", "DN_SUPERVISOR_CANAL_MES", "DN_DISTRIBUIDOR_MES", "DN_DISTRIBUIDOR_CAT_MES", "DN_CANAL_CAT_MES"):
            q_ = T.get(tab_)
            if q_ is None or not {"positivados", "base_ativa", "pct_cobertura"} <= set(q_.columns):
                continue
            n_cubos += 1
            for r_ in q_[(q_["ANO_MES"] == mes_ref) & q_["base_ativa"].notna()][["positivados", "base_ativa", "pct_cobertura"]].itertuples(index=False):
                n_chk += 1; difs += memoria_mod.confere_linha(fdn_, {"cobertura_pdv": r_.positivados, "base_ativa": r_.base_ativa, "pct_cobertura": r_.pct_cobertura})
        dcx_ = T["DN_PEN_DIST_CAT"]; ncx_ = T["DN_PEN_NIVEL_CAT"]
        som_ = dcx_.groupby("CAT")[["potencial_t", "regime_t", "potencial_rs", "regime_rs"]].sum(min_count=1)
        cnx_ = ncx_[ncx_["NIVEL"] == "canal"].set_index("CAT")
        for cat_ in som_.index:
            for col_ in som_.columns:
                a_ = som_.loc[cat_, col_]; b_ = cnx_.loc[cat_, col_] if cat_ in cnx_.index else np.nan
                n_chk += 1
                if (pd.isna(a_) != pd.isna(b_)) or (not pd.isna(a_) and abs(float(a_) - float(b_)) > max(1e-6, abs(float(b_)) * 1e-9)):
                    difs.append(f"canal {cat_} {col_}: Σ distribuidores {a_} x nivel {b_}")
        ndx_ = ncx_[ncx_["NIVEL"] == "distribuidor"]
        kx_ = pd.concat([dcx_.set_index(dcx_["DIST"].astype(str) + "|" + dcx_["CAT"].astype(str))["kg_loja"].astype(float).rename("usado"),
                         ndx_.set_index(ndx_["K1"].astype(str) + "|" + ndx_["CAT"].astype(str))["kg_loja"].astype(float).rename("exibido")], axis=1)
        d_a = int(((kx_["usado"] - kx_["exibido"]).abs() > 1e-9).sum() + (kx_["usado"].isna() != kx_["exibido"].isna()).sum())
        ok("memoria · aritmetica = curated", not difs and d_a == 0,
           (f"{n_chk:,} conferencias: cards de {len(J['segmentos'])} segmentos em t e R$, {len(J['pen_nivel_cat']):,} linhas nivel x categoria no grao, RTM, "
            f"{n_cubos} cubos (cobertura ÷ base ativa), potencial e regime dos niveis = Σ distribuidores · D-A: kg/loja do distribuidor = usado no potencial em {len(kx_):,} pares")
           if not difs and d_a == 0 else "; ".join(difs[:4]) + f" ({len(difs)} diferencas) · kg/loja exibido ≠ usado em {d_a}")
        inv_f = {e_["path"].split(".")[-1] for e_ in json.loads((render.TEMPLATE_DIR / "data-inventory.json").read_text(encoding="utf-8"))}
        cols_blob = set(json.loads(_gz.decompress(_b64.b64decode(J["pdv_blob"]["b64"])))["cols"])
        faltam_ = sorted({f"{f_['id']}.{p_}" for f_ in FM for p_ in memoria_mod.parcelas(f_) if p_ not in inv_f and p_ not in cols_blob})
        ok("memoria · toda parcela existe no inventario", not faltam_,
           f"{sum(len(memoria_mod.parcelas(f_)) for f_ in FM)} parcelas de {len(FM)} fichas no data-inventory.json (kg_janela e rs_janela: colunas declaradas do blob de PDVs)"
           if not faltam_ else "fora do inventario: " + ", ".join(faltam_))
        dic_ = memoria_mod.dicionario(); cit_ = memoria_mod.rns_citadas()
        ruins_ = [x_ for x_ in cit_ if x_ not in dic_ or "vigente" not in dic_[x_]["status"].lower()]
        ok("memoria · RN citada existe e esta vigente", not ruins_,
           f"{len(cit_)} RN citadas, todas vigentes em docs/regras_negocio.md" if not ruins_ else "ausente ou nao vigente: " + ", ".join(ruins_))
        fcfg_ = set((CFG.get("fontes") or {}).keys())
        cur_ = set(T.keys()) | {p_.stem for p_ in (memoria_mod.RAIZ / str(CFG["projeto"]["pasta_dados"]) / "curated").glob("*.parquet")}
        ruins_ = [f"{f_['id']}: {x_}" for f_ in FM for x_ in (f_.get("fonte") or []) if x_ not in fcfg_] + \
                 [f"{f_['id']}: {x_}" for f_ in FM for x_ in (f_.get("curated") or []) if x_ not in cur_]
        ok("memoria · fonte = config", not ruins_,
           f"fontes das {len(FM)} fichas = chaves de `fontes` ({', '.join(sorted({x_ for f_ in FM for x_ in f_.get('fonte') or []}))}); tabelas citadas existem na curated"
           if not ruins_ else "; ".join(ruins_))
        lig_ = memoria_mod.ligacoes(FM); ruins_ = []
        for alvo_, fid_ in lig_["alvo"].items():
            if f'data-mem="{fid_}"' not in html and f"dnMemPen('{fid_}'" not in html and f"dnMemRtm('{fid_}'" not in html:
                ruins_.append(alvo_)
        for chave_, fid_ in lig_["col"].items():
            tab_, colk_ = chave_.split(".", 1)
            if f"{tab_}:{{id:'{tab_}'" not in html or (f"'{colk_}'" not in html and f"k:{colk_}," not in html):
                ruins_.append("col:" + chave_)
        usados_ = set(_re.findall(r'data-mem="([a-z_]+)"', html)) | set(_re.findall(r"dnMem(?:Pen|Rtm)\('([a-z_]+)'", html))
        orf_ = sorted(usados_ - {f_["id"] for f_ in FM}); sem_ = sorted({f_["id"] for f_ in FM} - set(lig_["alvo"].values()) - set(lig_["col"].values()))
        ok("memoria · todo numero marcado tem ficha", not ruins_ and not orf_ and not sem_,
           f"{len(lig_['alvo'])} cards (Visão geral, Penetração, RTM) e {len(lig_['col'])} colunas ligadas, todos no HTML; nenhum botão sem ficha; nenhuma ficha sem ligação"
           if not (ruins_ or orf_ or sem_) else f"ligacao sem alvo: {ruins_} · botao sem ficha: {orf_} · ficha sem ligacao: {sem_}")
        lint_m = memoria_mod.lint_textos()
        ok("memoria · textos sem termos vetados", not lint_m,
           f"{len((CFG['painel'].get('resumos') or {}).get('termos_vetados') or [])} termos vetados conferidos nas {len(FM)} fichas e nos textos (o rótulo obrigatório do potencial, RN-35, é permitido)"
           if not lint_m else "; ".join(lint_m))
        ok("memoria · modal no HTML", 'id="dnmem"' in html and "dnMemCopiar" in html and 'class="mem-i"' in html, "dialog da memoria, botao copiar e marcas no HTML")
    # RN-56: carteira de PDVs ponderados — toda linha classificada pela regra, pares no HTML = validos na base ativa, botoes = config
    KC = T.get("DN_PDV_CARTEIRA"); CB = J.get("carteira") or {}
    if KC is None or not len(KC) or not CB.get("ativo"):
        ok("carteira · linhas = validas + invalidas", True, "fonte opcional ausente ou vazia: painel sem a carteira")
        ok("carteira · pares no HTML = validos na base ativa", 'id="dados-carteira"' in html, "sem carteira: JSON inativo no HTML")
        ok("carteira · botoes e padrao = config", True, "sem carteira: sem botões")
    else:
        pon_n = len(parquet.carregar("DIM_PDV_PONDERADA"))
        fx_ = c["fato"]; alvo_ = set(KC["COD_PDV"].dropna().astype(str))
        g_ = fx_[(fx_["PESO_KG"] > 0) & fx_["COD_PDV"].isin(alvo_)]
        comp_ = set(zip(g_["DIST"].astype(str), g_["COD_PDV"].astype(str)))
        pain_ = set(c["dist"]["CNPJ_DISTRIBUIDOR"].astype(str))
        V_ = KC[KC["VALIDA"].astype(bool)]
        ruins_ = [int(r_.LINHA) for r_ in V_.itertuples() if (str(r_.CNPJ_DISTRIBUIDOR), str(r_.COD_PDV)) not in comp_ or str(r_.CNPJ_DISTRIBUIDOR) not in pain_]
        sem_mot = int(((~KC["VALIDA"].astype(bool)) & KC["MOTIVO"].fillna("").eq("")).sum())
        cond_ = len(KC) == pon_n and not ruins_ and sem_mot == 0
        ok("carteira · linhas = validas + invalidas", cond_,
           (f"{len(KC)} linhas da planilha = {len(V_)} válidas (" + ", ".join(f"{k_} {v_}" for k_, v_ in V_["CLUSTER"].value_counts().items())
            + f") + {len(KC) - len(V_)} fora da regra, todas com motivo · cada válida conferida na fato (compra na série, distribuidor no painel)")
           if cond_ else f"linhas {len(KC)} x planilha {pon_n} · válidas sem compra ou fora do painel: {ruins_[:8]} · fora sem motivo: {sem_mot}")
        pares_ = json.loads(CB["json"].replace("<" + chr(92) + "/", "</"))["pares"]
        ba_ = T["DN_PDV_BASE_ATIVA"]; nb_ = c["dist"].set_index("DIST_ID")["DISTRIBUIDOR_MTRIX"].to_dict()
        blob_ = {f"{nb_.get(d_)}|{p_}" for d_, p_ in zip(ba_["DIST"], ba_["COD_PDV"])}
        esp_ = int(V_["NA_BASE_ATIVA"].astype(bool).sum()); fb_ = [k_ for k_ in pares_ if k_ not in blob_]
        ok("carteira · pares no HTML = validos na base ativa", len(pares_) == esp_ and not fb_,
           f"{len(pares_)} pares no JSON = {esp_} válidos na base ativa de {mes_ref}; todos encontrados na lista de PDVs" if len(pares_) == esp_ and not fb_
           else f"JSON {len(pares_)} x esperado {esp_} · fora da lista de PDVs: {fb_[:5]}")
        PC_ = CFG["painel"].get("pdv_carteira") or {}
        rot_ok = all(str(o_[1]) in html for o_ in PC_.get("opcoes") or []) and f'"padrao":"{PC_.get("padrao")}"' in html and 'id="pdv-cart-nota"' in html and "dnCartExtras()" in html
        ok("carteira · botoes e padrao = config", rot_ok,
           f"botões {' · '.join(str(o_[1]) for o_ in PC_.get('opcoes') or [])} no HTML · padrão {PC_.get('padrao')} · nota presente" if rot_ok else "rótulos, padrão, nota ou botões ausentes no HTML")
    # F8: positivados do distribuidor na Penetracao = cubo (a Matriz saiu no refino E1; a conferencia fica)
    dmv = T["DN_DISTRIBUIDOR_MES"]; dmv = dmv[dmv["ANO_MES"] == mp].set_index("DIST")["positivados"]
    nome2id = c["dist"].set_index("DISTRIBUIDOR_MTRIX")["DIST_ID"].to_dict(); difs = []; n_m = 0
    for x_ in J["pen_nivel_cat"]:
        if x_["nivel"] != "distribuidor": continue
        did_ = nome2id.get(x_["dist_nome"]); n_m += 1
        if did_ not in dmv.index or int(x_["positivados_nivel"]) != int(dmv[did_]): difs.append(x_["dist_nome"][:20])
    ok("penetracao · positivados do distribuidor = cubo", not difs, f"{n_m} pares distribuidor x categoria = DN_DISTRIBUIDOR_MES em {rot2am_inv(mp)}" if not difs else "; ".join(difs[:3]))
    # F7 (RN-38): situacoes por categoria e rotulo "novo" chegam ao HTML (PDV_ROT) e os blocos de ativacao/recorrencia existem
    ok("pdv · situacoes por categoria no HTML", 'var PDV_ROT=' in html and J["penetracao"]["sit_ativar"] in html
       and 'data-tabela="pen_ativacao"' in html and 'data-tabela="pen_recorrencia"' in html,
       f"PDV_ROT com '{J['penetracao']['sit_ativar']}' / '{J['penetracao']['sit_sem_mes']}' / '{J['penetracao']['sit_mes']}' · blocos pen_ativacao e pen_recorrencia")
    # F6 (RN-36): limiares de cor do config chegam ao HTML (DN_PEN) e a competencia aparece na aba
    PRc = CFG["regras"]["penetracao"]
    tem_cores = f"verde:{float(PRc['cor_verde_pct']):g},vermelho:{float(PRc['cor_vermelho_pct']):g}" in html
    ok("penetracao · cores e competencia no HTML", tem_cores and J["penetracao"]["texto_competencia"] in html,
       f"verde {float(PRc['cor_verde_pct']):g}% · vermelho {float(PRc['cor_vermelho_pct']):g}% · '{J['penetracao']['texto_competencia']}'")
    # F4 (RN-44): select de supervisores no HTML = lista; series supervisor x categoria (evo) = curated
    n_opt = len(re.findall(r'<select[^>]*id="fsel-sup"[^>]*>(.*?)</select>', html, flags=re.S)[0].split("<option")) - 1 if re.search(r'id="fsel-sup"', html) else -1
    ok("supervisores · select no HTML", n_opt == len(J["supervisores_lista"]) + 1, f"{n_opt} opcoes = {len(J['supervisores_lista'])} supervisores + Todos")
    evo_sup = json.loads(J["evo_sup_json"].replace("<\\/", "</"))
    n_evo = sum(len(v) for v in evo_sup.values())
    n_cur = int(T["DN_SUPERVISOR_CANAL_CAT_MES"].groupby(["SUP", "CAT"]).ngroups)
    ok("evo_sup · series supervisor x categoria", n_evo == n_cur and all(len(x["t"]) == len(J["dn"]["serie"]) for v in evo_sup.values() for x in v.values()),
       f"{n_evo} series = {n_cur} pares na curated · {len(J['dn']['serie'])} pontos cada")
    # Refino E3 (D7): diferencas absolutas vs mes anterior (supervisor, distribuidor e suas linhas por categoria) = recalculo nos cubos
    ant_e3 = meses[meses.index(mes_ref) - 1] if meses.index(mes_ref) > 0 else None
    difs = []; n_e3 = 0
    def _chk_dif(item, cubo, filtro, nome):
        a_ = cubo[filtro & (cubo["ANO_MES"] == mes_ref)]; b_ = cubo[filtro & (cubo["ANO_MES"] == ant_e3)] if ant_e3 else cubo.iloc[0:0]
        if a_.empty or b_.empty:
            if any(item.get(k) is not None for k in painel.DIFS): difs.append(nome + ": dif sem par")
            return 1
        ep = int(a_.iloc[0]["positivados"]) - int(b_.iloc[0]["positivados"])
        ev = (float(a_.iloc[0]["volume_kg"]) - float(b_.iloc[0]["volume_kg"])) / 1000; er = float(a_.iloc[0]["receita_rs"]) - float(b_.iloc[0]["receita_rs"])
        if item.get("cobertura_dif_mes_anterior") != ep or abs(float(item.get("volume_dif_mes_anterior") or 0) - ev) > 1e-6 or abs(float(item.get("receita_dif_mes_anterior") or 0) - er) > 1e-3:
            difs.append(f"{nome}: {item.get('cobertura_dif_mes_anterior')} x {ep}")
        return 1
    dm3 = T["DN_DISTRIBUIDOR_MES"]; dc3 = T["DN_DISTRIBUIDOR_CAT_MES"].assign(_slug=lambda x: x["CAT"].map(lambda v: painel.slug(str(v))))
    for d_ in J["distribuidores"]:
        n_e3 += _chk_dif(d_, dm3, dm3["DIST"] == d_["cnpj"], "dist " + d_["nome"][:20])
        for c_ in d_.get("categorias") or []:
            n_e3 += _chk_dif(c_, dc3, (dc3["DIST"] == d_["cnpj"]) & (dc3["_slug"] == c_["id"]), "dist×cat " + c_["id"])
    for sg in J["segmentos"]:
        cub = T["DN_SUPERVISOR_CANAL_MES"] if sg["id"] == "todos" else T["DN_SUPERVISOR_MES"][T["DN_SUPERVISOR_MES"]["SEG"] == sg["id"]]
        for su in sg["supervisores"]:
            n_e3 += _chk_dif(su, cub, cub["SUP"] == su["id"], f"sup {sg['id']} {su['id']}")
    ok("mes · diferencas vs mes anterior = cubos", not difs,
       f"{n_e3:,} linhas (distribuidores, distribuidor × categoria e supervisores por segmento): PDVs, t e R$ = mês − {rot2am_inv(ant_e3) if ant_e3 else '—'}" if not difs else "; ".join(difs[:3]))
    n_seg_js = sum(1 for sg in J["segmentos"] if sg.get("serie_js")); n_sc_js = sum(len(sg.get("categorias_serie") or []) for sg in J["segmentos"])
    n_clu = sum(len(sg["clusters"]) for sg in J["segmentos"]); n_clu_js = len(re.findall(r"DN_SERIES\['clu-[^']+'\]=", html))
    n_sc_cur = int(T["DN_SEGMENTO_CAT_MES"].groupby(["SEG", "CAT"]).ngroups)
    ok("series · segmento, segmento × categoria e cluster no HTML", n_seg_js == len(metrics.SEGMENTOS) and n_sc_js == n_sc_cur and n_clu_js == n_clu and len(re.findall(r"DN_SERIES\['seg-[^']+'\]=", html)) == len(metrics.SEGMENTOS),
       f"{n_seg_js} séries de segmento · {n_sc_js} segmento × categoria = {n_sc_cur} pares na curated · {n_clu_js} clusters = {n_clu} linhas")
    # Refino E4a (D2, D22): pacotes comprimidos = tabelas de cada mes; lista de PDVs combinada = listas de cada mes; mes fechado conferido
    import gzip as _gz4, base64 as _b644
    JF_ = c["_JF"]
    DC = json.loads(JF_["dados_comprimidos_json"].replace("<\\/", "</"))
    meses_arq = [x["id"] for x in DC["meses"]]
    fontes4 = [JF_] + ([c["_JF2"]] if c.get("_JF2") is not None else []) + [render.formatar(c["_J_hist"][x_["id"]], "", render.inventario()) for x_ in DC["meses"] if x_["id"] in c.get("_J_hist", {})]
    difs = []
    for x, jf_ in zip(DC["meses"], fontes4):
        pk = json.loads(_gz4.decompress(_b644.b64decode(x["b64"])))
        tt = tabelas_mod.tabelas(jf_)
        for k_ in tabelas_mod.MES_TABELAS:
            cols_, rows_ = pk["tabelas"][k_]["c"], pk["tabelas"][k_]["r"]
            back = [dict(zip(cols_, r_)) for r_ in rows_]
            if len(rows_) != len(tt[k_]) or any(any(o_.get(kk) != b_.get(kk) for kk in cols_) for o_, b_ in zip(tt[k_], back)):
                difs.append(f"{x['id']} {k_}")
        if pk["kpi"] != {s_["id"]: s_["kpi"] for s_ in jf_["segmentos"]}: difs.append(f"{x['id']} kpi")
    est = json.loads(_gz4.decompress(_b644.b64decode(DC["est"]))); tt0 = tabelas_mod.tabelas(JF_)
    for k_ in tabelas_mod.EST_TABELAS:
        if len(est[k_]["r"]) != len(tt0[k_]): difs.append(f"est {k_}")
    # Refino E4b: montar leve no mes de referencia e no fechado = montar completo (prova de que os meses do historico seguem a mesma conta)
    for cc_, jj_ in ([(c, J)] + ([(c["_c2"], c["_J2"])] if c.get("_J2") is not None else [])):
        ccl = dict(cc_); Tl = c["_com_acum"](T if cc_ is c else c["_T2"], cc_["mes_ref"])
        jl = painel.montar(ccl, Tl, leve=True)
        a_ = render.formatar(jj_, "", render.inventario()); b_ = render.formatar(jl, "", render.inventario())
        ta, tb = tabelas_mod.tabelas(a_), tabelas_mod.tabelas(b_)
        for k_ in tabelas_mod.MES_TABELAS:
            if len(ta[k_]) != len(tb[k_]) or any(any(x_.get(kk) != y_.get(kk) for kk in set(x_) | set(y_) if kk not in ("serie", "serie_js")) for x_, y_ in zip(ta[k_], tb[k_])):
                difs.append(f"leve {cc_['mes_ref']} {k_}")
        if {s_["id"]: s_["kpi"] for s_ in a_["segmentos"]} != {s_["id"]: s_["kpi"] for s_ in b_["segmentos"]}: difs.append(f"leve {cc_['mes_ref']} kpi")
        ra_, rb_ = a_["rtm"], b_["rtm"]
        if ra_["kpi"] != rb_["kpi"] or ra_["por_supervisor_json"] != rb_["por_supervisor_json"] or ra_["rastreaveis"] != rb_["rastreaveis"]: difs.append(f"leve {cc_['mes_ref']} rtm")
        if a_["calendario"]["fiscal"] != b_["calendario"]["fiscal"] or a_["calendario"]["civil"] != b_["calendario"]["civil"]: difs.append(f"leve {cc_['mes_ref']} calendario")
        cl_ = painel.rtm_clientes_da_lista(J["rtm"]["blob"], cc_["mes_ref"]); cp_ = jj_["rtm"]["clientes"]
        campos_ = ("cnpj", "nome", "nome_origem", "destino", "supervisor", "uf", "cidade", "estado", "situacao", "ultimo_mes_compra", "ativado", "mes_ativacao", "ativado_mig", "mes_ativacao_mig")
        cld_ = {x_["cnpj"]: x_ for x_ in cl_}
        dcl = sum(1 for x_ in cp_ if x_["cnpj"] not in cld_ or any(x_.get(k2) != cld_[x_["cnpj"]].get(k2) for k2 in campos_)
                  or any(abs(float(x_.get(k2) or 0) - float(cld_[x_["cnpj"]].get(k2) or 0)) > 0.051 for k2 in ("kg_certo", "kg_outro"))
                  or any(abs(float(x_.get(k2) or 0) - float(cld_[x_["cnpj"]].get(k2) or 0)) > 0.51 for k2 in ("receita_rs", "receita_outro_rs")))
        ordem_ok = [x_["cnpj"] for x_ in cp_] == [x_["cnpj"] for x_ in cl_]
        if len(cp_) != len(cl_) or dcl: difs.append(f"clientes RTM {cc_['mes_ref']}: {len(cp_)} x {len(cl_)}, {dcl} diferentes")
        if not ordem_ok: log(f"clientes RTM {cc_['mes_ref']}: mesma lista, ordem de desempate diferente da do pipeline (a tabela ordena na tela)", "aviso")
    ok("comprimidos · pacotes = tabelas de cada mes", not difs and 'id="dados-comprimidos"' in html,
       f"{len(meses_arq)} meses no arquivo ({meses_arq[0]} a {meses_arq[-1]}) · {len(tabelas_mod.MES_TABELAS)} tabelas por mês (só colunas lidas pelo template) + cards + RTM · montar leve = completo no mês de referência e no fechado · clientes RTM pela lista = tabela do pipeline · {len(tabelas_mod.EST_TABELAS)} tabelas fixas" if not difs else "; ".join(difs[:4]))
    # Refino E4b: cards do canal de cada mes = cubo; PDVs distintos acumulados de cada mes (canal) = fato
    difs = []
    cm4 = T["DN_CANAL_MES"].set_index("ANO_MES")
    for x_ in DC["meses"]:
        jm_ = c["_J_hist"].get(x_["id"])
        if jm_ is None: continue
        k_ = jm_["segmentos"][0]["kpi"]; r_ = cm4.loc[x_["id"]]
        if k_["cobertura_pdv"] != int(r_["positivados"]) or abs(float(k_["volume_t"]) * 1000 - float(r_["volume_kg"])) > 0.5: difs.append(f"cards {x_['id']}")
    calx4 = c["cal"].set_index("ANO_MES"); pos4 = posK   # P5: codigos (mesmas linhas kg > 0 da fato)
    AMc = c["_AM"][c["_AM"]["NIVEL"] == "canal"].set_index(["PERSPECTIVA", "ANO_MES"])["pdvs_distintos"]
    n4 = 0
    for persp4, col4 in (("civil", "ANO"), ("fiscal", "ANO_FISCAL")):
        for m_ in c["meses"]:
            ms_ = [x for x in c["meses"] if x <= m_ and int(calx4.loc[x, col4]) == int(calx4.loc[m_, col4])]
            esp_ = int(pos4.loc[pos4["ANO_MES"].isin([i_mes[x] for x in ms_]), "COD_PDV"].nunique()); n4 += 1
            if int(AMc.loc[(persp4, m_)]) != esp_: difs.append(f"acum {persp4} {m_}: {int(AMc.loc[(persp4, m_)])} x {esp_}")
    AA = T["DN_ACUM_ANO"]; AAc = AA[(AA["NIVEL"] != "categoria")]
    for r_ in AAc.itertuples():
        k4 = (r_.PERSPECTIVA, r_.mes_ate)
        sel = c["_AM"][(c["_AM"]["PERSPECTIVA"] == r_.PERSPECTIVA) & (c["_AM"]["ANO_MES"] == r_.mes_ate) & (c["_AM"]["NIVEL"] == r_.NIVEL) & (c["_AM"]["K1"] == r_.K1) & (c["_AM"]["K2"] == r_.K2) & (c["_AM"]["K3"] == "")]
        if len(sel) != 1 or int(sel.iloc[0]["pdvs_distintos"]) != int(r_.pdvs_distintos): difs.append(f"acum x DN_ACUM_ANO {r_.PERSPECTIVA} {r_.ANO_P} {r_.NIVEL} {r_.K1}")
    ok("historico · cards e PDVs distintos acumulados de cada mes", not difs,
       f"cards do canal de {len(c['_J_hist'])} meses = cubo · PDVs distintos acumulados do canal em {n4} mês × perspectiva = fato · {len(AAc)} linhas de DN_ACUM_ANO (fim de cada ano da série) iguais" if not difs else "; ".join(difs[:4]))
    cb_ = json.loads(_gz4.decompress(_b644.b64decode(J["pdv_blob_comb"]["b64"])))
    difs = []; n_cmp = 0
    blobs_ = [J["pdv_blob"]] + ([c["_J2"]["pdv_blob"]] if c.get("_J2") is not None else [])
    idx_fix = [cb_["cols"].index(x_) for x_ in cb_["cols_fixas"]]; idx_mes = [i_ for i_ in range(len(cb_["cols"])) if i_ not in idx_fix]
    for k_mes, b_ in enumerate(blobs_):
        d_ = json.loads(_gz4.decompress(_b644.b64decode(b_["b64"])))
        orig = {(str(r_[0]), d_["dists"][r_[2]]): r_ for r_ in d_["rows"]}
        rec = {}
        for r_ in cb_["rows"]:
            m_ = r_[len(cb_["cols_fixas"]) + k_mes]
            if m_ is None: continue
            full = [None] * len(cb_["cols"])
            for j_, i_ in enumerate(idx_fix): full[i_] = r_[j_]
            for j_, i_ in enumerate(idx_mes): full[i_] = m_[j_]
            nome_d = cb_["dists"][full[2]]; full[2] = d_["dists"].index(nome_d); full[3] = d_["clusters"].index(cb_["clusters"][r_[3]])
            rec[(str(full[0]), nome_d)] = full
        n_cmp += len(orig)
        if set(orig) != set(rec) or any(orig[k2] != rec[k2] for k2 in orig): difs.append(f"mes {k_mes}: {len(set(orig) ^ set(rec))} pares diferentes")
    ok("pdv · lista combinada = listas de cada mes", not difs and cb_["meses"] == meses_arq[:len(blobs_)],
       f"{len(cb_['rows']):,} pares distribuidor × PDV no arquivo · {n_cmp:,} linhas conferidas coluna a coluna ({', '.join(cb_['meses'])})" if not difs else "; ".join(difs))
    if c.get("_J2") is not None:
        c2_, J2_ = c["_c2"], c["_J2"]; mp_ = c2_["mes_ref"]; f_ = c["fato"]; k2_ = J2_["segmentos"][0]["kpi"]
        pos2 = f_[(f_["PESO_KG"] > 0) & (f_["ANO_MES"] == mp_)]["COD_PDV"].nunique()
        i2 = c2_["meses"].index(mp_); jan_ = c2_["meses"][i2 - c["janela"] + 1:i2 + 1]
        ba2 = f_[(f_["PESO_KG"] > 0) & (f_["ANO_MES"].isin(jan_))]["COD_PDV"].nunique()
        kg2 = float(f_[f_["ANO_MES"] == mp_]["PESO_KG"].sum()); rs2 = float(f_[f_["ANO_MES"] == mp_]["RECEITA"].sum())
        cond2 = (k2_["cobertura_pdv"] == pos2 and k2_["base_ativa"] == ba2 and abs(float(k2_["volume_t"]) * 1000 - kg2) < 0.5
                 and abs(float(k2_["receita_rs"]) - rs2) <= float(CFG["validacao"]["tolerancia_receita_reais"]) and len(J2_["distribuidores"]) == int((c["dist"]["NO_PAINEL"] & c["dist"]["TEM_SELLOUT"]).sum()))
        ok("mes fechado · cards do canal = fato", cond2,
           f"{rot2am_inv(mp_)}: positivados {k2_['cobertura_pdv']:,} = {pos2:,} · base ativa {k2_['base_ativa']:,.0f} = {ba2:,} · {float(k2_['volume_t']):,.1f} t · R$ {float(k2_['receita_rs']):,.0f} · {len(J2_['distribuidores'])} distribuidores")
        r2_ = J2_["rtm"]; kk2 = r2_["kpi"]
        ano2 = int(c2_["cal"].set_index("ANO_MES").loc[mp_, "ANO"]); jan2 = [m_ for m_ in c2_["meses"] if m_.startswith(str(ano2))]
        pd2 = f_[(f_["PESO_KG"] > 0) & (f_["ANO_MES"].isin(jan2))]["COD_PDV"].nunique()
        ok("mes fechado · acumulado de PDVs distintos = fato", k2_.get("acum_civil_pdvs") == pd2,
           f"Ano Calendário {ano2} até {rot2am_inv(mp_)}: {k2_.get('acum_civil_pdvs')} = {pd2:,} PDVs distintos")
        ok("mes fechado · RTM estados = mensuraveis", kk2["certo"] + kk2["so_outro"] + kk2["sem_compra"] == r2_["rastreaveis"],
           f"{rot2am_inv(mp_)}: {kk2['certo']} + {kk2['so_outro']} + {kk2['sem_compra']} = {r2_['rastreaveis']}")
        ok("mes fechado · lista de PDVs = base ativa", J2_["pdv_blob"]["n"] == len(c["_T2"]["DN_PDV_BASE_ATIVA"]),
           f"{rot2am_inv(mp_)}: {J2_['pdv_blob']['n']:,} pares = {len(c['_T2']['DN_PDV_BASE_ATIVA']):,}")
    # Refino E5 (D8, D25, D26): acumulado de cada linha = cubo; PDVs distintos do periodo de cluster e categoria = fato; Δ = recalculo
    difs = []; n5 = 0
    fx5 = c["fato"][c["fato"]["PESO_KG"] > 0]; cal5 = c["cal"].set_index("ANO_MES")
    ano5 = int(cal5.loc[mes_ref, "ANO_FISCAL"]); ms5 = [x for x in meses if int(cal5.loc[x, "ANO_FISCAL"]) == ano5 and x <= mes_ref]
    ly5 = f"{int(mes_ref[:4]) - 1}{mes_ref[4:]}"; ms5ly = [x for x in meses if int(cal5.loc[x, "ANO_FISCAL"]) == ano5 - 1 and x <= ly5]
    f5 = fx5[fx5["ANO_MES"].isin(ms5)]; f5ly = fx5[fx5["ANO_MES"].isin(ms5ly)]
    cl5 = f5.groupby("CLUSTER", observed=True)["COD_PDV"].nunique(); ct5 = f5.groupby("CAT", observed=True)["COD_PDV"].nunique()
    ctly5 = f5ly.groupby("CAT", observed=True)["COD_PDV"].nunique()
    dmc5 = T["DN_DISTRIBUIDOR_MES"]; dmc5 = dmc5[dmc5["ANO_MES"] == mes_ref].set_index("DIST")
    for d_ in J["distribuidores"]:
        n5 += 1
        if abs(float(d_["acum_fiscal_t"] or 0) * 1000 - float(dmc5.loc[d_["cnpj"], "ytd_fiscal_volume_kg"] or 0)) > 0.5: difs.append(f"dist {d_['nome'][:15]} acum t")
    for cl_ in next(s_ for s_ in J["segmentos"] if s_["id"] == "todos")["clusters"]:
        n5 += 1
        if cl_["acum_fiscal_pdvs"] != int(cl5.get(cl_["nome"], -1)): difs.append(f"cluster {cl_['nome']} pdvs {cl_['acum_fiscal_pdvs']} x {cl5.get(cl_['nome'])}")
    for cx in J["categorias"]:
        n5 += 1; raw_ = str(cx["nome"]).upper()
        esp_ = int(ct5.get(raw_, -1)); esly_ = ctly5.get(raw_)
        if cx["acum_fiscal_pdvs"] != esp_: difs.append(f"categoria {raw_} pdvs {cx['acum_fiscal_pdvs']} x {esp_}")
        if esly_ and ms5ly and len(ms5ly) == len(ms5) and cx["acum_fiscal_var_pdvs"] is not None and abs(cx["acum_fiscal_var_pdvs"] - (esp_ / esly_ - 1) * 100) > 1e-6:
            difs.append(f"categoria {raw_} Δ pdvs")
    ok("periodo · acumulado de cada linha = cubo e fato", not difs,
       f"FY{str(ano5)[2:]} até {rot2am_inv(mes_ref)}: {n5} linhas (distribuidores: t acumulada = cubo; clusters e categorias: PDVs distintos do período = fato; Δ de PDVs das categorias vs mesmo período do ano anterior)" if not difs else "; ".join(difs[:4]))
    # F3 (RN-46): participacao das categorias soma 100 (t e R$); Δ vs LY = recalculo na curated
    for suf, col in (("vol", "volume_kg"), ("rs", "receita_rs")):
        soma = sum(float(cat.get(f"participacao_{suf}") or 0) for cat in J["categorias"])
        ok(f"categorias · participacao ({suf}) soma 100", abs(soma - 100) <= 0.05, f"{soma:.2f}%")
    ccm = T["DN_CANAL_CAT_MES"]; tcm2 = T["DN_CANAL_MES"].set_index("ANO_MES"); difs = []
    ly_am = tcm2.loc[mes_ref, "ANO_MES_LY"]
    for cat in J["categorias"]:
        for suf, col in (("vol", "volume_kg"), ("rs", "receita_rs")):
            v = cat.get(f"participacao_var_ly_{suf}")
            if ly_am is None or pd.isna(ly_am) or ly_am not in tcm2.index:
                if v is not None: difs.append(f"{cat['id']} {suf}: sem par LY mas com Δ")
                continue
            g = ccm[ccm["CAT"].map(lambda x: str(x).title()) == cat["nome"]]
            a = g[g["ANO_MES"] == mes_ref]; b = g[g["ANO_MES"] == ly_am]
            if a.empty or b.empty:
                if v is not None: difs.append(f"{cat['id']} {suf}: sem linha no LY mas com Δ")
                continue
            rec = float(a.iloc[0][col]) / float(tcm2.loc[mes_ref, col]) * 100 - float(b.iloc[0][col]) / float(tcm2.loc[ly_am, col]) * 100
            if v is None or abs(float(v) - rec) > 0.011: difs.append(f"{cat['id']} {suf}: {v} x {rec:.2f}")
    ok("categorias · participacao vs LY = recalculo", not difs, f"{len(J['categorias'])} categorias x t/R$" if not difs else "; ".join(difs[:3]))
    # F1 (RN-43): os dois lados do seletor de metrica sempre pareados na marcacao
    n_kg = len(re.findall(r'class="m-kg"', html)); n_rs = len(re.findall(r'class="m-rs"', html))
    ok("metrica · pares t/R$ no HTML", n_kg == n_rs and n_kg > 0, f"{n_kg} marcacoes m-kg = {n_rs} m-rs")

    # tabelas (Fase 3): registros embutidos = tabelas DN_* do mes; nenhuma linha estatica sobrando no template
    JF_tab = tabelas_mod.tabelas(render.formatar(J, "", render.inventario()))
    mref = c["mes_ref"]
    esperado = {
        # 10/09/2026: a tabela traz o total do distribuidor e uma linha por categoria
        "distribuidores": int((T["DN_DISTRIBUIDOR_MES"]["ANO_MES"] == mref).sum())
                          + int((T["DN_DISTRIBUIDOR_CAT_MES"]["ANO_MES"] == mref).sum()),
        "categorias": int((T["DN_CANAL_CAT_MES"]["ANO_MES"] == mref).sum()),
        "clusters": int((T["DN_CLUSTER_CANAL_MES"]["ANO_MES"] == mref).sum()) + int((T["DN_CLUSTER_MES"]["ANO_MES"] == mref).sum())
        + int((T["DN_CLUSTER_CANAL_CAT_MES"]["ANO_MES"] == mref).sum()) + int((T["DN_CLUSTER_CAT_MES"]["ANO_MES"] == mref).sum()),   # F4: linhas por categoria
        "supervisores": int((T["DN_SUPERVISOR_CANAL_MES"]["ANO_MES"] == mref).sum()) + int((T["DN_SUPERVISOR_MES"]["ANO_MES"] == mref).sum())
        + int((T["DN_SUPERVISOR_CANAL_CAT_MES"]["ANO_MES"] == mref).sum()) + int((T["DN_SUPERVISOR_CAT_MES"]["ANO_MES"] == mref).sum()),   # F4: linhas por categoria
        "categorias_sup": int((T["DN_SUPERVISOR_CANAL_CAT_MES"]["ANO_MES"] == mref).sum()),   # F4
        # F6 (RN-27..RN-36): tabelas da Penetracao = DN_PEN_*
        "pen_nivel_cat": int((~T["DN_PEN_NIVEL_CAT"]["NIVEL"].isin(["cluster", "cluster_canal"])).sum()), "pen_nivel": int(len(T["DN_PEN_NIVEL"])),   # F7: clusters so no pivot
        "pen_supervisores": int(T["DN_PEN_NIVEL"]["NIVEL"].isin(["supervisor", "supervisor_canal"]).sum()),
        "pen_clusters": int(T["DN_PEN_NIVEL"]["NIVEL"].isin(["cluster", "cluster_canal"]).sum()),
        # a serie exibida pode ser menor que a calculada (painel.serie_meses_exibidos); com o seletor de periodo (RN-59) vai a serie
        # inteira; D18 revista (RN-44): + as linhas por supervisor do destino (DN_RTM_SUP_MES)
        "rtm_serie": (len(painel._cortar(list(range(len(T["DN_RTM_MES"]))))) + sum(len(painel._cortar(list(range(len(g_))))) for _, g_ in T["DN_RTM_SUP_MES"].groupby("SUP"))) if painel.PERIODO_ATIVO
        else min(int(len(T["DN_RTM_MES"])), painel.SERIE_EXIBIDA or 10 ** 6),
        "rtm_destinos": int(len(T["DN_RTM_DESTINO"])), "rtm_clientes": int(len(T["DN_RTM_CLIENTE"])),
    }
    for k, n in esperado.items():
        ok(f"tabela {k} · registros", len(JF_tab[k]) == n, f"{len(JF_tab[k]):,} no JSON = {n:,} na curated")
    # categoria x distribuidor (10/09/2026): o kg das categorias fecha com o do distribuidor e
    # a cobertura de uma categoria nunca passa a do distribuidor (PDV que compra 2 categorias
    # conta uma vez no total e uma em cada categoria: a SOMA das categorias e maior, e e assim mesmo)
    dcat_m = T["DN_DISTRIBUIDOR_CAT_MES"]
    dcat_m = dcat_m[dcat_m["ANO_MES"] == mref]
    dtot_m = T["DN_DISTRIBUIDOR_MES"]
    dtot_m = dtot_m[dtot_m["ANO_MES"] == mref].set_index("DIST")
    kg_cat = dcat_m.groupby("DIST")["volume_kg"].sum()
    dkg_cat = float((kg_cat - dtot_m["volume_kg"]).abs().max()) if len(kg_cat) else 0.0
    ok("categorias x distribuidor · volume", dkg_cat < 0.01, f"maior diferenca {dkg_cat:.4f} kg")
    # F4 (RN-37): os cubos supervisor x categoria e cluster x categoria fecham com os cubos do nivel (kg, todos os meses)
    for nome, chave, cubo_cat, cubo_niv in (("supervisor", ["SEG", "SUP"], "DN_SUPERVISOR_CAT_MES", "DN_SUPERVISOR_MES"),
                                             ("supervisor (canal)", ["SUP"], "DN_SUPERVISOR_CANAL_CAT_MES", "DN_SUPERVISOR_CANAL_MES"),
                                             ("cluster", ["SEG", "CLUSTER"], "DN_CLUSTER_CAT_MES", "DN_CLUSTER_MES"),
                                             ("cluster (canal)", ["CLUSTER"], "DN_CLUSTER_CANAL_CAT_MES", "DN_CLUSTER_CANAL_MES")):
        a_ = T[cubo_cat].groupby(["ANO_MES"] + chave)["volume_kg"].sum()
        b_ = T[cubo_niv].set_index(["ANO_MES"] + chave)["volume_kg"]
        d_ = float((a_ - b_.reindex(a_.index)).abs().max()) if len(a_) else 0.0
        pc = T[cubo_cat].set_index(["ANO_MES"] + chave)["positivados"]
        pn = T[cubo_niv].set_index(["ANO_MES"] + chave)["positivados"].reindex(pc.index)
        exc = int((pc > pn).sum()) if len(a_) else 0
        ok(f"categorias x {nome} · volume", d_ < 0.01 and exc == 0, f"maior diferenca {d_:.4f} kg · {len(a_):,} celulas · {exc} categoria(s) com cobertura acima do nivel")
    excede = [f"{d}/{c}" for d, c, p in zip(dcat_m["DIST"], dcat_m["CAT"], dcat_m["positivados"])
              if d in dtot_m.index and p > dtot_m.loc[d, "positivados"]]
    ok("categorias x distribuidor · cobertura", not excede,
       f"{len(dcat_m):,} par(es) distribuidor x categoria conferido(s)" if not excede else "; ".join(excede[:4]))

    tpl_html = tpl.split("<!-- JS compartilhado")[0]          # so a parte de marcacao (o JS monta <tbody> em texto)
    ok("tabelas · sem linhas estaticas", "<tbody" not in tpl_html, f"{tpl_html.count('<tbody')} <tbody> na marcacao do template (esperado 0)")
    ok("drill · modal no HTML", 'id="dndrill"' in html and 'data-tabela="drill"' not in html, "dialog do drill presente")
    for k in esperado:
        # F4: categorias_sup alimenta a tabela de categorias; F6: pen_nivel_cat e pen_nivel alimentam cards, grafico e tabelas da Penetracao
        tem = (f'data-tabela="{k}"' in html) or (k in ("categorias_sup", "pen_nivel_cat", "pen_nivel") and (f'id="dados-{k}"' in html or 'id="dados-comprimidos"' in html))
        ok(f"tabela {k} · host no HTML", tem, "componente presente" if tem else "AUSENTE")

    # ---- RN-58 · frequencia de compra (Etapa 3 da frequencia, 13/09/2026) -------------------------------------------------
    V_ = CFG["validacao"]
    GB = parquet.carregar("SELLOUT_GABARITO")
    kk_ = GB["freq_total"].astype(float) * GB["pdvs_distintos"].astype(float)
    dist_int = float((kk_ - kk_.round()).abs().max()) if len(GB) else 0.0
    ok("freq · total x PDVs inteiro", bool(len(GB)) and GB["freq_total"].notna().all() and dist_int <= float(V_["frequencia_tolerancia_inteiro"]),
       f"{len(GB)} arquivo(s): maior distancia ao inteiro {dist_int:.2e} (tolerancia {float(V_['frequencia_tolerancia_inteiro']):g})")
    FC_ = T["DN_FREQ_CALIBRACAO"]
    err_ = float(FC_["erro_nfs"].abs().max()) if len(FC_) else 0.0
    ok("freq · Σ estimativa = total Mtrix", len(FC_) == len(c["meses"]) and err_ <= float(V_["frequencia_tolerancia_total"]),
       f"{len(FC_)} meses calibrados · maior erro {err_:.4f} NF · alfa {FC_['alfa'].min():.4f} a {FC_['alfa'].max():.4f}")
    fora_ = [f"{r_.ANO_MES} alfa {r_.alfa:.4f}" for r_ in FC_.itertuples()
             if not (float(V_["frequencia_alfa_min"]) <= r_.alfa <= float(V_["frequencia_alfa_max"]))
             and not (r_.ANO_MES == mes_ref and metrics.mes_em_andamento(mes_ref))]
    if fora_:
        log(f"freq · alfa fora da faixa {float(V_['frequencia_alfa_min']):g}–{float(V_['frequencia_alfa_max']):g} (so aviso, decisao 6): {fora_}", "aviso")
    # por par e por par x categoria: minimo <= estimativa <= soma; par de uma linha = frequencia da linha; categoria <= par
    fp_ = K_[K_["PESO_KG"] > 0]   # P5: codigos inteiros (mesmas linhas kg > 0 da fato, com FREQ, ATEND e NF_MIN)
    gp_ = fp_.groupby(["ANO_MES", "DIST", "COD_PDV"], observed=True).agg(mx=("FREQ", "max"), sm=("FREQ", "sum"), n=("FREQ", "size"),
                                                                        at=("ATEND", "sum"), am=("NF_MIN", "sum"))
    tol_p = 1e-6
    ruim_faixa = int(((gp_["at"] < gp_["mx"] - tol_p) | (gp_["at"] > gp_["sm"] + tol_p)).sum())
    ruim_um = int(((gp_["n"] == 1) & ((gp_["at"] - gp_["mx"]).abs() > tol_p)).sum())
    ruim_min = int(((gp_["am"] - gp_["mx"]).abs() > tol_p).sum())
    ok("freq · minimo <= estimativa <= soma (pares)", ruim_faixa == 0 and ruim_min == 0,
       f"{len(gp_):,} pares distribuidor x PDV x mes" + ("" if not ruim_faixa and not ruim_min else f" · fora da faixa {ruim_faixa} · minimo errado {ruim_min}"))
    ok("freq · par de uma linha = frequencia da linha", ruim_um == 0, f"{int((gp_['n'] == 1).sum()):,} pares de uma linha conferidos" + ("" if not ruim_um else f" · {ruim_um} diferentes"))
    gc_ = fp_.groupby(["ANO_MES", "DIST", "COD_PDV", "CAT"], observed=True)["ATEND_CAT"].sum()
    cat_max_ = gc_.groupby(level=[0, 1, 2]).max()
    ruim_cat = int((cat_max_ > gp_["at"].reindex(cat_max_.index) + tol_p).sum())
    ok("freq · categoria <= par", ruim_cat == 0, f"{len(gc_):,} pares x categoria" + ("" if not ruim_cat else f" · {ruim_cat} pares com categoria acima do par"))
    cm_ = T["DN_CANAL_MES"].set_index("ANO_MES")
    rec_fr = float(fp_.loc[fp_["ANO_MES"] == i_mes[mes_ref], "ATEND"].sum()) / float(fp_.loc[fp_["ANO_MES"] == i_mes[mes_ref], "COD_PDV"].nunique())
    k_fr = next(s_ for s_ in J["segmentos"] if s_["id"] == "todos")["kpi"].get("frequencia")
    ok("freq · card canal = curated = recalculo", k_fr is not None and abs(float(k_fr) - float(cm_.loc[mes_ref, "frequencia"])) < 1e-9 and abs(rec_fr - float(k_fr)) < 1e-9,
       f"{float(k_fr):.4f} = {float(cm_.loc[mes_ref, 'frequencia']):.4f} = {rec_fr:.4f}" if k_fr is not None else "card sem frequencia")
    dm_ = T["DN_DISTRIBUIDOR_MES"]
    sd_ = float(dm_.loc[dm_["ANO_MES"] == mes_ref, "atendimentos"].sum())
    ok("freq · Σ distribuidores = canal (NFs)", abs(sd_ - float(cm_.loc[mes_ref, "atendimentos"])) < 1e-6,
       f"{sd_:,.2f} = {float(cm_.loc[mes_ref, 'atendimentos']):,.2f} (cada NF e de um distribuidor)")
    # 22/09/2026 (Douglas): a coluna nf_min saiu do blob de PDVs; a validacao "freq · NFs min. no mes (blob) = fato" foi retirada com ela
    db_ = json.loads(gzip.decompress(base64.b64decode(J["pdv_blob"]["b64"])))
    ok("freq · blob de PDVs sem nf_min", "nf_min" not in db_["cols"], f"colunas do blob: {', '.join(db_['cols'])}")
    # ---- RN-59 · seletor de periodo: serie inteira embutida e compacta ------------------------------------------------------
    js_ = str(J["dn"].get("serie_js") or "")
    n_js = js_.count("{m:")
    n_jan = min(len(c["meses"]), painel.JANELA_ARQ) if painel.JANELA_ARQ else len(c["meses"])   # Refino E6
    ok("periodo · serie inteira embutida", (not painel.PERIODO_ATIVO) or (len(J["dn"]["serie"]) == n_jan == n_js and "DN_PER=" in html and 'id="per-chips"' in html),
       f"{n_js} pontos compactos = {len(c['meses'])} meses da serie · seletor no HTML")
    difs_js = []
    for p_ in J["dn"]["serie"]:
        seg_ = js_.split('{m:' + json.dumps(p_["mes"], ensure_ascii=False))[1].split("}")[0] if ('{m:' + json.dumps(p_["mes"], ensure_ascii=False)) in js_ else ""
        for curta, longa in painel._SERIE_JS[1:]:
            v_ = p_.get(longa)
            tem_ = f",{curta}:" in seg_
            if (v_ is None) == tem_:
                difs_js.append(f"{p_['mes']}.{curta}")
    ok("periodo · serie compacta = serie do JSON", not difs_js, f"{len(J['dn']['serie'])} pontos do canal x {len(painel._SERIE_JS) - 1} campos (nulo omitido, valor presente)" if not difs_js else "; ".join(difs_js[:6]))
    # ---- D18 revista (RN-44) e chave por codigo (RN-52) --------------------------------------------------------------------
    RS_ = T.get("DN_RTM_SUP_MES"); RM_ = T["DN_RTM_MES"].set_index("ANO_MES")
    difs_r = []
    if RS_ is not None and len(RS_):
        sm_r = RS_.groupby("ANO_MES")[["base_rtm", "certo", "so_outro", "sem_compra"]].sum()
        for m_, r_ in sm_r.iterrows():
            for col_ in ("base_rtm", "certo", "so_outro", "sem_compra"):
                if int(r_[col_]) != int(RM_.loc[m_, col_]):
                    difs_r.append(f"{m_} {col_}: Σ supervisores {int(r_[col_])} x canal {int(RM_.loc[m_, col_])}")
    ok("RTM · Σ supervisores do destino = canal", RS_ is not None and len(RS_) > 0 and not difs_r,
       f"{RS_['SUP'].nunique() if RS_ is not None and len(RS_) else 0} supervisores x {len(RM_)} meses x 4 contagens" if not difs_r else "; ".join(difs_r[:4]))
    CL_ = T["DN_RTM_CLIENTE"]
    n_sup_dest = CL_[CL_["COBERTO"]].groupby("DESTINO")["SUP_DESTINO"].nunique()
    ok("RTM · 1 supervisor por destino mensuravel", bool((n_sup_dest == 1).all()), f"{len(n_sup_dest)} destinos mensuraveis, cada um com 1 supervisor")
    if str(CFG["regras"].get("rtm_destino_chave", "nome")) == "codigo":
        cod_ok = CL_["COBERTO"] <= CL_["DESTINO_POR_CHAVE"].astype(bool)
        ok("RTM · destino pela chave do codigo", bool(cod_ok.all()), f"{int(CL_['COBERTO'].sum())} mensuraveis, todos casados pelo codigo do distribuidor")

    if erros:
        abortar("validacao FALHOU:\n  " + "\n  ".join(erros),
                situacao="o curated e o HTML em data/dn/painel/ foram gravados, mas NADA foi publicado.")
    L.etapa_fim("ok", checagens=len(checks))
    return checks


# ============================================================= 5 · publicar
def publicar(origem: Path) -> Path:
    L.etapa_inicio("5 · publicar")
    pub = CFG["publicacao"]
    pasta = caminho(pub["pasta"])
    try:
        pasta.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        abortar(f"nao foi possivel criar a pasta de publicacao {pasta}: {e}",
                situacao="curated e HTML gerados; NADA publicado.")
    destino = pasta / pub["arquivo"]
    estranhos = sorted(x.name for x in pasta.iterdir() if x.name != pub["arquivo"] and not x.name.startswith("~$"))
    if estranhos:
        log(f"pasta de publicacao tem {len(estranhos)} item(ns) alem de {pub['arquivo']} (nao removidos; "
            f"a pasta deveria conter so o painel): {estranhos[:8]}", "aviso")
    md5_origem = _md5(origem)
    # P6 (Etapa 1): conteudo identico ao ja publicado = nada a copiar (evita ressincronizacao do OneDrive e arquivo "em uso")
    if bool(pub.get("pular_se_identico", True)) and destino.exists() and destino.stat().st_size == origem.stat().st_size \
            and _md5(destino) == md5_origem:
        log(f"publicado sem mudanca: {destino} ja tem o mesmo conteudo (md5 {md5_origem[:8]}…); nada copiado", "ok")
        L.etapa_fim("ok", destino=str(destino), md5=md5_origem, bytes=destino.stat().st_size, itens_estranhos=estranhos, copiado=False)
        return destino
    tmp = pasta / (pub["arquivo"] + ".tmp")
    try:
        shutil.copyfile(origem, tmp)
        os.replace(tmp, destino)
    except OSError as e:
        abortar(f"falha ao copiar para {destino}: {e}", situacao="curated e HTML gerados; NADA publicado.")
    md5_destino = _md5(destino)
    if md5_origem != md5_destino or origem.stat().st_size != destino.stat().st_size:
        abortar(f"o arquivo publicado difere do gerado: {destino}", situacao="publicacao CORROMPIDA; rode de novo.")
    log(f"publicado -> {destino} ({destino.stat().st_size / 1024 / 1024:.1f} MB, md5 conferido)", "ok")
    L.etapa_fim("ok", destino=str(destino), md5=md5_destino, bytes=destino.stat().st_size, itens_estranhos=estranhos, copiado=True)
    return destino


# ================================================================ resumo
def gravar_resumo(extra: dict) -> Path:
    r = {"execucao": L.EXECUCAO_ID, "inicio": L.INICIO.isoformat(timespec="seconds"),
         "fim": pd.Timestamp.now().isoformat(timespec="seconds"), "etapas": L.etapas(),
         "linhas_por_arquivo": L.contagens(), "avisos": L.avisos(), "erros": L.erros(), **extra}
    alvo = PASTA_LOGS / f"resumo_{L.EXECUCAO_ID}.json"
    alvo.write_text(json.dumps(r, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return alvo


# ============================================================== executar
def executar(mes: str | None, sem_publicar: bool, forcar: bool, regerar_exemplo: bool,
             usuario: str | None = None, sem_usuarios: bool = False) -> int:
    preparar_pastas()
    alvo_log = L.abrir()
    L.titulo(f"{CFG['projeto']['nome']} · run_dn · execucao {L.EXECUCAO_ID}")
    log(f"log: {alvo_log}")
    from .utils import recursos as _rec   # P6
    _rec.aplicar_pyarrow()
    log(f"recursos: {_rec.aplicar_ambiente()} · painel gerado em {PASTA_PAINEL}")
    mes_ref = mes or CFG["painel"].get("mes_referencia")

    diff = verificar(forcar)
    if diff["precisa_ingerir"]:
        ingestao = ingerir()
    else:
        L.etapa_inicio("1 · ingerir (raw -> staging -> curated)")
        log(f"pulada: {diff['motivo']}", "ok")
        L.etapa_fim("pulada", motivo=diff["motivo"])
        ingestao = json.loads((PASTA_CURATED / "resumo.json").read_text(encoding="utf-8"))
    c, T = calcular(mes_ref)
    c2, T2 = calcular_fechado(c, T)   # Refino E4a
    J, JF, alvo, html = renderizar(c, T, regerar_exemplo, c2, T2)
    checks = validar(c, T, J, html, alvo)
    destino = None
    parcial = bool(J["periodo"].get("mes_em_andamento"))
    pode_parcial = bool((CFG.get("publicacao") or {}).get("publicar_mes_em_andamento", False))
    if sem_publicar:
        L.etapa_inicio("5 · publicar")
        log("pulada: --sem-publicar", "ok")
        L.etapa_fim("pulada", motivo="--sem-publicar")
    elif parcial and not pode_parcial:
        # 10/09/2026: mes parcial nao substitui o ultimo mes fechado que o time ja ve
        L.etapa_inicio("5 · publicar")
        log(f"pulada: {c['mes_ref']} esta em andamento e publicacao.publicar_mes_em_andamento e false — "
            f"o publicado continua sendo o ultimo mes fechado; o parcial ficou em {alvo}", "aviso")
        L.etapa_fim("pulada", motivo="mes em andamento")
    else:
        destino = publicar(alvo)

    # Etapa 2 (16/09/2026): um painel por usuario da hierarquia, no modelo dos Gerenciais
    dist_resumo = None
    if (CFG.get("distribuicao") or {}).get("ativo") and not sem_usuarios:
        from . import distribuicao
        dist_resumo = distribuicao.executar(c, T, html, sem_publicar=sem_publicar or (parcial and not pode_parcial), filtro=usuario)

    k = J["segmentos"][0]["kpi"]
    numeros = {"mes_referencia": c["mes_ref"], "base_ativa": k["base_ativa"], "positivados": k["cobertura_pdv"],
               "pct_cobertura": k["pct_cobertura"], "volume_t": k["volume_t"],
               "distribuidores_painel": len(J["distribuidores"]),
               "mes_em_andamento": bool(J["periodo"].get("mes_em_andamento")),
               "rtm": {kk: J["rtm"].get(kk) for kk in ("base_total", "rastreaveis", "nao_mensuravel")},
               "rtm_kpi": {kk: J["rtm"]["kpi"].get(kk) for kk in ("certo", "so_outro", "sem_compra", "pct_aderencia")}}
    resumo = gravar_resumo({"ingestao": {"executada": diff["precisa_ingerir"], "motivo": diff["motivo"],
                                         "resumo_curated": ingestao},
                            "validacao": checks, "numeros": numeros,
                            "html": str(alvo), "publicado": str(destino) if destino else None,
                            "publicado_md5": _md5(destino) if destino else None,
                            "publicado_bytes": destino.stat().st_size if destino else None,
                            "dados_atualizados_em": J["meta_execucao"]["dados_atualizados_em"],
                            "distribuicao": dist_resumo})
    L.titulo("FIM")
    log(f"{c['mes_ref']}: base ativa {k['base_ativa']:,.0f} · positivados {k['cobertura_pdv']:,} · "
        f"DN {k['pct_cobertura']:.1f}% · volume {k['volume_t']:,.1f} t · {len(J['distribuidores'])} distribuidores · "
        f"RTM {J['rtm']['base_total']}/{J['rtm']['rastreaveis']}/{J['rtm']['nao_mensuravel']}", "ok")
    log(f"{len(L.avisos())} aviso(s) · resumo -> {resumo}", "ok")
    _motivo = "--sem-publicar" if sem_publicar else (f"{c['mes_ref']} em andamento" if parcial else "nao publicado")
    log(f"publicado em {destino}" if destino else f"nao publicado ({_motivo})", "ok")
    L.fechar()
    if dist_resumo and dist_resumo.get("erros"):
        print(f"PAINEIS POR USUARIO COM ERRO: {len(dist_resumo['erros'])} (o painel do canal foi gerado; veja o log)")
        return 1
    return 0
