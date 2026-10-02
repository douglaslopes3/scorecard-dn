# Mapeamento · bases, suficiência, ferramentas e fases

Painel de Distribuição Numérica (DN) · pasta `DN/` · 08/09/2026 · modo somente leitura.

Nada foi alterado, movido, executado como pipeline ou instalado. Para inspecionar os arquivos rodei apenas leituras: `find`/`ls`, `cat` dos scripts, `pyarrow.parquet.read_table` nos Parquet, `openpyxl` em modo `read_only` e `pandas.read_excel(engine="calamine")` nos Excel. Bibliotecas presentes no Python 3.14 local: pandas 3.0.5, pyarrow 25.0.1, openpyxl 3.1.5, python-calamine, pyyaml. Ausentes: duckdb, polars.

**Aviso de escopo.** As pastas anunciadas foram `bases/` e `ferramentas/`. Junto vieram `data/`, `src/` e `Sell Out - MTRIX/`, que mapeei também porque são o pipeline pronto do outro projeto e a base que sustenta a DN. A pasta `processos/` citada na tarefa 3 não existe em `DN/` nem na pasta pai.

---

## 0. Resumo executivo

1. **A base da DN existe e está completa no grão certo**: `Sell Out - MTRIX/` traz 13 meses (jul/25 a jul/26) de sell-out por distribuidor × PDV (CNPJ) × SKU × mês, com kg, R$, unidades, cluster do PDV, UF e cidade. É o que o protótipo chamou de "Mtrix por CNPJ, pendência nº 1". Com ela dá para calcular volume, positivação, base ativa, DN, os segmentos por 6 meses e os comparativos.
2. **A Mtrix não conversava com nenhuma outra base por chave; a rodada 3 resolveu o lado do distribuidor.** Mtrix identifica PDV e distribuidor por CNPJ; sell-in, hierarquia, canais e RTM identificam cliente por código interno. O `Distribuidores_DePara.xlsx` (subido em 08/09) liga CNPJ do distribuidor ↔ código interno ↔ supervisor para os 79 distribuidores dos 13 meses. Continua sem ponte o lado do **PDV**: os clientes da base RTM não têm CNPJ.
3. **O pipeline `src/` é de sell-in, não de sell-out.** Está bem construído (cache, reconciliação contra a linha Total, relatório de qualidade), mas veio sem `config/`, `run_pipeline.py`, `run_dashboard.py`, templates e testes. Não roda como está. A parte reaproveitável é a infraestrutura (utils, cache, calendário, parquet, padrão de leitor e de qualidade); as regras de negócio (hierarquia, RTM, saneamento, cubos) não se aplicam à visão base.
4. **Duas fraquezas de dado a tratar na ingestão**: o arquivo de jul/26 perdeu os zeros à esquerda nos CNPJs (43 "distribuidores novos" falsos e PDVs duplicados), e cerca de 6% das linhas têm `Cód. PDV` com 3 a 8 dígitos, ou seja, não é CNPJ.
5. **Decisões fechadas em 08/09 (rodada 2)**: denominador = base ativa por janela de **5 meses**; positivado = **kg > 0**; distribuidor = **CNPJ de filial**; série a partir de **set/24** (ano fiscal Dori: setembro a agosto). Regra geral: **nada é derivado por inferência nem suposto; tudo vem das bases**, e o que não existir em base entra na lista de coleta do §5.3.
6. **Base RTM (definição confirmada)**: clientes que eram atendidos direto pela Dori e passaram a ser atendidos por distribuidor. Daqui para a frente o sell-through desses PDVs aparece na Mtrix sob o distribuidor. Para medi-los à parte é preciso saber o CNPJ de cada um (a base atual só tem o código interno).

---

## 1. Inventário das bases

### 1.1 `Sell Out - MTRIX/` · 13 arquivos `ScoreCard_Mtrix_MM.AAAA.xlsx` (a base da DN)

| Item | Valor |
|---|---|
| Formato | xlsx, aba única `Sheet1`, 18 colunas, 33 a 46 MB por arquivo, ~5,8 milhões de linhas no total |
| Período | jul/25 a jul/26, um mês por arquivo (o mês vem da coluna `Ano/Mês`, não do nome) |
| Linhas por arquivo | 382.088 (dez/25) a 502.280 (jul/26) |
| Granularidade | 1 linha = distribuidor (`CNPJ do AD.`) × PDV (`Cód. PDV`) × SKU × mês. Zero duplicidade nessa chave nos 13 arquivos |
| Linha especial | a 2ª linha da planilha é um **total** (colunas de dimensão vazias, métricas somadas, `# PDVs Positivados` = total de PDVs do mês). Serve de gabarito, como a linha `Total` do sell-in |
| Encoding | UTF-8 com acentos preservados ("GOVERNADOR VALADARES", "MERCEARIA/EMPÓRIO"); sem nulos nas 18 colunas |

Colunas (tipo, exemplo, papel):

| Coluna | Tipo | Exemplo | Papel |
|---|---|---|---|
| `CNPJ do AD.` | texto 14 dígitos (jul/26: 12–13, sem zeros à esquerda) | `01978813000113` | chave do distribuidor |
| `Agente de Distribuição` | texto | `CLAUMAR - CUIABA MT` | nome do distribuidor + praça |
| `CNPJ Reduzido` | texto 8 dígitos (raiz) | `00877761` | raiz do CNPJ do PDV (rede/empresa) |
| `Cód. PDV` | texto 14 dígitos; 6% com 3–8 dígitos | `00877761001440` | chave do PDV |
| `Razão Social PDV` | texto | `DEL MORO E DEL MORO LTDA` | nome do PDV |
| `UF PDV`, `Cidade PDV`, `Endereço PDV`, `Bairro PDV`, `CEP PDV` | texto | `MT`, `SORRISO` | geografia do PDV |
| `Segmento do PDV` | texto, 34 valores | `AS 10 A 19 CK` | cluster de loja |
| `SKU` | texto 7 dígitos | `9012134` | produto; 287 SKUs distintos nos 13 meses, **100% presentes em `Produtos.xlsx`** |
| `Ano/Mês` | texto `AAAA/MMM` | `2026/JUN` | competência |
| `# Sell-Out (R$)` | número | `449.28` | receita sell-out |
| `# Sell-Out (Und)` | número | `72` | unidades |
| `# Sell-Out (Quilos)` | número | `8.64` | **volume em kg** (métrica do painel) |
| `# PDVs Positivados` | número | `1` | flag: vale 1 em todas as linhas de dado |
| `# Total SKUs` | número | `1` | flag por linha |

Medições por mês (PDVs distintos com kg > 0, distribuidores por CNPJ):

| Mês | Linhas | Distrib. | PDVs positivados | Pares distrib.×PDV | SKUs | Volume t |
|---|---:|---:|---:|---:|---:|---:|
| 2025-07 | 482.905 | 70 | 66.767 | 68.179 | 240 | 1.257,7 |
| 2025-08 | 465.856 | 70 | 65.012 | 65.961 | 240 | 1.233,8 |
| 2025-09 | 455.240 | 71 | 64.949 | 65.473 | 238 | 1.201,9 |
| 2025-10 | 459.948 | 72 | 67.163 | 68.056 | 235 | 1.208,7 |
| 2025-11 | 433.216 | 74 | 63.127 | 63.933 | 239 | 1.140,1 |
| 2025-12 | 382.088 | 72 | 56.448 | 56.821 | 238 | 1.054,0 |
| 2026-01 | 434.808 | 72 | 63.234 | 63.925 | 226 | 1.038,3 |
| 2026-02 | 406.560 | 72 | 61.688 | 62.107 | 234 | 1.004,5 |
| 2026-03 | 447.872 | 72 | 66.177 | 66.722 | 233 | 1.113,4 |
| 2026-04 | 428.474 | 73 | 63.498 | 64.338 | 232 | 1.097,6 |
| 2026-05 | 468.908 | 72 | 68.239 | 68.858 | 231 | 1.206,3 |
| 2026-06 | 462.250 | 72 | 66.788 | 68.419 | 234 | 1.181,7 |
| 2026-07 | 502.280 | 71* | 71.179* | 71.712* | 221 | 1.249,8 |

\* jul/26 tem os CNPJs sem zero à esquerda; os números de PDV e distribuidor desse mês estão inflados até a chave ser normalizada.

Qualidade aparente:
- **Zeros à esquerda perdidos em jul/26**: `CNPJ do AD.` com 12–13 dígitos em 285 mil linhas; `Cód. PDV` com 12–13 dígitos em 119 mil linhas. Sem normalizar, jun/26 e jul/26 têm só 32.967 PDVs em comum; com `zfill(14)`, 42.625. Os 43 "distribuidores que entraram em jul/26" são os mesmos 68 CNPJs de sempre com outro formato.
- **`Cód. PDV` que não é CNPJ**: em jun/26, 27.243 linhas (5,9%) têm códigos de 3 a 8 dígitos e `CNPJ Reduzido` de 1 a 7 dígitos. Provavelmente PDVs identificados por CPF ou por código do distribuidor. Contam como PDV distinto, mas não são cruzáveis por CNPJ.
- **Linhas com kg ≤ 0**: 0 a 88 por mês (jul/26 tem 88). Devolução ou ajuste. Define "positivado".
- **PDV atendido por mais de um distribuidor no mesmo mês**: 371 a 1.601 por mês (jun/26: 1.601 de 66.788). A DN por distribuidor conta o PDV em cada um; a DN do canal precisa contar uma vez.
- **Distribuidor com várias filiais**: 79 nomes para 68–74 CNPJs. CHUA aparece em 3 praças, EBD em 12, ZAFFALON em 2, DAB em 2, NORDIL em 2, CHOCOSUL em 2, FRANCAL em 2. O protótipo tratava EBD por praça (EBD CE, EBD PA…) e CHUA como um só.
- `# PDVs Positivados` é sempre 1 na linha de dado: não é uma medida, é uma flag. A positivação real é "existe linha com kg > 0".
- Clusters: 34 valores em `Segmento do PDV`. Os 6 do protótipo (AS 20+ CK, AS 10 a 19 CK, AS 05 a 09 CK, AS 01 a 04 CK, Mercearia/Empório, Outros) cobrem os 5 primeiros diretamente; "Outros segmentos" do protótipo é a soma dos outros 29 (conveniência, padaria, farmácia, NC, distribuidor/atacadista, bar, restaurante…).

Base ativa e DN medidas com o que há (PDVs distintos com kg > 0, janela móvel, ordem cronológica):

| Mês | No mês | Janela 3m | Janela 5m | Janela 6m | Janela 12m | DN com janela 6m |
|---|---:|---:|---:|---:|---:|---:|
| 2025-12 | 56.448 | 99.777 | 115.569 | 121.548 | 121.548 | 46,4% |
| 2026-01 | 63.234 | 98.135 | 114.930 | 120.770 | 126.006 | 52,4% |
| 2026-02 | 61.688 | 98.996 | 115.553 | 121.298 | 131.092 | 50,9% |
| 2026-03 | 66.177 | 102.098 | 115.617 | 121.762 | 135.715 | 54,3% |
| 2026-04 | 63.498 | 102.507 | 116.141 | 121.680 | 139.901 | 52,2% |
| 2026-05 | 68.239 | 104.523 | 118.974 | 123.363 | 144.847 | 55,3% |
| 2026-06 | 66.788 | 105.169 | 120.221 | 125.541 | 149.453 | 53,2% |

Leitura: a janela de 6 meses dá uma base ativa de ~120 a 125 mil PDVs e uma DN de ~50 a 55%. O protótipo mostrava 88 mil e 76%. A diferença vem da definição (o protótipo simulava a base) e da janela (5 vs 6 meses muda pouco: 120 mil vs 125 mil em jun/26). Só a partir de dez/25 a janela de 6 meses está completa.

### 1.2 `bases/Sell In/` · 29 arquivos `sellin_AAAA-MM[_pN].xlsx`

| Item | Valor |
|---|---|
| Formato | xlsx, aba `Export`, 13 colunas, 1,4 a 5,2 MB. Rodapé com linha `Total` e "Filtros aplicados" |
| Período | set/24 a set/26, 25 meses; set/24, out/24, nov/24 e mai/25 partidos em `_p1`/`_p2` com filtros complementares de gerente |
| Linhas | 3.134.928 após limpeza (medido pelo pipeline em 08/09/2026) |
| Granularidade | 1 linha = mês × cliente × SKU (faturamento líquido). Zero duplicidade |
| Colunas | `Ano`, `Ano mês` (`2026/08`), `Cód. cliente` (zero-preenchido `0001000000`), `Cliente`, `Bandeira cliente`, `Estado`, `Desc. categoria`, `Cód. material`, `Desc. material sem código`, `Receita Líquida`, `Peso Líquido`, `Qtde Faturado`, `Comissão Faturada Líquida` |
| Chaves | `Cód. cliente` (código interno SAP, 7 dígitos sem zeros), `Cód. material` (SKU, mesmo código da Mtrix), `Ano mês` |
| Qualidade | 81.831 linhas com receita negativa (devolução); `Qtde Faturado` nula em 76.675 linhas; 3.520 linhas 100% zeradas; três recortes de extração diferentes na série (avisado pelo pipeline); set/26 parcial (19 mil linhas) |

Relação com a DN: é sell-in (Dori → cliente), não sell-through. Contém os distribuidores como clientes (canal `DISTRIBUIDOR`: 395 códigos no de-para de canais, 1.718 na DIM_CLIENTE já com os RTM reatribuídos). Não tem CNPJ.

### 1.3 `bases/Bases para tabelas dimensões/`

| Arquivo | Aba | Linhas | Colunas | Chave | Uso para a DN |
|---|---|---:|---|---|---|
| `Produtos.xlsx` | `Produtos` | 1.712 | `Código Produto`, `Descrição Produto`, `Marca`, `Categoria` (11 valores) | `Código Produto` = `SKU` da Mtrix | **categoria da DN**: todos os 287 SKUs da Mtrix estão aqui |
| `Hierarquia_Consolidada.xlsx` | `Planilha1` | 13.516 | `CÓDIGO CLIENTE`, `CLIENTE`, `CÓDIGO BANDEIRA`, `BANDEIRA`, `CÓDIGO REDE`, `REDE`, N1 head (código, papel, nome), N2 gerente, N3 sup./exec., N4 vend./RCA, `PROJETO` | `CÓDIGO CLIENTE` (interno) | supervisor do distribuidor, **se** houver ponte código ↔ CNPJ do AD. Cabeçalhos têm quebra de linha; 106 gerentes sem nome; 13 clientes com dois N4 |
| `Hierarquia_Clientes_Faltando.xlsx` | `Planilha1` | 850 | `CÓDIGO CLIENTE`, `CLIENTE`, `Hierarquia` (SIM/NÃO) | `CÓDIGO CLIENTE` | não se aplica (saneamento da hierarquia de sell-in) |
| **`Distribuidores_DePara.xlsx`** (subida em 08/09, rodada 3) | `Planilha1` | 79 | `CNPJ DISTRIBUIDOR`, `DESCRIÇÃO DISTRIBUIDOR MTRIX`, `DESCRIÇÃO BI` (64 razões), `Cód. Interno Cliente`, `Status` (75 Ativo, 4 Inativo), `Head` (1: "Michel - 1000"), `Gerente` (3), `Supervisor` (14 territórios, ex.: "Supervisor MG"), `Distribuidora Nome Reduzido` (64; agrupa filiais: EBD CE, EBD PA, EBD RJ, EBD SP, EBD PE, CHUA, CHOCOSUL, D.A.B. DIST., FABIANO ZAFFALON, FRANCAL, NORDIL, V.M. DIST) | `CNPJ DISTRIBUIDOR` = `CNPJ do AD.` da Mtrix; `Cód. Interno Cliente` = `CÓDIGO CLIENTE` da Hierarquia | **é a ponte Mtrix ↔ hierarquia**. Medido: os 79 CNPJs cobrem 100% dos distribuidores dos 13 meses da Mtrix (nenhum sobrando de um lado ou do outro); 70 dos 79 códigos internos estão na `Hierarquia_Consolidada` (os 9 que faltam: RAYO, KRUPER, NORTESUL, MMD, CBX ativos, e CHUA Serra, AVANT, MDB, IREZ E SIQUEIRA inativos). O supervisor do de-para e o N3 da hierarquia coincidem 1 para 1 nos 70 (ex.: "Supervisor MG" ↔ "1140 - Superv_MG - BONIFACIO ARAUJO") |

### 1.4 `bases/Canais/Canais.xlsx`

Aba `Export`, 43.072 clientes, colunas `Cód. cliente` (zero-preenchido), `Cód. canal` (9 códigos), `Canal`, `Subcanal` (43). Rodapé com filtro da extração. Canal `DISTRIBUIDOR` = 395 clientes. Uso para a DN: identificar quais códigos internos são distribuidores; não cruza com a Mtrix sem ponte de CNPJ.

### 1.5 `bases/RTM-Transicao/RTM_DePara_Transicao.xlsx`

Aba `De-Para RTM`: 1.762 linhas, colunas `Cód. Cliente [Antigo]`, `Bandeira cliente [Antigo]`, `Dsitribuidor Nome Reduzido` (grafia da origem), `Cód. Cliente [Distribuidor]`. 27 distribuidores; 166 clientes sem código de distribuidor (placeholders "NOVO RIBEIRÃO PRETO", "NOVO SJRP", listados na aba `Descobrir Código`). Zero cliente com dois distribuidores.

O que ela é: a lista de clientes que **eram atendidos direto pela Dori e migraram para distribuidor**, por código interno. É a "Base RTM" que ficou combinada de medir à parte. **Não é** o universo de PDVs por distribuidor: são 1.762 clientes contra 66 mil PDVs positivados por mês na Mtrix, e não tem CNPJ.

Ponte parcial com a Mtrix: o primeiro token de `Agente de Distribuição` bate com o nome reduzido do RTM em 13 dos 79 nomes (ARRUDA, BREDA, CENTRAL, CHUA, CLAUMAR, DIN, DISO, DOM JASON, FRANCAL, PORTAL, SULGERAIS, UNIVALE). Os outros 14 do RTM (DISPAN, PELLAH, EBD SP, SINAIS, VJS, DIPAM GAÚCHA…) exigiriam de-para manual por nome.

### 1.6 `data/` · saídas do pipeline do outro projeto (execução `20260908-131902`)

| Pasta | Conteúdo | Observação |
|---|---|---|
| `staging/` | 1 Parquet + 1 JSON por Excel lido (cache por hash): 29 sell-in, Canais, Produtos, Hierarquia_Consolidada, Hierarquia_Clientes_Faltando, RTM_DePara, DePara_Estrutura_Comercial (base antiga, 16.062 linhas), Metas_FY'27 | o JSON guarda o gabarito da linha Total e o texto do filtro |
| `curated/` | `DIM_CALENDARIO` (26 meses, calendário e fiscal, `ANO_MES_LY`), `DIM_CLIENTE` (16.140 clientes, 26 colunas: hierarquia, canal, RTM, inativação), `DIM_PRODUTO` (400 SKUs movimentados), `FATO_SELLIN` (3,13 M linhas, partição por ano), `FATO_META` (146.794 pares cliente × categoria para set e out/26), `cubos.json` (52 MB, cubos do painel gerencial), `resumo.json` | tudo sell-in; nada de sell-out |
| `quality/` | `relatorio_qualidade.md` e 14 CSVs (clientes sem estrutura/canal, SKUs sem cadastro, RTM sem distribuidor, saneamento, metas negativas, linhagem, assinatura do filtro) | modelo de relatório a replicar |
| `raw/sell_in/` | vazia | |

`Metas_FY'27.xlsx` aparece só no staging; o Excel não está em `bases/`. É meta de sell-in por cliente × categoria, não meta de DN.

### 1.7 Como as bases se relacionam

| De | Para | Chave | Situação |
|---|---|---|---|
| Mtrix `SKU` | `Produtos.xlsx` `Código Produto` | código de 7 dígitos | **funciona**: 287 de 287 SKUs, dá a categoria |
| Mtrix `SKU` | Sell In `Cód. material` | mesmo código | funciona (não necessário para a DN) |
| Mtrix `CNPJ do AD.` | `Distribuidores_DePara.xlsx` `CNPJ DISTRIBUIDOR` | CNPJ 14 dígitos (normalizar zeros) | **funciona**: 79 de 79 nos 13 meses (rodada 3) |
| `Distribuidores_DePara` `Cód. Interno Cliente` | Sell In `Cód. cliente` / Hierarquia / Canais / RTM | código interno | **funciona** para 70 de 79 na Hierarquia; o supervisor já vem no próprio de-para para os 79 |
| Mtrix `Cód. PDV` | RTM `Cód. Cliente [Antigo]` | não existe | lacuna (universo RTM por PDV) |
| Mtrix `Agente de Distribuição` | RTM `Dsitribuidor Nome Reduzido` | nome, parcial | 13 de 79 casam pelo primeiro token |
| Sell In `Cód. cliente` | Hierarquia, Canais, RTM, Faltando | código interno normalizado por `digitos()` | funciona (é o que o pipeline `src/` já faz) |
| Sell In `Ano mês` | `DIM_CALENDARIO.ANO_MES` | `AAAA-MM` | funciona; a Mtrix usa `AAAA/MMM`, que `texto.ano_mes()` já aceita |

Diagrama do que existe hoje:

```
Produtos.xlsx ──SKU──► Mtrix (AD × PDV × SKU × mês)      ← base da DN, isolada
                        │ CNPJ do AD.        │ Cód. PDV (CNPJ)
                        ✗ sem ponte          ✗ sem ponte
Sell In ──Cód. cliente──► Hierarquia_Consolidada (N1..N4, projeto)
        ──Cód. cliente──► Canais.xlsx (canal DISTRIBUIDOR = 395)
        ──Cód. cliente──► RTM_DePara (1.762 clientes → 27 distribuidores)
        ──Cód. cliente──► Hierarquia_Clientes_Faltando (SIM/NÃO)
```

---

## 2. Suficiência das bases para o HTML (`template/template.html`, 129 campos do `data-inventory.json`)

Legenda: **Direto** = coluna existe · **Derivado** = calculável, regra indicada · **Lacuna** = não existe.

### 2.1 Período e canal

| Campo | Classe | Regra / colunas |
|---|---|---|
| `periodo.mes_atual`, `mes_anterior`, `mesmo_mes_ano_anterior`, `janela_l3m` | Derivado | último `Ano/Mês` da Mtrix com arquivo fechado; aritmética de mês. `texto.ano_mes()` converte `2026/JUN` |
| `canal.nome` | Direto (fixo) | "CANAL DISTRIBUIÇÃO" |

### 2.2 Métricas base (canal, segmento, cluster, supervisor, distribuidor, categoria)

| Campo | Classe | Regra / colunas |
|---|---|---|
| `cobertura_pdv` (positivados) | Derivado | `COUNT DISTINCT Cód. PDV` com `# Sell-Out (Quilos) > 0` no mês, por recorte. Normalizar a chave (`digitos` + `zfill(14)`) |
| `base_ativa` | Derivado | `COUNT DISTINCT Cód. PDV` com kg > 0 nos últimos N meses (janela móvel fechada no mês). N = 5 ou 6, a decidir (§5). Precisa de N−1 meses antes do 1º mês da série |
| `pct_cobertura` (DN) | Derivado | `cobertura_pdv ÷ base_ativa` |
| `volume_t` | Direto | `SUM(# Sell-Out (Quilos)) ÷ 1000` |
| `kg_pdv` | Derivado | `volume_t × 1000 ÷ cobertura_pdv` |
| `*_var_mes_anterior`, `*_var_l3m`, `*_var_ly` | Derivado | série mensal do mesmo recorte; LY = mês − 12 via `DIM_CALENDARIO.ANO_MES_LY` (junção, não deslocamento) |
| Receita (R$), unidades, nº de SKUs por PDV | Direto (não usados na visão base) | `# Sell-Out (R$)`, `# Sell-Out (Und)`, `COUNT DISTINCT SKU`. O toggle R$ que foi removido do protótipo poderia voltar com dado real |

### 2.3 Séries de 13 meses (`dn.serie`, `categoria.serie`, `distribuidor.serie`, `segmento.supervisor.serie`)

| Campo | Classe | Regra |
|---|---|---|
| `mes`, `cobertura_pdv`, `volume_t`, `base_ativa`, `pct_cobertura` | Derivado | as mesmas regras por mês |
| `cobertura_ly` | **Lacuna parcial** | só jul/26 tem jul/25 na base. Para LY nos 13 meses da série é preciso Mtrix de jul/24 a jun/25 (12 arquivos a mais) |
| `cobertura_base_atual`, `cobertura_novos` | Derivado | positivados por segmento do distribuidor (§2.5) |

### 2.4 Categoria

| Campo | Classe | Regra |
|---|---|---|
| `categoria.id`, `nome` | Direto | `Produtos.xlsx.Categoria` via `SKU` (10 categorias com volume; `DISPLAY/MAT.PROMOCIONAL` e `NAO INFORMADO` não aparecem na Mtrix) |
| `categoria.cobertura_pdv` | Derivado | PDVs distintos com kg > 0 em SKUs da categoria |
| `categoria.pct_cobertura` | Derivado | ÷ `base_ativa` do canal |
| `categoria.penetracao` | Derivado | ÷ `cobertura_pdv` do canal |
| `categoria.volume_t`, comparativos | Derivado | idem |

### 2.5 Segmentos e distribuidores

| Campo | Classe | Regra |
|---|---|---|
| `distribuidor.id`, `nome` | Direto | `CNPJ do AD.` normalizado (id) e `Agente de Distribuição` (nome). Decidir se filial é distribuidor (§5) |
| `distribuidor.meses_historico` | Derivado, **censurado** | meses desde o 1º `Ano/Mês` com kg > 0. Com 13 meses de base só se sabe "≥ 13" para os 70 presentes em jul/25; os que entraram depois são 6 (EBD S. Bernardo set/25, EBD São Paulo out/25, Boa Distribuidora nov/25, um CNPJ sem nome nov/25, Favinha abr/26, Dipam Gaúcha jun/26) |
| `distribuidor.segmento_id`, `segmento` | Derivado | `meses_historico > 6 → base_atual`, senão `novos` |
| `segmento.kpi.*`, `segmento.clusters[]` | Derivado | agregação dos distribuidores do segmento |
| `segmento.cluster.nome` | Direto + mapeamento | `Segmento do PDV` (34 valores) → 6 clusters do protótipo. O mapa dos 29 "outros" é decisão de negócio |
| `distribuidor.supervisor`, `segmento.supervisores[]` | **Direto** (rodada 3) | `Distribuidores_DePara.xlsx.Supervisor` por `CNPJ DISTRIBUIDOR` (14 territórios, 79 de 79). Alternativa pelo `Cód. Interno Cliente` → `Hierarquia_Consolidada` N3 (código + nome, ex.: "1140 - Superv_MG - BONIFACIO ARAUJO") para 70 de 79. Decidir qual rótulo o painel mostra |
| `distribuidor.nome_reduzido`, `status` | Direto (rodada 3) | `Distribuidora Nome Reduzido` (agrupa filiais, é o nome que o protótipo usava) e `Status`. Não estão no template hoje; entram como atributos se você quiser |

### 2.6 Ponto de venda

| Campo | Classe | Regra |
|---|---|---|
| `pdv.cnpj`, `nome`, `uf`, `cluster`, `distribuidor` | Direto | `Cód. PDV`, `Razão Social PDV`, `UF PDV`, `Segmento do PDV`, `Agente de Distribuição`. Cidade, bairro, CEP também existem (não estão no template) |
| `pdv.volume_kg` | Direto | soma dos SKUs do PDV no mês |
| `pdv.positivado_mes`, `positivado_mes_anterior`, `positivado_mesmo_mes_ly` | Derivado | presença com kg > 0 no mês, mês − 1, mês − 12 |
| `pdv.meses_positivado_janela` | Derivado | contagem de meses com kg > 0 na janela |
| Tamanho | Atenção | 66 mil PDVs × atributos numa tabela HTML estática é pesado (o protótipo listava 100). Precisa de corte ou de renderização por filtro |

### 2.7 Confirmações pedidas

| Pergunta | Resposta | Condição |
|---|---|---|
| Dá para calcular DN? | **Sim**, com a Mtrix sozinha, para o denominador "base ativa por janela" | normalizar chaves; decidir N; definir positivado = kg > 0 |
| Dá para calcular DN com denominador "universo RTM"? | **Não hoje** | a base RTM tem 1.762 clientes por código interno, sem CNPJ; não é universo de PDVs |
| Base ativa? | **Sim** (janela móvel) | janela completa só a partir de dez/25 (6 meses) ou nov/25 (5 meses) |
| Segmentação por 6 meses? | **Sim, com censura** | 70 distribuidores já tinham histórico em jul/25 (ficam "Base atual"); 6 entraram depois. Uma série mais longa ou um cadastro de "data de início" resolve a censura |
| Comparativos? | mês anterior e L3M: **sim** nos 13 meses (L3M a partir do 4º); LY: **só jul/26** | LY completo exige Mtrix de jul/24 a jun/25 |
| Drill categoria / PDV / distribuidor? | **Sim** | categoria via `Produtos.xlsx`; PDV nominal e cluster diretos; distribuidor direto |
| Drill supervisor? | **Sim** (rodada 3) | `Distribuidores_DePara.xlsx` cobre os 79 distribuidores |

### 2.8 Ambiguidades encontradas

1. **"Positivado"**: linha existente vs. `# Sell-Out (Quilos) > 0` vs. `# PDVs Positivados = 1` (é 1 em toda linha, inclusive nas de kg ≤ 0). Proposta: kg > 0.
2. **Identidade do PDV**: `Cód. PDV` (14 dígitos, mas 6% com 3–8) vs. `CNPJ Reduzido` (raiz de 8, agrupa filiais de uma rede). Proposta: `Cód. PDV` normalizado como PDV; raiz como atributo "rede".
3. **PDV em dois distribuidores no mês** (até 1.601): conta em cada distribuidor e uma vez no canal. Confirmar.
4. **Identidade do distribuidor**: CNPJ (68–74) vs. nome (79) vs. razão (CHUA, EBD, ZAFFALON com filiais). O protótipo usava nome de praça para EBD e nome único para CHUA.
5. **Categoria**: via SKU e `Produtos.xlsx` (11 categorias, 10 com volume). O protótipo tinha as mesmas 10. Sem ambiguidade, desde que o cadastro seja atualizado quando entrar SKU novo.
6. **Cluster**: 34 segmentos Mtrix → 6 clusters do protótipo. Falta o mapa dos 29 restantes.
7. **Formato das chaves em jul/26** (zeros perdidos): tratar na ingestão com `digitos()` + `zfill(14)`, e registrar no relatório de qualidade quando um arquivo vier nesse formato.
8. **Janela da base ativa**: 5 (protótipo e resposta anterior) ou 6 meses (definição dada). Diferença medida em jun/26: 120.221 vs 125.541 PDVs (DN 55,6% vs 53,2%).

---

## 3. Ferramentas e processos reaproveitáveis

Não há pasta `processos/`. O que existe de processo está descrito nos docstrings dos módulos e no `LEIA-ME.md` de `ferramentas/`, que referenciam `docs/12`, `docs/04_GAPS_E_RISCOS.md` e `docs/09_ARQUITETURA_SOLUCAO.md` do outro projeto, que **não vieram**. Também não vieram `config/config.yaml`, `config/geografia.yaml`, `run_pipeline.py`, `run_dashboard.py`, a pasta `dashboard/` (templates) e `tests/`. Consequência: nenhum módulo de `src/` nem de `ferramentas/` roda hoje em `DN/` (o `src/utils/config.py` aborta na ausência do YAML).

### 3.1 `ferramentas/`

| Script | O que faz | Entradas → saídas | Dependências | Veredito |
|---|---|---|---|---|
| `LEIA-ME.md` | explica que os 4 scripts são de medição/manutenção, não etapas do pipeline | — | — | **adaptar**: manter o padrão "medir antes de decidir" |
| `diagnostico_cobertura.py` | explica queda de cobertura da hierarquia de sell-in (cascata RTM, chave que parou de casar) | bases sell-in + hierarquia → 2 CSVs em `data/quality/` | `src.*`, config | **não se aplica** à visão base (hierarquia de sell-in). Útil só na fase de supervisor, se a ponte AD ↔ hierarquia existir |
| `analise_bandeira_rtm.py` | mede o custo de o cliente RTM herdar a bandeira do distribuidor | idem → 1 CSV | `src.*`, config | **não se aplica** (bandeira e head são do painel gerencial) |
| `comparar_paineis.py` | compara dois conjuntos de HTML sem navegador: descompacta o bloco de dados de cada painel e confere totais por mês/bandeira, cubo de SKU e dimensões, com teto de arredondamento | 2 pastas de HTML → exit code | lê `/*DADOS_INICIO*/…/*DADOS_FIM*/` gzip+base64 | **adaptar**: a ideia (provar que um redeploy não mudou número) vale para o DN; aqui o dado vive em `example-data.json` e nas séries `DN_SERIES` do HTML, então a comparação é de JSON, não de cubo |
| `limpar_paineis_antigos.py` | recolhe HTMLs que a geração atual não produz para quarentena | destino de publicação → move arquivos | `run_dashboard` (ausente), config, `cubos.json` | **não se aplica** agora (um único HTML de saída). Reavaliar se houver um painel por distribuidor/supervisor |

### 3.2 `src/` (pipeline de sell-in do painel gerencial)

| Módulo | O que faz | Veredito para o DN | Justificativa |
|---|---|---|---|
| `utils/config.py` | raiz do projeto, `config/*.yaml`, pastas `data/raw|staging|curated|quality` | **replicar** (criando `config/config.yaml` novo) | padrão bom: caminhos a partir da raiz, não do cwd |
| `utils/log.py` | log em console e arquivo com `EXECUCAO_ID`, `abortar()` | **replicar como está** | linhagem "este número veio desta execução" |
| `utils/texto.py` | `texto()`, `digitos()`, `numero()`, `ano_mes()` (aceita `AAAA/MMM`), `pct()`, `div()` | **replicar como está** | resolve exatamente os problemas da Mtrix: zeros perdidos, `2026/JUN`, decimal com ponto. Só acrescentar `zfill(14)` para CNPJ |
| `extract/cache.py` | cache Excel → Parquet por (caminho, tamanho, mtime, hash 64 KB, versão) | **replicar como está** | ler 13 × 40 MB de Excel a cada execução custa minutos; o cache resolve |
| `extract/sellin.py` | leitor de sell-in: valida schema, tira rodapé, guarda gabarito da linha Total e o texto do filtro, aborta em mês irreconhecível, descarta linhas zeradas com contagem, detecta recorte diferente entre meses e cópia duplicada | **adaptar → `extract/sellout.py`** | mesma estrutura, outro layout: 18 colunas, total na 2ª linha (não no rodapé), sem "Filtros aplicados", mês `AAAA/MMM`, normalização de CNPJ. Mantém: schema obrigatório, gabarito, abort em mês ruim, contagem de descartes |
| `extract/cadastros.py` | leitores de Produtos, Canais, Hierarquia, RTM, Faltando, com correções declaradas em config | **replicar** `_ler_produtos`; **adaptar** `_ler_rtm` (para a base RTM à parte); **não se aplica** estrutura/canais/faltando na visão base | produtos é a única dimensão que a DN consome hoje |
| `extract/metas.py` | leitor de metas por cliente × categoria × mês (aborta em duplicidade, tipo desconhecido, mês em dois arquivos) | **não se aplica agora**; guardar para quando a meta de DN vier por Excel | o padrão "arquivo decide, mês substitui, nunca soma" serve para a meta de DN |
| `transform/calendario.py` | `DIM_CALENDARIO` com calendário civil e fiscal (set–ago) e `ANO_MES_LY` por junção | **replicar como está** | o LY por junção evita o erro de deslocar posição quando falta mês; acrescentar `ANO_MES_M1` e a lista L3M se quiser o mesmo padrão |
| `transform/dimensoes.py` | `DIM_CLIENTE` (sell-in + hierarquia + canal) e `DIM_PRODUTO` (cadastro + fallback do próprio fato) | **adaptar**: `DIM_PDV` e `DIM_DISTRIBUIDOR` a partir da Mtrix, com a regra "último atributo vence" e "quem está no fato existe na dimensão"; `dim_produto` replicar | o princípio de nunca descartar e reportar divergência vale igual |
| `transform/fato.py` | `FATO_SELLIN`, grão declarado, duplicidade aborta, integridade fato ↔ dimensões, reconciliação contra o gabarito, piso de cobertura | **adaptar → `FATO_SELLOUT`** com grão AD × PDV × SKU × mês, reconciliação contra a linha total da Mtrix nas 3 métricas (R$, und, kg) | é a checagem que impede publicar número errado |
| `transform/saneamento.py` | reatribuição RTM e inativação por janela de 6 meses na `DIM_CLIENTE` | **não se aplica** à hierarquia; **reaproveitar `_janela()`** (janela de calendário ancorada na última competência fechada) para a base ativa e para a regra dos 6 meses | a lógica de janela já foi pensada para não esticar quando falta mês |
| `load/parquet.py` | grava curated em zstd, partição por ano, tolera o lock do OneDrive | **replicar como está** | o projeto mora no OneDrive; o tratamento de `PermissionError` é necessário |
| `load/cubos.py` | cubos posicionais com inteiros escalados para o painel gerencial | **não se aplica** | o template DN consome `example-data.json` (Handlebars). Guardar a ideia de inteiros escalados só se um dia o DN embutir cubo no HTML |
| `qualidade.py` | relatório Markdown + CSVs de exceção (linhagem, período, totais, duplicidade, integridade, valores não reconhecidos, sem classificação) | **adaptar** | mesmas seções, com as exceções da DN: PDVs sem CNPJ, chaves normalizadas, PDV multi-distribuidor, meses sem janela completa, SKU fora do cadastro |

### 3.3 O que de `template/` (sessão anterior) já é etapa do pipeline

| Artefato | Papel | Veredito |
|---|---|---|
| `template/template.html` + `data-inventory.json` | contrato do painel (129 campos) | **replicar**: é a saída-alvo da etapa de métricas |
| `template/tools/build.py` | gera o HTML a partir de um JSON e formata pt-BR; validado com Handlebars | **adaptar**: separar o renderizador (JSON formatado → HTML) do extrator do protótipo |
| `template/business-rules.md` | regras e dúvidas | **replicar**: as dúvidas D1–D13 viram decisões da Fase 0 |

### 3.4 O que já resolve cada etapa do pipeline do DN

| Etapa | Já resolvido por | Falta |
|---|---|---|
| Ingestão | `cache.py`, `texto.py`, padrão de `sellin.py`, `parquet.py` | leitor da Mtrix, `config.yaml` |
| Limpeza | `texto.digitos/ano_mes/numero`, contagem de descartes, gabarito | normalização de CNPJ, tratamento de `Cód. PDV` não-CNPJ |
| Cálculo de métricas | `calendario.py` (LY), `saneamento._janela` (janela) | tudo de DN: positivação, base ativa, segmentos, comparativos, agregações por recorte |
| Qualidade | `qualidade.py`, `fato.py` (integridade, reconciliação) | adaptação das seções |
| Renderização | `template/tools/build.py` (formatação + Handlebars) | ligar ao JSON de métricas em vez do protótipo |
| Publicação / regressão | `comparar_paineis.py` (ideia) | versão para JSON do DN |

---

## 4. Proposta de fases (nenhuma executada)

| Fase | Objetivo | Entradas | Saídas | Riscos |
|---|---|---|---|---|
| **0 · Decisões** | fechar as definições que mudam o cálculo | este documento; `template/business-rules.md` | respostas às perguntas do §5.3 registradas em `docs/decisoes.md` | decidir com pressa o denominador (base ativa × universo RTM) e refazer depois |
| **1 · Ingestão da Mtrix** | 13 arquivos → `FATO_SELLOUT` Parquet reconciliada, `DIM_PDV`, `DIM_DISTRIBUIDOR`, `DIM_PRODUTO`, `DIM_CALENDARIO` | `Sell Out - MTRIX/*.xlsx`, `Produtos.xlsx`; `src/utils`, `cache.py`, `parquet.py`, `calendario.py` copiados; `config/config.yaml` novo | `data/curated/FATO_SELLOUT/ANO=…`, dimensões, `data/quality/relatorio_qualidade.md` com linhagem por arquivo, gabarito da linha total, chaves normalizadas, PDVs não-CNPJ, PDV multi-distribuidor | zeros perdidos em jul/26; arquivo de mês novo com layout diferente; 40 MB × 13 no OneDrive (cache obrigatório) |
| **2 · Métricas de DN** | calcular a visão base no grão mês × distribuidor × categoria × PDV | `FATO_SELLOUT`, dimensões, decisões da Fase 0 (N da janela, positivado, clusters, filiais) | `data/curated/DN_MENSAL.parquet` (mês × distribuidor × categoria: positivados, base ativa, DN, volume), `DN_PDV.parquet` (mês × distribuidor × PDV: positivado, kg), `DN_SERIE`; `example-data.json` real no contrato do template (`data-inventory.json`) | janela incompleta antes de dez/25; LY só em jul/26; censura da regra de 6 meses; supervisor vazio |
| **3 · Renderização** | HTML da visão base com dados reais | `example-data.json` real, `template/template.html`, renderizador derivado de `build.py` | `Scorecard_DN_<mês>.html`; validação Handlebars byte a byte; comparação JSON entre execuções (herdeira de `comparar_paineis.py`) | tabela nominal de 66 mil PDVs no HTML: definir corte ou carregamento por filtro |
| **4 · Histórico e LY** | completar 25 meses de Mtrix para LY em toda a série e janela completa desde o início | Mtrix jul/24 a jun/25 (a pedir) | série de 13 meses com LY em todos os pontos | os arquivos antigos podem vir em outro layout |
| **5 · Supervisor e hierarquia** (agora cabe na Fase 1/2) | ler `Distribuidores_DePara.xlsx` como `DIM_DISTRIBUIDOR` (CNPJ, código interno, nome Mtrix, razão BI, nome reduzido, status, head, gerente, supervisor) e, se o rótulo escolhido for o da hierarquia, juntar o N3 pela `Hierarquia_Consolidada` | `Distribuidores_DePara.xlsx`; `cadastros.py` adaptado | `distribuidor.supervisor`, bloco de supervisores preenchido | 9 códigos fora da hierarquia (4 inativos, 5 ativos) ficam com o supervisor do de-para |
| **6 · Base RTM (à parte)** | medir a base RTM separadamente, como combinado | `RTM_DePara_Transicao.xlsx` + de-para de CNPJ dos 1.762 clientes (a construir) | visão RTM própria ou universo RTM como denominador alternativo | sem CNPJ não cruza com a Mtrix |
| **7 · Meta e projeção** | preencher os `TODO: meta/projeção` do template via Excel | arquivo de meta de DN por mês × distribuidor × categoria; padrão de `metas.py` | colunas de meta no JSON e no HTML | formato do Excel de meta ainda não definido |

Ordem sugerida: 0 → 1 → 2 → 3 (entrega a visão base) → 4 (melhora os comparativos) → 5 e 6 em paralelo → 7.

---

## 5. Rodada 2 (08/09/2026) · decisões, regra "tudo vem das bases" e lista de coleta

### 5.1 Decisões registradas

| Tema | Decisão | Efeito no cálculo |
|---|---|---|
| Denominador da DN | base ativa por janela (não o universo RTM) | `base_ativa` = PDVs distintos com kg > 0 nos últimos 5 meses, por recorte |
| Janela | **5 meses** | janela completa a partir do 5º mês da série |
| Positivado | **kg > 0** (`# Sell-Out (Quilos)`) | linhas com kg ≤ 0 não positivam; a flag `# PDVs Positivados` não é usada |
| Distribuidor | **CNPJ de filial** (`CNPJ do AD.`) | CHUA, EBD, ZAFFALON etc. contam por praça; o nome vem de `Agente de Distribuição` |
| Série | **set/24 em diante** (ano fiscal set–ago) | precisa dos arquivos Mtrix de set/24 a jun/25, que não estão na pasta |
| Base RTM | clientes que eram atendidos direto pela Dori e passaram ao distribuidor; o sell-through deles passa a vir na Mtrix sob o distribuidor | medida à parte, por PDV, dentro da própria Mtrix, **quando houver o CNPJ de cada cliente RTM** |
| Método | **nada derivado por inferência, nada suposto** | mapeamentos, cadastros e datas vêm de base; o que faltar entra em 5.3 |

O que continua sendo cálculo (aritmética sobre colunas da base, sem suposição): contagem distinta de PDVs, soma de kg, divisão positivados ÷ base ativa, variação % contra mês anterior, média de 3 meses e mesmo mês do ano anterior, categoria por junção SKU → `Produtos.xlsx`. O que deixa de ser feito: casar distribuidor por nome, agrupar os 34 segmentos em 6 clusters, inferir data de início pelo primeiro mês da série, completar zeros em CNPJ sem confirmação da origem.

### 5.2 Por que a ponte CNPJ do distribuidor ↔ código de cliente é necessária (pergunta 6)

O template tem o bloco "Supervisores · acompanhamento do mês" (mantido por decisão da sessão anterior) e a coluna `distribuidor.supervisor`. O supervisor existe em uma única base, a `Hierarquia_Consolidada.xlsx`, e lá a chave é `CÓDIGO CLIENTE` (código interno, ex.: `1003318` = CLAUMAR). A Mtrix identifica o mesmo distribuidor por `CNPJ do AD.` (`01978813000113`). Nenhuma base traz os dois códigos na mesma linha. Sem essa ponte, o supervisor de cada distribuidor não pode ser preenchido e o bloco fica vazio. A mesma ponte serve depois para cruzar sell-in e sell-through do distribuidor. O `RTM_DePara_Transicao.xlsx` tem o código interno de 27 distribuidores (`Cód. Cliente [Distribuidor]`), mas também sem CNPJ.

Forma mais simples de resolver: um cadastro de distribuidores com `CNPJ` (por filial), `CÓDIGO CLIENTE` (SAP) e, se existir, `data de início da operação`.

### 5.3 Lista de coleta (o que não está nas bases e precisa vir de fora)

| # | Item | Para quê | Onde deve estar |
|---|---|---|---|
| C1 | ~~Mtrix de set/24 a jun/25~~ **Não disponível** (rodada 3: "por enquanto só vamos ter essas bases da Mtrix"). Consequências: série = jul/25 a jul/26 (13 meses); janela de 5 meses completa a partir de nov/25; comparativo LY só em jul/26; L3M a partir de out/25. Reabrir quando houver mais meses | — | — |
| C2 | ~~Cadastro de distribuidores~~ **Resolvido** pelo `Distribuidores_DePara.xlsx` (rodada 3): CNPJ × código interno × supervisor × status × nome reduzido, 79 de 79 distribuidores | `distribuidor.supervisor` direto | — |
| C3 | **Data de início de cada distribuidor** (ou do contrato) | segmentação Base atual (> 6 meses) × Novos (< 6 meses) sem depender do primeiro mês que aparece na série | Comercial |
| C4 | ~~Base RTM com CNPJ~~ **Fechado** (rodadas 6 e 7): coluna `CNPJ` completa; migração em andamento é o comportamento esperado, sem data de migração | — | — |
| C5 | **Definição oficial dos clusters de loja** | hoje a Mtrix traz 34 valores em `Segmento do PDV`; o protótipo usava 6. Sem uma lista oficial, o painel usa os 34 como vêm | Trade / Mtrix |
| C6 | **Reextração de jul/26** (ou confirmação da Mtrix de que `CNPJ do AD.` e `Cód. PDV` devem ser completados com zeros à esquerda até 14 dígitos) | o arquivo de jul/26 veio com 12–13 dígitos; sem confirmação, não completo zeros | Mtrix / BI |
| C7 | **O que são os `Cód. PDV` de 3 a 8 dígitos** (5,9% das linhas em jun/26) | decidir se são PDVs válidos (CPF, código interno do distribuidor) ou lixo; hoje entram como PDV distinto | Mtrix |
| C8 | ~~Regra para PDV atendido por dois distribuidores~~ **Resolvido** (rodada 5): conta em cada distribuidor e uma vez no canal | — | — |
| C9 | ~~Corte da tabela de PDVs~~ **Fechado** (rodada 7): os maiores PDVs em tela, busca sobre toda a base ativa, para ver onde o distribuidor deixou de vender no mês | lista compactada no HTML, tabela sob demanda | — |
| C10 | **Arquivos do outro projeto que não vieram**: `config/config.yaml`, `config/geografia.yaml`, `run_pipeline.py`, `run_dashboard.py`, `dashboard/`, `tests/`, `docs/` | reaproveitar utilitários sem reescrever config; entender publicação | Pasta do projeto gerencial |

Situação após a rodada 3: C2 resolvido; C1 indisponível por ora. Continuam abertos C3 (data de início; sem ela a segmentação depende do primeiro mês em que o distribuidor aparece entre jul/25 e jul/26, e os 70 presentes em jul/25 só podem ser "Base atual"), C4 (base RTM com CNPJ), C5 (clusters), C6 e C7 (chaves da Mtrix), C3 (data de início dos distribuidores), C10 (arquivos do outro projeto). Decisão nova a tomar: **rótulo do supervisor** no painel: o território do de-para ("Supervisor MG") ou o N3 da hierarquia com nome ("1140 - Superv_MG - BONIFACIO ARAUJO"), que é o formato que o protótipo usava ("BONIFÁCIO (4300)").

### 5.4 Rodada 4 (08/09/2026) · respostas com dado

**CNPJ dos clientes RTM (C4).** Confirmado: nenhuma base tem CNPJ ao lado do código interno de cliente. Procurei coluna com "CNPJ" no nome e coluna com valores de 14 dígitos em sell-in, Canais, Hierarquia_Consolidada, Hierarquia_Clientes_Faltando, RTM_DePara e Produtos: nada. Só o `Distribuidores_DePara.xlsx` tem CNPJ, e só de distribuidor. Fica para você buscar (o cadastro SAP do cliente tem CNPJ): uma coluna `CNPJ` no próprio `RTM_DePara_Transicao.xlsx` resolve.

**Segmentos da Mtrix (C5).** São 34 valores em `Segmento do PDV`. Em jun/26, PDVs com kg > 0 e participação:

| Segmento Mtrix | PDVs | % | Segmento Mtrix | PDVs | % |
|---|---:|---:|---|---:|---:|
| AS 01 A 04 CK | 24.971 | 37,1 | BOMBONIERE/DOCERIA | 461 | 0,7 |
| MERCEARIA/EMPÓRIO | 10.357 | 15,4 | AS 20+ CK | 289 | 0,4 |
| LOJA DE CONVENIÊNCIA | 5.035 | 7,5 | LOJA DE VARIEDADES | 233 | 0,3 |
| AS 05 A 09 CK | 4.299 | 6,4 | BANCA DE JORNAL | 189 | 0,3 |
| OUTROS | 4.108 | 6,1 | HOTEL/MOTEL | 171 | 0,3 |
| PADARIA/CONFEITARIA | 3.304 | 4,9 | SORVETERIA | 78 | 0,1 |
| AS 10 A 19 CK | 2.836 | 4,2 | NATURAIS | 63 | 0,1 |
| FARMÁCIA/PERFUMARIA | 2.569 | 3,8 | CASH & CARRY | 60 | 0,1 |
| NC | 1.664 | 2,5 | CANTINAS | 50 | 0,1 |
| DISTRIBUIDOR/ATACADISTA | 1.306 | 1,9 | ROTISSERIA / DELICATESSEN | 37 | 0,1 |
| BAR/CASA NOTURNA | 1.290 | 1,9 | ACADEMIAS | 27 | 0,0 |
| RESTAURANTE | 1.110 | 1,6 | QUIOSQUE | 22 | 0,0 |
| TRADICIONAL | 850 | 1,3 | LOJA DE FESTAS | 19 | 0,0 |
| LANCHONETE | 802 | 1,2 | LOJA DE VP | 15 | 0,0 |
| VAREJÃO HORTIFRUTI | 592 | 0,9 | CAFETERIA | 9 | 0,0 |
| ADEGA/EMPÓRIO | 524 | 0,8 | CINEMA/TEATRO | 9 | 0,0 |
| | | | EVENTOS/BUFFET | 8 | 0,0 |
| | | | ORGÃO INSTITUCIONAL | 5 | 0,0 |

Decisão: fazer um **de-para** (`Clusters_DePara.xlsx`, colunas `SEGMENTO MTRIX` e `CLUSTER PAINEL`, uma linha por segmento acima). Enquanto ele não existir, o painel usa os 34 como vêm. Sugestão de partida, para você validar, não aplicada: os 5 "AS …/MERCEARIA" como estão; os outros 29 em um ou poucos grupos.

**jul/26 (C6).** Decidido: reextração. Até chegar, jul/26 fica fora do cálculo (mês de referência = jun/26).

**Códigos curtos de PDV (C7).** Sua hipótese está certa: são PDVs **anonimizados pela Mtrix por LGPD**. Nessas linhas `Razão Social PDV` e `Endereço PDV` valem `LGPD MTX -129746`, e `Cód. PDV` = `CNPJ Reduzido` = o mesmo número negativo. Em jun/26: 27.080 linhas, **6.187 PDVs (9,3% dos PDVs do mês)**, 31,6 t (2,7% do volume), em 56 distribuidores (mais em FRANCAL São Luís, EBD Pará, AVANTE, A S DA S E SILVA). UF, cidade, bairro, CEP e segmento vêm preenchidos. O id anonimizado é **estável entre meses**: 52% dos ids LGPD de jun/26 já existiam em mai/26, contra 64% dos CNPJs normais, ou seja, recorrência parecida. Conclusão: entram no cálculo como PDV, com o id negativo como chave; só não cruzam com CNPJ externo (RTM, cadastro). Exemplos de linha:

| Coluna | Exemplo 1 | Exemplo 2 | Exemplo 3 |
|---|---|---|---|
| Agente de Distribuição | EBD (Pará) | PROPEC DISTRIBUIDORA LTDA | EBD - S. BERNARDO DO CAMPO SP |
| Cód. PDV = CNPJ Reduzido | -129746 | -3702432 | -3892847 |
| Razão Social PDV | LGPD MTX -129746 | LGPD MTX -3702432 | LGPD MTX -3892847 |
| UF / Cidade / Bairro / CEP | PA / BARCARENA / CENTRO / 68445000 | RR / BOA VISTA / AEROPORTO / 69310000 | SP / SAO BERNARDO DO CAMPO / COOPERATIVA / 09852060 |
| Segmento do PDV | AS 01 A 04 CK | OUTROS | OUTROS |
| SKU · kg · R$ (jun/26) | 9010541 · 0,15 · 4,80 | 9010541 · 0,45 · 15,90 | 9012167 · 0,10 · 6,04 |

**PDV com dois distribuidores no mês (C8).** O caso é: o mesmo `Cód. PDV` tem sell-out, no mesmo mês, vindo de dois `CNPJ do AD.` diferentes. Em jun/26 são 1.601 PDVs. Usando o nome reduzido do de-para (base, não inferência): **1.156 são duas filiais do mesmo distribuidor** (ex.: EBD São Paulo e EBD S. Bernardo, 4,7 kg e 5,0 kg no mesmo PDV; V.M. Santo Antônio de Jesus e VM Senhor do Bonfim, 47,2 kg cada) e **445 são distribuidores realmente diferentes** (ex.: SANCHES FRATA LTDA com SINAIS 7,2 kg e TOP SERVICE 10,8 kg; um PDV LGPD com CSR 6,0 kg e SULGERAIS 3,6 kg; um PDV da Bahia com MAM, V.M. e VM). **Regra confirmada (08/09, rodada 5): o PDV conta em cada distribuidor e uma vez no canal.** Consequência: a soma de `cobertura_pdv` dos distribuidores é maior que a do canal (em jun/26, 68.419 pares distribuidor × PDV contra 66.788 PDVs); o mesmo vale para a base ativa. Segmento (Base atual / Novos) e supervisor seguem a regra do distribuidor: PDV conta em cada segmento ou supervisor em que tem distribuidor; no total do canal, uma vez.

### 5.5 Rodada 6 (08/09/2026) · CNPJ do RTM, rótulo do supervisor, tabela de PDVs

**Base RTM com CNPJ (C4 resolvido).** O `RTM_DePara_Transicao.xlsx` ganhou a coluna `CNPJ`: 1.762 preenchidos, 1.762 distintos, todos com 14 dígitos, zero duplicado. Cruzamento com a Mtrix (PDV com kg > 0, chave normalizada), só leitura:

| Mês | Clientes RTM com sell-out na Mtrix |
|---|---:|
| 2025-07 | 119 |
| 2025-08 | 118 |
| 2025-09 | 129 |
| 2025-10 | 175 |
| 2025-11 | 175 |
| 2025-12 | 245 |
| 2026-01 | 171 |
| 2026-02 | 236 |
| 2026-03 | 264 |
| 2026-04 | 240 |
| 2026-05 | 273 |
| 2026-06 | 258 |
| 2026-07 | 279 |

- **592 dos 1.762 (34%)** aparecem em algum mês da Mtrix; **1.170 nunca aparecem** nos 13 meses. A curva cresce ao longo da série (119 em jul/25 para 279 em jul/26), coerente com uma migração em andamento.
- Em jun/26, o distribuidor que vendeu ao cliente na Mtrix **nem sempre é o do de-para**: dos 175 encontrados, 65 batem pelo primeiro token do nome e 110 não. Parte é grafia (A.S DA S E SILVA × A S DA S E SILVA), parte é distribuidor diferente de fato (SINAIS no de-para, TOP SERVICE na Mtrix; CHUA no de-para, DIN na Mtrix). Não foi aplicada nenhuma regra: fica como medida para você validar com o Comercial.
- Para a visão RTM à parte, o que a base permite: por mês, quantos dos 1.762 estão positivados na Mtrix, por qual distribuidor, com que volume. O que falta: a **data de migração** de cada cliente (para separar "ainda não migrou" de "migrou e não comprou").

**Rótulo do supervisor (decidido).** Concatenação `código - função - nome` do N3 da `Hierarquia_Consolidada` (ex.: `4120 - Exec Ctas_SPC 2 - MAURO MALPELI`), pela ponte `Distribuidores_DePara.Cód. Interno Cliente` → `CÓDIGO CLIENTE`. É exatamente o que `src/extract/cadastros.py::_rotulo_concatenado` já monta (`SUPERVISOR = (N3) CÓDIGO SUP./EXEC. - (N3) SUP./EXEC. - (N3) NOME SUP./EXEC.`). Cobre 70 dos 79 distribuidores. **Os 9 fora da hierarquia** (RAYO, KRUPER, NORTESUL, MMD, CBX ativos; CHUA Serra, AVANT, MDB, IREZ E SIQUEIRA inativos) não têm N3: para eles a única informação é o território do de-para ("Supervisor GO/DF/TO"). Decidir: incluí-los na `Hierarquia_Consolidada` (caminho limpo) ou exibir o território como rótulo de exceção.

**Tabela nominal de PDVs (C9 decidido).** Exibir alguns PDVs e ter um filtro de busca. Para a busca funcionar, a lista completa (66 mil PDVs do mês, ou ~125 mil da base ativa) precisa estar no HTML em forma compacta e a tabela renderizada sob demanda pelo filtro. Estimativa: 66 mil × 8 campos ≈ 6 a 8 MB em JSON cru, 1 a 2 MB compactado (o padrão gzip+base64 do `run_dashboard` do outro projeto). Duas definições que faltam: **quais PDVs aparecem antes da busca** (ex.: os N maiores por kg do distribuidor selecionado) e **qual universo entra na busca** (só positivados no mês ou toda a base ativa).

### 5.6 Rodada 7 (08/09/2026) · RTM em migração, distribuidores fora da hierarquia, busca de PDVs

**Base RTM.** Confirmado: a migração está em andamento e o comportamento medido (592 de 1.762 já com sell-out via distribuidor; 119 em jul/25 para 279 em jul/26) é o esperado. Não precisa de data de migração. A visão RTM à parte fica definida como: por mês, quantos dos 1.762 CNPJs estão positivados na Mtrix, sob qual distribuidor, com que volume; os demais aparecem como "ainda sem sell-out via distribuidor". C4 fechado.

**Os 9 distribuidores fora da `Hierarquia_Consolidada`.** Decisão: **não incluir**; eles não vão mais comprar da Dori. Peso deles em jun/26, para registro: 1.107 PDVs (1,7%) e 19,6 t (1,7%), quase tudo RAYO Brasília (802 PDVs, 17,1 t) e NORTESUL Capivari (264 PDVs, 2,0 t); KRUPER, CBX e MMD são residuais; os 4 inativos já não têm sell-out em jun/26. Leitura da decisão: esses CNPJs saem do painel (não entram em distribuidor, segmento, supervisor nem no total do canal). Como o `Status` do de-para ainda diz "Ativo" para 5 deles, a regra fica registrada aqui como lista explícita, não inferida: `Cód. Interno Cliente` sem linha na `Hierarquia_Consolidada` = fora do painel. Se preferir mantê-los no total do canal sem supervisor, basta dizer.

**Tabela de PDVs (C9 fechado).** Exibir os **maiores PDVs** e ter busca sobre **toda a base ativa** (PDVs com compra na janela de 5 meses), não só os positivados no mês. Objetivo declarado: ver onde o distribuidor deixou de vender no mês, ou seja, PDV da base ativa **sem** positivação no mês. Consequências para o modelo:
- `pdvs[]` passa a ser a base ativa por distribuidor (em jun/26, ~130 mil pares distribuidor × PDV na janela de 6 meses; com 5 meses um pouco menos), com `positivado_mes` = sim/não.
- Campos que a Mtrix fornece para essa leitura, todos diretos da base: `positivado_mes`, `positivado_mes_anterior`, `meses_positivado_janela`, **último mês com compra** e **kg do último mês com compra** (dois campos novos, candidatos ao inventário), cluster, UF, cidade.
- Ordenação "os maiores": por kg na janela (soma dos meses da base ativa), o que traz ao topo o PDV grande que sumiu. Critério a confirmar.
- Tamanho: a lista completa vai compactada no HTML e a tabela é montada pelo filtro; estimativa 2 a 3 MB compactados para ~130 mil linhas com 10 campos.

## 6. Perguntas abertas da rodada 1 (histórico; as respondidas estão em 5.1)

1. **Denominador da DN.** O contexto desta tarefa diz "universo RTM"; a sessão anterior fixou "base ativa = PDVs com compra na janela". As bases só suportam a segunda hoje. Confirma base ativa por janela? Se for universo RTM, de onde vem a lista de PDVs por CNPJ?
2. **Janela da base ativa: 5 ou 6 meses?** Em jun/26 dá 120.221 ou 125.541 PDVs (DN 55,6% ou 53,2%).
3. **Positivado** = linha com `# Sell-Out (Quilos) > 0`? Ou qualquer linha, mesmo com kg ≤ 0 (até 88 linhas por mês)?
4. **Identidade do distribuidor**: CNPJ (filial) ou nome/razão (CHUA, EBD, ZAFFALON, DAB, NORDIL, CHOCOSUL, FRANCAL têm mais de uma praça)? O protótipo tratava EBD por praça e CHUA como um.
5. **Identidade do PDV**: `Cód. PDV` normalizado a 14 dígitos, aceitando os 6% de códigos curtos como PDVs válidos? Ou descartar/relatar os que não são CNPJ?
6. **PDV atendido por dois distribuidores no mesmo mês**: conta nos dois e uma vez no canal?
7. **Mapa de clusters**: os 29 segmentos fora dos 5 "AS/Mercearia" viram "Outros segmentos", como no protótipo, ou você quer agrupamentos (conveniência, padaria, farmácia, atacado)?
8. **Regra dos 6 meses com histórico censurado**: os 70 distribuidores presentes desde jul/25 são "Base atual"; os 6 que entraram depois são "Novos" enquanto tiverem ≤ 6 meses. Serve, ou existe uma data de início por distribuidor no Comercial?
9. **Mtrix de jul/24 a jun/25**: dá para pedir? Sem ela o comparativo LY só existe em jul/26.
10. **Ponte distribuidor ↔ hierarquia**: quem fornece o de-para `CNPJ do AD.` ↔ `CÓDIGO CLIENTE` (para supervisor)? Alternativa: de-para manual por nome para os ~70 distribuidores.
11. **Base RTM**: fica realmente fora da visão base (Fase 6)? Se sim, o chip "Novos distribuidores" continua sendo só a regra de 6 meses.
12. **Tabela nominal de PDVs**: 66 mil linhas no HTML ou um corte (por distribuidor selecionado, top N por volume, só os que mudaram de status)?
13. **Arquivos que faltaram do outro projeto**: `config/config.yaml`, `config/geografia.yaml`, `run_pipeline.py`, `run_dashboard.py`, `dashboard/`, `tests/`, `docs/`. Devo criar um `config.yaml` novo para o DN ou você prefere trazer os originais como referência?
14. **Mês de referência**: o painel fecha em jul/26 (último arquivo) ou em jun/26 (último mês com chave íntegra)? Vale a regra "último mês fechado" e jul/26 entra depois de normalizado?
