# Frequência de compra · Etapa 1 · Medição das bases Mtrix

**Data:** 13/09/2026 · **Escopo:** só medição (itens 1 a 8 do pedido). **Nada foi proposto, e nada foi alterado** em `dn/`, `config/`,
`template/`, `bases/` ou `data/`. Este arquivo é o único gravado fora do scratchpad.

**Regra seguida:** nenhuma conclusão anterior (inclusive a memória `dn-mtrix-frequencia`) foi usada como fato. Todo número abaixo
foi calculado nesta sessão sobre os **25 arquivos** de `bases/Sell Out - MTRIX/` (lidos hoje; arquivos gravados em 11 e 12/09/2026).
Cada afirmação está marcada **MEDIDO** ou **HIPÓTESE**. Hipóteses ficam só na §9 e não são usadas em nenhuma conta.

## Como foi medido

| Passo | Script (scratchpad `…\scratchpad\freq\`) | O que faz |
|---|---|---|
| Leitura crua | `s01_converter.py` | Lê cada `.xlsx` com calamine, célula a célula, sem corrigir nada: guarda o cabeçalho exato, o nº da linha na planilha, o tipo de cada célula e o valor (texto e número) em `raw/*.parquet` |
| Itens 1–7 | `s02_por_arquivo.py` + `comum.py` | Normaliza as chaves com **as mesmas funções do pipeline** (`dn/utils/texto.py`: `cnpj`, `digitos`, `texto`, `ano_mes`, importadas sem gravar `.pyc`) e mede arquivo a arquivo → `out/<arquivo>.json` |
| Item 8 | `s03_comparar_publicado.py`, `s05_base_ativa.py` | Compara com `data/dn/staging` (leitura anterior, mesma etapa do leitor), `data/dn/curated/FATO_SELLOUT` e os cubos publicados `DN_CANAL_MES` / `DN_DISTRIBUIDOR_MES` |
| Tabelas | `s04_tabelas.py` | Só formata os JSON (não recalcula) |

Cadastros lidos do mesmo jeito que o pipeline (`pd.read_excel(dtype=str)` + normalização): `Produtos.xlsx` 1.712 SKUs, 0 repetidos,
11 categorias; `Distribuidores_DePara.xlsx` 80 CNPJs, 9 sem linha na `Hierarquia_Consolidada.xlsx`.

Conferência do método (MEDIDO): recalculando a partir de `curated/FATO_SELLOUT` com a régua RN-01/RN-02, obtive exatamente os números
publicados de ago/26 (positivados 71.478, base ativa 124.600) e de todos os meses nov/25–ago/26 de `DN_CANAL_MES`.

## 0. Resumo do que foi MEDIDO

1. **25 arquivos, set/24 a set/26**, um mês por arquivo, competência do conteúdo = nome do arquivo em todos; **nenhum mês faltando ou repetido**. set/26 é parcial (91.431 linhas).
2. **Dois layouts.** set/24–ago/25 (12 arquivos): 19 colunas, com `# PDVs Positivados`. **set/25–set/26 (13 arquivos): 18 colunas, sem `# PDVs Positivados`** e com as duas primeiras colunas trocadas de ordem. A coluna de frequência chama-se exatamente **`# Frequência de compra`** nos 25.
3. **Grão:** `mês × CNPJ do AD. × Cód. PDV × SKU` — 0 duplicados nos 25 arquivos. Uma linha de total por arquivo (linha 2 da planilha), 0 rodapés, 0 dimensões vazias.
4. **Linha de total:** R$, und e kg = soma das linhas (diferença ≤ 3×10⁻⁷). `# PDVs Positivados` = Cód. PDV distintos (12 de 12). `# Total SKUs` = SKUs distintos (25 de 25). Nas linhas, essas duas colunas valem 1 em todas.
5. **Frequência nas linhas:** número inteiro (gravado como float), **0 nulos, mínimo 1 em todos os arquivos**, máximo 8 a 20 (5 em set/26). Em 93,1% a 95,6% das linhas vale 1. Nunca é 0, nem nas linhas com kg ≤ 0.
6. **Varia entre SKUs do mesmo PDV:** em 10,1% a 16,6% dos PDVs com mais de uma linha (4.061 a 9.420 PDVs por mês fechado, com 24,7% a 36,5% do kg). No nível PDV × categoria, varia em 7,0% a 11,7%.
7. **Frequência da linha de total × linhas:** **nenhuma das 99 combinações testadas (regra × população) bate.** A mais próxima erra de 2,98% a 7,18%. Fato medido: **frequência do total × Cód. PDV distintos dá um número inteiro nos 25 arquivos** (distância ≤ 4,4×10⁻¹¹). Nenhum outro denominador testado dá inteiro. Esse inteiro fica sempre entre Σ(máximo por par distribuidor×PDV) e Σ(linhas).
8. **Categoria:** 0 SKUs sem categoria em todos os meses (0 kg).
9. **Hoje o pipeline aborta com estas bases, por dois motivos:** (a) as 13 bases de set/25–set/26 não trazem a coluna obrigatória `# PDVs Positivados`; (b) set/24 traz a SBM COMÉRCIO (01026770000176), que não está no de-para: 5.546 linhas, 14.833,2 kg. Além disso, o leitor atual **não lê** a coluna de frequência.
10. **Contra o publicado:** nos meses jul/25–ago/26, 6.345.324 linhas são idênticas em chave e métrica, e nenhuma linha antiga sumiu. As diferenças vêm **só de linhas novas**: DIERO de jul/25 a jun/26 (4.548 linhas, 15.213,2 kg) e PELLAH em jul/26 (1.793 linhas, 4.348,5 kg). **ago/26 não muda em kg, R$ ou positivados**, mas a base ativa de ago/26 iria de 124.600 para 124.800 (DN de 57,37% para 57,27%).

---

## 1. Inventário (MEDIDO)

| Arquivo | Competência (conteúdo) | Ano/Mês bruto | MB | Linhas na planilha (sem cabeçalho) | Linhas de dado | Colunas | Coluna de frequência (nome exato) | Obrigatórias ausentes (config) |
|---|---|---|---:|---:|---:|---:|---|---|
| ScoreCard_Mtrix_09.2024.xlsx | 2024-09 | 2024/SET | 38,8 | 425.283 | 425.282 | 19 | `# Frequência de compra` | — |
| ScoreCard_Mtrix_10.2024.xlsx | 2024-10 | 2024/OUT | 42,0 | 459.690 | 459.689 | 19 | `# Frequência de compra` | — |
| ScoreCard_Mtrix_11.2024.xlsx | 2024-11 | 2024/NOV | 39,7 | 435.312 | 435.311 | 19 | `# Frequência de compra` | — |
| ScoreCard_Mtrix_12.2024.xlsx | 2024-12 | 2024/DEZ | 32,1 | 352.386 | 352.385 | 19 | `# Frequência de compra` | — |
| ScoreCard_Mtrix_01.2025.xlsx | 2025-01 | 2025/JAN | 38,8 | 425.784 | 425.783 | 19 | `# Frequência de compra` | — |
| ScoreCard_Mtrix_02.2025.xlsx | 2025-02 | 2025/FEV | 38,1 | 416.663 | 416.662 | 19 | `# Frequência de compra` | — |
| ScoreCard_Mtrix_03.2025.xlsx | 2025-03 | 2025/MAR | 39,7 | 435.148 | 435.147 | 19 | `# Frequência de compra` | — |
| ScoreCard_Mtrix_04.2025.xlsx | 2025-04 | 2025/ABR | 38,1 | 415.845 | 415.844 | 19 | `# Frequência de compra` | — |
| ScoreCard_Mtrix_05.2025.xlsx | 2025-05 | 2025/MAI | 42,3 | 462.225 | 462.224 | 19 | `# Frequência de compra` | — |
| ScoreCard_Mtrix_06.2025.xlsx | 2025-06 | 2025/JUN | 39,5 | 431.232 | 431.231 | 19 | `# Frequência de compra` | — |
| ScoreCard_Mtrix_07.2025.xlsx | 2025-07 | 2025/JUL | 44,2 | 483.510 | 483.509 | 19 | `# Frequência de compra` | — |
| ScoreCard_Mtrix_08.2025.xlsx | 2025-08 | 2025/AGO | 42,6 | 465.976 | 465.975 | 19 | `# Frequência de compra` | — |
| ScoreCard_Mtrix_09.2025.xlsx | 2025-09 | 2025/SET | 39,9 | 455.603 | 455.602 | 18 | `# Frequência de compra` | `# PDVs Positivados` |
| ScoreCard_Mtrix_10.2025.xlsx | 2025-10 | 2025/OUT | 40,4 | 460.289 | 460.288 | 18 | `# Frequência de compra` | `# PDVs Positivados` |
| ScoreCard_Mtrix_11.2025.xlsx | 2025-11 | 2025/NOV | 37,9 | 433.387 | 433.386 | 18 | `# Frequência de compra` | `# PDVs Positivados` |
| ScoreCard_Mtrix_12.2025.xlsx | 2025-12 | 2025/DEZ | 33,4 | 382.116 | 382.115 | 18 | `# Frequência de compra` | `# PDVs Positivados` |
| ScoreCard_Mtrix_01.2026.xlsx | 2026-01 | 2026/JAN | 38,0 | 434.912 | 434.911 | 18 | `# Frequência de compra` | `# PDVs Positivados` |
| ScoreCard_Mtrix_02.2026.xlsx | 2026-02 | 2026/FEV | 35,7 | 406.989 | 406.988 | 18 | `# Frequência de compra` | `# PDVs Positivados` |
| ScoreCard_Mtrix_03.2026.xlsx | 2026-03 | 2026/MAR | 39,3 | 448.104 | 448.103 | 18 | `# Frequência de compra` | `# PDVs Positivados` |
| ScoreCard_Mtrix_04.2026.xlsx | 2026-04 | 2026/ABR | 37,6 | 428.912 | 428.911 | 18 | `# Frequência de compra` | `# PDVs Positivados` |
| ScoreCard_Mtrix_05.2026.xlsx | 2026-05 | 2026/MAI | 41,1 | 469.976 | 469.975 | 18 | `# Frequência de compra` | `# PDVs Positivados` |
| ScoreCard_Mtrix_06.2026.xlsx | 2026-06 | 2026/JUN | 40,5 | 462.911 | 462.910 | 18 | `# Frequência de compra` | `# PDVs Positivados` |
| ScoreCard_Mtrix_07.2026.xlsx | 2026-07 | 2026/JUL | 44,8 | 525.178 | 525.177 | 18 | `# Frequência de compra` | `# PDVs Positivados` |
| ScoreCard_Mtrix_08.2026.xlsx | 2026-08 | 2026/AGO | 42,2 | 493.816 | 493.815 | 18 | `# Frequência de compra` | `# PDVs Positivados` |
| ScoreCard_Mtrix_09.2026.xlsx | 2026-09 | 2026/SET | 7,8 | 91.432 | 91.431 | 18 | `# Frequência de compra` | `# PDVs Positivados` |

**Cabeçalhos distintos (ordem exata das colunas):**

- Layout 1 (12 arquivos: 09.2024, 10.2024, 11.2024, 12.2024, 01.2025, 02.2025, 03.2025, 04.2025, 05.2025, 06.2025, 07.2025, 08.2025): `CNPJ do AD.` · `Agente de Distribuição` · `CNPJ Reduzido` · `Cód. PDV` · `Razão Social PDV` · `UF PDV` · `Cidade PDV` · `Endereço PDV` · `Bairro PDV` · `CEP PDV` · `Segmento do PDV` · `SKU` · `Ano/Mês` · `# Sell-Out (R$)` · `# Sell-Out (Und)` · `# Sell-Out (Quilos)` · `# PDVs Positivados` · `# Total SKUs` · `# Frequência de compra`
- Layout 2 (13 arquivos: 09.2025, 10.2025, 11.2025, 12.2025, 01.2026, 02.2026, 03.2026, 04.2026, 05.2026, 06.2026, 07.2026, 08.2026, 09.2026): `Agente de Distribuição` · `CNPJ do AD.` · `CNPJ Reduzido` · `Cód. PDV` · `Razão Social PDV` · `UF PDV` · `Cidade PDV` · `Endereço PDV` · `Bairro PDV` · `CEP PDV` · `Segmento do PDV` · `SKU` · `Ano/Mês` · `# Sell-Out (R$)` · `# Sell-Out (Und)` · `# Sell-Out (Quilos)` · `# Total SKUs` · `# Frequência de compra`

**Sequência de meses (MEDIDO):** 2024-09 … 2026-09, 25 meses consecutivos; faltando: nenhum; repetidos: nenhum; competência ≠ nome do arquivo: nenhum.
Nenhum arquivo tem mais de uma competência. A aba é `Sheet1` nos 25. Todas as linhas têm a mesma largura que o cabeçalho.

## 2. Estrutura e grão (MEDIDO)

| Arquivo | Linhas de total (nº da linha) | Rodapé | Dimensão vazia no corpo | Dup. grão pipeline | Dup. sem distribuidor | Dup. 13 dimensões | Linha idêntica | Atributo muda dentro do par |
|---|---|---:|---|---:|---:|---:|---:|---|
| 09.2024 | 1 (2) | 0 | — | 0 | 393 | 0 | 0 | — |
| 10.2024 | 1 (2) | 0 | — | 0 | 554 | 0 | 0 | — |
| 11.2024 | 1 (2) | 0 | — | 0 | 242 | 0 | 0 | — |
| 12.2024 | 1 (2) | 0 | — | 0 | 178 | 0 | 0 | — |
| 01.2025 | 1 (2) | 0 | — | 0 | 565 | 0 | 0 | — |
| 02.2025 | 1 (2) | 0 | — | 0 | 159 | 0 | 0 | — |
| 03.2025 | 1 (2) | 0 | — | 0 | 194 | 0 | 0 | — |
| 04.2025 | 1 (2) | 0 | — | 0 | 445 | 0 | 0 | — |
| 05.2025 | 1 (2) | 0 | — | 0 | 223 | 0 | 0 | — |
| 06.2025 | 1 (2) | 0 | — | 0 | 5438 | 0 | 0 | — |
| 07.2025 | 1 (2) | 0 | — | 0 | 4816 | 0 | 0 | — |
| 08.2025 | 1 (2) | 0 | — | 0 | 2444 | 0 | 0 | — |
| 09.2025 | 1 (2) | 0 | — | 0 | 212 | 0 | 0 | — |
| 10.2025 | 1 (2) | 0 | — | 0 | 2319 | 0 | 0 | — |
| 11.2025 | 1 (2) | 0 | — | 0 | 2646 | 0 | 0 | — |
| 12.2025 | 1 (2) | 0 | — | 0 | 182 | 0 | 0 | — |
| 01.2026 | 1 (2) | 0 | — | 0 | 2138 | 0 | 0 | — |
| 02.2026 | 1 (2) | 0 | — | 0 | 264 | 0 | 0 | — |
| 03.2026 | 1 (2) | 0 | — | 0 | 240 | 0 | 0 | — |
| 04.2026 | 1 (2) | 0 | — | 0 | 2054 | 0 | 0 | — |
| 05.2026 | 1 (2) | 0 | — | 0 | 1179 | 0 | 0 | — |
| 06.2026 | 1 (2) | 0 | — | 0 | 8418 | 0 | 0 | — |
| 07.2026 | 1 (2) | 0 | — | 0 | 540 | 0 | 0 | — |
| 08.2026 | 1 (2) | 0 | — | 0 | 873 | 0 | 0 | — |
| 09.2026 | 1 (2) | 0 | — | 0 | 10 | 0 | 0 | — |

| Arquivo | R$ total | R$ Σ linhas − total | und total | und Σ − total | kg total | kg Σ − total | PDVs positivados (total) | Cód. PDV distintos | Cód. PDV kg>0 | CNPJ Reduzido distintos | Total SKUs (total) | SKUs distintos | **Frequência (total)** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 09.2024 | 36.250.370,52 | 4.47e-08 | 15.334.087,04 | 0.00e+00 | 1.151.762,980 | 2.51e-08 | 59.120 | 59.120 | 59.119 | 54.006 | 274 | 274 | 1.253112313937754 |
| 10.2024 | 38.283.668,04 | -7.45e-09 | 16.460.276,82 | -1.12e-08 | 1.219.938,150 | 3.40e-08 | 63.064 | 63.064 | 63.064 | 57.753 | 277 | 277 | 1.312539642268172 |
| 11.2024 | 38.312.475,58 | -7.45e-08 | 16.160.455,61 | 0.00e+00 | 1.236.193,203 | 3.10e-08 | 60.094 | 60.094 | 60.088 | 54.694 | 267 | 267 | 1.249642227177422 |
| 12.2024 | 30.821.428,04 | -6.33e-08 | 12.625.168,80 | 0.00e+00 | 982.043,480 | 1.33e-08 | 50.548 | 50.548 | 50.548 | 45.809 | 258 | 258 | 1.191125267072881 |
| 01.2025 | 33.702.572,52 | -1.04e-07 | 14.149.882,62 | 1.86e-09 | 1.051.842,417 | 2.10e-08 | 59.660 | 59.660 | 59.660 | 54.442 | 253 | 253 | 1.229601072745558 |
| 02.2025 | 34.392.054,76 | -6.71e-08 | 14.404.421,38 | 0.00e+00 | 1.063.416,167 | 2.00e-08 | 59.780 | 59.780 | 59.780 | 54.383 | 247 | 247 | 1.228270324523252 |
| 03.2025 | 35.813.328,94 | -7.45e-08 | 15.362.671,79 | 0.00e+00 | 1.109.148,714 | 2.51e-08 | 61.569 | 61.569 | 61.569 | 56.071 | 249 | 249 | 1.220549302408680 |
| 04.2025 | 34.051.356,43 | -2.98e-08 | 14.400.793,50 | 0.00e+00 | 1.078.779,118 | 2.10e-08 | 60.415 | 60.415 | 60.412 | 55.048 | 250 | 250 | 1.268426715219730 |
| 05.2025 | 40.888.855,70 | 1.49e-08 | 17.209.072,34 | -7.45e-09 | 1.276.409,401 | 3.40e-08 | 65.714 | 65.714 | 65.713 | 59.922 | 241 | 241 | 1.261435919286606 |
| 06.2025 | 34.782.164,34 | -7.45e-09 | 15.418.874,40 | -1.86e-08 | 1.119.543,097 | 7.71e-08 | 62.031 | 62.031 | 62.022 | 56.634 | 240 | 240 | 1.246006029243443 |
| 07.2025 | 39.652.852,24 | 7.45e-08 | 17.456.011,23 | -2.98e-08 | 1.259.134,949 | 9.01e-08 | 66.816 | 66.816 | 66.816 | 60.888 | 240 | 240 | 1.301394875478927 |
| 08.2025 | 39.035.583,63 | 5.22e-08 | 17.531.458,88 | -2.24e-08 | 1.234.265,686 | 8.29e-08 | 65.025 | 65.025 | 65.025 | 59.301 | 240 | 240 | 1.260484429065744 |
| 09.2025 | 38.520.169,36 | -7.45e-09 | 16.777.139,84 | -2.98e-08 | 1.203.356,117 | 8.50e-08 | — | 64.976 | 64.976 | 59.101 | 238 | 238 | 1.275809529672495 |
| 10.2025 | 39.110.294,35 | 6.71e-08 | 16.806.090,84 | -2.98e-08 | 1.209.288,385 | 8.43e-08 | — | 67.195 | 67.195 | 61.178 | 235 | 235 | 1.295736289902522 |
| 11.2025 | 37.791.375,40 | -2.24e-08 | 15.293.787,76 | -2.05e-08 | 1.141.791,590 | 7.59e-08 | — | 63.134 | 63.134 | 57.414 | 239 | 239 | 1.232806411759116 |
| 12.2025 | 35.252.439,79 | 0.00e+00 | 14.028.015,76 | -1.86e-08 | 1.054.079,062 | 6.01e-08 | — | 56.451 | 56.451 | 50.933 | 238 | 238 | 1.207666826096969 |
| 01.2026 | 36.234.374,42 | 1.49e-08 | 14.221.055,18 | -3.17e-08 | 1.038.655,466 | 6.89e-08 | — | 63.247 | 63.244 | 57.771 | 226 | 226 | 1.215014150868816 |
| 02.2026 | 34.912.225,86 | 5.96e-08 | 14.078.438,42 | -2.98e-08 | 1.005.330,376 | 6.30e-08 | — | 61.724 | 61.723 | 56.183 | 234 | 234 | 1.218261940250146 |
| 03.2026 | 38.267.784,02 | 2.24e-08 | 15.529.456,91 | -2.98e-08 | 1.114.997,699 | 7.59e-08 | — | 66.198 | 66.197 | 60.247 | 233 | 233 | 1.270869210550168 |
| 04.2026 | 38.044.539,54 | -5.96e-08 | 15.299.246,86 | -3.17e-08 | 1.098.579,337 | 6.89e-08 | — | 63.533 | 63.533 | 57.892 | 232 | 232 | 1.246013882549226 |
| 05.2026 | 42.197.251,94 | 5.22e-08 | 16.624.237,82 | -4.10e-08 | 1.209.840,399 | 8.50e-08 | — | 68.372 | 68.370 | 62.504 | 231 | 231 | 1.240902708711168 |
| 06.2026 | 40.543.816,87 | -7.45e-09 | 16.170.962,45 | -4.10e-08 | 1.183.909,853 | 7.99e-08 | — | 66.899 | 66.899 | 61.189 | 234 | 234 | 1.256700399109105 |
| 07.2026 | 44.062.836,65 | 2.91e-07 | 18.668.851,73 | -7.08e-08 | 1.300.935,455 | 1.01e-07 | — | 74.530 | 74.524 | 68.428 | 221 | 221 | 1.288514692070307 |
| 08.2026 | 40.891.387,76 | 1.79e-07 | 17.560.857,16 | 0.00e+00 | 1.212.878,548 | 9.22e-08 | — | 72.251 | 72.251 | 66.157 | 221 | 221 | 1.248923890326777 |
| 09.2026 | 6.834.195,73 | -1.86e-09 | 2.924.215,78 | 9.31e-10 | 204.540,229 | -1.02e-09 | — | 15.908 | 15.908 | 14.605 | 206 | 206 | 1.025521750062862 |

Leitura das tabelas (MEDIDO):
- O grão do pipeline (`mês × CNPJ do AD. × Cód. PDV × SKU`) tem 0 duplicados, tanto normalizado quanto em texto cru. Tirando o distribuidor (`mês × Cód. PDV × SKU`), aparecem duplicados (159 a 8.418 por mês fechado): é o mesmo PDV comprando o mesmo SKU de mais de um distribuidor (§4).
- `CNPJ Reduzido` **não** identifica PDV: dentro de `mês × CNPJ do AD. × CNPJ Reduzido × SKU` há duplicados (8.170 em set/26, por exemplo), e em set/26 504 CNPJs Reduzidos correspondem a mais de um Cód. PDV. Nenhum Cód. PDV tem dois CNPJs Reduzidos.
- Dentro de cada par distribuidor × PDV, CNPJ Reduzido, razão social, segmento, UF e cidade não mudam (0 casos em todos os arquivos).
- **O que a linha de total traz em cada métrica:** R$, und e kg = soma exata. `# PDVs Positivados` = Cód. PDV distintos contando **também os PDVs que só têm linhas com kg ≤ 0** (ex.: nov/24, total 60.094 = distintos 60.094, contra 60.088 com kg > 0). `# Total SKUs` = SKUs distintos. `# Frequência de compra` = ver §5.

## 3. O campo de frequência (MEDIDO)

| Arquivo | Tipo na planilha | Nulos | Mín | Máx | Média | p50 | p90 | p99 | Com decimal | =1 | 2 | 3 | 4 | 5 | 6–10 | 11–20 | 21–31 | >31 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 09.2024 | {'float': 425283} | 0 | 1 | 13 | 1,0653 | 1 | 1 | 2 | 0 | 401.402 | 20.692 | 2.728 | 304 | 114 | 39 | 3 | 0 | 0 |
| 10.2024 | {'float': 459690} | 0 | 1 | 13 | 1,0796 | 1 | 1 | 2 | 0 | 428.143 | 27.312 | 3.645 | 444 | 105 | 38 | 2 | 0 | 0 |
| 11.2024 | {'float': 435312} | 0 | 1 | 8 | 1,0662 | 1 | 1 | 2 | 0 | 409.828 | 22.638 | 2.502 | 249 | 66 | 28 | 0 | 0 | 0 |
| 12.2024 | {'float': 352386} | 0 | 1 | 9 | 1,0500 | 1 | 1 | 2 | 0 | 337.025 | 13.416 | 1.716 | 155 | 59 | 14 | 0 | 0 | 0 |
| 01.2025 | {'float': 425784} | 0 | 1 | 9 | 1,0590 | 1 | 1 | 2 | 0 | 403.860 | 19.092 | 2.555 | 229 | 24 | 23 | 0 | 0 | 0 |
| 02.2025 | {'float': 416663} | 0 | 1 | 9 | 1,0586 | 1 | 1 | 2 | 0 | 395.410 | 18.447 | 2.512 | 242 | 36 | 15 | 0 | 0 | 0 |
| 03.2025 | {'float': 435148} | 0 | 1 | 16 | 1,0603 | 1 | 1 | 2 | 0 | 412.372 | 19.911 | 2.506 | 257 | 54 | 38 | 9 | 0 | 0 |
| 04.2025 | {'float': 415845} | 0 | 1 | 15 | 1,0737 | 1 | 1 | 2 | 0 | 389.672 | 22.413 | 3.317 | 331 | 57 | 45 | 9 | 0 | 0 |
| 05.2025 | {'float': 462225} | 0 | 1 | 16 | 1,0701 | 1 | 1 | 2 | 0 | 434.258 | 24.481 | 2.919 | 408 | 91 | 57 | 10 | 0 | 0 |
| 06.2025 | {'float': 431232} | 0 | 1 | 16 | 1,0647 | 1 | 1 | 2 | 0 | 407.401 | 20.663 | 2.688 | 306 | 87 | 75 | 11 | 0 | 0 |
| 07.2025 | {'float': 483510} | 0 | 1 | 17 | 1,0786 | 1 | 1 | 2 | 0 | 451.005 | 28.163 | 3.690 | 447 | 121 | 64 | 19 | 0 | 0 |
| 08.2025 | {'float': 465976} | 0 | 1 | 16 | 1,0715 | 1 | 1 | 2 | 0 | 437.429 | 24.706 | 3.277 | 392 | 102 | 61 | 8 | 0 | 0 |
| 09.2025 | {'float': 455603} | 0 | 1 | 16 | 1,0754 | 1 | 1 | 2 | 0 | 426.746 | 24.528 | 3.673 | 473 | 91 | 61 | 30 | 0 | 0 |
| 10.2025 | {'float': 460289} | 0 | 1 | 18 | 1,0776 | 1 | 1 | 2 | 0 | 429.814 | 26.284 | 3.648 | 390 | 76 | 52 | 24 | 0 | 0 |
| 11.2025 | {'float': 433387} | 0 | 1 | 17 | 1,0586 | 1 | 1 | 2 | 0 | 411.227 | 19.631 | 2.155 | 268 | 46 | 41 | 18 | 0 | 0 |
| 12.2025 | {'float': 382116} | 0 | 1 | 10 | 1,0612 | 1 | 1 | 2 | 0 | 362.134 | 17.121 | 2.470 | 295 | 65 | 30 | 0 | 0 | 0 |
| 01.2026 | {'float': 434912} | 0 | 1 | 14 | 1,0559 | 1 | 1 | 2 | 0 | 413.904 | 18.224 | 2.418 | 296 | 41 | 24 | 4 | 0 | 0 |
| 02.2026 | {'float': 406989} | 0 | 1 | 13 | 1,0570 | 1 | 1 | 2 | 0 | 386.738 | 17.761 | 2.228 | 165 | 63 | 28 | 5 | 0 | 0 |
| 03.2026 | {'float': 448104} | 0 | 1 | 14 | 1,0720 | 1 | 1 | 2 | 0 | 420.266 | 24.141 | 3.253 | 313 | 73 | 46 | 11 | 0 | 0 |
| 04.2026 | {'float': 428912} | 0 | 1 | 17 | 1,0612 | 1 | 1 | 2 | 0 | 406.122 | 19.989 | 2.413 | 277 | 70 | 32 | 8 | 0 | 0 |
| 05.2026 | {'float': 469976} | 0 | 1 | 15 | 1,0646 | 1 | 1 | 2 | 0 | 443.876 | 22.624 | 2.984 | 376 | 55 | 53 | 7 | 0 | 0 |
| 06.2026 | {'float': 462911} | 0 | 1 | 14 | 1,0673 | 1 | 1 | 2 | 0 | 436.174 | 23.054 | 3.232 | 318 | 84 | 41 | 7 | 0 | 0 |
| 07.2026 | {'float': 525178} | 0 | 1 | 20 | 1,0817 | 1 | 1 | 3 | 0 | 489.013 | 30.829 | 4.482 | 603 | 170 | 58 | 22 | 0 | 0 |
| 08.2026 | {'float': 493816} | 0 | 1 | 15 | 1,0651 | 1 | 1 | 2 | 0 | 466.040 | 24.243 | 3.032 | 328 | 111 | 50 | 11 | 0 | 0 |
| 09.2026 | {'float': 91432} | 0 | 1 | 5 | 1,0092 | 1 | 1 | 1 | 0 | 90.708 | 624 | 87 | 8 | 4 | 0 | 0 | 0 | 0 |

| Arquivo | linhas kg=0 | kg<0 | und≤0 | R$=0 | R$<0 | kg≤0 e R$>0 | kg>0 e R$≤0 | kg,und,R$ ≤0 | freq nas linhas kg≤0 (mín–máx; valores) | freq nas linhas R$≤0 | Spearman freq×kg (kg>0) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---:|
| 09.2024 | 26 | 5 | 31 | 56 | 9 | 3 | 37 | 28 | 2–2; {'2.0': 31} | 1–3; {'1.0': 33, '2.0': 31, '3.0': 1} | 0,188 |
| 10.2024 | 33 | 1 | 34 | 108 | 4 | 1 | 79 | 33 | 2–2; {'2.0': 34} | 1–2; {'1.0': 76, '2.0': 36} | 0,205 |
| 11.2024 | 53 | 0 | 53 | 96 | 4 | 2 | 49 | 51 | 2–2; {'2.0': 53} | 1–2; {'2.0': 55, '1.0': 45} | 0,187 |
| 12.2024 | 0 | 0 | 0 | 40 | 1 | 0 | 41 | 0 | — | 1–2; {'1.0': 23, '2.0': 18} | 0,149 |
| 01.2025 | 0 | 0 | 0 | 36 | 3 | 0 | 39 | 0 | — | 1–2; {'1.0': 35, '2.0': 4} | 0,182 |
| 02.2025 | 0 | 0 | 0 | 41 | 3 | 0 | 44 | 0 | — | 1–4; {'1.0': 36, '2.0': 7, '4.0': 1} | 0,180 |
| 03.2025 | 0 | 0 | 0 | 53 | 4 | 0 | 57 | 0 | — | 1–4; {'1.0': 45, '2.0': 11, '4.0': 1} | 0,181 |
| 04.2025 | 15 | 0 | 15 | 54 | 7 | 0 | 46 | 15 | 2–2; {'2.0': 15} | 1–4; {'1.0': 39, '2.0': 21, '4.0': 1} | 0,202 |
| 05.2025 | 14 | 6 | 20 | 44 | 9 | 0 | 33 | 20 | 2–2; {'2.0': 20} | 1–3; {'1.0': 28, '2.0': 23, '3.0': 2} | 0,200 |
| 06.2025 | 32 | 6 | 38 | 79 | 13 | 0 | 54 | 38 | 2–2; {'2.0': 38} | 1–3; {'1.0': 41, '2.0': 49, '3.0': 2} | 0,185 |
| 07.2025 | 7 | 0 | 7 | 40 | 3 | 0 | 36 | 7 | 2–2; {'2.0': 7} | 1–2; {'1.0': 31, '2.0': 12} | 0,203 |
| 08.2025 | 1 | 0 | 1 | 78 | 6 | 0 | 83 | 1 | 2–2; {'2.0': 1} | 1–3; {'1.0': 60, '2.0': 16, '3.0': 8} | 0,199 |
| 09.2025 | 0 | 0 | 0 | 38 | 9 | 0 | 47 | 0 | — | 1–2; {'1.0': 37, '2.0': 10} | 0,198 |
| 10.2025 | 5 | 0 | 5 | 45 | 5 | 0 | 45 | 5 | 2–2; {'2.0': 5} | 1–2; {'1.0': 42, '2.0': 8} | 0,203 |
| 11.2025 | 0 | 3 | 3 | 48 | 5 | 1 | 51 | 2 | 1–2; {'2.0': 2, '1.0': 1} | 1–2; {'1.0': 26, '2.0': 27} | 0,180 |
| 12.2025 | 0 | 0 | 0 | 94 | 3 | 0 | 97 | 0 | — | 1–2; {'1.0': 53, '2.0': 44} | 0,166 |
| 01.2026 | 22 | 0 | 22 | 62 | 1 | 0 | 41 | 22 | 2–2; {'2.0': 22} | 1–4; {'1.0': 40, '2.0': 22, '4.0': 1} | 0,179 |
| 02.2026 | 33 | 3 | 36 | 62 | 8 | 0 | 34 | 36 | 2–2; {'2.0': 36} | 1–2; {'2.0': 44, '1.0': 26} | 0,175 |
| 03.2026 | 2 | 1 | 3 | 39 | 4 | 0 | 40 | 3 | 2–2; {'2.0': 3} | 1–2; {'1.0': 35, '2.0': 8} | 0,189 |
| 04.2026 | 1 | 0 | 1 | 45 | 3 | 0 | 47 | 1 | 2–2; {'2.0': 1} | 1–3; {'1.0': 43, '2.0': 4, '3.0': 1} | 0,186 |
| 05.2026 | 4 | 0 | 4 | 54 | 2 | 0 | 52 | 4 | 2–2; {'2.0': 4} | 1–2; {'1.0': 46, '2.0': 10} | 0,190 |
| 06.2026 | 0 | 0 | 0 | 32 | 3 | 0 | 35 | 0 | — | 1–2; {'1.0': 31, '2.0': 4} | 0,190 |
| 07.2026 | 26 | 0 | 26 | 586 | 6 | 2 | 568 | 24 | 2–4; {'2.0': 19, '4.0': 5, '3.0': 2} | 1–6; {'1.0': 507, '2.0': 76, '4.0': 6, '3.0': 2, '6.0': 1} | 0,211 |
| 08.2026 | 0 | 0 | 0 | 272 | 5 | 0 | 277 | 0 | — | 1–2; {'1.0': 228, '2.0': 49} | 0,186 |
| 09.2026 | 0 | 0 | 0 | 1 | 2 | 0 | 3 | 0 | — | 1–2; {'1.0': 1, '2.0': 2} | 0,055 |

- Tipo: célula numérica (float) em 100% das linhas dos 25 arquivos, **sem casas decimais em nenhuma linha**, nenhum texto e nenhum nulo.
- Linhas com kg ≤ 0 (299 no total dos 25 arquivos): a frequência nunca é 0. Em quase todas vale 2. As exceções são uma linha com 1 (nov/25) e valores 3 e 4 em jul/26.
- Linhas com R$ ≤ 0: frequência de 1 a 6.
- Correlação de postos (Spearman) entre frequência e kg da linha, nas linhas com kg > 0: 0,15 a 0,21 nos meses fechados (0,055 em set/26).
- set/26 (parcial) difere dos meses fechados: nenhuma linha com kg ≤ 0, máximo 5, média 1,009.

## 4. Relações dentro do PDV (MEDIDO)

| Arquivo | PDVs | PDVs c/ >1 linha | **PDVs em que varia** | % | kg nesses PDVs (% do mês) | Pares dist×PDV | Pares c/ >1 linha | **Pares em que varia** | % | Amplitude máx | Varia por tipo de chave (pares) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 09.2024 | 59.120 | 47.589 | 6.594 | 13,86 | 395.041 (34,3%) | 59.632 | 47.831 | 6.589 | 13,78 | 12 | {'CNPJ': 6151, 'LGPD': 328, 'OUTRO': 110} |
| 10.2024 | 63.064 | 51.051 | 8.449 | 16,55 | 435.598 (35,7%) | 63.654 | 51.320 | 8.440 | 16,45 | 12 | {'CNPJ': 7917, 'LGPD': 378, 'OUTRO': 145} |
| 11.2024 | 60.094 | 48.400 | 6.915 | 14,29 | 402.074 (32,5%) | 60.498 | 48.593 | 6.908 | 14,22 | 7 | {'CNPJ': 6459, 'LGPD': 334, 'OUTRO': 115} |
| 12.2024 | 50.548 | 40.304 | 4.061 | 10,08 | 242.259 (24,7%) | 50.815 | 40.419 | 4.061 | 10,05 | 8 | {'CNPJ': 3560, 'LGPD': 384, 'OUTRO': 117} |
| 01.2025 | 59.660 | 48.019 | 6.032 | 12,56 | 298.111 (28,3%) | 60.136 | 48.222 | 6.023 | 12,49 | 8 | {'CNPJ': 5575, 'LGPD': 443, 'OUTRO': 5} |
| 02.2025 | 59.780 | 47.751 | 5.892 | 12,34 | 316.810 (29,8%) | 60.103 | 47.886 | 5.888 | 12,30 | 8 | {'CNPJ': 5525, 'LGPD': 358, 'OUTRO': 5} |
| 03.2025 | 61.569 | 49.347 | 5.974 | 12,11 | 328.061 (29,6%) | 61.909 | 49.489 | 5.971 | 12,07 | 15 | {'CNPJ': 5578, 'LGPD': 387, 'OUTRO': 6} |
| 04.2025 | 60.415 | 48.373 | 7.118 | 14,71 | 365.707 (33,9%) | 60.808 | 48.519 | 7.115 | 14,66 | 14 | {'CNPJ': 6647, 'LGPD': 462, 'OUTRO': 6} |
| 05.2025 | 65.714 | 52.469 | 7.595 | 14,48 | 444.910 (34,9%) | 66.093 | 52.615 | 7.592 | 14,43 | 15 | {'CNPJ': 7119, 'LGPD': 467, 'OUTRO': 6} |
| 06.2025 | 62.031 | 50.004 | 6.709 | 13,42 | 347.563 (31,0%) | 63.276 | 50.630 | 6.796 | 13,42 | 15 | {'CNPJ': 6317, 'LGPD': 472, 'OUTRO': 7} |
| 07.2025 | 66.816 | 54.219 | 8.983 | 16,57 | 442.612 (35,2%) | 68.228 | 54.859 | 8.995 | 16,40 | 16 | {'CNPJ': 8475, 'LGPD': 514, 'OUTRO': 6} |
| 08.2025 | 65.025 | 52.859 | 7.697 | 14,56 | 402.540 (32,6%) | 65.974 | 53.275 | 7.688 | 14,43 | 15 | {'CNPJ': 7231, 'LGPD': 450, 'OUTRO': 7} |
| 09.2025 | 64.976 | 51.875 | 7.668 | 14,78 | 394.976 (32,8%) | 65.500 | 52.047 | 7.658 | 14,71 | 15 | {'CNPJ': 7210, 'LGPD': 441, 'OUTRO': 7} |
| 10.2025 | 67.195 | 53.549 | 8.501 | 15,88 | 434.440 (35,9%) | 68.088 | 53.906 | 8.494 | 15,76 | 17 | {'CNPJ': 8002, 'LGPD': 485, 'OUTRO': 7} |
| 11.2025 | 63.134 | 49.635 | 6.399 | 12,89 | 328.948 (28,8%) | 63.940 | 50.000 | 6.389 | 12,78 | 16 | {'CNPJ': 6020, 'LGPD': 364, 'OUTRO': 5} |
| 12.2025 | 56.451 | 44.367 | 4.852 | 10,94 | 266.335 (25,3%) | 56.824 | 44.463 | 4.845 | 10,90 | 9 | {'CNPJ': 4427, 'LGPD': 413, 'OUTRO': 5} |
| 01.2026 | 63.247 | 50.595 | 5.778 | 11,42 | 293.477 (28,3%) | 63.938 | 50.933 | 5.771 | 11,33 | 13 | {'CNPJ': 5377, 'LGPD': 389, 'OUTRO': 5} |
| 02.2026 | 61.724 | 49.110 | 5.925 | 12,06 | 283.376 (28,2%) | 62.143 | 49.248 | 5.926 | 12,03 | 12 | {'CNPJ': 5549, 'LGPD': 372, 'OUTRO': 5} |
| 03.2026 | 66.198 | 52.387 | 7.457 | 14,23 | 349.252 (31,3%) | 66.743 | 52.568 | 7.450 | 14,17 | 13 | {'CNPJ': 7015, 'LGPD': 429, 'OUTRO': 6} |
| 04.2026 | 63.533 | 50.530 | 6.731 | 13,32 | 340.676 (31,0%) | 64.373 | 50.875 | 6.724 | 13,22 | 16 | {'CNPJ': 6334, 'LGPD': 384, 'OUTRO': 6} |
| 05.2026 | 68.372 | 53.847 | 7.062 | 13,11 | 409.592 (33,9%) | 68.994 | 54.088 | 7.047 | 13,03 | 14 | {'CNPJ': 6622, 'LGPD': 420, 'OUTRO': 5} |
| 06.2026 | 66.899 | 53.550 | 7.350 | 13,73 | 383.092 (32,4%) | 68.532 | 54.503 | 7.386 | 13,55 | 13 | {'CNPJ': 6949, 'LGPD': 432, 'OUTRO': 5} |
| 07.2026 | 74.530 | 59.535 | 9.420 | 15,82 | 474.620 (36,5%) | 75.121 | 59.766 | 9.411 | 15,75 | 19 | {'CNPJ': 8889, 'LGPD': 517, 'OUTRO': 5} |
| 08.2026 | 72.251 | 56.531 | 7.457 | 13,19 | 371.342 (30,6%) | 73.060 | 56.887 | 7.453 | 13,10 | 14 | {'CNPJ': 7019, 'LGPD': 431, 'OUTRO': 3} |
| 09.2026 | 15.908 | 12.071 | 160 | 1,33 | 11.325 (5,5%) | 15.934 | 12.074 | 160 | 1,33 | 4 | {'CNPJ': 141, 'LGPD': 17, 'OUTRO': 2} |

| Arquivo | PDVs em >1 distribuidor | por nº de dist. | kg desses PDVs | por tipo de chave | multi com freq constante em todos os pares | desses, freq igual entre distribuidores |
|---|---:|---|---:|---|---:|---:|
| 09.2024 | 511 | {'1': 58609, '2': 510, '3': 1} | 12.732 | {'CNPJ': 497, 'LGPD': 12, 'OUTRO': 2} | 445 | 436 |
| 10.2024 | 581 | {'1': 62483, '2': 572, '3': 9} | 15.409 | {'CNPJ': 561, 'LGPD': 18, 'OUTRO': 2} | 487 | 474 |
| 11.2024 | 404 | {'1': 59690, '2': 404} | 13.348 | {'CNPJ': 396, 'LGPD': 7, 'OUTRO': 1} | 351 | 343 |
| 12.2024 | 266 | {'1': 50282, '2': 265, '3': 1} | 6.932 | {'CNPJ': 263, 'OUTRO': 2, 'LGPD': 1} | 253 | 252 |
| 01.2025 | 473 | {'1': 59187, '2': 470, '3': 3} | 11.582 | {'CNPJ': 468, 'LGPD': 3, 'OUTRO': 2} | 422 | 412 |
| 02.2025 | 321 | {'1': 59459, '2': 319, '3': 2} | 8.619 | {'CNPJ': 320, 'OUTRO': 1} | 280 | 271 |
| 03.2025 | 340 | {'1': 61229, '2': 340} | 7.966 | {'CNPJ': 338, 'OUTRO': 2} | 302 | 297 |
| 04.2025 | 386 | {'1': 60029, '2': 379, '3': 7} | 8.945 | {'CNPJ': 382, 'LGPD': 2, 'OUTRO': 2} | 340 | 336 |
| 05.2025 | 379 | {'1': 65335, '2': 379} | 10.725 | {'CNPJ': 374, 'LGPD': 3, 'OUTRO': 2} | 317 | 312 |
| 06.2025 | 1.239 | {'1': 60792, '2': 1233, '3': 6} | 49.531 | {'CNPJ': 1064, 'LGPD': 173, 'OUTRO': 2} | 1097 | 1084 |
| 07.2025 | 1.409 | {'1': 65407, '2': 1406, '3': 3} | 49.024 | {'CNPJ': 1268, 'LGPD': 139, 'OUTRO': 2} | 1140 | 1106 |
| 08.2025 | 948 | {'1': 64077, '2': 947, '3': 1} | 20.193 | {'CNPJ': 803, 'LGPD': 143, 'OUTRO': 2} | 851 | 837 |
| 09.2025 | 521 | {'1': 64455, '2': 518, '3': 3} | 10.977 | {'CNPJ': 518, 'OUTRO': 2, 'LGPD': 1} | 432 | 417 |
| 10.2025 | 877 | {'1': 66318, '2': 861, '3': 16} | 19.190 | {'CNPJ': 863, 'LGPD': 12, 'OUTRO': 2} | 768 | 754 |
| 11.2025 | 800 | {'1': 62334, '2': 794, '3': 6} | 23.189 | {'CNPJ': 773, 'LGPD': 25, 'OUTRO': 2} | 689 | 674 |
| 12.2025 | 371 | {'1': 56080, '2': 369, '3': 2} | 7.900 | {'CNPJ': 367, 'OUTRO': 2, 'LGPD': 2} | 341 | 333 |
| 01.2026 | 678 | {'1': 62569, '2': 665, '3': 13} | 19.555 | {'CNPJ': 671, 'LGPD': 5, 'OUTRO': 2} | 586 | 576 |
| 02.2026 | 412 | {'1': 61312, '2': 405, '3': 7} | 8.326 | {'CNPJ': 406, 'LGPD': 3, 'OUTRO': 3} | 341 | 337 |
| 03.2026 | 537 | {'1': 65661, '2': 529, '3': 8} | 12.935 | {'CNPJ': 530, 'LGPD': 5, 'OUTRO': 2} | 436 | 422 |
| 04.2026 | 828 | {'1': 62705, '2': 816, '3': 12} | 20.534 | {'CNPJ': 790, 'LGPD': 35, 'OUTRO': 3} | 714 | 695 |
| 05.2026 | 620 | {'1': 67752, '2': 618, '3': 2} | 16.557 | {'CNPJ': 575, 'LGPD': 43, 'OUTRO': 2} | 533 | 514 |
| 06.2026 | 1.603 | {'1': 65296, '2': 1573, '3': 30} | 50.589 | {'CNPJ': 1578, 'OUTRO': 23, 'LGPD': 2} | 1473 | 1457 |
| 07.2026 | 582 | {'1': 73948, '2': 573, '3': 9} | 17.448 | {'CNPJ': 578, 'LGPD': 2, 'OUTRO': 2} | 468 | 456 |
| 08.2026 | 804 | {'1': 71447, '2': 799, '3': 5} | 23.527 | {'CNPJ': 683, 'LGPD': 119, 'OUTRO': 2} | 710 | 700 |
| 09.2026 | 26 | {'1': 15882, '2': 26} | 599 | {'CNPJ': 25, 'OUTRO': 1} | 24 | 24 |

- **A frequência não é uma propriedade constante do PDV no arquivo:** nos meses fechados, ela muda entre SKUs em 10,1% a 16,6% dos PDVs com mais de uma linha. Olhando o par distribuidor × PDV, o resultado é praticamente o mesmo (10,0% a 16,4%). A amplitude (máximo − mínimo) chega a 19.
- **O mesmo PDV compra de mais de um distribuidor:** 266 a 1.603 PDVs por mês (0,5% a 2,4%), quase todos com 2 distribuidores e até 30 com 3 (jun/26).
- Entre os PDVs com mais de um distribuidor que têm a frequência constante dentro de cada par, a frequência é **diferente entre os distribuidores** em 1 a 34 PDVs por mês fechado.

## 5. Linha de total × linhas (MEDIDO)

**Teste 1 · agregações.** Testei 99 combinações de regra × população: linhas todas, linhas com kg > 0 e linhas com frequência > 0. As regras:
média simples; médias ponderadas por kg, R$ e und; soma ÷ PDVs, ÷ pares, ÷ linhas, ÷ PDVs positivados do total e ÷ Σ`# PDVs Positivados`;
max, min, média, mediana, soma e primeiro valor por par (tirando a média dos pares ou dividindo a soma pelos PDVs); max/min/média/soma por PDV;
max por CNPJ Reduzido; médias por SKU; médias por distribuidor. **Nenhuma bate em nenhum mês.** Resumo nos 24 meses fechados
(tabela completa, mês a mês, no Anexo A):

| # | Regra testada | População | meses testados | dif. mín (%) | dif. máx (%) | menor \|dif\| (%) | set/26 parcial (%) | Bate? |
|---:|---|---|---:|---:|---:|---:|---:|---|
| 1 | média ponderada por KG (pesos<0 = 0) | linhas kg>0 | 24 | -7.18 | -2.98 | 2.98 | +0.54 | não |
| 2 | média ponderada por KG (pesos<0 = 0) | todas as linhas | 24 | -7.18 | -2.98 | 2.98 | +0.54 | não |
| 3 | média ponderada por KG (pesos<0 = 0) | linhas FREQ>0 | 24 | -7.18 | -2.98 | 2.98 | +0.54 | não |
| 4 | média ponderada por RS (pesos<0 = 0) | todas as linhas | 24 | -7.65 | -3.54 | 3.54 | +0.11 | não |
| 5 | média ponderada por RS (pesos<0 = 0) | linhas kg>0 | 24 | -7.65 | -3.54 | 3.54 | +0.11 | não |
| 6 | média ponderada por RS (pesos<0 = 0) | linhas FREQ>0 | 24 | -7.65 | -3.54 | 3.54 | +0.11 | não |
| 7 | média ponderada por UND (pesos<0 = 0) | todas as linhas | 24 | -7.39 | -3.72 | 3.72 | -0.18 | não |
| 8 | média ponderada por UND (pesos<0 = 0) | linhas kg>0 | 24 | -7.39 | -3.72 | 3.72 | -0.18 | não |
| 9 | média ponderada por UND (pesos<0 = 0) | linhas FREQ>0 | 24 | -7.39 | -3.72 | 3.72 | -0.18 | não |
| 10 | max por par distribuidor×PDV → soma ÷ PDVs distintos | todas as linhas | 24 | -9.65 | -6.54 | 6.54 | -1.00 | não |
| 11 | max por par → soma por PDV → média dos PDVs | todas as linhas | 24 | -9.65 | -6.54 | 6.54 | -1.00 | não |
| 12 | max por par distribuidor×PDV → soma ÷ PDVs distintos | linhas FREQ>0 | 24 | -9.65 | -6.54 | 6.54 | -1.00 | não |
| 13 | max por par → soma por PDV → média dos PDVs | linhas FREQ>0 | 24 | -9.65 | -6.54 | 6.54 | -1.00 | não |
| 14 | max por par distribuidor×PDV → soma ÷ PDVs distintos | linhas kg>0 | 24 | -9.66 | -6.55 | 6.55 | -1.00 | não |
| 15 | max por par → soma por PDV → média dos PDVs | linhas kg>0 | 24 | -9.66 | -6.55 | 6.55 | -1.00 | não |
| 16 | max por PDV (Cód. PDV) → média dos PDVs | todas as linhas | 24 | -10.37 | -7.01 | 7.01 | -1.16 | não |
| 17 | max por PDV (Cód. PDV) → média dos PDVs | linhas kg>0 | 24 | -10.38 | -7.01 | 7.01 | -1.16 | não |
| 18 | max por PDV (Cód. PDV) → média dos PDVs | linhas FREQ>0 | 24 | -10.37 | -7.01 | 7.01 | -1.16 | não |
| 19 | max por par distribuidor×PDV → média dos pares | todas as linhas | 24 | -10.49 | -7.05 | 7.05 | -1.16 | não |
| 20 | max por par distribuidor×PDV → média dos pares | linhas kg>0 | 24 | -10.50 | -7.05 | 7.05 | -1.16 | não |
| 21 | max por par distribuidor×PDV → média dos pares | linhas FREQ>0 | 24 | -10.49 | -7.05 | 7.05 | -1.16 | não |
| 22 | max por CNPJ Reduzido → média | todas as linhas | 24 | -11.29 | -7.42 | 7.42 | -1.17 | não |
| 23 | max por CNPJ Reduzido → média | linhas kg>0 | 24 | -11.30 | -7.42 | 7.42 | -1.17 | não |
| 24 | max por CNPJ Reduzido → média | linhas FREQ>0 | 24 | -11.29 | -7.42 | 7.42 | -1.17 | não |
| 25 | (max por par → média) por distribuidor → média dos distribuidores | todas as linhas | 24 | -10.91 | -7.44 | 7.44 | -1.18 | não |
| 26 | (max por par → média) por distribuidor → média dos distribuidores | linhas kg>0 | 24 | -10.92 | -7.44 | 7.44 | -1.18 | não |
| 27 | (max por par → média) por distribuidor → média dos distribuidores | linhas FREQ>0 | 24 | -10.91 | -7.44 | 7.44 | -1.18 | não |
| 28 | média simples das linhas | todas as linhas | 24 | -17.75 | -11.84 | 11.84 | -1.59 | não |
| 29 | soma das linhas ÷ linhas | todas as linhas | 24 | -17.75 | -11.84 | 11.84 | -1.59 | não |
| 30 | soma das linhas ÷ soma de '# PDVs Positivados' das linhas | todas as linhas | 12 | -17.75 | -11.84 | 11.84 | — | não |
| 31 | média simples das linhas | linhas kg>0 | 24 | -17.75 | -11.84 | 11.84 | -1.59 | não |
| 32 | soma das linhas ÷ linhas | linhas kg>0 | 24 | -17.75 | -11.84 | 11.84 | -1.59 | não |
| 33 | soma das linhas ÷ soma de '# PDVs Positivados' das linhas | linhas kg>0 | 12 | -17.75 | -11.84 | 11.84 | — | não |
| 34 | média simples das linhas | linhas FREQ>0 | 24 | -17.75 | -11.84 | 11.84 | -1.59 | não |
| 35 | soma das linhas ÷ linhas | linhas FREQ>0 | 24 | -17.75 | -11.84 | 11.84 | -1.59 | não |
| 36 | soma das linhas ÷ soma de '# PDVs Positivados' das linhas | linhas FREQ>0 | 12 | -17.75 | -11.84 | 11.84 | — | não |
| 37 | soma ÷ PDVs distintos por SKU → média dos SKUs | todas as linhas | 24 | -19.32 | -12.20 | 12.20 | -1.43 | não |
| 38 | soma ÷ PDVs distintos por SKU → média dos SKUs | linhas kg>0 | 24 | -19.32 | -12.20 | 12.20 | -1.43 | não |
| 39 | soma ÷ PDVs distintos por SKU → média dos SKUs | linhas FREQ>0 | 24 | -19.32 | -12.20 | 12.20 | -1.43 | não |
| 40 | média por SKU → média dos SKUs | todas as linhas | 24 | -19.38 | -12.21 | 12.21 | -1.43 | não |
| 41 | média por SKU → média dos SKUs | linhas kg>0 | 24 | -19.38 | -12.21 | 12.21 | -1.43 | não |
| 42 | média por SKU → média dos SKUs | linhas FREQ>0 | 24 | -19.38 | -12.21 | 12.21 | -1.43 | não |
| 43 | mean por par distribuidor×PDV → soma ÷ PDVs distintos | todas as linhas | 24 | -18.51 | -12.27 | 12.27 | -1.72 | não |
| 44 | mean por par distribuidor×PDV → soma ÷ PDVs distintos | linhas kg>0 | 24 | -18.51 | -12.27 | 12.27 | -1.72 | não |
| 45 | mean por par distribuidor×PDV → soma ÷ PDVs distintos | linhas FREQ>0 | 24 | -18.51 | -12.27 | 12.27 | -1.72 | não |
| 46 | mean por PDV (Cód. PDV) → média dos PDVs | todas as linhas | 24 | -19.25 | -12.72 | 12.72 | -1.88 | não |
| 47 | mean por PDV (Cód. PDV) → média dos PDVs | linhas kg>0 | 24 | -19.25 | -12.72 | 12.72 | -1.88 | não |
| 48 | mean por PDV (Cód. PDV) → média dos PDVs | linhas FREQ>0 | 24 | -19.25 | -12.72 | 12.72 | -1.88 | não |
| 49 | mean por par distribuidor×PDV → média dos pares | todas as linhas | 24 | -19.27 | -12.73 | 12.73 | -1.88 | não |
| 50 | mean por par distribuidor×PDV → média dos pares | linhas kg>0 | 24 | -19.27 | -12.73 | 12.73 | -1.88 | não |
| 51 | mean por par distribuidor×PDV → média dos pares | linhas FREQ>0 | 24 | -19.27 | -12.73 | 12.73 | -1.88 | não |
| 52 | median por par distribuidor×PDV → soma ÷ PDVs distintos | todas as linhas | 24 | -20.16 | -13.31 | 13.31 | -1.83 | não |
| 53 | median por par distribuidor×PDV → soma ÷ PDVs distintos | linhas kg>0 | 24 | -20.17 | -13.31 | 13.31 | -1.83 | não |
| 54 | median por par distribuidor×PDV → soma ÷ PDVs distintos | linhas FREQ>0 | 24 | -20.16 | -13.31 | 13.31 | -1.83 | não |
| 55 | median por par distribuidor×PDV → média dos pares | todas as linhas | 24 | -20.90 | -13.77 | 13.77 | -1.99 | não |
| 56 | median por par distribuidor×PDV → média dos pares | linhas kg>0 | 24 | -20.90 | -13.77 | 13.77 | -1.99 | não |
| 57 | median por par distribuidor×PDV → média dos pares | linhas FREQ>0 | 24 | -20.90 | -13.77 | 13.77 | -1.99 | não |
| 58 | min por par distribuidor×PDV → soma ÷ PDVs distintos | todas as linhas | 24 | -21.85 | -14.48 | 14.48 | -2.07 | não |
| 59 | first por par distribuidor×PDV → soma ÷ PDVs distintos | todas as linhas | 24 | -21.85 | -14.48 | 14.48 | -2.07 | não |
| 60 | min por par distribuidor×PDV → soma ÷ PDVs distintos | linhas kg>0 | 24 | -21.85 | -14.48 | 14.48 | -2.07 | não |
| 61 | first por par distribuidor×PDV → soma ÷ PDVs distintos | linhas kg>0 | 24 | -21.85 | -14.48 | 14.48 | -2.07 | não |
| 62 | min por par distribuidor×PDV → soma ÷ PDVs distintos | linhas FREQ>0 | 24 | -21.85 | -14.48 | 14.48 | -2.07 | não |
| 63 | first por par distribuidor×PDV → soma ÷ PDVs distintos | linhas FREQ>0 | 24 | -21.85 | -14.48 | 14.48 | -2.07 | não |
| 64 | min por PDV (Cód. PDV) → média dos PDVs | todas as linhas | 24 | -22.59 | -14.92 | 14.92 | -2.23 | não |
| 65 | min por PDV (Cód. PDV) → média dos PDVs | linhas kg>0 | 24 | -22.59 | -14.92 | 14.92 | -2.23 | não |
| 66 | min por PDV (Cód. PDV) → média dos PDVs | linhas FREQ>0 | 24 | -22.59 | -14.92 | 14.92 | -2.23 | não |
| 67 | min por par distribuidor×PDV → média dos pares | todas as linhas | 24 | -22.58 | -14.93 | 14.93 | -2.23 | não |
| 68 | first por par distribuidor×PDV → média dos pares | todas as linhas | 24 | -22.58 | -14.93 | 14.93 | -2.23 | não |
| 69 | min por par distribuidor×PDV → média dos pares | linhas kg>0 | 24 | -22.58 | -14.93 | 14.93 | -2.23 | não |
| 70 | first por par distribuidor×PDV → média dos pares | linhas kg>0 | 24 | -22.58 | -14.93 | 14.93 | -2.23 | não |
| 71 | min por par distribuidor×PDV → média dos pares | linhas FREQ>0 | 24 | -22.58 | -14.93 | 14.93 | -2.23 | não |
| 72 | first por par distribuidor×PDV → média dos pares | linhas FREQ>0 | 24 | -22.58 | -14.93 | 14.93 | -2.23 | não |
| 73 | max por SKU → média dos SKUs | todas as linhas | 24 | +149.58 | +306.30 | 149.58 | +102.60 | não |
| 74 | max por SKU → média dos SKUs | linhas kg>0 | 24 | +149.58 | +305.95 | 149.58 | +102.60 | não |
| 75 | max por SKU → média dos SKUs | linhas FREQ>0 | 24 | +149.58 | +306.30 | 149.58 | +102.60 | não |
| 76 | (soma ÷ PDVs) por distribuidor → média dos distribuidores | linhas kg>0 | 24 | +436.28 | +476.33 | 436.28 | +450.90 | não |
| 77 | (soma ÷ PDVs) por distribuidor → média dos distribuidores | todas as linhas | 24 | +436.29 | +476.33 | 436.29 | +450.90 | não |
| 78 | (soma ÷ PDVs) por distribuidor → média dos distribuidores | linhas FREQ>0 | 24 | +436.29 | +476.33 | 436.29 | +450.90 | não |
| 79 | soma das linhas ÷ pares distribuidor×PDV | linhas kg>0 | 24 | +462.18 | +513.83 | 462.18 | +464.66 | não |
| 80 | sum por par distribuidor×PDV → média dos pares | linhas kg>0 | 24 | +462.18 | +513.83 | 462.18 | +464.66 | não |
| 81 | soma das linhas ÷ pares distribuidor×PDV | todas as linhas | 24 | +462.19 | +513.90 | 462.19 | +464.66 | não |
| 82 | sum por par distribuidor×PDV → média dos pares | todas as linhas | 24 | +462.19 | +513.90 | 462.19 | +464.66 | não |
| 83 | soma das linhas ÷ pares distribuidor×PDV | linhas FREQ>0 | 24 | +462.19 | +513.90 | 462.19 | +464.66 | não |
| 84 | sum por par distribuidor×PDV → média dos pares | linhas FREQ>0 | 24 | +462.19 | +513.90 | 462.19 | +464.66 | não |
| 85 | soma das linhas ÷ PDVs distintos (Cód. PDV) | linhas kg>0 | 24 | +469.65 | +517.95 | 469.65 | +465.58 | não |
| 86 | sum por par distribuidor×PDV → soma ÷ PDVs distintos | linhas kg>0 | 24 | +469.65 | +517.95 | 469.65 | +465.58 | não |
| 87 | sum por PDV (Cód. PDV) → média dos PDVs | linhas kg>0 | 24 | +469.65 | +517.95 | 469.65 | +465.58 | não |
| 88 | soma das linhas ÷ PDVs distintos (Cód. PDV) | todas as linhas | 24 | +469.66 | +518.03 | 469.66 | +465.58 | não |
| 89 | sum por par distribuidor×PDV → soma ÷ PDVs distintos | todas as linhas | 24 | +469.66 | +518.03 | 469.66 | +465.58 | não |
| 90 | sum por PDV (Cód. PDV) → média dos PDVs | todas as linhas | 24 | +469.66 | +518.03 | 469.66 | +465.58 | não |
| 91 | soma das linhas ÷ PDVs distintos (Cód. PDV) | linhas FREQ>0 | 24 | +469.66 | +518.03 | 469.66 | +465.58 | não |
| 92 | sum por par distribuidor×PDV → soma ÷ PDVs distintos | linhas FREQ>0 | 24 | +469.66 | +518.03 | 469.66 | +465.58 | não |
| 93 | sum por PDV (Cód. PDV) → média dos PDVs | linhas FREQ>0 | 24 | +469.66 | +518.03 | 469.66 | +465.58 | não |
| 94 | soma das linhas ÷ PDVs positivados da linha de total | linhas kg>0 | 12 | +482.60 | +517.89 | 482.60 | — | não |
| 95 | soma das linhas ÷ PDVs positivados da linha de total | todas as linhas | 12 | +482.64 | +518.03 | 482.64 | — | não |
| 96 | soma das linhas ÷ PDVs positivados da linha de total | linhas FREQ>0 | 12 | +482.64 | +518.03 | 482.64 | — | não |
| 97 | soma das linhas ÷ CNPJ Reduzido distintos | linhas kg>0 | 24 | +525.68 | +578.97 | 525.68 | +516.04 | não |
| 98 | soma das linhas ÷ CNPJ Reduzido distintos | todas as linhas | 24 | +525.69 | +579.05 | 525.69 | +516.04 | não |
| 99 | soma das linhas ÷ CNPJ Reduzido distintos | linhas FREQ>0 | 24 | +525.69 | +579.05 | 525.69 | +516.04 | não |

**Teste 2 · estrutura do número.** Para cada denominador candidato N, calculei a distância de T × N ao inteiro mais próximo:

| Arquivo | Frequência (total) | PDVs distintos (todas as linhas) | PDVs distintos (kg>0) | pares dist×PDV (todas) | pares dist×PDV (kg>0) | CNPJ Reduzido distintos | linhas | linhas kg>0 | SKUs distintos | distribuidores | PDVs positivados (linha de total) | Total SKUs (linha de total) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 09.2024 | 1.253112 | N=59.120; 1.5e-11 | N=59.119; 2.5e-01 | N=59.632; 4.1e-01 | N=59.631; 3.4e-01 | N=54.006; 4.2e-01 | N=425.282; 1.1e-01 | N=425.251; 2.6e-01 | N=274; 3.5e-01 | N=72; 2.2e-01 | N=59.120; 1.5e-11 | N=274; 3.5e-01 |
| 10.2024 | 1.312540 | N=63.064; 0.0e+00 | N=63.064; 0.0e+00 | N=63.654; 4.0e-01 | N=63.653; 8.6e-02 | N=57.753; 1.0e-01 | N=459.689; 3.6e-02 | N=459.655; 4.1e-01 | N=277; 4.3e-01 | N=71; 1.9e-01 | N=63.064; 0.0e+00 | N=277; 4.3e-01 |
| 11.2024 | 1.249642 | N=60.094; 1.5e-11 | N=60.088; 5.0e-01 | N=60.498; 1.4e-01 | N=60.492; 3.6e-01 | N=54.694; 6.8e-02 | N=435.311; 7.6e-03 | N=435.258; 2.2e-01 | N=267; 3.5e-01 | N=71; 2.8e-01 | N=60.094; 1.5e-11 | N=267; 3.5e-01 |
| 12.2024 | 1.191125 | N=50.548; 1.5e-11 | N=50.548; 1.5e-11 | N=50.815; 3.0e-02 | N=50.815; 3.0e-02 | N=45.809; 2.6e-01 | N=352.385; 3.2e-01 | N=352.385; 3.2e-01 | N=258; 3.1e-01 | N=70; 3.8e-01 | N=50.548; 1.5e-11 | N=258; 3.1e-01 |
| 01.2025 | 1.229601 | N=59.660; 1.5e-11 | N=59.660; 1.5e-11 | N=60.136; 2.9e-01 | N=60.136; 2.9e-01 | N=54.442; 5.8e-02 | N=425.783; 2.3e-01 | N=425.783; 2.3e-01 | N=253; 8.9e-02 | N=71; 3.0e-01 | N=59.660; 1.5e-11 | N=253; 8.9e-02 |
| 02.2025 | 1.228270 | N=59.780; 0.0e+00 | N=59.780; 0.0e+00 | N=60.103; 2.7e-01 | N=60.103; 2.7e-01 | N=54.383; 2.5e-02 | N=416.662; 4.3e-01 | N=416.662; 4.3e-01 | N=247; 3.8e-01 | N=71; 2.1e-01 | N=59.780; 0.0e+00 | N=247; 3.8e-01 |
| 03.2025 | 1.220549 | N=61.569; 1.5e-11 | N=61.569; 1.5e-11 | N=61.909; 1.3e-02 | N=61.909; 1.3e-02 | N=56.071; 4.2e-01 | N=435.147; 3.7e-01 | N=435.147; 3.7e-01 | N=249; 8.3e-02 | N=71; 3.4e-01 | N=61.569; 1.5e-11 | N=249; 8.3e-02 |
| 04.2025 | 1.268427 | N=60.415; 1.5e-11 | N=60.412; 1.9e-01 | N=60.808; 4.9e-01 | N=60.805; 3.1e-01 | N=55.048; 3.5e-01 | N=415.844; 3.6e-01 | N=415.829; 3.9e-01 | N=250; 1.1e-01 | N=71; 5.8e-02 | N=60.415; 1.5e-11 | N=250; 1.1e-01 |
| 05.2025 | 1.261436 | N=65.714; 2.9e-11 | N=65.713; 2.6e-01 | N=66.093; 8.4e-02 | N=66.092; 1.8e-01 | N=59.922; 2.4e-01 | N=462.224; 4.4e-02 | N=462.204; 2.7e-01 | N=241; 6.1e-03 | N=71; 4.4e-01 | N=65.714; 2.9e-11 | N=241; 6.1e-03 |
| 06.2025 | 1.246006 | N=62.031; 1.5e-11 | N=62.022; 2.1e-01 | N=63.276; 2.8e-01 | N=63.267; 6.3e-02 | N=56.634; 3.1e-01 | N=431.231; 4.3e-01 | N=431.193; 7.8e-02 | N=240; 4.1e-02 | N=71; 4.7e-01 | N=62.031; 1.5e-11 | N=240; 4.1e-02 |
| 07.2025 | 1.301395 | N=66.816; 1.5e-11 | N=66.816; 1.5e-11 | N=68.228; 4.3e-01 | N=68.228; 4.3e-01 | N=60.888; 3.3e-01 | N=483.509; 1.3e-01 | N=483.502; 2.5e-02 | N=240; 3.3e-01 | N=71; 4.0e-01 | N=66.816; 1.5e-11 | N=240; 3.3e-01 |
| 08.2025 | 1.260484 | N=65.025; 0.0e+00 | N=65.025; 0.0e+00 | N=65.974; 2.0e-01 | N=65.974; 2.0e-01 | N=59.301; 1.3e-02 | N=465.975; 2.3e-01 | N=465.974; 2.9e-02 | N=240; 4.8e-01 | N=71; 4.9e-01 | N=65.025; 0.0e+00 | N=240; 4.8e-01 |
| 09.2025 | 1.275810 | N=64.976; 2.9e-11 | N=64.976; 2.9e-11 | N=65.500; 4.8e-01 | N=65.500; 4.8e-01 | N=59.101; 3.8e-01 | N=455.602; 3.7e-01 | N=455.602; 3.7e-01 | N=238; 3.6e-01 | N=72; 1.4e-01 | — | N=238; 3.6e-01 |
| 10.2025 | 1.295736 | N=67.195; 2.9e-11 | N=67.195; 2.9e-11 | N=68.088; 9.3e-02 | N=68.088; 9.3e-02 | N=61.178; 4.5e-01 | N=460.288; 1.3e-01 | N=460.283; 3.9e-01 | N=235; 5.0e-01 | N=73; 4.1e-01 | — | N=235; 5.0e-01 |
| 11.2025 | 1.232806 | N=63.134; 2.9e-11 | N=63.134; 2.9e-11 | N=63.940; 3.6e-01 | N=63.940; 3.6e-01 | N=57.414; 3.5e-01 | N=433.386; 4.0e-02 | N=433.383; 3.4e-01 | N=239; 3.6e-01 | N=75; 4.6e-01 | — | N=239; 3.6e-01 |
| 12.2025 | 1.207667 | N=56.451; 0.0e+00 | N=56.451; 0.0e+00 | N=56.824; 4.6e-01 | N=56.824; 4.6e-01 | N=50.933; 9.4e-02 | N=382.115; 3.9e-01 | N=382.115; 3.9e-01 | N=238; 4.2e-01 | N=73; 1.6e-01 | — | N=238; 4.2e-01 |
| 01.2026 | 1.215014 | N=63.247; 0.0e+00 | N=63.244; 3.5e-01 | N=63.938; 4.3e-01 | N=63.935; 7.0e-02 | N=57.771; 4.2e-01 | N=434.911; 1.9e-02 | N=434.889; 2.9e-01 | N=226; 4.1e-01 | N=73; 3.0e-01 | — | N=226; 4.1e-01 |
| 02.2026 | 1.218262 | N=61.724; 1.5e-11 | N=61.723; 2.2e-01 | N=62.143; 4.5e-01 | N=62.142; 2.3e-01 | N=56.183; 3.9e-01 | N=406.988; 9.5e-03 | N=406.952; 1.3e-01 | N=234; 7.3e-02 | N=73; 6.7e-02 | — | N=234; 7.3e-02 |
| 03.2026 | 1.270869 | N=66.198; 1.5e-11 | N=66.197; 2.7e-01 | N=66.743; 3.8e-01 | N=66.742; 3.5e-01 | N=60.247; 5.7e-02 | N=448.103; 3.1e-01 | N=448.100; 4.9e-01 | N=233; 1.1e-01 | N=73; 2.3e-01 | — | N=233; 1.1e-01 |
| 04.2026 | 1.246014 | N=63.533; 2.9e-11 | N=63.533; 2.9e-11 | N=64.373; 3.5e-01 | N=64.373; 3.5e-01 | N=57.892; 2.4e-01 | N=428.911; 6.0e-02 | N=428.910; 1.9e-01 | N=232; 7.5e-02 | N=74; 2.1e-01 | — | N=232; 7.5e-02 |
| 05.2026 | 1.240903 | N=68.372; 2.9e-11 | N=68.370; 4.8e-01 | N=68.994; 1.6e-01 | N=68.992; 3.6e-01 | N=62.504; 3.8e-01 | N=469.975; 2.5e-01 | N=469.971; 2.9e-01 | N=231; 3.5e-01 | N=73; 4.1e-01 | — | N=231; 3.5e-01 |
| 06.2026 | 1.256700 | N=66.899; 1.5e-11 | N=66.899; 1.5e-11 | N=68.532; 1.9e-01 | N=68.532; 1.9e-01 | N=61.189; 2.4e-01 | N=462.910; 1.8e-01 | N=462.910; 1.8e-01 | N=234; 6.8e-02 | N=73; 2.6e-01 | — | N=234; 6.8e-02 |
| 07.2026 | 1.288515 | N=74.530; 1.5e-11 | N=74.524; 2.7e-01 | N=75.121; 4.9e-01 | N=75.115; 2.2e-01 | N=68.428; 4.8e-01 | N=525.177; 2.8e-01 | N=525.151; 2.2e-01 | N=221; 2.4e-01 | N=72; 2.3e-01 | — | N=221; 2.4e-01 |
| 08.2026 | 1.248924 | N=72.251; 4.4e-11 | N=72.251; 4.4e-11 | N=73.060; 3.8e-01 | N=73.060; 3.8e-01 | N=66.157; 5.8e-02 | N=493.815; 3.5e-01 | N=493.815; 3.5e-01 | N=221; 1.2e-02 | N=72; 7.7e-02 | — | N=221; 1.2e-02 |
| 09.2026 | 1.025522 | N=15.908; 7.3e-12 | N=15.908; 7.3e-12 | N=15.934; 3.4e-01 | N=15.934; 3.4e-01 | N=14.605; 2.5e-01 | N=91.431; 4.8e-01 | N=91.431; 4.8e-01 | N=206; 2.6e-01 | N=68; 2.6e-01 | — | N=206; 2.6e-01 |

| Arquivo | N = Cód. PDV distintos | K = T × N | Σ max por PDV | Σ max por par | Σ max por PDV×categoria | Σ das linhas | K − Σ max por par | K dentro de [Σ max por par ; Σ linhas]? |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| 09.2024 | 59.120 | 74.084,000000 | 67.678 | 68.195 | 180.051 | 453.071 | 5.889 | sim |
| 10.2024 | 63.064 | 82.774,000000 | 74.187 | 74.784 | 198.095 | 496.279 | 7.990 | sim |
| 11.2024 | 60.094 | 75.096,000000 | 68.880 | 69.286 | 183.229 | 464.117 | 5.810 | sim |
| 12.2024 | 50.548 | 60.209,000000 | 55.991 | 56.260 | 146.555 | 370.018 | 3.949 | sim |
| 01.2025 | 59.660 | 73.358,000000 | 67.564 | 68.041 | 177.496 | 450.906 | 5.317 | sim |
| 02.2025 | 59.780 | 73.426,000000 | 67.420 | 67.749 | 177.055 | 441.099 | 5.677 | sim |
| 03.2025 | 61.569 | 75.148,000000 | 69.374 | 69.718 | 184.022 | 461.394 | 5.430 | sim |
| 04.2025 | 60.415 | 76.632,000000 | 69.881 | 70.278 | 182.481 | 446.486 | 6.354 | sim |
| 05.2025 | 65.714 | 82.894,000000 | 75.597 | 75.981 | 196.524 | 494.603 | 6.913 | sim |
| 06.2025 | 62.031 | 77.291,000000 | 70.840 | 72.240 | 184.953 | 459.124 | 5.051 | sim |
| 07.2025 | 66.816 | 86.954,000000 | 78.628 | 80.100 | 207.306 | 521.505 | 6.854 | sim |
| 08.2025 | 65.025 | 81.963,000000 | 75.009 | 75.965 | 198.600 | 499.304 | 5.998 | sim |
| 09.2025 | 64.976 | 82.897,000000 | 75.313 | 75.848 | 195.248 | 489.969 | 7.049 | sim |
| 10.2025 | 67.195 | 87.067,000000 | 78.440 | 79.343 | 201.571 | 495.987 | 7.724 | sim |
| 11.2025 | 63.134 | 77.832,000000 | 71.382 | 72.200 | 183.418 | 458.768 | 5.632 | sim |
| 12.2025 | 56.451 | 68.174,000000 | 63.174 | 63.549 | 160.310 | 405.504 | 4.625 | sim |
| 01.2026 | 63.247 | 76.846,000000 | 70.872 | 71.568 | 185.511 | 459.222 | 5.278 | sim |
| 02.2026 | 61.724 | 75.196,000000 | 69.366 | 69.795 | 180.886 | 430.177 | 5.401 | sim |
| 03.2026 | 66.198 | 84.129,000000 | 76.201 | 76.757 | 198.646 | 480.387 | 7.372 | sim |
| 04.2026 | 63.533 | 79.163,000000 | 72.194 | 73.049 | 185.962 | 455.141 | 6.114 | sim |
| 05.2026 | 68.372 | 84.843,000000 | 77.535 | 78.166 | 200.807 | 500.329 | 6.677 | sim |
| 06.2026 | 66.899 | 84.072,000000 | 76.699 | 78.401 | 199.325 | 494.066 | 5.671 | sim |
| 07.2026 | 74.530 | 96.033,000000 | 87.024 | 87.622 | 229.527 | 568.102 | 8.411 | sim |
| 08.2026 | 72.251 | 90.236,000000 | 81.962 | 82.779 | 212.497 | 525.971 | 7.457 | sim |
| 09.2026 | 15.908 | 16.314,000000 | 16.125 | 16.151 | 39.411 | 92.269 | 163 | sim |

- **MEDIDO:** T × (Cód. PDV distintos, contando todas as linhas) é inteiro nos 25 arquivos (distância ≤ 4,4×10⁻¹¹). Com kg > 0, só dá inteiro quando o número de PDVs é o mesmo. Pares, CNPJ Reduzido, linhas, SKUs e distribuidores não dão inteiro (menor distância encontrada: 0,006).
- **MEDIDO:** esse inteiro K fica sempre entre Σ(máximo por par) e Σ(linhas). Ele supera Σ(máximo por par) em 3.949 a 8.411 por mês fechado e Σ(máximo por PDV) em 7,5% a 11,6%. **Não dá para reproduzir K a partir das linhas por SKU** com nenhuma regra testada.
- **Não concluo aqui o que o campo significa**, porque nenhuma agregação bateu. As leituras possíveis estão na §9, marcadas como hipótese.

## 6. Categoria (MEDIDO)

| Arquivo | SKUs | SKUs sem categoria | linhas | kg sem categoria | % kg | Grupos PDV×cat c/ >1 linha | **varia** | % | Pares×cat c/ >1 linha | **varia** | % | Pares c/ 2+ categorias | const. em cada categoria e diferente entre elas | const. e igual entre categorias |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 09.2024 | 274 | 0  | 0 | 0,0 | 0,000 | 95.320 | 8.935 | 9,37 | 95.333 | 8.913 | 9,35 | 40.524 | 1.092 | 34.327 |
| 10.2024 | 277 | 0  | 0 | 0,0 | 0,000 | 103.191 | 11.972 | 11,60 | 103.212 | 11.956 | 11,58 | 43.377 | 1.328 | 35.460 |
| 11.2024 | 267 | 0  | 0 | 0,0 | 0,000 | 97.534 | 9.520 | 9,76 | 97.533 | 9.511 | 9,75 | 40.654 | 1.088 | 34.165 |
| 12.2024 | 258 | 0  | 0 | 0,0 | 0,000 | 78.777 | 5.513 | 7,00 | 78.785 | 5.516 | 7,00 | 33.742 | 634 | 29.986 |
| 01.2025 | 253 | 0  | 0 | 0,0 | 0,000 | 95.801 | 8.047 | 8,40 | 95.831 | 8.028 | 8,38 | 40.315 | 946 | 34.709 |
| 02.2025 | 247 | 0  | 0 | 0,0 | 0,000 | 93.662 | 7.794 | 8,32 | 93.664 | 7.787 | 8,31 | 40.049 | 996 | 34.536 |
| 03.2025 | 249 | 0  | 0 | 0,0 | 0,000 | 97.741 | 8.300 | 8,49 | 97.738 | 8.294 | 8,49 | 41.640 | 946 | 36.025 |
| 04.2025 | 250 | 0  | 0 | 0,0 | 0,000 | 93.417 | 9.778 | 10,47 | 93.411 | 9.775 | 10,46 | 40.866 | 1.193 | 34.200 |
| 05.2025 | 241 | 0  | 0 | 0,0 | 0,000 | 102.785 | 10.356 | 10,08 | 102.780 | 10.347 | 10,07 | 44.130 | 1.209 | 37.037 |
| 06.2025 | 240 | 0  | 0 | 0,0 | 0,000 | 97.144 | 9.042 | 9,31 | 97.621 | 9.156 | 9,38 | 42.469 | 1.150 | 36.121 |
| 07.2025 | 240 | 0  | 0 | 0,0 | 0,000 | 108.973 | 12.555 | 11,52 | 109.201 | 12.493 | 11,44 | 46.199 | 1.491 | 37.738 |
| 08.2025 | 240 | 0  | 0 | 0,0 | 0,000 | 105.227 | 10.644 | 10,12 | 105.282 | 10.614 | 10,08 | 44.666 | 1.274 | 37.488 |
| 09.2025 | 238 | 0  | 0 | 0,0 | 0,000 | 102.226 | 10.745 | 10,51 | 102.196 | 10.730 | 10,50 | 43.466 | 1.194 | 36.303 |
| 10.2025 | 235 | 0  | 0 | 0,0 | 0,000 | 104.647 | 11.859 | 11,33 | 104.753 | 11.828 | 11,29 | 44.952 | 1.310 | 36.986 |
| 11.2025 | 239 | 0  | 0 | 0,0 | 0,000 | 97.597 | 8.527 | 8,74 | 97.743 | 8.486 | 8,68 | 41.490 | 1.082 | 35.555 |
| 12.2025 | 238 | 0  | 0 | 0,0 | 0,000 | 86.009 | 6.469 | 7,52 | 85.994 | 6.468 | 7,52 | 36.443 | 773 | 32.013 |
| 01.2026 | 226 | 0  | 0 | 0,0 | 0,000 | 97.301 | 7.708 | 7,92 | 97.468 | 7.685 | 7,88 | 42.693 | 977 | 37.298 |
| 02.2026 | 234 | 0  | 0 | 0,0 | 0,000 | 90.800 | 7.838 | 8,63 | 90.777 | 7.828 | 8,62 | 41.718 | 1.002 | 36.152 |
| 03.2026 | 233 | 0  | 0 | 0,0 | 0,000 | 100.499 | 10.020 | 9,97 | 100.454 | 9.997 | 9,95 | 44.488 | 1.310 | 37.468 |
| 04.2026 | 232 | 0  | 0 | 0,0 | 0,000 | 95.082 | 8.874 | 9,33 | 95.155 | 8.845 | 9,30 | 42.975 | 1.149 | 36.642 |
| 05.2026 | 231 | 0  | 0 | 0,0 | 0,000 | 102.641 | 9.734 | 9,48 | 102.677 | 9.715 | 9,46 | 45.886 | 1.187 | 39.242 |
| 06.2026 | 234 | 0  | 0 | 0,0 | 0,000 | 101.016 | 9.991 | 9,89 | 101.562 | 10.028 | 9,87 | 46.093 | 1.263 | 39.166 |
| 07.2026 | 221 | 0  | 0 | 0,0 | 0,000 | 113.934 | 13.305 | 11,68 | 113.960 | 13.291 | 11,66 | 51.044 | 1.582 | 42.142 |
| 08.2026 | 221 | 0  | 0 | 0,0 | 0,000 | 107.646 | 10.178 | 9,46 | 107.737 | 10.156 | 9,43 | 48.202 | 1.306 | 41.194 |
| 09.2026 | 206 | 0  | 0 | 0,0 | 0,000 | 20.724 | 184 | 0,89 | 20.726 | 184 | 0,89 | 9.786 | 33 | 9.645 |

- 0 SKUs sem categoria e 0 kg sem categoria nos 25 arquivos (206 a 277 SKUs por mês; o cadastro tem 1.712).
- Nos meses fechados, a frequência varia entre SKUs da mesma categoria no mesmo PDV em 7,0% a 11,7% dos grupos PDV × categoria com mais de uma linha. No par distribuidor × PDV × categoria o resultado é praticamente o mesmo.
- Nos pares com 2 ou mais categorias em que a frequência é constante dentro de cada categoria, ela é **diferente entre as categorias** em 634 a 1.582 pares por mês. Na maior parte desses pares (29.986 a 42.142) ela é igual entre as categorias.

## 7. Bloqueios para o pipeline atual (MEDIDO)

**Resumo dos bloqueios que abortam a execução:**

| # | Onde aborta (código atual) | Arquivo(s) · mês | Linhas | kg |
|---|---|---|---:|---:|
| B1 | `dn/extract/sellout.py::_validar_schema`: coluna obrigatória `# PDVs Positivados` ausente (`config.yaml → fontes.sellout.colunas_obrigatorias`). O arquivo inteiro é rejeitado | 13 arquivos: 09.2025, 10.2025, 11.2025, 12.2025, 01.2026, 02.2026, 03.2026, 04.2026, 05.2026, 06.2026, 07.2026, 08.2026, 09.2026 · 2025-09 a 2026-09 | 5.493.612 | 13.978.182,5 |
| B2 | `dn/transform/dimensoes.py::dim_distribuidor`: CNPJ do distribuidor sem linha no `Distribuidores_DePara.xlsx` | ScoreCard_Mtrix_09.2024.xlsx · 2024-09 · 01026770000176 SBM COMÉRCIO DE PROD. - CAMPO GRANDE MS | 5.546 | 14.833,2 |

**Verificado e sem bloqueio (MEDIDO, 25 arquivos):** CNPJ do AD. fora de 14 dígitos 0; Cód. PDV vazio 0; SKU vazio 0; Ano/Mês não
reconhecido 0; mais de uma competência por arquivo 0; mês em dois arquivos 0; duplicado no grão 0; reconciliação R$/und/kg dentro da
tolerância em 25 de 25; chave OUTRO de 0,040% a 0,851% das linhas (limite 1,0%; o maior é out/24, 0,851%); SKU fora do cadastro 0;
nenhum mês faltando na série (a validação `serie · sem buraco de mes` passaria).

**Não aborta, mas precisa ser registrado (MEDIDO):**
- O leitor (`DESTINO` em `sellout.py`) **não lê** `# Frequência de compra`: hoje a coluna seria descartada sem aviso.
- A linha de total é lida com `t["# PDVs Positivados"]`. Nas 13 bases sem a coluna, o schema aborta antes de chegar aí.
- Distribuidores que estão no de-para mas não na Hierarquia (ficam fora do painel, RN-13) aparecem em todos os meses. O kg de cada um está na tabela abaixo.
- Todos os 25 arquivos mudaram em relação ao manifesto, então a próxima execução faria a ingestão completa. A série calculada passaria de 15 para 25 meses. **Efeito no tamanho do HTML, no tempo de execução e nas 124 validações: NÃO medido** (exigiria rodar o pipeline, fora do escopo desta etapa).

| Arquivo | Mês | Obrigatória ausente → leitor ABORTA | CNPJ AD ≠ 14 díg. | Cód. PDV vazio | SKU vazio | Ano/Mês não reconhecido | % OUTRO (limite 1.0) | kg OUTRO | Distribuidores (kg>0) | Fora do de-para (CNPJ · nome · linhas · kg) | No de-para sem hierarquia (fica fora do painel) | Reconcilia R$/und/kg na tolerância |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| 09.2024 | 2024-09 | — | 0 | 0 | 0 | 0 | 0,613 | 3.786,8 | 72 (72) | 01026770000176 · SBM COMÉRCIO DE PROD. - CAMPO GRANDE MS · 5.546 · 14.833,2 | RAYO - BRASILIA DF · 6.884 lin · 15.388,3 kg<br>IREZ E SIQUEIRA - MARABA PA · 237 lin · 685,9 kg<br>CBX COMERCIO DE ALIMENTOS E BEBIDAS LTDA · 184 lin · 244,4 kg<br>MDB · 3.276 lin · 7.823,0 kg<br>NORTESUL - CAPIVARI SP · 1.329 lin · 2.243,4 kg<br>CHUA - SERRA ES · 7.190 lin · 23.106,4 kg<br>AVANT DISTRIBUIDORA DE ALIMENTOS - CAMPINAS SP · 1.929 lin · 6.582,6 kg<br>MMD - CAÇAPAVA SP · 1.775 lin · 2.395,1 kg<br>KRUPER - PORTO ALEGRE RS · 15.771 lin · 50.579,5 kg | sim |
| 10.2024 | 2024-10 | — | 0 | 0 | 0 | 0 | 0,851 | 6.494,5 | 71 (71) | — | RAYO - BRASILIA DF · 7.945 lin · 16.997,5 kg<br>IREZ E SIQUEIRA - MARABA PA · 166 lin · 398,9 kg<br>CBX COMERCIO DE ALIMENTOS E BEBIDAS LTDA · 216 lin · 536,5 kg<br>MDB · 3.533 lin · 8.135,1 kg<br>NORTESUL - CAPIVARI SP · 1.128 lin · 1.950,2 kg<br>CHUA - SERRA ES · 8.151 lin · 26.289,0 kg<br>AVANT DISTRIBUIDORA DE ALIMENTOS - CAMPINAS SP · 2.262 lin · 7.782,3 kg<br>MMD - CAÇAPAVA SP · 2.108 lin · 2.729,7 kg<br>KRUPER - PORTO ALEGRE RS · 15.296 lin · 38.797,9 kg | sim |
| 11.2024 | 2024-11 | — | 0 | 0 | 0 | 0 | 0,702 | 5.031,6 | 71 (71) | — | RAYO - BRASILIA DF · 6.545 lin · 13.802,2 kg<br>IREZ E SIQUEIRA - MARABA PA · 11 lin · 22,1 kg<br>CBX COMERCIO DE ALIMENTOS E BEBIDAS LTDA · 173 lin · 270,8 kg<br>MDB · 3.723 lin · 8.761,0 kg<br>NORTESUL - CAPIVARI SP · 1.134 lin · 1.790,7 kg<br>CHUA - SERRA ES · 7.031 lin · 25.441,0 kg<br>AVANT DISTRIBUIDORA DE ALIMENTOS - CAMPINAS SP · 1.771 lin · 6.244,4 kg<br>MMD - CAÇAPAVA SP · 1.751 lin · 2.275,9 kg<br>KRUPER - PORTO ALEGRE RS · 12.723 lin · 29.376,2 kg | sim |
| 12.2024 | 2024-12 | — | 0 | 0 | 0 | 0 | 0,800 | 4.629,5 | 70 (70) | — | RAYO - BRASILIA DF · 4.835 lin · 9.978,3 kg<br>CBX COMERCIO DE ALIMENTOS E BEBIDAS LTDA · 91 lin · 123,9 kg<br>MDB · 3.075 lin · 7.730,0 kg<br>NORTESUL - CAPIVARI SP · 747 lin · 1.018,4 kg<br>CHUA - SERRA ES · 6.161 lin · 25.548,0 kg<br>AVANT DISTRIBUIDORA DE ALIMENTOS - CAMPINAS SP · 863 lin · 3.763,3 kg<br>MMD - CAÇAPAVA SP · 1.419 lin · 2.149,1 kg<br>KRUPER - PORTO ALEGRE RS · 12.759 lin · 34.288,8 kg | sim |
| 01.2025 | 2025-01 | — | 0 | 0 | 0 | 0 | 0,040 | 128,6 | 71 (71) | — | RAYO - BRASILIA DF · 7.415 lin · 13.619,5 kg<br>CBX COMERCIO DE ALIMENTOS E BEBIDAS LTDA · 159 lin · 277,6 kg<br>MDB · 1.970 lin · 3.878,9 kg<br>NORTESUL - CAPIVARI SP · 778 lin · 1.033,8 kg<br>CHUA - SERRA ES · 5.836 lin · 20.160,6 kg<br>AVANT DISTRIBUIDORA DE ALIMENTOS - CAMPINAS SP · 1.334 lin · 4.169,7 kg<br>MMD - CAÇAPAVA SP · 2.075 lin · 2.631,9 kg<br>KRUPER - PORTO ALEGRE RS · 12.249 lin · 27.612,1 kg | sim |
| 02.2025 | 2025-02 | — | 0 | 0 | 0 | 0 | 0,048 | 131,4 | 71 (71) | — | RAYO - BRASILIA DF · 6.718 lin · 13.223,1 kg<br>CBX COMERCIO DE ALIMENTOS E BEBIDAS LTDA · 154 lin · 215,2 kg<br>MDB · 3.397 lin · 6.521,7 kg<br>NORTESUL - CAPIVARI SP · 756 lin · 1.178,3 kg<br>CHUA - SERRA ES · 5.571 lin · 18.292,7 kg<br>AVANT DISTRIBUIDORA DE ALIMENTOS - CAMPINAS SP · 1.947 lin · 6.357,9 kg<br>MMD - CAÇAPAVA SP · 1.872 lin · 2.263,1 kg<br>KRUPER - PORTO ALEGRE RS · 11.641 lin · 26.806,0 kg | sim |
| 03.2025 | 2025-03 | — | 0 | 0 | 0 | 0 | 0,052 | 250,3 | 71 (71) | — | RAYO - BRASILIA DF · 7.434 lin · 14.927,9 kg<br>CBX COMERCIO DE ALIMENTOS E BEBIDAS LTDA · 188 lin · 240,8 kg<br>MDB · 4.647 lin · 9.972,9 kg<br>NORTESUL - CAPIVARI SP · 943 lin · 1.448,0 kg<br>CHUA - SERRA ES · 5.778 lin · 18.633,8 kg<br>AVANT DISTRIBUIDORA DE ALIMENTOS - CAMPINAS SP · 1.342 lin · 3.808,0 kg<br>MMD - CAÇAPAVA SP · 1.948 lin · 2.564,2 kg<br>KRUPER - PORTO ALEGRE RS · 16.721 lin · 44.210,5 kg | sim |
| 04.2025 | 2025-04 | — | 0 | 0 | 0 | 0 | 0,063 | 321,0 | 71 (71) | — | RAYO - BRASILIA DF · 7.021 lin · 14.495,1 kg<br>CBX COMERCIO DE ALIMENTOS E BEBIDAS LTDA · 232 lin · 438,1 kg<br>MDB · 1.923 lin · 5.038,3 kg<br>NORTESUL - CAPIVARI SP · 920 lin · 1.403,8 kg<br>CHUA - SERRA ES · 5.154 lin · 16.590,0 kg<br>AVANT DISTRIBUIDORA DE ALIMENTOS - CAMPINAS SP · 1.367 lin · 5.226,2 kg<br>MMD - CAÇAPAVA SP · 1.667 lin · 2.381,2 kg<br>KRUPER - PORTO ALEGRE RS · 14.064 lin · 32.038,5 kg | sim |
| 05.2025 | 2025-05 | — | 0 | 0 | 0 | 0 | 0,060 | 207,4 | 71 (71) | — | RAYO - BRASILIA DF · 7.104 lin · 14.634,1 kg<br>CBX COMERCIO DE ALIMENTOS E BEBIDAS LTDA · 214 lin · 270,8 kg<br>MDB · 3.782 lin · 8.411,0 kg<br>NORTESUL - CAPIVARI SP · 1.069 lin · 1.665,5 kg<br>CHUA - SERRA ES · 6.732 lin · 23.484,8 kg<br>AVANT DISTRIBUIDORA DE ALIMENTOS - CAMPINAS SP · 1.309 lin · 3.618,3 kg<br>MMD - CAÇAPAVA SP · 1.780 lin · 2.301,8 kg<br>KRUPER - PORTO ALEGRE RS · 14.110 lin · 33.148,9 kg | sim |
| 06.2025 | 2025-06 | — | 0 | 0 | 0 | 0 | 0,065 | 1.024,8 | 71 (71) | — | RAYO - BRASILIA DF · 7.496 lin · 17.295,0 kg<br>CBX COMERCIO DE ALIMENTOS E BEBIDAS LTDA · 222 lin · 301,0 kg<br>MDB · 3.504 lin · 8.081,4 kg<br>NORTESUL - CAPIVARI SP · 940 lin · 1.362,2 kg<br>CHUA - SERRA ES · 5.396 lin · 17.586,9 kg<br>AVANT DISTRIBUIDORA DE ALIMENTOS - CAMPINAS SP · 1.662 lin · 6.045,8 kg<br>MMD - CAÇAPAVA SP · 2.178 lin · 3.155,2 kg<br>KRUPER - PORTO ALEGRE RS · 10.319 lin · 25.139,2 kg | sim |
| 07.2025 | 2025-07 | — | 0 | 0 | 0 | 0 | 0,057 | 786,0 | 71 (71) | — | RAYO - BRASILIA DF · 8.093 lin · 16.740,1 kg<br>CBX COMERCIO DE ALIMENTOS E BEBIDAS LTDA · 301 lin · 447,5 kg<br>MDB · 4.008 lin · 9.773,4 kg<br>NORTESUL - CAPIVARI SP · 976 lin · 1.712,1 kg<br>CHUA - SERRA ES · 5.465 lin · 19.166,1 kg<br>AVANT DISTRIBUIDORA DE ALIMENTOS - CAMPINAS SP · 1.642 lin · 5.643,5 kg<br>MMD - CAÇAPAVA SP · 2.054 lin · 2.823,9 kg<br>KRUPER - PORTO ALEGRE RS · 15.585 lin · 36.915,8 kg | sim |
| 08.2025 | 2025-08 | — | 0 | 0 | 0 | 0 | 0,058 | 474,1 | 71 (71) | — | RAYO - BRASILIA DF · 7.086 lin · 15.656,0 kg<br>CBX COMERCIO DE ALIMENTOS E BEBIDAS LTDA · 196 lin · 319,7 kg<br>MDB · 3.736 lin · 8.460,8 kg<br>NORTESUL - CAPIVARI SP · 958 lin · 1.734,5 kg<br>CHUA - SERRA ES · 6.731 lin · 25.200,6 kg<br>AVANT DISTRIBUIDORA DE ALIMENTOS - CAMPINAS SP · 1.833 lin · 6.390,5 kg<br>MMD - CAÇAPAVA SP · 2.082 lin · 2.803,8 kg<br>KRUPER - PORTO ALEGRE RS · 13.827 lin · 34.919,2 kg | sim |
| 09.2025 | 2025-09 | # PDVs Positivados | 0 | 0 | 0 | 0 | 0,052 | 521,9 | 72 (72) | — | RAYO - BRASILIA DF · 7.350 lin · 16.565,3 kg<br>CBX COMERCIO DE ALIMENTOS E BEBIDAS LTDA · 141 lin · 165,6 kg<br>MDB · 3.993 lin · 8.218,6 kg<br>NORTESUL - CAPIVARI SP · 943 lin · 1.692,8 kg<br>CHUA - SERRA ES · 6.967 lin · 22.562,2 kg<br>AVANT DISTRIBUIDORA DE ALIMENTOS - CAMPINAS SP · 1.175 lin · 4.318,4 kg<br>MMD - CAÇAPAVA SP · 1.590 lin · 2.139,5 kg<br>KRUPER - PORTO ALEGRE RS · 16.025 lin · 49.009,9 kg | sim |
| 10.2025 | 2025-10 | # PDVs Positivados | 0 | 0 | 0 | 0 | 0,055 | 335,9 | 73 (73) | — | RAYO - BRASILIA DF · 7.745 lin · 15.239,3 kg<br>CBX COMERCIO DE ALIMENTOS E BEBIDAS LTDA · 206 lin · 273,7 kg<br>MDB · 3.619 lin · 9.848,1 kg<br>NORTESUL - CAPIVARI SP · 1.101 lin · 1.797,4 kg<br>CHUA - SERRA ES · 6.149 lin · 19.837,0 kg<br>AVANT DISTRIBUIDORA DE ALIMENTOS - CAMPINAS SP · 1.518 lin · 4.429,8 kg<br>MMD - CAÇAPAVA SP · 1.789 lin · 2.243,7 kg<br>KRUPER - PORTO ALEGRE RS · 12.443 lin · 28.246,1 kg | sim |
| 11.2025 | 2025-11 | # PDVs Positivados | 0 | 0 | 0 | 0 | 0,051 | 465,8 | 75 (75) | — | RAYO - BRASILIA DF · 6.611 lin · 12.157,8 kg<br>IREZ E SIQUEIRA - MARABA PA · 76 lin · 82,1 kg<br>CBX COMERCIO DE ALIMENTOS E BEBIDAS LTDA · 154 lin · 199,1 kg<br>MDB · 2.085 lin · 4.579,4 kg<br>NORTESUL - CAPIVARI SP · 854 lin · 1.566,7 kg<br>CHUA - SERRA ES · 6.158 lin · 24.784,6 kg<br>AVANT DISTRIBUIDORA DE ALIMENTOS - CAMPINAS SP · 1.228 lin · 3.584,1 kg<br>MMD - CAÇAPAVA SP · 1.471 lin · 2.171,6 kg<br>KRUPER - PORTO ALEGRE RS · 11.931 lin · 28.115,2 kg | sim |
| 12.2025 | 2025-12 | # PDVs Positivados | 0 | 0 | 0 | 0 | 0,053 | 399,2 | 73 (73) | — | RAYO - BRASILIA DF · 5.668 lin · 11.236,7 kg<br>CBX COMERCIO DE ALIMENTOS E BEBIDAS LTDA · 184 lin · 224,4 kg<br>NORTESUL - CAPIVARI SP · 962 lin · 1.817,5 kg<br>CHUA - SERRA ES · 5.610 lin · 21.669,4 kg<br>AVANT DISTRIBUIDORA DE ALIMENTOS - CAMPINAS SP · 1.504 lin · 5.773,5 kg<br>MMD - CAÇAPAVA SP · 1.341 lin · 2.205,2 kg<br>KRUPER - PORTO ALEGRE RS · 9.748 lin · 23.653,6 kg | sim |
| 01.2026 | 2026-01 | # PDVs Positivados | 0 | 0 | 0 | 0 | 0,066 | 805,7 | 73 (73) | — | RAYO - BRASILIA DF · 6.994 lin · 14.227,8 kg<br>CBX COMERCIO DE ALIMENTOS E BEBIDAS LTDA · 166 lin · 232,5 kg<br>NORTESUL - CAPIVARI SP · 1.204 lin · 2.858,6 kg<br>CHUA - SERRA ES · 4.678 lin · 15.138,7 kg<br>AVANT DISTRIBUIDORA DE ALIMENTOS - CAMPINAS SP · 1.294 lin · 4.484,7 kg<br>MMD - CAÇAPAVA SP · 1.598 lin · 2.117,8 kg<br>KRUPER - PORTO ALEGRE RS · 9.694 lin · 21.480,6 kg | sim |
| 02.2026 | 2026-02 | # PDVs Positivados | 0 | 0 | 0 | 0 | 0,064 | 415,1 | 73 (73) | — | RAYO - BRASILIA DF · 5.628 lin · 11.612,3 kg<br>CBX COMERCIO DE ALIMENTOS E BEBIDAS LTDA · 182 lin · 287,4 kg<br>NORTESUL - CAPIVARI SP · 974 lin · 1.636,8 kg<br>CHUA - SERRA ES · 3.241 lin · 9.934,1 kg<br>AVANT DISTRIBUIDORA DE ALIMENTOS - CAMPINAS SP · 1.880 lin · 6.195,1 kg<br>MMD - CAÇAPAVA SP · 1.532 lin · 2.397,9 kg<br>KRUPER - PORTO ALEGRE RS · 6.663 lin · 16.042,7 kg | sim |
| 03.2026 | 2026-03 | # PDVs Positivados | 0 | 0 | 0 | 0 | 0,060 | 577,0 | 73 (73) | — | RAYO - BRASILIA DF · 7.154 lin · 16.221,9 kg<br>CBX COMERCIO DE ALIMENTOS E BEBIDAS LTDA · 215 lin · 382,4 kg<br>NORTESUL - CAPIVARI SP · 1.224 lin · 1.951,6 kg<br>CHUA - SERRA ES · 4.031 lin · 13.025,2 kg<br>AVANT DISTRIBUIDORA DE ALIMENTOS - CAMPINAS SP · 2.356 lin · 7.038,6 kg<br>MMD - CAÇAPAVA SP · 1.634 lin · 2.207,7 kg<br>KRUPER - PORTO ALEGRE RS · 12.676 lin · 29.785,6 kg | sim |
| 04.2026 | 2026-04 | # PDVs Positivados | 0 | 0 | 0 | 0 | 0,071 | 696,3 | 74 (74) | — | RAYO - BRASILIA DF · 6.339 lin · 13.800,4 kg<br>CBX COMERCIO DE ALIMENTOS E BEBIDAS LTDA · 156 lin · 329,8 kg<br>NORTESUL - CAPIVARI SP · 1.079 lin · 1.684,2 kg<br>CHUA - SERRA ES · 1.735 lin · 5.177,7 kg<br>AVANT DISTRIBUIDORA DE ALIMENTOS - CAMPINAS SP · 2.034 lin · 5.978,7 kg<br>MMD - CAÇAPAVA SP · 1.531 lin · 2.067,6 kg<br>KRUPER - PORTO ALEGRE RS · 6.341 lin · 13.950,8 kg | sim |
| 05.2026 | 2026-05 | # PDVs Positivados | 0 | 0 | 0 | 0 | 0,071 | 1.152,9 | 73 (73) | — | RAYO - BRASILIA DF · 7.782 lin · 17.796,7 kg<br>CBX COMERCIO DE ALIMENTOS E BEBIDAS LTDA · 196 lin · 269,9 kg<br>NORTESUL - CAPIVARI SP · 1.066 lin · 1.690,4 kg<br>AVANT DISTRIBUIDORA DE ALIMENTOS - CAMPINAS SP · 1.471 lin · 3.301,4 kg<br>MMD - CAÇAPAVA SP · 1.553 lin · 2.104,2 kg<br>KRUPER - PORTO ALEGRE RS · 6.484 lin · 12.604,3 kg | sim |
| 06.2026 | 2026-06 | # PDVs Positivados | 0 | 0 | 0 | 0 | 0,073 | 504,1 | 73 (73) | — | RAYO - BRASILIA DF · 7.345 lin · 17.055,7 kg<br>CBX COMERCIO DE ALIMENTOS E BEBIDAS LTDA · 22 lin · 17,0 kg<br>NORTESUL - CAPIVARI SP · 899 lin · 1.956,3 kg<br>MMD - CAÇAPAVA SP · 11 lin · 13,4 kg<br>KRUPER - PORTO ALEGRE RS · 163 lin · 566,8 kg | sim |
| 07.2026 | 2026-07 | # PDVs Positivados | 0 | 0 | 0 | 0 | 0,047 | 1.120,3 | 72 (72) | — | RAYO - BRASILIA DF · 7.925 lin · 17.074,1 kg | sim |
| 08.2026 | 2026-08 | # PDVs Positivados | 0 | 0 | 0 | 0 | 0,050 | 291,0 | 72 (72) | — | RAYO - BRASILIA DF · 6.663 lin · 13.019,1 kg | sim |
| 09.2026 | 2026-09 | # PDVs Positivados | 0 | 0 | 0 | 0 | 0,125 | 115,1 | 68 (68) | — | RAYO - BRASILIA DF · 1.692 lin · 3.367,2 kg | sim |

## 8. Comparação com o publicado (MEDIDO)

Referência: `data/dn/staging` (leitura de 11/09/2026 15h56, mesma etapa do leitor), `curated/FATO_SELLOUT` (= staging: 0 diferença de
linhas e kg em todos os meses) e os cubos publicados. O painel no ar calcula jul/25–ago/26 e exibe set/25–ago/26. set/26 não é publicado.

| Mês | Linhas iguais (chave) | Só na nova | Só na antiga | Iguais c/ métrica diferente | kg painel publicado → novo | Δ R$ painel | Positivados publicado → novo | Base ativa publicado → nova | DN publicado → nova (p.p.) | Distribuidores c/ venda no painel antes → novo |
|---|---:|---:|---:|---:|---|---:|---|---|---|---|
| 2025-07 | 482.905 | 604 | 0 | 0 | 1.164.504,4 → 1.165.912,5 | 57.008,44 | 62.278 → 62.327 | — → 107.299 | — → 58,09 | 62 → 63 |
| 2025-08 | 465.856 | 119 | 0 | 0 | 1.138.339,9 → 1.138.780,6 | 18.968,28 | 60.796 → 60.809 | — → 108.283 | — → 56,16 | 62 → 63 |
| 2025-09 | 455.240 | 362 | 0 | 0 | 1.097.253,9 → 1.098.683,8 | 43.325,39 | 60.572 → 60.599 | — → 109.188 | — → 55,50 | 63 → 64 |
| 2025-10 | 459.948 | 340 | 0 | 0 | 1.126.742,5 → 1.127.373,2 | 28.536,91 | 62.827 → 62.859 | — → 109.899 | — → 57,20 | 64 → 65 |
| 2025-11 | 433.216 | 170 | 0 | 0 | 1.062.817,6 → 1.064.550,9 | 43.795,43 | 59.468 → 59.475 | 110.136 → 110.192 | 54,00 → 53,97 (-0,021) | 65 → 66 |
| 2025-12 | 382.088 | 27 | 0 | 0 | 987.436,7 → 987.498,8 | 3.242,87 | 53.205 → 53.208 | 108.613 → 108.661 | 48,99 → 48,97 (-0,019) | 65 → 66 |
| 2026-01 | 434.808 | 103 | 0 | 0 | 977.754,5 → 978.114,8 | 15.540,92 | 59.951 → 59.961 | 108.243 → 108.290 | 55,39 → 55,37 (-0,015) | 65 → 66 |
| 2026-02 | 406.560 | 428 | 0 | 0 | 956.408,7 → 957.223,9 | 37.038,89 | 58.767 → 58.802 | 109.055 → 109.105 | 53,89 → 53,89 (+0,007) | 65 → 66 |
| 2026-03 | 447.872 | 231 | 0 | 0 | 1.042.836,8 → 1.044.384,7 | 46.602,91 | 62.530 → 62.550 | 109.269 → 109.319 | 57,23 → 57,22 (-0,008) | 65 → 66 |
| 2026-04 | 428.474 | 437 | 0 | 0 | 1.054.624,8 → 1.055.590,1 | 39.845,04 | 60.767 → 60.802 | 109.998 → 110.051 | 55,24 → 55,25 (+0,005) | 66 → 67 |
| 2026-05 | 468.908 | 1.067 | 0 | 0 | 1.168.485,3 → 1.172.073,5 | 134.031,44 | 65.778 → 65.909 | 113.015 → 113.154 | 58,20 → 58,25 (+0,044) | 66 → 67 |
| 2026-06 | 462.250 | 660 | 0 | 0 | 1.162.069,3 → 1.164.300,7 | 81.662,18 | 65.709 → 65.820 | 115.017 → 115.196 | 57,13 → 57,14 (+0,008) | 67 → 68 |
| 2026-07 | 523.384 | 1.793 | 0 | 0 | 1.279.512,9 → 1.283.861,4 | 109.187,54 | 73.185 → 73.644 | 120.817 → 121.341 | 60,58 → 60,69 (+0,117) | 70 → 71 |
| 2026-08 | 493.815 | 0 | 0 | 0 | 1.199.859,4 → 1.199.859,4 | 0,00 | 71.478 → 71.478 | 124.600 → 124.800 | 57,37 → 57,27 (-0,092) | 71 → 71 |
| 2026-09 *(parcial; staging)* | 75.566 | 15.865 | 64 | 262 | 163.447,2 → 201.173,1 | 1.247.877,52 | 12.811 → 15.644 | — → 120.742 | — → 12,96 | 66 → 67 |

*kg/R$/positivados "publicado" = `DN_CANAL_MES` (jul/25–ago/26); set/26 = staging. "No painel" = distribuidores com `NO_PAINEL` na `DIM_DISTRIBUIDOR` atual.*

- **Linha a linha, jul/25 a ago/26:** nenhuma linha antiga sumiu, e nenhuma linha em comum mudou de R$, und ou kg. As únicas diferenças são linhas novas:

| Distribuidor | CNPJ | Mês | Linhas novas | kg | R$ | PDVs positivados no distribuidor |
|---|---|---|---:|---:|---:|---:|
| DIERO | 07266768000150 | 2025-07 | 604 | 1.408,2 | 57.008,44 | 49 |
| DIERO | 07266768000150 | 2025-08 | 119 | 440,7 | 18.968,28 | 13 |
| DIERO | 07266768000150 | 2025-09 | 362 | 1.429,9 | 43.325,39 | 27 |
| DIERO | 07266768000150 | 2025-10 | 340 | 630,8 | 28.536,91 | 32 |
| DIERO | 07266768000150 | 2025-11 | 170 | 1.733,3 | 43.795,43 | 7 |
| DIERO | 07266768000150 | 2025-12 | 27 | 62,1 | 3.242,87 | 3 |
| DIERO | 07266768000150 | 2026-01 | 103 | 360,3 | 15.540,92 | 10 |
| DIERO | 07266768000150 | 2026-02 | 428 | 815,2 | 37.038,89 | 35 |
| DIERO | 07266768000150 | 2026-03 | 231 | 1.547,8 | 46.602,91 | 20 |
| DIERO | 07266768000150 | 2026-04 | 437 | 965,2 | 39.845,04 | 35 |
| DIERO | 07266768000150 | 2026-05 | 1.067 | 3.588,1 | 134.031,44 | 134 |
| DIERO | 07266768000150 | 2026-06 | 660 | 2.231,4 | 81.662,18 | 113 |
| PELLAH | 01227691000123 | 2026-07 | 1.793 | 4.348,5 | 109.187,54 | 466 |
| **Total** | | | **6.341** | **19.561,7** | **658.786,24** | |

- Nos 916 pares distribuidor × mês que já estão em `DN_DISTRIBUIDOR_MES`, a diferença é 0 em positivados e em kg. As linhas novas criam pares distribuidor × mês que o painel não tem.
- **ago/26 (mês publicado):** kg, R$, positivados e distribuidores são idênticos. Muda só a base ativa: 124.600 → 124.800 (+200, porque a janela abr–ago/26 ganha PDVs da DIERO de abr–jun e da PELLAH de jul) e, com ela, a DN: 57,37% → 57,27% (−0,09 p.p.).
- **Distribuidores com venda no painel:** +1 em cada mês de jul/25 a jul/26 (DIERO até jun/26; PELLAH em jul/26). ago/26 continua com 71.
- **set/26 (parcial, não publicado):** a base nova tem 15.865 linhas a mais, 64 linhas que sumiram (171,5 kg) e 262 linhas com métrica diferente (Σ|Δkg| 632,5). Em kg no painel, passou de 163.447 para 201.173.
- **Meses novos set/24–jun/25:** nunca estiveram no painel. Com eles, a base ativa passaria a existir desde jan/25, e jul–out/25 deixariam de ser nulos. O efeito na tela (LY, acumulados, Alavancas com par) **não foi medido**.

## 9. MEDIDO × HIPÓTESE

| Tema | MEDIDO | HIPÓTESE (não verificada, não usada em conta) |
|---|---|---|
| Significado do campo | Inteiro ≥ 1 por linha; varia entre SKUs do PDV; no total é K ÷ PDVs distintos, com K inteiro entre Σ max por par e Σ linhas | H1: é a quantidade de ocasiões de compra (datas ou notas) no mês, calculada pela Mtrix **no nível da consulta**: por SKU nas linhas e com o PDV como unidade no total. O PDV que compra SKUs diferentes em dias diferentes teria mais ocasiões que o maior valor de um SKU, e isso explicaria K > Σ max. Só a Mtrix confirma |
| Linhas kg ≤ 0 com frequência 2 | 299 linhas; quase todas com frequência 2 | H2: venda e devolução no mesmo mês (duas ocasiões que se anulam no kg) |
| Total de PDVs positivados | = Cód. PDV distintos, incluindo PDVs só com kg ≤ 0 | H3: a Mtrix conta "PDV com movimento", não "kg > 0" (RN-01) |
| DIERO jul/25–jun/26 e PELLAH jul/26 | Linhas presentes só na base nova | H4: a extração anterior não trazia esses distribuidores nesses meses (cadastro na Mtrix posterior à primeira extração) |
| Frequência do PDV a partir do arquivo | Nenhuma regra testada reproduz o total | H5: com a base por SKU, a frequência do PDV (e da categoria) não pode ser obtida exatamente; só limites. Isso é assunto da Etapa 2 e depende de medir se existe extração no grão PDV |

## 10. O que ficou em aberto

1. O significado oficial de `# Frequência de compra` (definição da Mtrix): não há nada nas bases que o documente.
2. Se a Mtrix consegue entregar o mesmo campo no grão **PDV** (sem SKU), **PDV × categoria** e **distribuidor × PDV**. Só uma extração nesse grão permite testar se as linhas somam o total.
3. Por que `# PDVs Positivados` saiu das 13 bases de set/25 em diante: mudança do layout da consulta ou omissão.
4. O efeito das 25 bases no pipeline (tamanho do HTML diante de `html_max_mb: 12`, tempo, 124 validações, Alavancas com LY): não medido.
5. Se as linhas novas da DIERO e da PELLAH estão corretas.
6. A SBM COMÉRCIO (set/24): cadastrar ou deixar de fora.

## 11. Perguntas para o Douglas

1. **Definição do campo:** você (ou a Mtrix) tem a definição oficial de `# Frequência de compra`? Ocasião = dia com compra, nota fiscal ou pedido? Conta devolução?
2. **Extração no grão PDV:** dá para pedir à Mtrix a mesma consulta **sem SKU**, com a frequência no grão `mês × CNPJ do AD. × Cód. PDV`, e outra no grão `mês × CNPJ do AD. × Cód. PDV × categoria`? Com o grão SKU, o total medido não é reprodutível (§5).
3. **Frequência do PDV multi-distribuidor:** o que você quer medir é a frequência do PDV **em cada distribuidor** ou a do PDV **no canal** (somando distribuidores)? Pelo §4, os dois números diferem em 1 a 34 PDVs por mês.
4. **`# PDVs Positivados`:** a coluna saiu das bases de set/25–set/26. Pede para voltar, ou prefere que a Etapa 2 avalie tirá-la das obrigatórias? No pipeline ela só serve para um aviso informativo.
5. **SBM COMÉRCIO (01026770000176, set/24, 14.833,2 kg):** entra no `Distribuidores_DePara.xlsx`, fica fora ou set/24 sai da carga?
6. **Série:** as bases set/24–jun/25 devem entrar no painel? A série calculada iria de 14 para 25 meses, a base ativa passaria a existir desde jan/25 e set/25–ago/26 ganhariam LY.
7. **Números publicados que mudariam:** as linhas novas da DIERO (jul/25–jun/26) e da PELLAH (jul/26) são esperadas? Aceita que a base ativa de ago/26 vá de 124.600 para 124.800 (DN 57,37% → 57,27%), com mudanças de +3 a +459 positivados em jul/25–jul/26?
8. **Linhas com kg ≤ 0 (299):** elas têm frequência (em geral 2). Na frequência, devem seguir a régua do positivado (kg > 0, RN-01) ou a da Mtrix (qualquer movimento)?
9. **Mês em andamento:** set/26 tem frequência bem menor (máximo 5, média 1,009). A frequência do mês parcial deve aparecer no painel etiquetada, como as outras medidas (RN-26), ou ficar de fora?

**Paro aqui e aguardo o seu ok na Etapa 1 antes de qualquer proposta.**

---

## Anexo A · Todas as regras testadas, mês a mês (diferença % contra a frequência da linha de total)

| Regra | População | 09.2024 | 10.2024 | 11.2024 | 12.2024 | 01.2025 | 02.2025 | 03.2025 | 04.2025 | 05.2025 | 06.2025 | 07.2025 | 08.2025 | 09.2025 | 10.2025 | 11.2025 | 12.2025 | 01.2026 | 02.2026 | 03.2026 | 04.2026 | 05.2026 | 06.2026 | 07.2026 | 08.2026 | 09.2026 | máx \|dif\| % |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| média ponderada por KG (pesos<0 = 0) | todas as linhas | -3.45 | -6.98 | -6.04 | -3.01 | -6.09 | -5.03 | -4.08 | -5.19 | -3.72 | -2.98 | -6.04 | -3.84 | -5.78 | -6.06 | -5.81 | -3.42 | -3.71 | -4.55 | -7.18 | -5.69 | -4.62 | -5.93 | -4.41 | -6.00 | +0.54 | 7.18 |
| média ponderada por KG (pesos<0 = 0) | linhas kg>0 | -3.45 | -6.98 | -6.04 | -3.01 | -6.09 | -5.03 | -4.08 | -5.19 | -3.72 | -2.98 | -6.04 | -3.84 | -5.78 | -6.06 | -5.81 | -3.42 | -3.71 | -4.55 | -7.18 | -5.69 | -4.62 | -5.93 | -4.41 | -6.00 | +0.54 | 7.18 |
| média ponderada por KG (pesos<0 = 0) | linhas FREQ>0 | -3.45 | -6.98 | -6.04 | -3.01 | -6.09 | -5.03 | -4.08 | -5.19 | -3.72 | -2.98 | -6.04 | -3.84 | -5.78 | -6.06 | -5.81 | -3.42 | -3.71 | -4.55 | -7.18 | -5.69 | -4.62 | -5.93 | -4.41 | -6.00 | +0.54 | 7.18 |
| média ponderada por UND (pesos<0 = 0) | todas as linhas | -4.08 | -6.68 | -7.12 | -4.25 | -7.04 | -6.42 | -5.03 | -5.79 | -4.78 | -3.91 | -6.92 | -5.07 | -5.88 | -6.51 | -6.48 | -3.72 | -4.87 | -4.70 | -7.39 | -6.61 | -5.11 | -6.00 | -5.86 | -5.49 | -0.18 | 7.39 |
| média ponderada por UND (pesos<0 = 0) | linhas kg>0 | -4.08 | -6.68 | -7.12 | -4.25 | -7.04 | -6.42 | -5.03 | -5.79 | -4.78 | -3.91 | -6.92 | -5.07 | -5.88 | -6.51 | -6.48 | -3.72 | -4.87 | -4.70 | -7.39 | -6.61 | -5.11 | -6.00 | -5.86 | -5.49 | -0.18 | 7.39 |
| média ponderada por UND (pesos<0 = 0) | linhas FREQ>0 | -4.08 | -6.68 | -7.12 | -4.25 | -7.04 | -6.42 | -5.03 | -5.79 | -4.78 | -3.91 | -6.92 | -5.07 | -5.88 | -6.51 | -6.48 | -3.72 | -4.87 | -4.70 | -7.39 | -6.61 | -5.11 | -6.00 | -5.86 | -5.49 | -0.18 | 7.39 |
| média ponderada por RS (pesos<0 = 0) | todas as linhas | -5.08 | -7.65 | -6.39 | -3.98 | -6.90 | -5.51 | -4.58 | -6.42 | -4.00 | -5.14 | -6.29 | -4.24 | -6.65 | -7.20 | -6.62 | -3.54 | -3.90 | -5.06 | -7.25 | -6.69 | -5.35 | -6.84 | -5.04 | -7.16 | +0.11 | 7.65 |
| média ponderada por RS (pesos<0 = 0) | linhas FREQ>0 | -5.08 | -7.65 | -6.39 | -3.98 | -6.90 | -5.51 | -4.58 | -6.42 | -4.00 | -5.14 | -6.29 | -4.24 | -6.65 | -7.20 | -6.62 | -3.54 | -3.90 | -5.06 | -7.25 | -6.69 | -5.35 | -6.84 | -5.04 | -7.16 | +0.11 | 7.65 |
| média ponderada por RS (pesos<0 = 0) | linhas kg>0 | -5.08 | -7.65 | -6.39 | -3.98 | -6.90 | -5.51 | -4.58 | -6.42 | -4.00 | -5.14 | -6.29 | -4.24 | -6.65 | -7.20 | -6.62 | -3.54 | -3.90 | -5.06 | -7.25 | -6.69 | -5.35 | -6.84 | -5.04 | -7.16 | +0.11 | 7.65 |
| max por par distribuidor×PDV → soma ÷ PDVs distintos | todas as linhas | -7.95 | -9.65 | -7.74 | -6.56 | -7.25 | -7.73 | -7.23 | -8.29 | -8.34 | -6.54 | -7.88 | -7.32 | -8.50 | -8.87 | -7.24 | -6.78 | -6.87 | -7.18 | -8.76 | -7.72 | -7.87 | -6.75 | -8.76 | -8.26 | -1.00 | 9.65 |
| max por par → soma por PDV → média dos PDVs | todas as linhas | -7.95 | -9.65 | -7.74 | -6.56 | -7.25 | -7.73 | -7.23 | -8.29 | -8.34 | -6.54 | -7.88 | -7.32 | -8.50 | -8.87 | -7.24 | -6.78 | -6.87 | -7.18 | -8.76 | -7.72 | -7.87 | -6.75 | -8.76 | -8.26 | -1.00 | 9.65 |
| max por par distribuidor×PDV → soma ÷ PDVs distintos | linhas FREQ>0 | -7.95 | -9.65 | -7.74 | -6.56 | -7.25 | -7.73 | -7.23 | -8.29 | -8.34 | -6.54 | -7.88 | -7.32 | -8.50 | -8.87 | -7.24 | -6.78 | -6.87 | -7.18 | -8.76 | -7.72 | -7.87 | -6.75 | -8.76 | -8.26 | -1.00 | 9.65 |
| max por par → soma por PDV → média dos PDVs | linhas FREQ>0 | -7.95 | -9.65 | -7.74 | -6.56 | -7.25 | -7.73 | -7.23 | -8.29 | -8.34 | -6.54 | -7.88 | -7.32 | -8.50 | -8.87 | -7.24 | -6.78 | -6.87 | -7.18 | -8.76 | -7.72 | -7.87 | -6.75 | -8.76 | -8.26 | -1.00 | 9.65 |
| max por par distribuidor×PDV → soma ÷ PDVs distintos | linhas kg>0 | -7.97 | -9.66 | -7.75 | -6.56 | -7.25 | -7.73 | -7.23 | -8.30 | -8.34 | -6.55 | -7.89 | -7.32 | -8.50 | -8.87 | -7.24 | -6.78 | -6.88 | -7.19 | -8.76 | -7.72 | -7.87 | -6.75 | -8.77 | -8.26 | -1.00 | 9.66 |
| max por par → soma por PDV → média dos PDVs | linhas kg>0 | -7.97 | -9.66 | -7.75 | -6.56 | -7.25 | -7.73 | -7.23 | -8.30 | -8.34 | -6.55 | -7.89 | -7.32 | -8.50 | -8.87 | -7.24 | -6.78 | -6.88 | -7.19 | -8.76 | -7.72 | -7.87 | -6.75 | -8.77 | -8.26 | -1.00 | 9.66 |
| max por PDV (Cód. PDV) → média dos PDVs | todas as linhas | -8.65 | -10.37 | -8.28 | -7.01 | -7.90 | -8.18 | -7.68 | -8.81 | -8.80 | -8.35 | -9.58 | -8.48 | -9.15 | -9.91 | -8.29 | -7.33 | -7.77 | -7.75 | -9.42 | -8.80 | -8.61 | -8.77 | -9.38 | -9.17 | -1.16 | 10.37 |
| max por PDV (Cód. PDV) → média dos PDVs | linhas FREQ>0 | -8.65 | -10.37 | -8.28 | -7.01 | -7.90 | -8.18 | -7.68 | -8.81 | -8.80 | -8.35 | -9.58 | -8.48 | -9.15 | -9.91 | -8.29 | -7.33 | -7.77 | -7.75 | -9.42 | -8.80 | -8.61 | -8.77 | -9.38 | -9.17 | -1.16 | 10.37 |
| max por PDV (Cód. PDV) → média dos PDVs | linhas kg>0 | -8.67 | -10.38 | -8.29 | -7.01 | -7.90 | -8.18 | -7.68 | -8.81 | -8.81 | -8.36 | -9.58 | -8.48 | -9.15 | -9.91 | -8.29 | -7.33 | -7.79 | -7.76 | -9.42 | -8.80 | -8.62 | -8.77 | -9.39 | -9.17 | -1.16 | 10.38 |
| max por par distribuidor×PDV → média dos pares | todas as linhas | -8.74 | -10.49 | -8.35 | -7.05 | -7.98 | -8.23 | -7.74 | -8.88 | -8.87 | -8.37 | -9.79 | -8.65 | -9.24 | -10.07 | -8.41 | -7.40 | -7.87 | -7.81 | -9.51 | -8.93 | -8.70 | -8.97 | -9.48 | -9.28 | -1.16 | 10.49 |
| max por par distribuidor×PDV → média dos pares | linhas FREQ>0 | -8.74 | -10.49 | -8.35 | -7.05 | -7.98 | -8.23 | -7.74 | -8.88 | -8.87 | -8.37 | -9.79 | -8.65 | -9.24 | -10.07 | -8.41 | -7.40 | -7.87 | -7.81 | -9.51 | -8.93 | -8.70 | -8.97 | -9.48 | -9.28 | -1.16 | 10.49 |
| max por par distribuidor×PDV → média dos pares | linhas kg>0 | -8.76 | -10.50 | -8.37 | -7.05 | -7.98 | -8.23 | -7.74 | -8.89 | -8.87 | -8.39 | -9.79 | -8.65 | -9.24 | -10.07 | -8.41 | -7.40 | -7.89 | -7.81 | -9.51 | -8.93 | -8.70 | -8.97 | -9.49 | -9.28 | -1.16 | 10.50 |
| (max por par → média) por distribuidor → média dos distribuidores | todas as linhas | -8.98 | -10.91 | -9.07 | -7.44 | -7.55 | -8.13 | -7.84 | -8.92 | -9.18 | -8.45 | -9.72 | -8.48 | -9.45 | -10.38 | -8.68 | -7.47 | -8.02 | -8.16 | -9.39 | -9.34 | -8.96 | -9.06 | -9.78 | -9.15 | -1.18 | 10.91 |
| (max por par → média) por distribuidor → média dos distribuidores | linhas FREQ>0 | -8.98 | -10.91 | -9.07 | -7.44 | -7.55 | -8.13 | -7.84 | -8.92 | -9.18 | -8.45 | -9.72 | -8.48 | -9.45 | -10.38 | -8.68 | -7.47 | -8.02 | -8.16 | -9.39 | -9.34 | -8.96 | -9.06 | -9.78 | -9.15 | -1.18 | 10.91 |
| (max por par → média) por distribuidor → média dos distribuidores | linhas kg>0 | -9.00 | -10.92 | -9.08 | -7.44 | -7.55 | -8.13 | -7.84 | -8.92 | -9.19 | -8.47 | -9.72 | -8.48 | -9.45 | -10.38 | -8.68 | -7.47 | -8.03 | -8.17 | -9.39 | -9.34 | -8.96 | -9.06 | -9.79 | -9.15 | -1.18 | 10.92 |
| max por CNPJ Reduzido → média | todas as linhas | -9.50 | -11.29 | -9.00 | -7.42 | -8.62 | -9.07 | -8.46 | -9.57 | -9.69 | -9.23 | -10.59 | -9.35 | -10.07 | -10.84 | -9.07 | -8.02 | -8.62 | -8.45 | -10.18 | -9.58 | -9.46 | -9.62 | -10.25 | -9.86 | -1.17 | 11.29 |
| max por CNPJ Reduzido → média | linhas FREQ>0 | -9.50 | -11.29 | -9.00 | -7.42 | -8.62 | -9.07 | -8.46 | -9.57 | -9.69 | -9.23 | -10.59 | -9.35 | -10.07 | -10.84 | -9.07 | -8.02 | -8.62 | -8.45 | -10.18 | -9.58 | -9.46 | -9.62 | -10.25 | -9.86 | -1.17 | 11.29 |
| max por CNPJ Reduzido → média | linhas kg>0 | -9.52 | -11.30 | -9.01 | -7.42 | -8.62 | -9.07 | -8.46 | -9.58 | -9.69 | -9.25 | -10.59 | -9.35 | -10.07 | -10.84 | -9.07 | -8.02 | -8.63 | -8.45 | -10.18 | -9.58 | -9.46 | -9.62 | -10.27 | -9.86 | -1.17 | 11.30 |
| média simples das linhas | todas as linhas | -14.98 | -17.75 | -14.68 | -11.84 | -13.87 | -13.81 | -13.13 | -15.35 | -15.17 | -14.55 | -17.12 | -14.99 | -15.71 | -16.84 | -14.13 | -12.13 | -13.10 | -13.24 | -15.64 | -14.84 | -14.21 | -15.07 | -16.05 | -14.72 | -1.59 | 17.75 |
| soma das linhas ÷ linhas | todas as linhas | -14.98 | -17.75 | -14.68 | -11.84 | -13.87 | -13.81 | -13.13 | -15.35 | -15.17 | -14.55 | -17.12 | -14.99 | -15.71 | -16.84 | -14.13 | -12.13 | -13.10 | -13.24 | -15.64 | -14.84 | -14.21 | -15.07 | -16.05 | -14.72 | -1.59 | 17.75 |
| soma das linhas ÷ soma de '# PDVs Positivados' das linhas | todas as linhas | -14.98 | -17.75 | -14.68 | -11.84 | -13.87 | -13.81 | -13.13 | -15.35 | -15.17 | -14.55 | -17.12 | -14.99 | — | — | — | — | — | — | — | — | — | — | — | — | — | 17.75 |
| média simples das linhas | linhas FREQ>0 | -14.98 | -17.75 | -14.68 | -11.84 | -13.87 | -13.81 | -13.13 | -15.35 | -15.17 | -14.55 | -17.12 | -14.99 | -15.71 | -16.84 | -14.13 | -12.13 | -13.10 | -13.24 | -15.64 | -14.84 | -14.21 | -15.07 | -16.05 | -14.72 | -1.59 | 17.75 |
| soma das linhas ÷ linhas | linhas FREQ>0 | -14.98 | -17.75 | -14.68 | -11.84 | -13.87 | -13.81 | -13.13 | -15.35 | -15.17 | -14.55 | -17.12 | -14.99 | -15.71 | -16.84 | -14.13 | -12.13 | -13.10 | -13.24 | -15.64 | -14.84 | -14.21 | -15.07 | -16.05 | -14.72 | -1.59 | 17.75 |
| soma das linhas ÷ soma de '# PDVs Positivados' das linhas | linhas FREQ>0 | -14.98 | -17.75 | -14.68 | -11.84 | -13.87 | -13.81 | -13.13 | -15.35 | -15.17 | -14.55 | -17.12 | -14.99 | — | — | — | — | — | — | — | — | — | — | — | — | — | 17.75 |
| média simples das linhas | linhas kg>0 | -14.99 | -17.75 | -14.69 | -11.84 | -13.87 | -13.81 | -13.13 | -15.36 | -15.18 | -14.56 | -17.12 | -14.99 | -15.71 | -16.84 | -14.13 | -12.13 | -13.10 | -13.25 | -15.65 | -14.84 | -14.21 | -15.07 | -16.05 | -14.72 | -1.59 | 17.75 |
| soma das linhas ÷ linhas | linhas kg>0 | -14.99 | -17.75 | -14.69 | -11.84 | -13.87 | -13.81 | -13.13 | -15.36 | -15.18 | -14.56 | -17.12 | -14.99 | -15.71 | -16.84 | -14.13 | -12.13 | -13.10 | -13.25 | -15.65 | -14.84 | -14.21 | -15.07 | -16.05 | -14.72 | -1.59 | 17.75 |
| soma das linhas ÷ soma de '# PDVs Positivados' das linhas | linhas kg>0 | -14.99 | -17.75 | -14.69 | -11.84 | -13.87 | -13.81 | -13.13 | -15.36 | -15.18 | -14.56 | -17.12 | -14.99 | — | — | — | — | — | — | — | — | — | — | — | — | — | 17.75 |
| mean por par distribuidor×PDV → soma ÷ PDVs distintos | todas as linhas | -15.43 | -18.51 | -15.30 | -12.27 | -14.10 | -14.44 | -13.87 | -16.25 | -16.12 | -13.96 | -16.71 | -15.12 | -16.41 | -17.13 | -14.01 | -12.69 | -13.13 | -13.70 | -16.21 | -14.84 | -14.89 | -14.25 | -17.10 | -15.19 | -1.72 | 18.51 |
| mean por par distribuidor×PDV → soma ÷ PDVs distintos | linhas FREQ>0 | -15.43 | -18.51 | -15.30 | -12.27 | -14.10 | -14.44 | -13.87 | -16.25 | -16.12 | -13.96 | -16.71 | -15.12 | -16.41 | -17.13 | -14.01 | -12.69 | -13.13 | -13.70 | -16.21 | -14.84 | -14.89 | -14.25 | -17.10 | -15.19 | -1.72 | 18.51 |
| mean por par distribuidor×PDV → soma ÷ PDVs distintos | linhas kg>0 | -15.43 | -18.51 | -15.31 | -12.27 | -14.10 | -14.44 | -13.87 | -16.25 | -16.12 | -13.97 | -16.71 | -15.12 | -16.41 | -17.13 | -14.01 | -12.69 | -13.13 | -13.71 | -16.21 | -14.84 | -14.89 | -14.25 | -17.11 | -15.19 | -1.72 | 18.51 |
| mean por PDV (Cód. PDV) → média dos PDVs | todas as linhas | -16.14 | -19.25 | -15.85 | -12.72 | -14.77 | -14.89 | -14.33 | -16.77 | -16.59 | -15.67 | -18.42 | -16.30 | -17.08 | -18.19 | -15.07 | -13.25 | -14.06 | -14.28 | -16.88 | -15.95 | -15.66 | -16.24 | -17.74 | -16.11 | -1.88 | 19.25 |
| mean por PDV (Cód. PDV) → média dos PDVs | linhas FREQ>0 | -16.14 | -19.25 | -15.85 | -12.72 | -14.77 | -14.89 | -14.33 | -16.77 | -16.59 | -15.67 | -18.42 | -16.30 | -17.08 | -18.19 | -15.07 | -13.25 | -14.06 | -14.28 | -16.88 | -15.95 | -15.66 | -16.24 | -17.74 | -16.11 | -1.88 | 19.25 |
| mean por PDV (Cód. PDV) → média dos PDVs | linhas kg>0 | -16.15 | -19.25 | -15.86 | -12.72 | -14.77 | -14.89 | -14.33 | -16.78 | -16.59 | -15.68 | -18.42 | -16.30 | -17.08 | -18.19 | -15.07 | -13.25 | -14.06 | -14.28 | -16.88 | -15.95 | -15.66 | -16.24 | -17.75 | -16.11 | -1.88 | 19.25 |
| mean por par distribuidor×PDV → média dos pares | todas as linhas | -16.15 | -19.27 | -15.86 | -12.73 | -14.78 | -14.90 | -14.34 | -16.79 | -16.60 | -15.65 | -18.43 | -16.34 | -17.08 | -18.22 | -15.09 | -13.27 | -14.06 | -14.28 | -16.89 | -15.95 | -15.66 | -16.29 | -17.75 | -16.13 | -1.88 | 19.27 |
| mean por par distribuidor×PDV → média dos pares | linhas FREQ>0 | -16.15 | -19.27 | -15.86 | -12.73 | -14.78 | -14.90 | -14.34 | -16.79 | -16.60 | -15.65 | -18.43 | -16.34 | -17.08 | -18.22 | -15.09 | -13.27 | -14.06 | -14.28 | -16.89 | -15.95 | -15.66 | -16.29 | -17.75 | -16.13 | -1.88 | 19.27 |
| mean por par distribuidor×PDV → média dos pares | linhas kg>0 | -16.16 | -19.27 | -15.87 | -12.73 | -14.78 | -14.90 | -14.34 | -16.79 | -16.60 | -15.67 | -18.43 | -16.34 | -17.08 | -18.22 | -15.09 | -13.27 | -14.07 | -14.29 | -16.89 | -15.95 | -15.66 | -16.29 | -17.76 | -16.13 | -1.88 | 19.27 |
| soma ÷ PDVs distintos por SKU → média dos SKUs | todas as linhas | -16.16 | -19.32 | -15.80 | -12.20 | -14.86 | -14.81 | -14.01 | -16.06 | -16.18 | -13.85 | -17.52 | -15.24 | -16.22 | -17.12 | -14.49 | -12.87 | -13.72 | -13.74 | -16.04 | -14.91 | -13.04 | -14.98 | -16.86 | -15.48 | -1.43 | 19.32 |
| soma ÷ PDVs distintos por SKU → média dos SKUs | linhas FREQ>0 | -16.16 | -19.32 | -15.80 | -12.20 | -14.86 | -14.81 | -14.01 | -16.06 | -16.18 | -13.85 | -17.52 | -15.24 | -16.22 | -17.12 | -14.49 | -12.87 | -13.72 | -13.74 | -16.04 | -14.91 | -13.04 | -14.98 | -16.86 | -15.48 | -1.43 | 19.32 |
| soma ÷ PDVs distintos por SKU → média dos SKUs | linhas kg>0 | -16.19 | -19.32 | -15.80 | -12.20 | -14.86 | -14.81 | -14.01 | -16.07 | -16.18 | -13.86 | -17.52 | -15.24 | -16.22 | -17.12 | -14.49 | -12.87 | -13.73 | -13.74 | -16.04 | -14.91 | -13.04 | -14.98 | -16.87 | -15.48 | -1.43 | 19.32 |
| média por SKU → média dos SKUs | todas as linhas | -16.19 | -19.38 | -15.82 | -12.21 | -14.94 | -14.83 | -14.03 | -16.13 | -16.21 | -14.80 | -18.16 | -15.61 | -16.24 | -17.42 | -14.79 | -12.89 | -14.00 | -13.77 | -16.06 | -15.19 | -13.22 | -16.17 | -16.92 | -15.56 | -1.43 | 19.38 |
| média por SKU → média dos SKUs | linhas FREQ>0 | -16.19 | -19.38 | -15.82 | -12.21 | -14.94 | -14.83 | -14.03 | -16.13 | -16.21 | -14.80 | -18.16 | -15.61 | -16.24 | -17.42 | -14.79 | -12.89 | -14.00 | -13.77 | -16.06 | -15.19 | -13.22 | -16.17 | -16.92 | -15.56 | -1.43 | 19.38 |
| média por SKU → média dos SKUs | linhas kg>0 | -16.22 | -19.38 | -15.83 | -12.21 | -14.94 | -14.83 | -14.03 | -16.13 | -16.21 | -14.81 | -18.16 | -15.61 | -16.24 | -17.42 | -14.79 | -12.89 | -14.01 | -13.77 | -16.06 | -15.19 | -13.22 | -16.17 | -16.93 | -15.56 | -1.43 | 19.38 |
| median por par distribuidor×PDV → soma ÷ PDVs distintos | todas as linhas | -16.83 | -20.16 | -16.74 | -13.31 | -15.38 | -15.68 | -15.08 | -17.74 | -17.53 | -15.38 | -18.37 | -16.55 | -17.85 | -18.68 | -15.30 | -13.73 | -14.26 | -14.91 | -17.58 | -16.16 | -16.19 | -15.65 | -18.65 | -16.53 | -1.83 | 20.16 |
| median por par distribuidor×PDV → soma ÷ PDVs distintos | linhas FREQ>0 | -16.83 | -20.16 | -16.74 | -13.31 | -15.38 | -15.68 | -15.08 | -17.74 | -17.53 | -15.38 | -18.37 | -16.55 | -17.85 | -18.68 | -15.30 | -13.73 | -14.26 | -14.91 | -17.58 | -16.16 | -16.19 | -15.65 | -18.65 | -16.53 | -1.83 | 20.16 |
| median por par distribuidor×PDV → soma ÷ PDVs distintos | linhas kg>0 | -16.83 | -20.17 | -16.74 | -13.31 | -15.38 | -15.68 | -15.08 | -17.75 | -17.53 | -15.39 | -18.37 | -16.55 | -17.85 | -18.68 | -15.30 | -13.73 | -14.27 | -14.91 | -17.58 | -16.16 | -16.19 | -15.65 | -18.66 | -16.53 | -1.83 | 20.17 |
| median por par distribuidor×PDV → média dos pares | todas as linhas | -17.55 | -20.90 | -17.29 | -13.77 | -16.05 | -16.13 | -15.54 | -18.27 | -18.00 | -17.04 | -20.06 | -17.75 | -18.51 | -19.74 | -16.37 | -14.29 | -15.19 | -15.48 | -18.25 | -17.25 | -16.95 | -17.66 | -19.29 | -17.45 | -1.99 | 20.90 |
| median por par distribuidor×PDV → média dos pares | linhas FREQ>0 | -17.55 | -20.90 | -17.29 | -13.77 | -16.05 | -16.13 | -15.54 | -18.27 | -18.00 | -17.04 | -20.06 | -17.75 | -18.51 | -19.74 | -16.37 | -14.29 | -15.19 | -15.48 | -18.25 | -17.25 | -16.95 | -17.66 | -19.29 | -17.45 | -1.99 | 20.90 |
| median por par distribuidor×PDV → média dos pares | linhas kg>0 | -17.55 | -20.90 | -17.30 | -13.77 | -16.05 | -16.13 | -15.54 | -18.28 | -18.01 | -17.05 | -20.06 | -17.75 | -18.51 | -19.75 | -16.37 | -14.29 | -15.19 | -15.49 | -18.26 | -17.25 | -16.95 | -17.66 | -19.30 | -17.45 | -1.99 | 20.90 |
| min por par distribuidor×PDV → soma ÷ PDVs distintos | todas as linhas | -18.24 | -21.85 | -18.16 | -14.48 | -16.71 | -16.96 | -16.35 | -19.26 | -19.01 | -16.79 | -20.12 | -18.12 | -19.48 | -20.32 | -16.57 | -15.19 | -15.56 | -16.17 | -19.06 | -17.48 | -17.47 | -17.08 | -20.33 | -17.78 | -2.07 | 21.85 |
| first por par distribuidor×PDV → soma ÷ PDVs distintos | todas as linhas | -18.24 | -21.85 | -18.16 | -14.48 | -16.71 | -16.96 | -16.35 | -19.26 | -19.01 | -16.79 | -20.12 | -18.12 | -19.48 | -20.32 | -16.57 | -15.19 | -15.56 | -16.17 | -19.06 | -17.48 | -17.47 | -17.08 | -20.33 | -17.78 | -2.07 | 21.85 |
| min por par distribuidor×PDV → soma ÷ PDVs distintos | linhas FREQ>0 | -18.24 | -21.85 | -18.16 | -14.48 | -16.71 | -16.96 | -16.35 | -19.26 | -19.01 | -16.79 | -20.12 | -18.12 | -19.48 | -20.32 | -16.57 | -15.19 | -15.56 | -16.17 | -19.06 | -17.48 | -17.47 | -17.08 | -20.33 | -17.78 | -2.07 | 21.85 |
| first por par distribuidor×PDV → soma ÷ PDVs distintos | linhas FREQ>0 | -18.24 | -21.85 | -18.16 | -14.48 | -16.71 | -16.96 | -16.35 | -19.26 | -19.01 | -16.79 | -20.12 | -18.12 | -19.48 | -20.32 | -16.57 | -15.19 | -15.56 | -16.17 | -19.06 | -17.48 | -17.47 | -17.08 | -20.33 | -17.78 | -2.07 | 21.85 |
| min por par distribuidor×PDV → soma ÷ PDVs distintos | linhas kg>0 | -18.24 | -21.85 | -18.17 | -14.48 | -16.71 | -16.96 | -16.35 | -19.26 | -19.01 | -16.80 | -20.12 | -18.12 | -19.48 | -20.32 | -16.57 | -15.19 | -15.56 | -16.17 | -19.06 | -17.48 | -17.47 | -17.08 | -20.34 | -17.78 | -2.07 | 21.85 |
| first por par distribuidor×PDV → soma ÷ PDVs distintos | linhas kg>0 | -18.24 | -21.85 | -18.17 | -14.48 | -16.71 | -16.96 | -16.35 | -19.26 | -19.01 | -16.80 | -20.12 | -18.12 | -19.48 | -20.32 | -16.57 | -15.19 | -15.56 | -16.17 | -19.06 | -17.48 | -17.47 | -17.08 | -20.34 | -17.78 | -2.07 | 21.85 |
| min por par distribuidor×PDV → média dos pares | todas as linhas | -18.94 | -22.58 | -18.71 | -14.93 | -17.37 | -17.40 | -16.80 | -19.78 | -19.48 | -18.42 | -21.78 | -19.30 | -20.12 | -21.36 | -17.62 | -15.74 | -16.47 | -16.73 | -19.72 | -18.56 | -18.22 | -19.06 | -20.96 | -18.69 | -2.23 | 22.58 |
| first por par distribuidor×PDV → média dos pares | todas as linhas | -18.94 | -22.58 | -18.71 | -14.93 | -17.37 | -17.40 | -16.80 | -19.78 | -19.48 | -18.42 | -21.78 | -19.30 | -20.12 | -21.36 | -17.62 | -15.74 | -16.47 | -16.73 | -19.72 | -18.56 | -18.22 | -19.06 | -20.96 | -18.69 | -2.23 | 22.58 |
| min por par distribuidor×PDV → média dos pares | linhas FREQ>0 | -18.94 | -22.58 | -18.71 | -14.93 | -17.37 | -17.40 | -16.80 | -19.78 | -19.48 | -18.42 | -21.78 | -19.30 | -20.12 | -21.36 | -17.62 | -15.74 | -16.47 | -16.73 | -19.72 | -18.56 | -18.22 | -19.06 | -20.96 | -18.69 | -2.23 | 22.58 |
| first por par distribuidor×PDV → média dos pares | linhas FREQ>0 | -18.94 | -22.58 | -18.71 | -14.93 | -17.37 | -17.40 | -16.80 | -19.78 | -19.48 | -18.42 | -21.78 | -19.30 | -20.12 | -21.36 | -17.62 | -15.74 | -16.47 | -16.73 | -19.72 | -18.56 | -18.22 | -19.06 | -20.96 | -18.69 | -2.23 | 22.58 |
| min por par distribuidor×PDV → média dos pares | linhas kg>0 | -18.94 | -22.58 | -18.72 | -14.93 | -17.37 | -17.40 | -16.80 | -19.79 | -19.48 | -18.43 | -21.78 | -19.30 | -20.12 | -21.36 | -17.62 | -15.74 | -16.48 | -16.73 | -19.72 | -18.56 | -18.22 | -19.06 | -20.97 | -18.69 | -2.23 | 22.58 |
| first por par distribuidor×PDV → média dos pares | linhas kg>0 | -18.94 | -22.58 | -18.72 | -14.93 | -17.37 | -17.40 | -16.80 | -19.79 | -19.48 | -18.43 | -21.78 | -19.30 | -20.12 | -21.36 | -17.62 | -15.74 | -16.48 | -16.73 | -19.72 | -18.56 | -18.22 | -19.06 | -20.97 | -18.69 | -2.23 | 22.58 |
| min por PDV (Cód. PDV) → média dos PDVs | todas as linhas | -18.95 | -22.59 | -18.71 | -14.92 | -17.37 | -17.41 | -16.81 | -19.78 | -19.48 | -18.45 | -21.81 | -19.30 | -20.15 | -21.37 | -17.64 | -15.75 | -16.48 | -16.73 | -19.73 | -18.58 | -18.23 | -19.06 | -20.97 | -18.69 | -2.23 | 22.59 |
| min por PDV (Cód. PDV) → média dos PDVs | linhas kg>0 | -18.95 | -22.59 | -18.72 | -14.92 | -17.37 | -17.41 | -16.81 | -19.79 | -19.48 | -18.46 | -21.81 | -19.30 | -20.15 | -21.37 | -17.64 | -15.75 | -16.48 | -16.74 | -19.73 | -18.58 | -18.24 | -19.06 | -20.98 | -18.69 | -2.23 | 22.59 |
| min por PDV (Cód. PDV) → média dos PDVs | linhas FREQ>0 | -18.95 | -22.59 | -18.71 | -14.92 | -17.37 | -17.41 | -16.81 | -19.78 | -19.48 | -18.45 | -21.81 | -19.30 | -20.15 | -21.37 | -17.64 | -15.75 | -16.48 | -16.73 | -19.73 | -18.58 | -18.23 | -19.06 | -20.97 | -18.69 | -2.23 | 22.59 |
| max por SKU → média dos SKUs | linhas kg>0 | +187.17 | +161.85 | +162.85 | +149.58 | +154.91 | +158.75 | +212.59 | +204.94 | +235.85 | +250.79 | +251.23 | +227.92 | +285.98 | +279.64 | +239.06 | +186.68 | +193.89 | +193.96 | +221.50 | +219.99 | +233.86 | +218.97 | +305.95 | +253.97 | +102.60 | 305.95 |
| max por SKU → média dos SKUs | todas as linhas | +187.46 | +161.85 | +162.85 | +149.58 | +154.91 | +158.75 | +212.59 | +204.94 | +235.85 | +251.12 | +251.23 | +227.92 | +285.98 | +279.64 | +239.06 | +186.68 | +193.89 | +193.96 | +221.50 | +219.99 | +233.86 | +218.97 | +306.30 | +253.97 | +102.60 | 306.30 |
| max por SKU → média dos SKUs | linhas FREQ>0 | +187.46 | +161.85 | +162.85 | +149.58 | +154.91 | +158.75 | +212.59 | +204.94 | +235.85 | +251.12 | +251.23 | +227.92 | +285.98 | +279.64 | +239.06 | +186.68 | +193.89 | +193.96 | +221.50 | +219.99 | +233.86 | +218.97 | +306.30 | +253.97 | +102.60 | 306.30 |
| (soma ÷ PDVs) por distribuidor → média dos distribuidores | todas as linhas | +470.97 | +459.41 | +469.74 | +476.33 | +475.23 | +461.68 | +467.12 | +442.51 | +457.73 | +457.62 | +462.31 | +470.11 | +452.95 | +436.29 | +467.20 | +465.78 | +470.29 | +448.02 | +444.17 | +450.59 | +468.37 | +451.09 | +469.96 | +456.90 | +450.90 | 476.33 |
| (soma ÷ PDVs) por distribuidor → média dos distribuidores | linhas kg>0 | +470.90 | +459.24 | +469.68 | +476.33 | +475.23 | +461.68 | +467.12 | +442.50 | +457.71 | +457.59 | +462.29 | +470.10 | +452.95 | +436.28 | +467.20 | +465.78 | +470.28 | +447.92 | +444.19 | +450.59 | +468.37 | +451.09 | +469.93 | +456.90 | +450.90 | 476.33 |
| (soma ÷ PDVs) por distribuidor → média dos distribuidores | linhas FREQ>0 | +470.97 | +459.41 | +469.74 | +476.33 | +475.23 | +461.68 | +467.12 | +442.51 | +457.73 | +457.62 | +462.31 | +470.11 | +452.95 | +436.29 | +467.20 | +465.78 | +470.29 | +448.02 | +444.17 | +450.59 | +468.37 | +451.09 | +469.96 | +456.90 | +450.90 | 476.33 |
| soma das linhas ÷ pares distribuidor×PDV | linhas kg>0 | +506.24 | +493.93 | +513.83 | +511.33 | +509.80 | +497.51 | +510.61 | +478.86 | +493.21 | +482.32 | +487.32 | +500.42 | +486.33 | +462.18 | +482.00 | +490.90 | +491.10 | +468.13 | +466.35 | +467.44 | +484.40 | +473.67 | +486.90 | +476.43 | +464.66 | 513.83 |
| sum por par distribuidor×PDV → média dos pares | linhas kg>0 | +506.24 | +493.93 | +513.83 | +511.33 | +509.80 | +497.51 | +510.61 | +478.86 | +493.21 | +482.32 | +487.32 | +500.42 | +486.33 | +462.18 | +482.00 | +490.90 | +491.10 | +468.13 | +466.35 | +467.44 | +484.40 | +473.67 | +486.90 | +476.43 | +464.66 | 513.83 |
| soma das linhas ÷ pares distribuidor×PDV | todas as linhas | +506.31 | +494.00 | +513.90 | +511.33 | +509.80 | +497.51 | +510.61 | +478.87 | +493.25 | +482.33 | +487.34 | +500.42 | +486.33 | +462.19 | +482.00 | +490.90 | +491.13 | +468.22 | +466.35 | +467.44 | +484.40 | +473.67 | +486.92 | +476.43 | +464.66 | 513.90 |
| sum por par distribuidor×PDV → média dos pares | todas as linhas | +506.31 | +494.00 | +513.90 | +511.33 | +509.80 | +497.51 | +510.61 | +478.87 | +493.25 | +482.33 | +487.34 | +500.42 | +486.33 | +462.19 | +482.00 | +490.90 | +491.13 | +468.22 | +466.35 | +467.44 | +484.40 | +473.67 | +486.92 | +476.43 | +464.66 | 513.90 |
| soma das linhas ÷ pares distribuidor×PDV | linhas FREQ>0 | +506.31 | +494.00 | +513.90 | +511.33 | +509.80 | +497.51 | +510.61 | +478.87 | +493.25 | +482.33 | +487.34 | +500.42 | +486.33 | +462.19 | +482.00 | +490.90 | +491.13 | +468.22 | +466.35 | +467.44 | +484.40 | +473.67 | +486.92 | +476.43 | +464.66 | 513.90 |
| sum por par distribuidor×PDV → média dos pares | linhas FREQ>0 | +506.31 | +494.00 | +513.90 | +511.33 | +509.80 | +497.51 | +510.61 | +478.87 | +493.25 | +482.33 | +487.34 | +500.42 | +486.33 | +462.19 | +482.00 | +490.90 | +491.13 | +468.22 | +466.35 | +467.44 | +484.40 | +473.67 | +486.92 | +476.43 | +464.66 | 513.90 |
| soma das linhas ÷ PDVs positivados da linha de total | linhas kg>0 | +511.48 | +499.48 | +517.89 | +514.56 | +514.67 | +500.74 | +513.98 | +482.60 | +496.62 | +493.92 | +499.73 | +509.18 | — | — | — | — | — | — | — | — | — | — | — | — | — | 517.89 |
| soma das linhas ÷ PDVs distintos (Cód. PDV) | linhas kg>0 | +511.49 | +499.48 | +517.95 | +514.56 | +514.67 | +500.74 | +513.98 | +482.63 | +496.63 | +494.01 | +499.73 | +509.18 | +491.06 | +469.65 | +489.43 | +494.81 | +497.56 | +471.99 | +471.01 | +474.94 | +489.72 | +487.67 | +491.55 | +482.88 | +465.58 | 517.95 |
| sum por par distribuidor×PDV → soma ÷ PDVs distintos | linhas kg>0 | +511.49 | +499.48 | +517.95 | +514.56 | +514.67 | +500.74 | +513.98 | +482.63 | +496.63 | +494.01 | +499.73 | +509.18 | +491.06 | +469.65 | +489.43 | +494.81 | +497.56 | +471.99 | +471.01 | +474.94 | +489.72 | +487.67 | +491.55 | +482.88 | +465.58 | 517.95 |
| sum por PDV (Cód. PDV) → média dos PDVs | linhas kg>0 | +511.49 | +499.48 | +517.95 | +514.56 | +514.67 | +500.74 | +513.98 | +482.63 | +496.63 | +494.01 | +499.73 | +509.18 | +491.06 | +469.65 | +489.43 | +494.81 | +497.56 | +471.99 | +471.01 | +474.94 | +489.72 | +487.67 | +491.55 | +482.88 | +465.58 | 517.95 |
| soma das linhas ÷ PDVs distintos (Cód. PDV) | todas as linhas | +511.56 | +499.56 | +518.03 | +514.56 | +514.67 | +500.74 | +513.98 | +482.64 | +496.67 | +494.02 | +499.75 | +509.18 | +491.06 | +469.66 | +489.43 | +494.81 | +497.59 | +472.07 | +471.01 | +474.94 | +489.71 | +487.67 | +491.57 | +482.88 | +465.58 | 518.03 |
| soma das linhas ÷ PDVs positivados da linha de total | todas as linhas | +511.56 | +499.56 | +518.03 | +514.56 | +514.67 | +500.74 | +513.98 | +482.64 | +496.67 | +494.02 | +499.75 | +509.18 | — | — | — | — | — | — | — | — | — | — | — | — | — | 518.03 |
| sum por par distribuidor×PDV → soma ÷ PDVs distintos | todas as linhas | +511.56 | +499.56 | +518.03 | +514.56 | +514.67 | +500.74 | +513.98 | +482.64 | +496.67 | +494.02 | +499.75 | +509.18 | +491.06 | +469.66 | +489.43 | +494.81 | +497.59 | +472.07 | +471.01 | +474.94 | +489.71 | +487.67 | +491.57 | +482.88 | +465.58 | 518.03 |
| sum por PDV (Cód. PDV) → média dos PDVs | todas as linhas | +511.56 | +499.56 | +518.03 | +514.56 | +514.67 | +500.74 | +513.98 | +482.64 | +496.67 | +494.02 | +499.75 | +509.18 | +491.06 | +469.66 | +489.43 | +494.81 | +497.59 | +472.07 | +471.01 | +474.94 | +489.71 | +487.67 | +491.57 | +482.88 | +465.58 | 518.03 |
| soma das linhas ÷ PDVs distintos (Cód. PDV) | linhas FREQ>0 | +511.56 | +499.56 | +518.03 | +514.56 | +514.67 | +500.74 | +513.98 | +482.64 | +496.67 | +494.02 | +499.75 | +509.18 | +491.06 | +469.66 | +489.43 | +494.81 | +497.59 | +472.07 | +471.01 | +474.94 | +489.71 | +487.67 | +491.57 | +482.88 | +465.58 | 518.03 |
| soma das linhas ÷ PDVs positivados da linha de total | linhas FREQ>0 | +511.56 | +499.56 | +518.03 | +514.56 | +514.67 | +500.74 | +513.98 | +482.64 | +496.67 | +494.02 | +499.75 | +509.18 | — | — | — | — | — | — | — | — | — | — | — | — | — | 518.03 |
| sum por par distribuidor×PDV → soma ÷ PDVs distintos | linhas FREQ>0 | +511.56 | +499.56 | +518.03 | +514.56 | +514.67 | +500.74 | +513.98 | +482.64 | +496.67 | +494.02 | +499.75 | +509.18 | +491.06 | +469.66 | +489.43 | +494.81 | +497.59 | +472.07 | +471.01 | +474.94 | +489.71 | +487.67 | +491.57 | +482.88 | +465.58 | 518.03 |
| sum por PDV (Cód. PDV) → média dos PDVs | linhas FREQ>0 | +511.56 | +499.56 | +518.03 | +514.56 | +514.67 | +500.74 | +513.98 | +482.64 | +496.67 | +494.02 | +499.75 | +509.18 | +491.06 | +469.66 | +489.43 | +494.81 | +497.59 | +472.07 | +471.01 | +474.94 | +489.71 | +487.67 | +491.57 | +482.88 | +465.58 | 518.03 |
| soma das linhas ÷ CNPJ Reduzido distintos | linhas kg>0 | +569.40 | +554.61 | +578.97 | +578.13 | +573.58 | +560.36 | +574.18 | +539.43 | +554.30 | +550.62 | +558.12 | +567.98 | +549.81 | +525.68 | +548.15 | +559.25 | +554.19 | +528.40 | +527.42 | +530.96 | +545.09 | +542.51 | +544.31 | +536.58 | +516.04 | 578.97 |
| soma das linhas ÷ CNPJ Reduzido distintos | todas as linhas | +569.47 | +554.69 | +579.05 | +578.13 | +573.58 | +560.36 | +574.18 | +539.44 | +554.34 | +550.63 | +558.14 | +567.98 | +549.81 | +525.69 | +548.16 | +559.25 | +554.23 | +528.49 | +527.42 | +530.96 | +545.07 | +542.51 | +544.32 | +536.58 | +516.04 | 579.05 |
| soma das linhas ÷ CNPJ Reduzido distintos | linhas FREQ>0 | +569.47 | +554.69 | +579.05 | +578.13 | +573.58 | +560.36 | +574.18 | +539.44 | +554.34 | +550.63 | +558.14 | +567.98 | +549.81 | +525.69 | +548.16 | +559.25 | +554.23 | +528.49 | +527.42 | +530.96 | +545.07 | +542.51 | +544.32 | +536.58 | +516.04 | 579.05 |

## Anexo B · Arquivos de apoio (scratchpad `…\scratchpad\freq\`)

`out/<arquivo>.json` (todas as medidas por arquivo) · `out/item8_por_mes.csv` · `out/item8_linhas_por_mes.csv` ·
`out/item8_dist_mes_diferencas.csv` · `out/item8_linhas_so_de_um_lado_por_dist.csv` · `out/item8_mudancas_metrica_por_mes.csv` ·
`out/item8_amostra_linhas_metrica_diferente.csv` · `out/item8_publicado_dist_x_nova.csv` · `out/item8_base_ativa_dn.csv` · `out/tabelas.md`

---

## 12. Respostas do Douglas às perguntas da §11 (13/09/2026)

| # | Tema | Resposta / decisão | Consequência registrada para a Etapa 2 (nada implementado) |
|---|---|---|---|
| 1 | Significado do campo | Frequência = nº de **atendimentos** do PDV no mês; atendimento = **uma NF**. PDV que compra SKUs diferentes em NFs diferentes tem frequência > 1. **Devolução não deveria contar como compra** | A hipótese H1 da §9 passa a definição de negócio (dada pelo Douglas, não medida nas bases) |
| 2 | Extração no grão PDV | **Não é possível obter da Mtrix** (só vem por SKU) | Frequência do PDV e da categoria **não é calculável exatamente** das bases; a Etapa 2 testa aproximações/limites contra a linha de total (único gabarito medido) e declara o erro |
| 3 | PDV em mais de um distribuidor | **As duas:** frequência do PDV **por distribuidor** (NFs daquele distribuidor) na visão distribuidor; **no canal** (NFs de todos os distribuidores) de supervisor para cima, PDV contado uma vez por nível (RN-10) | Duas réguas, uma por nível |
| 4 | `# PDVs Positivados` | **Tirar das colunas obrigatórias** | Proposta de config + ficha; aviso informativo só onde a coluna existir (set/24–ago/25) |
| 5 | SBM COMÉRCIO (01026770000176, set/24) | **Douglas inclui no `Distribuidores_DePara.xlsx`** | Reconferir de-para e Hierarquia antes de rodar |
| 6 | Série | **Carregar os 25 meses e exibir 12**, com **seletor em todas as abas**: "Últimos 12 meses" (padrão) · "Série completa" · anos conforme o toggle fiscal/civil (fiscal: set/24–ago/25 · set/25–ago/26 · set/26 em diante; civil: 2024 · 2025 · 2026) | Medir tamanho do HTML (limite 12 MB), validações e quais abas fazem sentido (Penetração/Matriz usam mês fechado) |
| 7 | Linhas novas DIERO (jul/25–jun/26) e PELLAH (jul/26) | **Corretas; mudança nos publicados aceita** (base ativa ago/26 124.600 → 124.800; DN 57,37% → 57,27%) | Atualizar a tabela de referência do RETOMADA após a carga |
| 8 | Linhas kg ≤ 0 | **Só linhas com kg > 0** entram na frequência (mesma régua do RN-01) | Limitação declarada: dentro de uma linha kg > 0 pode haver NF de devolução, não mensurável |
| 9 | Mês em andamento | **Etiquetada como parcial**, igual às outras medidas (RN-26) | Sem regra especial para a frequência |

Pendentes fora do Douglas: nenhum (definição de atendimento dada; extração no grão PDV declarada impossível).
