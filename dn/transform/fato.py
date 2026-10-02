# -*- coding: utf-8 -*-
"""FATO_SELLOUT e as conferências que travam a gravação.

GRÃO DECLARADO: uma linha = o sell-out de um SKU, vendido por um distribuidor a
um PDV, em um mês. Chave: `ANO_MES × CNPJ_DISTRIBUIDOR × COD_PDV × COD_PRODUTO`.
Medido em 12 arquivos (jul/25 a jun/26): zero duplicidade. O ETL não agrega nem
desagrega; positivação (kg > 0), base ativa e DN são da Fase 2.

Adaptado de `src/transform/fato.py` (projeto gerencial).
"""
from __future__ import annotations

import pandas as pd

from ..utils.config import CFG
from ..utils.log import EXECUCAO_ID, INICIO, abortar, log

_TOL = CFG["validacao"]

GRAO = ["ANO_MES", "CNPJ_DISTRIBUIDOR", "COD_PDV", "COD_PRODUTO"]
COLUNAS = GRAO + ["RECEITA", "UNIDADES", "PESO_KG", "FREQ", "ARQUIVO_ORIGEM", "EXECUCAO_ID", "PROCESSADO_EM"]


def construir(bruto: pd.DataFrame) -> pd.DataFrame:
    f = pd.DataFrame({
        "ANO_MES": bruto["ANO_MES"].astype("string"),
        "CNPJ_DISTRIBUIDOR": bruto["CNPJ_DISTRIBUIDOR"].astype("string"),
        "COD_PDV": bruto["COD_PDV"].astype("string"),
        "COD_PRODUTO": bruto["COD_PRODUTO"].astype("string"),
        "RECEITA": bruto["RECEITA"].astype("float64").fillna(0.0),
        "UNIDADES": bruto["UNIDADES"].astype("float64").fillna(0.0),
        "PESO_KG": bruto["PESO_KG"].astype("float64").fillna(0.0),
        "FREQ": bruto["FREQ"].astype("float64"),          # RN-58: atendimentos do SKU no mes (o leitor rejeita vazio ou < 1)
        "ARQUIVO_ORIGEM": bruto["ARQUIVO_ORIGEM"].astype("category"),
    })
    f["EXECUCAO_ID"] = pd.Series(EXECUCAO_ID, index=f.index).astype("category")
    f["PROCESSADO_EM"] = pd.Timestamp(INICIO)
    return f[COLUNAS]


def conferir_grao(f: pd.DataFrame) -> None:
    dup = int(f.duplicated(GRAO).sum())
    if not dup:
        log(f"grao {' x '.join(GRAO)}: zero duplicados em {len(f):,} linhas", "ok")
        return
    dup_df = f[f.duplicated(GRAO, keep=False)]
    amostra = (dup_df.assign(_ARQ=dup_df["ARQUIVO_ORIGEM"].astype("string"))
               .groupby(GRAO)["_ARQ"].agg(lambda s: sorted(set(s))).head(5))
    abortar(f"{dup:,} linha(s) fora do grao declarado (mes x distribuidor x PDV x SKU).\n"
            "  Duplicidade aqui significa arquivo reextraido ou mes duplicado.\n"
            + "\n".join(f"    {k} -> {v}" for k, v in amostra.items()))


def contar_orfaos(f: pd.DataFrame, dim: pd.DataFrame, coluna: str) -> int:
    return int((~f[coluna].isin(set(dim[coluna].dropna()))).sum())


def conferir_integridade(f: pd.DataFrame, dim_pdv, dim_dist, dim_prod, dim_cal) -> None:
    for coluna, dim, nome in (("COD_PDV", dim_pdv, "DIM_PDV"),
                              ("CNPJ_DISTRIBUIDOR", dim_dist, "DIM_DISTRIBUIDOR"),
                              ("COD_PRODUTO", dim_prod, "DIM_PRODUTO"),
                              ("ANO_MES", dim_cal, "DIM_CALENDARIO")):
        orfaos = ~f[coluna].isin(set(dim[coluna].dropna()))
        if orfaos.any():
            abortar(f"integridade referencial: {int(orfaos.sum()):,} linha(s) da fato com "
                    f"{coluna} fora de {nome}. Exemplos: {sorted(f.loc[orfaos, coluna].unique())[:5]}")
        log(f"FK {coluna:<18} -> {nome:<16} ok")


def reconciliar_origem(f: pd.DataFrame, meta: dict) -> list[str]:
    """Soma da fato × linha de total de cada arquivo, em R$, unidades e kg
    (aborta fora da tolerância). PDVs positivados e SKUs do total são
    conferidos como INFORMAÇÃO: a Mtrix conta com a chave crua dela."""
    gab = meta["gabaritos"]
    avisos: list[str] = []
    if not gab:
        msg = "arquivos sem linha de total — reconciliacao contra a origem NAO executada"
        log(msg, "aviso")
        return [msg]
    calc = f.groupby("ARQUIVO_ORIGEM", observed=True)[["RECEITA", "UNIDADES", "PESO_KG"]].sum()
    n_pdv = f.groupby("ARQUIVO_ORIGEM", observed=True)["COD_PDV"].nunique()
    n_sku = f.groupby("ARQUIVO_ORIGEM", observed=True)["COD_PRODUTO"].nunique()
    ruins = []
    for arq in meta["arquivos"]:
        if arq not in gab:
            msg = f"{arq}: sem linha de total legivel — reconciliacao NAO executada"
            log(msg, "aviso")
            avisos.append(msg)
            continue
        g = gab[arq]
        c = calc.loc[arq]
        for chave, col, tol in (("receita", "RECEITA", _TOL["tolerancia_receita_reais"]),
                                ("unidades", "UNIDADES", _TOL["tolerancia_unidades"]),
                                ("peso_kg", "PESO_KG", _TOL["tolerancia_peso_kg"])):
            esperado = g.get(chave)
            if esperado is None:
                msg = f"{arq}: gabarito sem '{chave}' — metrica NAO conferida"
                log(msg, "aviso")
                avisos.append(msg)
                continue
            dif = float(c[col]) - float(esperado)
            if abs(dif) > float(tol):
                ruins.append(f"{arq} [{chave}]: calculado {c[col]:,.4f} x gabarito {esperado:,.4f} (dif {dif:,.4f})")
        for chave, serie, rot in (("pdvs_positivados", n_pdv, "PDVs"), ("total_skus", n_sku, "SKUs")):
            esperado = g.get(chave)
            if esperado is not None and int(serie.loc[arq]) != int(esperado):
                msg = (f"{arq}: {rot} distintos calculados {int(serie.loc[arq]):,} x "
                       f"total da Mtrix {int(esperado):,} (dif {int(serie.loc[arq]) - int(esperado):+,}) — informativo")
                log(msg, "aviso")
                avisos.append(msg)
    # RN-58 (decisao 6 da Etapa 2): frequencia da linha de total x Cod. PDV distintos do arquivo = total de atendimentos,
    # inteiro nos 25 arquivos medidos. Sem frequencia no total ou longe de inteiro = a estimativa nao calibra = aborta.
    tol_i = float(_TOL["frequencia_tolerancia_inteiro"])
    for arq in meta["arquivos"]:
        g = gab.get(arq)
        if g is None:
            continue
        ft = g.get("freq_total")
        if ft is None:
            ruins.append(f"{arq} [frequencia]: linha de total sem '# Frequência de compra' — a estimativa nao calibra (RN-58)")
            continue
        n_ = int(n_pdv.loc[arq]); kk = float(ft) * n_
        if abs(kk - round(kk)) > tol_i:
            ruins.append(f"{arq} [frequencia]: total {ft} x {n_:,} PDVs = {kk:.6f}, nao inteiro (tolerancia {tol_i:g})")
            continue
        g["atendimentos_total"] = int(round(kk)); g["pdvs_distintos"] = n_
    if ruins:
        abortar("a fato NAO bate com a linha de total da fonte:\n  " + "\n  ".join(ruins))
    log(f"reconciliado contra a linha de total em {len(gab)} arquivo(s), em R$, unidades e kg; "
        f"atendimentos do total inteiros nos {len(gab)} arquivo(s) (RN-58)", "ok")
    return avisos
