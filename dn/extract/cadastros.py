# -*- coding: utf-8 -*-
"""Leitura dos cadastros: produtos, de-para de distribuidores, hierarquia e RTM.

Adaptado de `src/extract/cadastros.py` (projeto gerencial). Nenhuma correção,
inferência ou desempate é feita aqui: o que a base traz é o que entra, e o que
não casa vira aviso e lista de exceção (regra "tudo vem das bases", rodada 2).
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import pandas as pd

from ..utils.config import CFG, caminho
from ..utils import log as L
from ..utils.log import abortar, log
from ..utils.texto import cnpj, digitos, texto
from . import cache

_PROD = CFG["fontes"]["produtos"]
_DIST = CFG["fontes"]["distribuidores"]
_HIER = CFG["fontes"]["hierarquia"]
_RTM = CFG["fontes"]["rtm"]
_CLU = CFG["fontes"].get("clusters") or {}
_PON = CFG["fontes"].get("pdv_ponderada") or {}


def _ler_aba(arq: Path, aba: str, chave_cfg: str) -> pd.DataFrame:
    try:
        df = pd.read_excel(arq, sheet_name=aba, engine="calamine", dtype=str)
    except Exception as e:                                   # noqa: BLE001
        abortar(f"arquivo REJEITADO: {arq.name}\n"
                f"  nao foi possivel ler a aba '{aba}': {e}\n"
                f"  (config/config.yaml -> fontes.{chave_cfg}.aba)")
    # cabecalhos com quebra de linha ("CÓDIGO\nCLIENTE") viram um espaco
    df.columns = [re.sub(r"\s+", " ", str(c)).strip() for c in df.columns]
    return df


def _data(s: pd.Series) -> pd.Series:
    """Coluna de data lida como texto -> datetime. Aceita ISO ("2013-12-10
    00:00:00", como o Excel entrega) e, no que sobrar, dia/mes/ano. Nada e
    inventado: o que nao converte vira NaT e o distribuidor segue sem data."""
    t = s.astype("string").str.strip().replace({"": pd.NA})
    d = pd.to_datetime(t, errors="coerce")
    falta = d.isna() & t.notna()
    if falta.any():
        d = d.where(~falta, pd.to_datetime(t.where(falta), errors="coerce", dayfirst=True))
    return d


def _validar(df: pd.DataFrame, obrig: list[str], arq: Path) -> None:
    faltando = [c for c in obrig if c not in df.columns]
    if faltando:
        abortar(f"arquivo REJEITADO: {arq.name}\n"
                f"  colunas obrigatorias ausentes: {faltando}\n"
                f"  colunas encontradas         : {list(df.columns)}")


def _contar(arq: Path, d: pd.DataFrame, extra: dict) -> None:
    """Linhas lidas x linhas que viraram cadastro (o resto: sem chave, duplicada, vazia)."""
    brutas = int(extra.get("linhas_brutas", len(d)))
    L.contar(arq.name, lidas=brutas, rejeitadas=max(brutas - int(len(d)), 0),
             detalhe="sem chave, duplicada ou vazia (1a linha vence)")


def _existe(cfg: dict, chave: str) -> Path:
    arq = caminho(cfg["arquivo"])
    if not arq.exists():
        abortar(f"cadastro nao encontrado: {arq}\n  (config/config.yaml -> fontes.{chave}.arquivo)")
    return arq


# ---------------------------------------------------------------- PRODUTOS
def _ler_produtos(arq: Path) -> tuple[pd.DataFrame, dict]:
    df = _ler_aba(arq, _PROD["aba"], "produtos")
    _validar(df, _PROD["colunas_obrigatorias"], arq)
    out = pd.DataFrame(index=df.index)
    out["COD_PRODUTO"] = digitos(df["Código Produto"])
    out["DESCRICAO_PRODUTO"] = texto(df["Descrição Produto"])
    out["CATEGORIA"] = texto(df["Categoria"])
    out["MARCA"] = texto(df["Marca"]) if "Marca" in df.columns else pd.Series(pd.NA, index=df.index, dtype="string")
    out = out.dropna(subset=["COD_PRODUTO"])
    dup = out.duplicated("COD_PRODUTO", keep=False)
    extra = {"duplicados": int(dup.sum()), "linhas_brutas": int(len(df))}
    return out.drop_duplicates("COD_PRODUTO", keep="first").reset_index(drop=True), extra


def ler_produtos() -> pd.DataFrame:
    arq = _existe(_PROD, "produtos")
    d, extra = cache.ler(arq, _ler_produtos)
    _contar(arq, d, extra)
    if extra.get("duplicados"):
        log(f"Produtos.xlsx: {extra['duplicados']} linha(s) com SKU repetido — vale a 1a", "aviso")
    log(f"produtos: {len(d):,} SKUs · {d['CATEGORIA'].nunique()} categorias")
    return d


# ---------------------------------------------------------- DISTRIBUIDORES
def _ler_distribuidores(arq: Path) -> tuple[pd.DataFrame, dict]:
    df = _ler_aba(arq, _DIST["aba"], "distribuidores")
    _validar(df, _DIST["colunas_obrigatorias"], arq)
    out = pd.DataFrame(index=df.index)
    out["CNPJ_DISTRIBUIDOR"] = cnpj(df["CNPJ DISTRIBUIDOR"])
    out["DISTRIBUIDOR_MTRIX"] = texto(df["DESCRIÇÃO DISTRIBUIDOR MTRIX"], maiuscula=False)
    out["RAZAO_SOCIAL"] = texto(df["DESCRIÇÃO BI"])
    out["COD_CLIENTE"] = digitos(df["Cód. Interno Cliente"])
    out["STATUS"] = texto(df["Status"], maiuscula=False)
    out["SUPERVISOR_DEPARA"] = texto(df["Supervisor"], maiuscula=False) if "Supervisor" in df.columns else pd.NA
    out["GERENTE_DEPARA"] = texto(df["Gerente"], maiuscula=False) if "Gerente" in df.columns else pd.NA
    out["NOME_REDUZIDO"] = texto(df["Distribuidora Nome Reduzido"])
    # C3 (09/09/2026): data de cadastro do distribuidor. Coluna OPCIONAL — sem ela,
    # a maturidade continua inferida do 1o mes com sell-out na Mtrix (censurada).
    out["DATA_CADASTRO"] = (_data(df["Data de Cadastro"]) if "Data de Cadastro" in df.columns
                            else pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns]"))
    out = out.dropna(subset=["CNPJ_DISTRIBUIDOR"])
    extra = {"duplicados": int(out.duplicated("CNPJ_DISTRIBUIDOR").sum()),
             "tem_coluna_data": "Data de Cadastro" in df.columns, "linhas_brutas": int(len(df)),
             "sem_data_cadastro": int(out["DATA_CADASTRO"].isna().sum())}
    return out.drop_duplicates("CNPJ_DISTRIBUIDOR", keep="first").reset_index(drop=True), extra


def ler_distribuidores() -> pd.DataFrame:
    arq = _existe(_DIST, "distribuidores")
    d, extra = cache.ler(arq, _ler_distribuidores)
    _contar(arq, d, extra)
    if extra.get("duplicados"):
        log(f"{arq.name}: {extra['duplicados']} CNPJ repetido(s) — vale a 1a linha", "aviso")
    if not extra.get("tem_coluna_data", False):
        log(f"{arq.name}: sem a coluna 'Data de Cadastro' — maturidade dos distribuidores "
            "continua inferida da serie (historico censurado, C3)", "aviso")
    elif extra.get("sem_data_cadastro"):
        log(f"{arq.name}: {extra['sem_data_cadastro']} distribuidor(es) sem data de cadastro "
            "— esses seguem com historico censurado", "aviso")
    com_data = int(d["DATA_CADASTRO"].notna().sum())
    log(f"distribuidores (de-para): {len(d):,} CNPJs · {d['NOME_REDUZIDO'].nunique()} nomes reduzidos · "
        f"status {d['STATUS'].value_counts().to_dict()} · {com_data} com data de cadastro")
    return d


# ---------------------------------------------------------------- HIERARQUIA
# 02/10/2026: a hierarquia oficial e a Hierarquia_AAAAMMDD.xlsx da pasta compartilhada (DN, Gerencial e ROTA).
# Vale a de data mais recente no NOME; arquivo do padrao sem data AAAAMMDD valida aborta (uma copia de conflito
# do OneDrive, "Hierarquia_20261001 (1).xlsx", cai aqui em vez de virar desempate silencioso).
def arquivo_hierarquia() -> Path:
    pasta = caminho(_HIER["pasta"])
    if not pasta.is_dir():
        abortar(f"pasta da hierarquia nao encontrada: {pasta}\n  (config/config.yaml -> fontes.hierarquia.pasta)")
    rx = re.compile(_HIER["data_regex"])
    datas: dict[datetime, Path] = {}
    fora: list[str] = []
    for a in sorted(pasta.glob(_HIER["padrao"])):
        if a.name.startswith("~$"):
            continue
        m = rx.match(a.name)
        try:
            d = datetime.strptime(m.group(1), "%Y%m%d") if m else None
        except ValueError:
            d = None
        if d is None:
            fora.append(a.name)
        else:
            datas[d] = a
    if fora:
        abortar(f"arquivo(s) de hierarquia fora do padrao {_HIER['data_regex']} em {pasta}:\n    "
                + "\n    ".join(fora) + "\n  Renomeie para Hierarquia_AAAAMMDD.xlsx ou tire da pasta.")
    if not datas:
        abortar(f"nenhum arquivo {_HIER['padrao']} em {pasta}\n  (config/config.yaml -> fontes.hierarquia)")
    return datas[max(datas)]


# Cada nivel vira UM rotulo "codigo - nome" (02/10/2026, mesmo formato no Gerencial e no ROTA). O nome e limpo
# quando termina com "(codigo)" igual ao codigo da linha: sai o "(codigo)" e o "_" inicial (regra unica dos tres
# paineis, decisao R2 de 02/10/2026); fora disso entra como veio.
def _nome_limpo(cod: pd.Series, nome: pd.Series) -> tuple[pd.Series, pd.Series]:
    partes = nome.str.extract(r"^_?(.+?)\s*\(\s*(\d+)\s*\)$")
    casa = partes[0].notna() & (partes[1] == cod)
    return nome.where(~casa, partes[0].str.strip()), casa.fillna(False)


def _ler_hierarquia(arq: Path) -> tuple[pd.DataFrame, dict]:
    df = _ler_aba(arq, _HIER["aba"], "hierarquia")
    niveis = _HIER["niveis"]
    _validar(df, [_HIER["coluna_cliente"]] + [c for cols in niveis.values() for c in cols], arq)
    out = pd.DataFrame(index=df.index)
    out["COD_CLIENTE"] = digitos(df[_HIER["coluna_cliente"]])
    fora_padrao = {}
    for destino, (c_cod, c_nome) in niveis.items():
        cod = texto(df[c_cod], maiuscula=False)
        nome, limpo = _nome_limpo(cod, texto(df[c_nome], maiuscula=False))
        out[destino] = (cod.fillna("") + (" - " + nome).fillna("")).str.strip(" -").replace({"": pd.NA})
        fora_padrao[destino] = sorted(out.loc[~limpo, destino].dropna().unique().tolist())
    out = out.dropna(subset=["COD_CLIENTE"])
    conflito = out.groupby("COD_CLIENTE")["SUPERVISOR"].nunique()
    extra = {"conflitos_supervisor": int((conflito > 1).sum()), "linhas_brutas": int(len(df)),
             "fora_padrao_nome": fora_padrao}
    return out.drop_duplicates("COD_CLIENTE", keep="first").reset_index(drop=True), extra


def ler_hierarquia() -> pd.DataFrame:
    arq = arquivo_hierarquia()
    log(f"hierarquia: {arq.name} (a de data mais recente em {arq.parent.name})")
    d, extra = cache.ler(arq, _ler_hierarquia)
    _contar(arq, d, extra)
    if extra.get("conflitos_supervisor"):
        log(f"{arq.name}: {extra['conflitos_supervisor']} cliente(s) com mais de um "
            "supervisor (N3) — vale a 1a linha", "aviso")
    for nivel, rots in (extra.get("fora_padrao_nome") or {}).items():
        if rots:
            log(f"hierarquia: {len(rots)} rotulo(s) de {nivel} com nome fora do padrao 'NOME (codigo)', "
                f"usados como vieram: {rots[:6]}")
    log(f"hierarquia: {len(d):,} clientes · {d['SUPERVISOR'].nunique()} supervisores")
    return d


# ------------------------------------------------------------------- RTM
def _ler_rtm(arq: Path) -> tuple[pd.DataFrame, dict]:
    df = _ler_aba(arq, _RTM["aba"], "rtm")
    _validar(df, _RTM["colunas_obrigatorias"], arq)
    out = pd.DataFrame(index=df.index)
    out["COD_PDV"] = cnpj(df["CNPJ"])
    out["COD_CLIENTE_ANTIGO"] = digitos(df["Cód. Cliente [Antigo]"])
    out["BANDEIRA_ANTIGA"] = texto(df["Bandeira cliente [Antigo]"]) if "Bandeira cliente [Antigo]" in df.columns else pd.NA
    out["DISTRIBUIDOR_RTM"] = texto(df["Dsitribuidor Nome Reduzido"])
    out["COD_CLIENTE_DISTRIBUIDOR_RTM"] = (digitos(df["Cód. Cliente [Distribuidor]"])
                                          if "Cód. Cliente [Distribuidor]" in df.columns else pd.NA)
    # Fase 4 (P2/P3): chave do destino por CNPJ, quando a coluna existir; sem ela, a juncao e por nome
    col_cnpj = next((c for c in (_RTM.get("colunas_opcionais") or []) if c in df.columns), None)
    out["CNPJ_DESTINO"] = cnpj(df[col_cnpj]) if col_cnpj else pd.Series(pd.NA, index=df.index, dtype="string")
    out = out.dropna(subset=["COD_PDV"])
    extra = {"duplicados": int(out.duplicated("COD_PDV").sum()),
             "sem_cnpj": int(df["CNPJ"].isna().sum()), "linhas_brutas": int(len(df)),
             "tem_cnpj_destino": bool(col_cnpj), "com_cnpj_destino": int(out["CNPJ_DESTINO"].notna().sum())}
    return out.drop_duplicates("COD_PDV", keep="first").reset_index(drop=True), extra


def ler_rtm() -> pd.DataFrame:
    arq = _existe(_RTM, "rtm")
    d, extra = cache.ler(arq, _ler_rtm)
    _contar(arq, d, extra)
    if extra.get("sem_cnpj"):
        log(f"{arq.name}: {extra['sem_cnpj']} cliente(s) sem CNPJ — ficam fora do cruzamento", "aviso")
    if extra.get("duplicados"):
        log(f"{arq.name}: {extra['duplicados']} CNPJ repetido(s) — vale a 1a linha", "aviso")
    if extra.get("tem_cnpj_destino"):
        log(f"RTM: destino por CNPJ em {extra.get('com_cnpj_destino', 0):,} cliente(s) (coluna opcional presente)")
    else:
        log(f"{arq.name}: sem coluna de CNPJ do destino ({_RTM.get('colunas_opcionais')}) — destino casado por NOME "
            "(nome que nao casar vira 'destino sem cadastro'; ver aviso da Fase 2)", "aviso")
    log(f"RTM: {len(d):,} clientes com CNPJ · {d['DISTRIBUIDOR_RTM'].nunique()} distribuidores de destino")
    return d


# ------------------------------------------------------- CLUSTERS (opcional, C5)
def _ler_clusters(arq: Path) -> tuple[pd.DataFrame, dict]:
    aba = _CLU.get("aba")
    df = _ler_aba(arq, aba if aba is not None else 0, "clusters")
    _validar(df, _CLU["colunas_obrigatorias"], arq)
    out = pd.DataFrame(index=df.index)
    out["SEGMENTO_MTRIX"] = texto(df["SEGMENTO MTRIX"])
    out["CLUSTER"] = texto(df["CLUSTER PAINEL"])
    out = out.dropna(subset=["SEGMENTO_MTRIX", "CLUSTER"])
    extra = {"duplicados": int(out.duplicated("SEGMENTO_MTRIX").sum()), "linhas_brutas": int(len(df))}
    return out.drop_duplicates("SEGMENTO_MTRIX", keep="first").reset_index(drop=True), extra


def ler_clusters() -> pd.DataFrame | None:
    """De-para de clusters. Ausente = None (o painel usa os segmentos da Mtrix como vem)."""
    if not _CLU:
        return None
    arq = caminho(_CLU["arquivo"])
    if not arq.exists():
        log(f"de-para de clusters ausente ({arq.name}) — clusters = Segmento do PDV da Mtrix (34 valores)", "aviso")
        return None
    d, extra = cache.ler(arq, _ler_clusters)
    _contar(arq, d, extra)
    if extra.get("duplicados"):
        log(f"{arq.name}: {extra['duplicados']} segmento(s) repetido(s) — vale a 1a linha", "aviso")
    log(f"clusters: {len(d)} segmentos Mtrix -> {d['CLUSTER'].nunique()} clusters do painel", "ok")
    return d


# ------------------------------------------- PDVs PONDERADOS (opcional, RN-56)
def _ler_pdv_ponderada(arq: Path) -> tuple[pd.DataFrame, dict]:
    df = _ler_aba(arq, _PON.get("aba") or 0, "pdv_ponderada")
    _validar(df, _PON["colunas_obrigatorias"], arq)
    out = pd.DataFrame(index=df.index)
    out["LINHA"] = (df.index + 2).astype("int64")          # linha do Excel (cabecalho na linha 1)
    # CNPJ como texto de 14 digitos: celula numerica no Excel perde o zero a esquerda, e sem ele o par nao casa com a Mtrix
    out["CNPJ_DISTRIBUIDOR"] = cnpj(df["CNPJ DISTRIBUIDOR"]).str.zfill(14)
    out["DISTRIBUIDOR"] = texto(df["DISTRIBUIDOR"])
    out["COD_PDV"] = cnpj(df["CNPJ PDV"]).str.zfill(14)
    out["RAZAO_SOCIAL"] = texto(df["RAZÃO SOCIAL VAREJO"])
    out["CLUSTER"] = texto(df["CLUSTER"])
    vazia = out[["CNPJ_DISTRIBUIDOR", "COD_PDV", "CLUSTER"]].isna().all(axis=1)
    return out[~vazia].reset_index(drop=True), {"linhas_brutas": int(len(df))}


def ler_pdv_ponderada() -> pd.DataFrame | None:
    """Planilha da carteira de PDVs ponderados (RN-56). Ausente = None (o painel sai sem a carteira).
    Nada e corrigido aqui: a validade de cada linha e decidida no calculo (`metrics.carteira`)."""
    if not _PON:
        return None
    arq = caminho(_PON["arquivo"])
    if not arq.exists():
        log(f"planilha da carteira ausente ({arq.name}) — painel sem a carteira de PDVs ponderados", "aviso")
        return None
    d, extra = cache.ler(arq, _ler_pdv_ponderada)
    _contar(arq, d, extra)
    log(f"carteira: {len(d)} linha(s) lidas de {arq.name} (" + ", ".join(f"{k} {v}" for k, v in d["CLUSTER"].value_counts().items()) + ")", "ok")
    return d
