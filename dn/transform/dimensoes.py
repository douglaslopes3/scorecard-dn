# -*- coding: utf-8 -*-
"""DIM_PDV, DIM_DISTRIBUIDOR e DIM_PRODUTO.

Regra comum (herdada do projeto gerencial): **quem aparece na fato existe na
dimensão**. Nada é descartado; o que não casa com cadastro recebe rótulo de
ausência declarado no config e sai na lista de exceções.
"""
from __future__ import annotations

import pandas as pd

from ..utils.config import CFG
from ..utils.log import abortar, log

_SEM_CAD = CFG["dimensoes"]["rotulo_sem_cadastro"]
_SEM_HIER = CFG["dimensoes"]["rotulo_sem_hierarquia"]
_EXCLUIR = bool(CFG["regras"].get("distribuidor_excluir_sem_hierarquia", False))


def dim_distribuidor(depara: pd.DataFrame, hier: pd.DataFrame, dist_fato: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por CNPJ do de-para (rodada 2: distribuidor = CNPJ de filial).

    - rótulos HEAD/GERENTE/SUPERVISOR = N1/N2/N3 "código - nome" da Hierarquia_AAAAMMDD
      (02/10/2026), pela ponte `COD_CLIENTE` (rodada 6);
    - `NA_HIERARQUIA` False -> rótulo de ausência e, se `regras.distribuidor_excluir_sem_hierarquia`,
      `NO_PAINEL` False (rodada 7: esses distribuidores saem do painel);
    - `PRIMEIRO_MES` / `ULTIMO_MES` com sell-out na série (dado, não regra: a segmentação
      Base atual / Novos e da Fase 2);
    - `DATA_CADASTRO` vem do de-para (C3, 09/09/2026) e e a fonte de maturidade quando
      existe; sem ela a Fase 2 volta a inferir pelo `PRIMEIRO_MES`, censurado pela serie.
    """
    d = depara.merge(hier[["COD_CLIENTE", "HEAD", "GERENTE", "SUPERVISOR"]],
                     on="COD_CLIENTE", how="left", validate="m:1")
    assert len(d) == len(depara), "o merge da hierarquia multiplicou distribuidores"
    d["NA_HIERARQUIA"] = d["SUPERVISOR"].notna()
    for c in ("HEAD", "GERENTE", "SUPERVISOR"):
        d[c] = d[c].fillna(_SEM_HIER)
    d["NO_PAINEL"] = ~(_EXCLUIR & ~d["NA_HIERARQUIA"])

    # presenca na fato
    primeiro = dist_fato.groupby("CNPJ_DISTRIBUIDOR")["ANO_MES"].min()
    ultimo = dist_fato.groupby("CNPJ_DISTRIBUIDOR")["ANO_MES"].max()
    d["PRIMEIRO_MES"] = d["CNPJ_DISTRIBUIDOR"].map(primeiro).astype("string")
    d["ULTIMO_MES"] = d["CNPJ_DISTRIBUIDOR"].map(ultimo).astype("string")
    d["TEM_SELLOUT"] = d["PRIMEIRO_MES"].notna()

    # distribuidor na fato sem linha no de-para: aborta (nao se inventa distribuidor)
    fora = set(dist_fato["CNPJ_DISTRIBUIDOR"]) - set(d["CNPJ_DISTRIBUIDOR"])
    if fora:
        nomes = dist_fato[dist_fato["CNPJ_DISTRIBUIDOR"].isin(fora)].drop_duplicates("CNPJ_DISTRIBUIDOR")
        abortar(f"{len(fora)} CNPJ(s) de distribuidor na Mtrix SEM linha no Distribuidores_DePara.xlsx:\n"
                + "\n".join(f"    {r.CNPJ_DISTRIBUIDOR}  {r.DISTRIBUIDOR_MTRIX}" for r in nomes.head(10).itertuples())
                + "\n  Complete o de-para e rode de novo.")
    n_fora = int((~d["NA_HIERARQUIA"]).sum())
    log(f"distribuidores: {len(d)} no de-para · {int(d['TEM_SELLOUT'].sum())} com sell-out · "
        f"{n_fora} sem linha na hierarquia" + (" (FORA do painel)" if _EXCLUIR else ""), "ok")
    d["DATA_CADASTRO"] = (pd.to_datetime(d["DATA_CADASTRO"], errors="coerce")
                          if "DATA_CADASTRO" in d.columns
                          else pd.Series(pd.NaT, index=d.index, dtype="datetime64[ns]"))
    # cadastro POSTERIOR ao 1o mes com sell-out e contradicao de base: avisa, nao corrige
    incoerente = d["DATA_CADASTRO"].notna() & d["PRIMEIRO_MES"].notna() & (
        d["DATA_CADASTRO"].dt.strftime("%Y-%m") > d["PRIMEIRO_MES"])
    if incoerente.any():
        ex = d.loc[incoerente, "NOME_REDUZIDO"].head(5).tolist()
        log(f"{int(incoerente.sum())} distribuidor(es) com data de cadastro POSTERIOR ao 1o mes "
            f"com sell-out — a data foi mantida como veio: {ex}", "aviso")
    cols = ["CNPJ_DISTRIBUIDOR", "DISTRIBUIDOR_MTRIX", "NOME_REDUZIDO", "RAZAO_SOCIAL", "COD_CLIENTE",
            "STATUS", "HEAD", "GERENTE", "SUPERVISOR", "SUPERVISOR_DEPARA", "GERENTE_DEPARA",
            "NA_HIERARQUIA", "NO_PAINEL", "TEM_SELLOUT", "PRIMEIRO_MES", "ULTIMO_MES", "DATA_CADASTRO"]
    return d[cols].sort_values("DISTRIBUIDOR_MTRIX").reset_index(drop=True)


def dim_pdv(pdv_attrs: pd.DataFrame, rtm: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por `COD_PDV`. O atributo MAIS RECENTE vence (PDV que muda de
    segmento ou de razão social no meio da série aparece uma vez). `ORIGEM_RTM`
    marca os CNPJs da base RTM (rodada 6)."""
    d = (pdv_attrs.sort_values("ANO_MES", kind="stable")
                  .drop_duplicates("COD_PDV", keep="last")
                  .drop(columns=["ANO_MES"]))
    primeiro = pdv_attrs.groupby("COD_PDV")["ANO_MES"].min()
    d["PRIMEIRO_MES"] = d["COD_PDV"].map(primeiro).astype("string")
    d["LGPD"] = d["TIPO_CHAVE_PDV"] == "LGPD"

    r = rtm.set_index("COD_PDV")
    d["ORIGEM_RTM"] = d["COD_PDV"].isin(r.index)
    d["DISTRIBUIDOR_RTM"] = d["COD_PDV"].map(r["DISTRIBUIDOR_RTM"]).astype("string")
    d["COD_CLIENTE_ANTIGO"] = d["COD_PDV"].map(r["COD_CLIENTE_ANTIGO"]).astype("string")
    n_rtm = int(d["ORIGEM_RTM"].sum())
    log(f"PDVs: {len(d):,} · chave {d['TIPO_CHAVE_PDV'].value_counts().to_dict()} · "
        f"{n_rtm:,} da base RTM ({len(rtm):,} na base)", "ok")
    return d.sort_values("COD_PDV").reset_index(drop=True)


def dim_produto(skus_fato: pd.Series, produtos: pd.DataFrame) -> pd.DataFrame:
    d = pd.DataFrame({"COD_PRODUTO": pd.Series(sorted(skus_fato.dropna().unique()), dtype="string")})
    d = d.merge(produtos, on="COD_PRODUTO", how="left", validate="1:1")
    d["FORA_DO_CADASTRO"] = d["DESCRICAO_PRODUTO"].isna()
    d["DESCRICAO_PRODUTO"] = d["DESCRICAO_PRODUTO"].fillna(_SEM_CAD)
    d["CATEGORIA"] = d["CATEGORIA"].fillna(_SEM_CAD)
    fora = int(d["FORA_DO_CADASTRO"].sum())
    if fora:
        log(f"{fora} SKU(s) da Mtrix FORA do Produtos.xlsx — entram como '{_SEM_CAD}' "
            "(categoria nao e inferida)", "aviso")
    log(f"produtos: {len(d)} SKUs movimentados · {d['CATEGORIA'].nunique()} categorias", "ok")
    return d[["COD_PRODUTO", "DESCRICAO_PRODUTO", "CATEGORIA", "MARCA", "FORA_DO_CADASTRO"]]
