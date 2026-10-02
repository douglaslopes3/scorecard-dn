# Fase 1 · ingestão da Mtrix → camada curada

Executada em 08/09/2026 (execução `20260908-175407-a3290c`). Código em `dn/`, config em `config/config.yaml`, runner `run_fase1.py`. O `src/` do projeto gerencial ficou intacto como referência; dele foram copiados sem alteração `utils/log.py`, `utils/texto.py`, `extract/cache.py`, `load/parquet.py` e `transform/calendario.py`, e adaptados `utils/config.py` (sem `geografia.yaml`), `extract/sellin.py` → `extract/sellout.py`, `extract/cadastros.py`, `transform/fato.py`, `transform/dimensoes.py` e `qualidade.py`.

## Como rodar

```bash
python run_fase1.py
```

- Primeira execução: ~4 min (lê 12 Excel de 40 MB e grava o cache em `data/dn/staging/`). Execuções seguintes: segundos, enquanto os Excel não mudarem (chave do cache: caminho, tamanho, data, hash e `VERSAO_CACHE`).
- Log em `data/dn/logs/pipeline_<execução>.log`. Exit code 1 e "PIPELINE ABORTADO" em qualquer conferência que falhe; nenhum Parquet é gravado pela metade.

## O que entra

| Fonte | Arquivo | Uso |
|---|---|---|
| Mtrix | `Sell Out - MTRIX/ScoreCard_Mtrix_*.xlsx` (12; `07.2026` ignorado por config até a reextração) | fato |
| Produtos | `bases/Bases para tabelas dimensões/Produtos.xlsx` | categoria por SKU |
| Distribuidores | `bases/Bases para tabelas dimensões/Distribuidores_DePara.xlsx` | CNPJ ↔ código interno ↔ status ↔ nome reduzido |
| Hierarquia | `bases/Bases para tabelas dimensões/Hierarquia_Consolidada.xlsx` | rótulos N1/N2/N3 (`código - função - nome`) |
| RTM | `bases/RTM-Transicao/RTM_DePara_Transicao.xlsx` (com a coluna `CNPJ`) | flag `ORIGEM_RTM` no PDV |

## O que sai (`data/dn/curated/`)

| Tabela | Grão | Linhas | Colunas |
|---|---|---:|---|
| `FATO_SELLOUT/ANO=…` | mês × distribuidor × PDV × SKU | 5.328.125 | `ANO_MES`, `CNPJ_DISTRIBUIDOR`, `COD_PDV`, `COD_PRODUTO`, `RECEITA`, `UNIDADES`, `PESO_KG`, `ARQUIVO_ORIGEM`, `EXECUCAO_ID`, `PROCESSADO_EM` |
| `DIM_PDV` | PDV | 149.454 | `COD_PDV`, `TIPO_CHAVE_PDV` (CNPJ/LGPD/OUTRO), `CNPJ_REDUZIDO`, `NOME_PDV`, `UF`, `CIDADE`, `ENDERECO`, `BAIRRO`, `CEP`, `SEGMENTO_MTRIX`, `PRIMEIRO_MES`, `LGPD`, `ORIGEM_RTM`, `DISTRIBUIDOR_RTM`, `COD_CLIENTE_ANTIGO` |
| `DIM_DISTRIBUIDOR` | CNPJ de filial | 79 | `CNPJ_DISTRIBUIDOR`, `DISTRIBUIDOR_MTRIX`, `NOME_REDUZIDO`, `RAZAO_SOCIAL`, `COD_CLIENTE`, `STATUS`, `HEAD`, `GERENTE`, `SUPERVISOR`, `SUPERVISOR_DEPARA`, `GERENTE_DEPARA`, `NA_HIERARQUIA`, `NO_PAINEL`, `TEM_SELLOUT`, `PRIMEIRO_MES`, `ULTIMO_MES` |
| `DIM_PRODUTO` | SKU movimentado | 286 | `COD_PRODUTO`, `DESCRICAO_PRODUTO`, `CATEGORIA`, `MARCA`, `FORA_DO_CADASTRO` |
| `DIM_CALENDARIO` | mês | 12 | civil e fiscal (set–ago), `ANO_MES_LY` por junção |
| `resumo.json` | execução | | contagens principais |

Relatório e listas de exceção em `data/dn/quality/` (`relatorio_qualidade.md`, `linhagem_arquivos.csv`, `pdvs_por_mes.csv`, `pdv_chave_outro.csv`, `distribuidores_fora_hierarquia.csv`, `skus_sem_cadastro.csv`, `segmentos_mtrix.csv`, `rtm_por_mes.csv`).

## Regras aplicadas (todas declaradas em `config/config.yaml → regras`)

- A fato não agrega nem filtra: entram todas as linhas dos 12 arquivos, inclusive kg ≤ 0 (82 linhas) e os distribuidores fora do painel. Positivação, base ativa, segmentos e exclusões são aplicados na Fase 2 a partir das flags das dimensões.
- Chave do distribuidor: `CNPJ do AD.` com 14 dígitos, zeros preservados (`texto.cnpj()`), obrigatoriamente presente no de-para. Fora disso o arquivo é rejeitado (é como jul/26 seria pego).
- Chave do PDV: classificada em CNPJ (14 dígitos), LGPD (id negativo com razão social "LGPD MTX") ou OUTRO; nada é corrigido; OUTRO acima de 1% das linhas rejeita o arquivo.
- Categoria: só do `Produtos.xlsx`; SKU fora do cadastro entra como `SEM CADASTRO` (hoje: 0).
- Distribuidor sem linha na `Hierarquia_Consolidada`: `NO_PAINEL = False` (9 CNPJs, rodada 7).
- Reconciliação: soma da fato × linha de total de cada arquivo em R$, unidades e kg, com tolerância de R$ 1, 1 unidade e 0,5 kg. PDVs e SKUs do total da Mtrix são conferidos como informação (diferenças de 1 a 6 PDVs em 8 arquivos; a Mtrix conta com a chave crua dela).

## Números desta execução

| Medida | Valor |
|---|---:|
| Meses | 12 (jul/25 a jun/26) |
| Linhas na fato | 5.328.125 |
| Volume total | 13.738 t |
| PDVs distintos na série | 149.454 (CNPJ 132.587 · LGPD 16.795 · OUTRO 72) |
| Distribuidores no de-para / com sell-out / no painel | 79 / 76 / 70 |
| Supervisores (N3) entre os do painel | 14 |
| SKUs movimentados / fora do cadastro | 286 / 0 |
| Clientes RTM com sell-out em algum mês | 567 de 1.762 |
| Primeiro mês com janela de 5 meses completa | nov/25 |
| Meses com LY possível | 0 (a série tem 12 meses) |
| Peso dos 9 distribuidores fora do painel | 9.965 PDVs e 798,7 t na série (5,8% do kg; em jun/26, 1,7%) |

## Pendências que a Fase 2 herda

- Reextração de jul/26 (retirar de `fontes.sellout.arquivos_ignorados` quando chegar).
- De-para de clusters: preencher `CLUSTER_PAINEL` em `data/dn/quality/segmentos_mtrix.csv` (ou entregar um Excel com as duas colunas) e declará-lo no config.
- Data de início dos distribuidores (C3): sem ela a segmentação usa `PRIMEIRO_MES` da série.
- Critério de "maiores PDVs" para a tabela do HTML (proposta: kg na janela da base ativa).
