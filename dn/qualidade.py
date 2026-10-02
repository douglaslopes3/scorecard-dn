# -*- coding: utf-8 -*-
"""Relatório de qualidade e linhagem da etapa de ingestão. Mede, escreve e conta; não corrige.

Saídas em `data/dn/quality/`:
  relatorio_qualidade.md            o relatório da execução
  linhagem_arquivos.csv             arquivo -> mês, linhas, totais, gabarito
  pdvs_por_mes.csv                  PDVs positivados, pares distribuidor×PDV, LGPD, multi-distribuidor, janela
  pdv_chave_outro.csv               PDVs cuja chave não é CNPJ nem LGPD
  distribuidores_fora_hierarquia.csv os que saem do painel (rodada 7)
  skus_sem_cadastro.csv             SKUs da Mtrix fora do Produtos.xlsx
  segmentos_mtrix.csv               os segmentos da Mtrix com PDVs e kg — esqueleto do de-para de clusters (C5)
  rtm_por_mes.csv                   clientes RTM positivados por mês e distribuidor
"""
from __future__ import annotations

from datetime import datetime

import pandas as pd

from .utils.config import CFG, PASTA_QUALITY
from .utils.log import EXECUCAO_ID, log

_JANELA = int(CFG["regras"]["janela_base_ativa_meses"])


def _csv(df: pd.DataFrame, nome: str) -> None:
    PASTA_QUALITY.mkdir(parents=True, exist_ok=True)
    df.to_csv(PASTA_QUALITY / nome, index=False, encoding="utf-8-sig", sep=";", decimal=",")


def _fmt(x: float, casas: int = 2) -> str:
    return f"{x:,.{casas}f}".replace(",", "@").replace(".", ",").replace("@", ".")


def gerar(fato: pd.DataFrame, dim_pdv: pd.DataFrame, dim_dist: pd.DataFrame,
          dim_prod: pd.DataFrame, dim_cal: pd.DataFrame, meta: dict,
          avisos: list[str]) -> dict:
    PASTA_QUALITY.mkdir(parents=True, exist_ok=True)
    L: list[str] = []
    resumo: dict = {}
    linha = L.append

    linha(f"# Relatório de qualidade · ingestão Mtrix — execução `{EXECUCAO_ID}`")
    linha("")
    linha(f"Gerado em {datetime.now():%d/%m/%Y %H:%M:%S}. Regras aplicadas: `config/config.yaml → regras`. Nada foi corrigido.")
    linha("")

    # ------------------------------------------------------- 1. arquivos
    linha("## 1. Arquivos processados")
    linha("")
    por_arq = (fato.groupby("ARQUIVO_ORIGEM", observed=True)
                   .agg(LINHAS=("RECEITA", "size"), RECEITA=("RECEITA", "sum"),
                        UNIDADES=("UNIDADES", "sum"), PESO_KG=("PESO_KG", "sum"),
                        PDVS=("COD_PDV", "nunique"), DISTRIBUIDORES=("CNPJ_DISTRIBUIDOR", "nunique"),
                        SKUS=("COD_PRODUTO", "nunique"))
                   .reset_index())
    por_arq["ARQUIVO_ORIGEM"] = por_arq["ARQUIVO_ORIGEM"].astype("string")
    por_arq["MESES"] = por_arq["ARQUIVO_ORIGEM"].map(lambda a: ", ".join(meta["meses_por_arquivo"].get(a, [])))
    gab = meta["gabaritos"]
    por_arq["GABARITO_PDVS"] = por_arq["ARQUIVO_ORIGEM"].map(lambda a: (gab.get(a) or {}).get("pdvs_positivados"))
    por_arq["GABARITO_KG"] = por_arq["ARQUIVO_ORIGEM"].map(lambda a: (gab.get(a) or {}).get("peso_kg"))
    por_arq = por_arq.sort_values("MESES")
    _csv(por_arq, "linhagem_arquivos.csv")
    linha(f"- **Aceitos:** {len(por_arq)}")
    ign = meta.get("ignorados") or {}
    linha(f"- **Ignorados por config:** {len(ign)}" + (" — " + "; ".join(f"`{k}` ({v})" for k, v in ign.items()) if ign else ""))
    linha("- **Rejeitados:** 0 — arquivo incompatível aborta antes deste ponto")
    linha("")
    linha("| Arquivo | Mês | Linhas | Distrib. | PDVs (calc.) | PDVs (total Mtrix) | SKUs | R$ | Unidades | kg |")
    linha("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for r in por_arq.itertuples():
        gp = "—" if pd.isna(r.GABARITO_PDVS) else f"{int(r.GABARITO_PDVS):,}"
        linha(f"| `{r.ARQUIVO_ORIGEM}` | {r.MESES} | {r.LINHAS:,} | {r.DISTRIBUIDORES} | {r.PDVS:,} | {gp} | {r.SKUS} | "
              f"{_fmt(r.RECEITA)} | {_fmt(r.UNIDADES, 0)} | {_fmt(r.PESO_KG)} |")
    linha("")
    linha("> Competência vem do conteúdo (`Ano/Mês`). R$, unidades e kg foram reconciliados contra a linha de total de cada arquivo (o pipeline aborta se não fechar). PDVs do total da Mtrix são informativos.")
    linha("")

    # -------------------------------------------------------- 2. período
    meses = sorted(fato["ANO_MES"].unique())
    resumo["meses"] = len(meses)
    resumo["periodo"] = f"{meses[0]} a {meses[-1]}"
    buracos = sorted(set(dim_cal["ANO_MES"]) - set(meses))
    linha("## 2. Período coberto")
    linha("")
    linha(f"- **{len(meses)} meses**, de `{meses[0]}` a `{meses[-1]}`")
    linha(f"- Meses sem arquivo dentro do intervalo: {('**' + ', '.join(buracos) + '**') if buracos else 'nenhum'}")
    com_ly = int(dim_cal["ANO_MES_LY"].notna().sum())
    linha(f"- Meses com ano anterior pareado (comparativo LY possível): **{com_ly} de {len(dim_cal)}**")
    linha(f"- Janela da base ativa: **{_JANELA} meses**; primeiro mês com janela completa: **{meses[_JANELA - 1] if len(meses) >= _JANELA else 'nenhum'}**")
    linha("")

    # -------------------------------------------------------- 3. totais
    linha("## 3. Totais e sinais")
    linha("")
    linha("| Métrica | Soma | Negativos | Zeros | Nulos |")
    linha("|---|---:|---:|---:|---:|")
    for col, nome in (("RECEITA", "Receita R$"), ("UNIDADES", "Unidades"), ("PESO_KG", "Peso kg")):
        s = fato[col]
        linha(f"| {nome} | {_fmt(s.sum())} | {int((s < 0).sum()):,} | {int((s == 0).sum()):,} | {int(s.isna().sum()):,} |")
        resumo[f"total_{col.lower()}"] = float(s.sum())
    n_np = int((fato["PESO_KG"] <= 0).sum())
    linha("")
    linha(f"- Linhas com kg ≤ 0 (não positivam, regra `PESO_KG > 0`): **{n_np:,}**")
    linha("")

    # -------------------------------------------------------- 4. chaves
    linha("## 4. Chaves e duplicidade")
    linha("")
    linha(f"- Duplicados no grão `ANO_MES × CNPJ_DISTRIBUIDOR × COD_PDV × COD_PRODUTO`: **0** de {len(fato):,} (o pipeline aborta se houver)")
    tipos = dim_pdv["TIPO_CHAVE_PDV"].value_counts()
    linha("- Tipo de chave dos PDVs (`Cód. PDV`): " + " · ".join(f"**{k}** {v:,}" for k, v in tipos.items()))
    outro = dim_pdv[dim_pdv["TIPO_CHAVE_PDV"] == "OUTRO"][["COD_PDV", "NOME_PDV", "UF", "SEGMENTO_MTRIX", "PRIMEIRO_MES"]]
    _csv(outro, "pdv_chave_outro.csv")
    linha(f"- PDVs com chave OUTRO (consumidor final, código interno etc.): **{len(outro):,}** → `pdv_chave_outro.csv`. Entram como PDV; não cruzam com CNPJ externo.")
    linha(f"- PDVs LGPD (anonimizados pela Mtrix, id estável): **{int(dim_pdv['LGPD'].sum()):,}**")
    linha("")

    # ------------------------------------------------ 5. distribuidores
    linha("## 5. Distribuidores")
    linha("")
    fora = dim_dist[~dim_dist["NA_HIERARQUIA"]]
    _csv(fora[["CNPJ_DISTRIBUIDOR", "DISTRIBUIDOR_MTRIX", "COD_CLIENTE", "STATUS", "SUPERVISOR_DEPARA", "TEM_SELLOUT", "ULTIMO_MES"]],
         "distribuidores_fora_hierarquia.csv")
    linha(f"- No de-para: **{len(dim_dist)}** CNPJs · com sell-out na série: **{int(dim_dist['TEM_SELLOUT'].sum())}** · status {dim_dist['STATUS'].value_counts().to_dict()}")
    linha(f"- Sem linha na Hierarquia: **{len(fora)}** → `distribuidores_fora_hierarquia.csv`; "
          + ("**fora do painel** (`regras.distribuidor_excluir_sem_hierarquia`)" if not fora["NO_PAINEL"].any() else "mantidos no painel"))
    if len(fora):
        peso = fato[fato["CNPJ_DISTRIBUIDOR"].isin(set(fora["CNPJ_DISTRIBUIDOR"]))]
        linha(f"- Peso deles na série: {peso['COD_PDV'].nunique():,} PDVs e {_fmt(peso['PESO_KG'].sum() / 1000, 1)} t "
              f"({peso['PESO_KG'].sum() / max(float(fato['PESO_KG'].sum()), 1):.2%} do kg)")
    linha(f"- Supervisores (N3 da hierarquia) entre os do painel: **{dim_dist.loc[dim_dist['NO_PAINEL'], 'SUPERVISOR'].nunique()}**")
    linha("")

    # ------------------------------------------------------- 6. produtos
    linha("## 6. Produtos e categorias")
    linha("")
    sem = dim_prod[dim_prod["FORA_DO_CADASTRO"]]
    _csv(sem, "skus_sem_cadastro.csv")
    linha(f"- SKUs movimentados: **{len(dim_prod)}** · fora do `Produtos.xlsx`: **{len(sem)}** → `skus_sem_cadastro.csv`")
    kgcat = (fato.merge(dim_prod[["COD_PRODUTO", "CATEGORIA"]], on="COD_PRODUTO", how="left")
                 .groupby("CATEGORIA")["PESO_KG"].sum().sort_values(ascending=False))
    linha("- kg por categoria na série: " + " · ".join(f"{k} {_fmt(v / 1000, 1)} t" for k, v in kgcat.items()))
    linha("")

    # ------------------------------------------------- 7. PDVs por mês
    linha("## 7. PDVs por mês (kg > 0), pares distribuidor × PDV e janela da base ativa")
    linha("")
    pos = fato[fato["PESO_KG"] > 0]
    pares = pos[["ANO_MES", "CNPJ_DISTRIBUIDOR", "COD_PDV"]].drop_duplicates()
    lgpd = set(dim_pdv.loc[dim_pdv["LGPD"], "COD_PDV"])
    rows = []
    sets: dict[str, set] = {}
    for m in meses:
        pm = pares[pares["ANO_MES"] == m]
        pdvs = set(pm["COD_PDV"])
        sets[m] = pdvs
        n_multi = int((pm.groupby("COD_PDV")["CNPJ_DISTRIBUIDOR"].nunique() > 1).sum())
        i = meses.index(m)
        jan = set().union(*[sets[x] for x in meses[max(0, i - _JANELA + 1):i + 1]])
        rows.append({"ANO_MES": m, "PDVS_POSITIVADOS": len(pdvs), "PARES_DIST_PDV": len(pm),
                     "PDVS_LGPD": len(pdvs & lgpd), "PDVS_MULTI_DISTRIBUIDOR": n_multi,
                     f"BASE_ATIVA_{_JANELA}M_CANAL": len(jan), "JANELA_COMPLETA": i >= _JANELA - 1,
                     "KG": float(pos.loc[pos["ANO_MES"] == m, "PESO_KG"].sum())})
    pm_df = pd.DataFrame(rows)
    _csv(pm_df, "pdvs_por_mes.csv")
    linha(f"| Mês | PDVs positivados | Pares dist.×PDV | LGPD | Multi-distribuidor | Base ativa {_JANELA}m (canal) | Janela completa | t |")
    linha("|---|---:|---:|---:|---:|---:|---|---:|")
    for r in pm_df.itertuples():
        linha(f"| {r.ANO_MES} | {r.PDVS_POSITIVADOS:,} | {r.PARES_DIST_PDV:,} | {r.PDVS_LGPD:,} | {r.PDVS_MULTI_DISTRIBUIDOR:,} | "
              f"{getattr(r, f'BASE_ATIVA_{_JANELA}M_CANAL'):,} | {'sim' if r.JANELA_COMPLETA else 'não'} | {_fmt(r.KG / 1000, 1)} |")
    linha("")
    linha("> PDV com mais de um distribuidor no mês conta em cada distribuidor e uma vez no canal (rodada 5). A base ativa do canal aqui é a contagem no canal; por distribuidor é calculada na Fase 2.")
    linha("")

    # ---------------------------------------------------------- 8. RTM
    linha("## 8. Base RTM")
    linha("")
    rtm_ids = set(dim_pdv.loc[dim_pdv["ORIGEM_RTM"], "COD_PDV"])
    n_base = int(meta.get("rtm_total", 0))
    rt = (pares[pares["COD_PDV"].isin(rtm_ids)]
          .merge(dim_dist[["CNPJ_DISTRIBUIDOR", "DISTRIBUIDOR_MTRIX"]], on="CNPJ_DISTRIBUIDOR", how="left")
          .groupby(["ANO_MES", "DISTRIBUIDOR_MTRIX"]).agg(CLIENTES_RTM=("COD_PDV", "nunique")).reset_index())
    _csv(rt, "rtm_por_mes.csv")
    por_mes = pares[pares["COD_PDV"].isin(rtm_ids)].groupby("ANO_MES")["COD_PDV"].nunique()
    linha(f"- Clientes na base RTM: **{n_base:,}** · com sell-out em algum mês da série: **{len(rtm_ids):,}** · nunca na Mtrix: **{n_base - len(rtm_ids):,}** (migração em andamento, comportamento esperado — rodada 7)")
    linha("- Positivados por mês: " + " · ".join(f"{m} {int(v):,}" for m, v in por_mes.items()))
    linha("")

    # ----------------------------------------------------- 9. segmentos
    linha("## 9. Segmentos da Mtrix (esqueleto do de-para de clusters, C5)")
    linha("")
    seg = (pos.merge(dim_pdv[["COD_PDV", "SEGMENTO_MTRIX"]], on="COD_PDV", how="left")
              .groupby("SEGMENTO_MTRIX").agg(PDVS=("COD_PDV", "nunique"), KG=("PESO_KG", "sum"))
              .sort_values("PDVS", ascending=False).reset_index())
    seg["CLUSTER_PAINEL"] = ""
    _csv(seg, "segmentos_mtrix.csv")
    linha(f"- **{len(seg)}** segmentos → `segmentos_mtrix.csv` com a coluna `CLUSTER_PAINEL` vazia para preencher. Enquanto não houver de-para, o painel usa os segmentos como vêm.")
    linha("")

    # -------------------------------------------------------- 10. avisos
    linha("## 10. Avisos desta execução")
    linha("")
    for a in avisos or ["nenhum"]:
        linha(f"- {a}")
    linha("")

    (PASTA_QUALITY / "relatorio_qualidade.md").write_text("\n".join(L), encoding="utf-8")
    log(f"relatorio de qualidade -> {PASTA_QUALITY / 'relatorio_qualidade.md'}", "ok")
    resumo.update({
        "execucao": EXECUCAO_ID, "arquivos": len(por_arq), "linhas": int(len(fato)),
        "pdvs": int(len(dim_pdv)), "distribuidores_painel": int(dim_dist["NO_PAINEL"].sum()),
        "skus": int(len(dim_prod)), "avisos": len(avisos),
    })
    return resumo
