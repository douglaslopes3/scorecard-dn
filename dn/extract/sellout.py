# -*- coding: utf-8 -*-
"""Leitura da fonte de Sell-Out Mtrix (camada bronze).

Adaptado de `src/extract/sellin.py` (projeto gerencial): mesma estrutura, outro
layout. Devolve o dado CRU, tipado e com nome de coluna normalizado, SEM regra de
negócio. O que acontece aqui e em nenhum outro lugar:

1. **A linha de total sai e vira gabarito.** Na Mtrix ela é a 2ª linha da planilha
   (dimensões vazias, métricas somadas). É contra ela que a reconciliação prova
   que não perdemos nem inventamos linha.
2. **A competência vem do conteúdo** (`Ano/Mês`, formato `AAAA/MMM`), nunca do
   nome do arquivo.
3. **As chaves são classificadas, não corrigidas.** `CNPJ do AD.` tem de ter 14
   dígitos e existir no de-para de distribuidores. `Cód. PDV` é CNPJ (14 dígitos),
   LGPD (id negativo anonimizado pela Mtrix) ou OUTRO; nada é completado com zero
   nem descartado — formato quebrado (o caso de jul/26) rejeita o arquivo.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from ..utils.config import CFG, caminho
from ..utils import log as L
from ..utils.log import abortar, log
from ..utils.texto import ano_mes, cnpj, digitos, numero, texto
from . import cache

FONTE = CFG["fontes"]["sellout"]
_VAL = CFG["validacao"]
_LGPD = str(CFG["regras"].get("pdv_chave_lgpd_prefixo", "LGPD")).upper()

# Como cada coluna de origem vira coluna do modelo.
DESTINO = {
    "CNPJ do AD.": ("CNPJ_DISTRIBUIDOR", cnpj),
    "Agente de Distribuição": ("DISTRIBUIDOR_MTRIX", lambda s: texto(s, maiuscula=False)),
    "CNPJ Reduzido": ("CNPJ_REDUZIDO", lambda s: texto(s, maiuscula=False)),
    "Cód. PDV": ("COD_PDV", lambda s: texto(s, maiuscula=False)),
    "Razão Social PDV": ("NOME_PDV", texto),
    "UF PDV": ("UF", texto),
    "Cidade PDV": ("CIDADE", texto),
    "Endereço PDV": ("ENDERECO", texto),
    "Bairro PDV": ("BAIRRO", texto),
    "CEP PDV": ("CEP", lambda s: texto(s, maiuscula=False)),
    "Segmento do PDV": ("SEGMENTO_MTRIX", texto),
    "SKU": ("COD_PRODUTO", digitos),
    "Ano/Mês": ("ANO_MES", ano_mes),
    "# Sell-Out (R$)": ("RECEITA", numero),
    "# Sell-Out (Und)": ("UNIDADES", numero),
    "# Sell-Out (Quilos)": ("PESO_KG", numero),
    "# PDVs Positivados": ("FLAG_PDV_MTRIX", numero),
    "# Total SKUs": ("FLAG_SKU_MTRIX", numero),
    "# Frequência de compra": ("FREQ", numero),     # RN-58 (13/09/2026): atendimentos (NFs) do SKU no mês
}

COLS_PDV = ["COD_PDV", "TIPO_CHAVE_PDV", "CNPJ_REDUZIDO", "NOME_PDV", "UF", "CIDADE",
            "ENDERECO", "BAIRRO", "CEP", "SEGMENTO_MTRIX"]
COLS_FATO = ["ANO_MES", "CNPJ_DISTRIBUIDOR", "COD_PDV", "COD_PRODUTO",
             "RECEITA", "UNIDADES", "PESO_KG", "FREQ", "ARQUIVO_ORIGEM"]

_RE_CNPJ = re.compile(r"^\d{14}$")
_RE_LGPD = re.compile(r"^-\d+$")


def arquivos() -> tuple[list[Path], dict[str, str]]:
    """Arquivos de entrada e os ignorados (com motivo), da pasta do config."""
    pasta = caminho(FONTE["pasta"])
    if not pasta.exists():
        abortar(f"pasta de Sell-Out nao encontrada: {pasta}\n"
                "  (config/config.yaml -> fontes.sellout.pasta)")
    achados: list[Path] = []
    for padrao in FONTE["padroes_aceitos"]:
        achados += [a for a in pasta.glob(padrao) if not a.name.startswith("~$")]
    ignorados = {str(k): str(v) for k, v in (FONTE.get("arquivos_ignorados") or {}).items()}
    usar = sorted(a for a in set(achados) if a.name not in ignorados)
    fora = {a.name: ignorados[a.name] for a in set(achados) if a.name in ignorados}
    if not usar:
        abortar(f"nenhum arquivo de Sell-Out encontrado em {pasta} "
                f"(padroes {FONTE['padroes_aceitos']})")
    return usar, fora


def _validar_schema(df: pd.DataFrame, arq: Path) -> None:
    faltando = [c for c in FONTE["colunas_obrigatorias"] if c not in df.columns]
    if faltando:
        abortar(f"arquivo REJEITADO: {arq.name}\n"
                f"  colunas obrigatorias ausentes: {faltando}\n"
                f"  colunas encontradas         : {list(df.columns)}\n"
                "  (config/config.yaml -> fontes.sellout.colunas_obrigatorias)")


def _tipo_chave_pdv(cod: pd.Series, nome: pd.Series) -> pd.Series:
    """CNPJ | LGPD | OUTRO. Regra declarada em config (regras.pdv_chave_*)."""
    c = cod.fillna("")
    n = nome.fillna("")
    e_cnpj = c.str.match(_RE_CNPJ)
    e_lgpd = c.str.match(_RE_LGPD) & n.str.upper().str.startswith(_LGPD)
    out = pd.Series("OUTRO", index=cod.index, dtype="string")
    out[e_cnpj] = "CNPJ"
    out[e_lgpd] = "LGPD"
    return out


def _ler_um(arq: Path) -> tuple[pd.DataFrame, dict]:
    try:
        df = pd.read_excel(arq, sheet_name=FONTE["aba"], engine="calamine", dtype=str)
    except Exception as e:                                   # noqa: BLE001
        abortar(f"arquivo REJEITADO: {arq.name}\n"
                f"  nao foi possivel ler a aba '{FONTE['aba']}': {e}")
    df.columns = [re.sub(r"\s+", " ", str(c)).strip() for c in df.columns]
    _validar_schema(df, arq)

    am_raw = df["Ano/Mês"]
    kg_raw = df["# Sell-Out (Quilos)"]

    # ---- linha de total (gabarito): sem competencia e com metrica ----------
    extra: dict = {}
    total = df[am_raw.isna() & kg_raw.notna()]
    if len(total):
        t = total.iloc[0]
        extra["gabarito"] = {
            "receita": _num(t["# Sell-Out (R$)"]),
            "unidades": _num(t["# Sell-Out (Und)"]),
            "peso_kg": _num(t["# Sell-Out (Quilos)"]),
            # 13/09/2026: "# PDVs Positivados" ficou opcional (saiu das extrações de set/25 em diante)
            "pdvs_positivados": _num(t["# PDVs Positivados"]) if "# PDVs Positivados" in t.index else None,
            "total_skus": _num(t["# Total SKUs"]),
            # RN-58: frequência da linha de total = atendimentos do arquivo ÷ Cód. PDV distintos (calibra a estimativa)
            "freq_total": _num(t["# Frequência de compra"]),
        }
        if len(total) > 1:
            log(f"{arq.name}: {len(total)} linhas de total; usada a 1a", "aviso")
    else:
        log(f"{arq.name}: sem linha de total — reconciliacao contra a origem "
            "NAO sera executada para este arquivo", "aviso")
    lixo = df[am_raw.isna() & kg_raw.isna()]
    if len(lixo):
        extra["linhas_rodape"] = int(len(lixo))

    corpo = df[am_raw.notna()]
    out = pd.DataFrame(index=corpo.index)
    for origem, (destino, conv) in DESTINO.items():
        if origem in corpo.columns:
            out[destino] = conv(corpo[origem])
    for c in ("ENDERECO", "BAIRRO", "CEP"):
        if c not in out.columns:
            out[c] = pd.Series(pd.NA, index=out.index, dtype="string")
    out["ARQUIVO_ORIGEM"] = arq.name

    # ---- competencia (A9): mes irreconhecivel aborta, nunca some no dropna --
    mal = out["ANO_MES"].isna()
    if mal.any():
        exemplos = sorted(set(corpo.loc[mal, "Ano/Mês"].astype(str)))[:5]
        abortar(f"arquivo REJEITADO: {arq.name}\n"
                f"  {int(mal.sum())} linha(s) com 'Ano/Mês' nao reconhecido. "
                f"Exemplos: {exemplos}\n"
                "  Formatos aceitos: AAAA/MMM, AAAA/MM e AAAA-MM (ex.: 2026/JUN).")
    meses = sorted(out["ANO_MES"].unique())
    if len(meses) > 1:
        log(f"{arq.name}: {len(meses)} competencias no mesmo arquivo ({meses})", "aviso")

    # ---- chave do distribuidor: 14 digitos, senao formato quebrado ---------
    n_dig = int(_VAL["cnpj_distribuidor_digitos"])
    ruim = out["CNPJ_DISTRIBUIDOR"].isna() | (out["CNPJ_DISTRIBUIDOR"].str.len() != n_dig)
    if ruim.any():
        ex = sorted(set(out.loc[ruim, "CNPJ_DISTRIBUIDOR"].fillna("(vazio)")))[:5]
        abortar(f"arquivo REJEITADO: {arq.name}\n"
                f"  {int(ruim.sum()):,} linha(s) com 'CNPJ do AD.' fora de {n_dig} digitos. "
                f"Exemplos: {ex}\n"
                "  E o sintoma de extracao com zeros a esquerda perdidos (caso de jul/26).\n"
                "  Nada e completado com zero aqui: peca a reextracao ou declare o arquivo\n"
                "  em fontes.sellout.arquivos_ignorados com o motivo.")

    # ---- chave do PDV: classificada, nunca corrigida -----------------------
    out["TIPO_CHAVE_PDV"] = _tipo_chave_pdv(out["COD_PDV"], out["NOME_PDV"])
    sem_pdv = out["COD_PDV"].isna()
    if sem_pdv.any():
        abortar(f"arquivo REJEITADO: {arq.name}\n"
                f"  {int(sem_pdv.sum()):,} linha(s) sem 'Cód. PDV'")
    tipos = out["TIPO_CHAVE_PDV"].value_counts().to_dict()
    extra["tipos_chave_pdv"] = {k: int(v) for k, v in tipos.items()}
    pct_outro = 100.0 * tipos.get("OUTRO", 0) / max(len(out), 1)
    if pct_outro > float(_VAL["pdv_outro_max_pct"]):
        ex = out.loc[out["TIPO_CHAVE_PDV"] == "OUTRO", "COD_PDV"].drop_duplicates().head(5).tolist()
        abortar(f"arquivo REJEITADO: {arq.name}\n"
                f"  {pct_outro:.2f}% das linhas com 'Cód. PDV' que nao e CNPJ nem id LGPD "
                f"(limite {_VAL['pdv_outro_max_pct']}%). Exemplos: {ex}\n"
                "  Formato de chave diferente do esperado — confira a extracao.")

    sem_sku = out["COD_PRODUTO"].isna()
    if sem_sku.any():
        abortar(f"arquivo REJEITADO: {arq.name}\n  {int(sem_sku.sum()):,} linha(s) sem SKU")

    # RN-58: frequencia por linha — numero >= 1 em todas as linhas (medido em 25 arquivos); vazio ou menor que 1 rejeita
    ruim_f = out["FREQ"].isna() | (out["FREQ"] < 1)
    if ruim_f.any():
        abortar(f"arquivo REJEITADO: {arq.name}\n  {int(ruim_f.sum()):,} linha(s) com '# Frequência de compra' vazia ou < 1")

    extra["meses"] = meses
    extra["linhas"] = int(len(out))
    extra["linhas_brutas"] = int(len(df))
    return out.reset_index(drop=True), extra


def _num(v) -> float | None:
    n = numero(pd.Series([v]))
    return float(n.iloc[0]) if pd.notna(n.iloc[0]) else None


def ler() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Consolida todos os arquivos.

    Devolve (fato_bruta, atributos_pdv, meta). A fato bruta carrega só chaves e
    métricas (5 milhões de linhas cabem); os atributos de PDV vêm reduzidos a
    uma linha por PDV × arquivo, com o mês, para a dimensão escolher o último.
    """
    arqs, ignorados = arquivos()
    for nome, motivo in sorted(ignorados.items()):
        log(f"IGNORADO (config): {nome} — {motivo}", "aviso")
    log(f"{len(arqs)} arquivo(s) de Sell-Out a processar")

    fatos, pdvs, dists = [], [], []
    gabaritos, meses_por_arq, tipos, linhas = {}, {}, {}, {}
    for a in arqs:
        d, extra = cache.ler(a, _ler_um)
        fatos.append(d[COLS_FATO])
        p = (d.sort_values("ANO_MES", kind="stable")
              .drop_duplicates("COD_PDV", keep="last")[COLS_PDV + ["ANO_MES"]])
        pdvs.append(p)
        dists.append(d[["CNPJ_DISTRIBUIDOR", "DISTRIBUIDOR_MTRIX", "ANO_MES"]]
                     .drop_duplicates("CNPJ_DISTRIBUIDOR"))
        if extra.get("gabarito"):
            gabaritos[a.name] = extra["gabarito"]
        meses_por_arq[a.name] = extra.get("meses") or sorted(d["ANO_MES"].dropna().unique())
        tipos[a.name] = extra.get("tipos_chave_pdv", {})
        linhas[a.name] = int(len(d))
        brutas = int(extra.get("linhas_brutas", len(d)))
        L.contar(a.name, lidas=brutas, rejeitadas=brutas - int(len(d)),
                 detalhe="linha de total + rodape (nao sao dado)", meses=extra.get("meses"))

    fato = pd.concat(fatos, ignore_index=True)
    pdv = pd.concat(pdvs, ignore_index=True)
    dist = pd.concat(dists, ignore_index=True)

    # o mesmo mes em dois arquivos: soma em dobro — aborta (regra do sell-in)
    dono: dict[str, str] = {}
    for arq, ms in meses_por_arq.items():
        for m in ms:
            if m in dono:
                abortar(f"o mes {m} aparece em DOIS arquivos: {dono[m]} e {arq}.\n"
                        "  Mes repetido somaria em dobro; deixe um arquivo por mes.")
            dono[m] = arq

    meta = {
        "arquivos": [a.name for a in arqs],
        "ignorados": ignorados,
        "gabaritos": gabaritos,
        "meses_por_arquivo": meses_por_arq,
        "tipos_chave_pdv": tipos,
        "linhas_por_arquivo": linhas,
    }
    return fato, pdv, dist, meta
