# Fase 2 · métricas de DN e JSON do painel

Executada em 08/09/2026 sobre a camada curada da Fase 1. Código: `dn/metrics.py` (cálculo), `dn/painel.py` (JSON no contrato do template), `dn/render.py` (formatação pelo inventário + Handlebars mínimo em Python), runner `run_fase2.py`.

## Como rodar

```bash
python run_fase2.py            # mês de referência = último da série
python run_fase2.py 2026-05    # ou um mês específico
```

Roda em ~30 s. Saídas em `data/dn/curated/DN_*.parquet` e `data/dn/painel/` (`painel_dn.raw.json` numérico, `painel_dn.json` formatado, `Scorecard_DN_<mês>.html` prévia com o template atual).

## Regras aplicadas (config `regras`, decisões em `docs/mapeamento.md` §5)

| Métrica | Cálculo |
|---|---|
| positivado | linha com `PESO_KG > 0` |
| `cobertura_pdv` | PDVs distintos positivados no mês, no nível |
| `base_ativa` | PDVs distintos positivados em algum dos últimos **5** meses (janela fechada no mês). Nula quando a janela não está completa (jul/25 a out/25) |
| `pct_cobertura` (DN) | `cobertura_pdv ÷ base_ativa` |
| `volume_t` | soma de `PESO_KG` ÷ 1000, todas as linhas |
| `kg_pdv` | `volume_t × 1000 ÷ cobertura_pdv` |
| categoria | `pct_cobertura` = positivados na categoria ÷ base ativa do nível; `penetracao` = positivados na categoria ÷ positivados do nível |
| comparativos | vs mês anterior; vs média dos 3 meses anteriores (só com os 3 presentes); vs LY pela `DIM_CALENDARIO.ANO_MES_LY` (nulo: a série tem 12 meses). Variação % para cobertura e volume, p.p. para o % de cobertura |
| contagem por nível | distribuidor: PDV conta em cada um; canal, segmento, supervisor e cluster: PDV conta uma vez dentro do nível (rodada 5) |
| distribuidores | só `NO_PAINEL` e com sell-out: **67** (79 no de-para − 9 sem hierarquia − 3 sem sell-out) |
| segmento | meses de histórico = de `PRIMEIRO_MES` na Mtrix até o mês de referência, inclusive; `> 6` → Base atual, senão Novos. Avaliado no mês de referência e aplicado à série inteira. `historico_censurado = true` para quem já vendia em jul/25 (C3 pendente) |
| supervisor | rótulo N3 `código - função - nome` da hierarquia, via de-para |
| cluster | `Segmento do PDV` da Mtrix como vem (34 valores) até haver o de-para (C5) |
| PDVs no JSON | os 20 maiores por kg na janela, por distribuidor (config `painel.pdv_top_por_distribuidor`); a base ativa completa (118.371 pares) fica em `DN_PDV_BASE_ATIVA` para a busca da Fase 3 |

## Tabelas geradas (`data/dn/curated/`)

| Tabela | Grão | Linhas |
|---|---|---:|
| `DN_CANAL_MES` | mês | 12 |
| `DN_SEGMENTO_MES` | mês × segmento | 15 |
| `DN_SUPERVISOR_MES` / `DN_SUPERVISOR_CANAL_MES` | mês × segmento × supervisor / mês × supervisor | 158 / 157 |
| `DN_CLUSTER_MES` / `DN_CLUSTER_CANAL_MES` | mês × segmento × cluster / mês × cluster | 428 / 408 |
| `DN_DISTRIBUIDOR_MES` | mês × distribuidor | 775 |
| `DN_CANAL_CAT_MES`, `DN_SEGMENTO_CAT_MES`, `DN_DISTRIBUIDOR_CAT_MES` | idem × categoria | 120 / 150 / 7.285 |
| `DN_PDV_BASE_ATIVA` | distribuidor × PDV da base ativa de jun/26 (positivado no mês, mês anterior, meses na janela, último mês e kg, kg na janela) | 118.371 |

Colunas comuns das séries: `ANO_MES`, chaves do nível, `positivados`, `base_ativa`, `pct_cobertura`, `volume_kg`, `kg_pdv`, `{cobertura,pct_cobertura,volume}_var_{mes_anterior,l3m,ly}`, `ANO_MES_LY`; nas de categoria também `CAT`, `positivados_nivel`, `penetracao`.

## Números de jun/26 (canal)

| Medida | Valor |
|---|---:|
| Base ativa (5 meses, fev a jun/26) | 115.017 PDVs |
| PDVs positivados | 65.709 |
| DN | 57,1% (mai/26: 58,2%; L3M: +0,2 p.p.) |
| Volume | 1.162,1 t (+6,7% vs L3M) |
| Soma dos distribuidores | 67.312 positivados, 118.371 na base ativa (PDV em mais de um distribuidor conta em cada um) |
| Segmentos | Base atual 65 distribuidores, DN 56,9%; Novos 2 (Favinha, Dipam Gaúcha), DN 80,1% |
| Categorias (DN / penetração) | Amendoim 34,8% / 61,0% · Gomas 30,9% / 54,1% · Regaliz 23,8% / 41,6% · Gelatina 20,6% / 36,1% |
| Extremos por distribuidor | PROPEC 24,0%, MAM 26,2%, FAVINHA 26,9% · CSR 71,6%, DISPAN 69,8%, A S DA S E SILVA 69,4% |
| Oportunidade | 51.059 pares distribuidor × PDV da base ativa **sem** compra em jun/26 |

Série do canal (DN só a partir de nov/25, primeira janela completa):

| Mês | Positivados | Base ativa | DN |
|---|---:|---:|---:|
| nov/25 | 59.468 | 110.136 | 54,0% |
| dez/25 | 53.205 | 108.613 | 49,0% |
| jan/26 | 59.951 | 108.243 | 55,4% |
| fev/26 | 58.767 | 109.055 | 53,9% |
| mar/26 | 62.530 | 109.269 | 57,2% |
| abr/26 | 60.767 | 109.998 | 55,2% |
| mai/26 | 65.778 | 113.015 | 58,2% |
| jun/26 | 65.709 | 115.017 | 57,1% |

## Contrato do JSON

Segue `template/data-inventory.json` (129 campos) e acrescenta campos novos, formatados pelo mesmo padrão: `periodo.janela_base_ativa`, `distribuidor.{cnpj,nome_reduzido,status,historico_censurado,primeiro_mes}`, `segmento.n_distribuidores`, `pdv.{cidade,ultimo_mes_compra,kg_ultimo_mes,kg_janela,origem_rtm,tipo_chave}`, `categoria.{base_ativa,kg_pdv,pct_cobertura_var_*,volume_var_*}` e `meta_execucao`. A Fase 3 atualiza o inventário e o template para usá-los (tabela de PDVs com busca sobre a base ativa, cluster via de-para).

## Verificações feitas

- O renderizador Python reproduz byte a byte `template/Scorecard_DN_base.html` a partir de `template/example-data.json` (o pipeline aborta se não reproduzir).
- Soma de positivados por distribuidor ≥ canal e categorias com a mesma base ativa do canal, conforme as regras.
- DN nula (não zero) nos meses sem janela completa; LY nulo em toda a série.
