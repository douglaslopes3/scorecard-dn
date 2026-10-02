# Fase 0 · Auditoria completa do Dashboard DN (09/09/2026)

Modo: **somente leitura**. Nada foi criado, alterado, movido ou executado dentro da pasta `DN/`.
Para inspecionar, rodei apenas leituras: `find`/`ls`/`cat`, `pyarrow.parquet.read_metadata`, `pandas.read_parquet`,
`pandas.read_excel(engine="calamine")`, e um script Node no scratchpad da sessão que só **lê** o HTML gerado para medir o
custo de descompactar a lista de PDVs. O navegador embutido desta sessão não abre `file://`, então o tempo de
carregamento real não foi medido aqui (ver 0.5.4). O único arquivo escrito é este relatório, fora do projeto.

---

## 0.0 Ambiguidades e contradições no prompt (regra 6 — antes de qualquer ação)

| # | Onde | O que conflita | O que preciso que você decida |
|---|---|---|---|
| A1 | Regra 1 (escopo isolado) × estado da pasta | `src/`, `ferramentas/`, `data/curated`, `data/staging`, `data/quality`, `data/raw` e `bases/Sell In`, `bases/Canais`, `Hierarquia_Clientes_Faltando.xlsx` são do **projeto gerencial** (sell-in, metas) e estão dentro de `DN/`. O pipeline DN não importa nada deles. | Podem sair da pasta DN (mover para fora / apagar)? Ou ficam e eu apenas ignoro? |
| A2 | Fase 5 "replicar o padrão do Painel Gerencial" × Regra 1 | A pasta-mãe `Painéis - Alavancas/` contém **só** `DN/`. O projeto gerencial não está acessível daqui. | Me passar o caminho da pasta de publicação do Painel Gerencial (ou descrever o padrão: nome da pasta, o que entra, como é compartilhado no SharePoint). |
| A3 | Fase 3 "usuário não pode acessar o dataset completo pelo export nem pelo código-fonte" × Fase 3 "busca por texto livre" e Fase 4 "drill com lista detalhada" | Hoje a busca de PDVs só funciona porque a base ativa **inteira** (124.395 pares) viaja embutida no HTML (gzip+base64, 4,9 MB) e os 1.762 clientes RTM estão renderizados na íntegra. Em HTML offline, **tudo que é pesquisável está no arquivo**. Não existe como buscar sobre "toda a base" e ao mesmo tempo impedir o acesso pelo código-fonte sem um servidor. | Escolher: (a) manter embutido e aceitar que quem abrir o fonte vê tudo (só o **botão** de exportar respeita o filtro); (b) embutir somente a amostra visível + agregados (perde a busca sobre a base inteira); (c) servidor/SharePoint com API (fora do padrão HTML único). |
| A4 | Fase 4.1 "migração em set/2026, visão principal a partir de 01/09/2026" × dados e decisões registradas | A série da Mtrix termina em **jul/26**; ago e set/26 ainda não existem. A visão "a partir da migração" nasceria **vazia** até a Mtrix de set/26 chegar (~out/26). Além disso, a rodada 7 (08/09) registrou "RTM em migração é normal, sem data de migração", e 199 clientes RTM já compram do destino desde jul/25. | Confirmar: a data de corte 01/09/2026 vale para **todos** os 1.762 clientes? O que o painel deve mostrar nos meses sem dado (vazio explícito, ou "histórico completo" como padrão até set/26 entrar)? |
| A5 | Fase 2 "carregamento lazy" × arquitetura atual | O painel é um HTML único renderizado **em Python** (Handlebars mínimo). Lazy de verdade exige renderizar no navegador a partir de um JSON embutido (troca de arquitetura do template). Alternativa barata: abas que só **exibem** blocos já renderizados (sem ganho de parse). | Aceita trocar a renderização das tabelas grandes (PDVs e RTM clientes) para JS a partir de dados embutidos? |
| A6 | Fase 3 "exportação XLSX" × HTML offline sem dependências externas | Gerar XLSX no navegador exige embutir uma biblioteca (SheetJS ≈ 0,8–1 MB minificado) no HTML. CSV é nativo. | XLSX obrigatório (aceita +1 MB no arquivo) ou CSV basta? |
| A7 | Fase 1 "consolidar TODAS as rotinas" | As "rotinas" hoje são `run_fase1.py` + `run_fase2.py` (DN) e os scripts de `ferramentas/` (gerencial, quebrados aqui). | Confirmar que o orquestrador cobre só o DN (Fase 1 + Fase 2 + publicação), e que `ferramentas/` fica de fora. |
| A8 | Fase 4.6 colunas padronizadas | "Razão social" do cliente RTM: a base RTM só tem `Bandeira cliente [Antigo]`; a razão social existe apenas na Mtrix (`Razão Social PDV`) para quem já apareceu em algum sell-out (592 de 1.762). "Data da última compra": a Mtrix é **mensal**, não há dia. "Distribuidor que atendeu": a fato tem o **CNPJ** do distribuidor; o código interno (SAP) vem do de-para. | Aceita "mês da última compra" no lugar de data? Razão social = bandeira antiga quando não houver Mtrix (rotulado como tal)? Distribuidor que atendeu = nome reduzido + CNPJ? |
| A9 | Regra 3 "nenhum valor de negócio hardcoded" × regra "não corrija por conta própria" | Encontrei rótulos fixos (lista em 0.3.2). Não corrigi nada. | Aprovar item a item o que vai para config (na Fase 1). |

---

## 0.1 Inventário do projeto

### 0.1.1 Estrutura e responsabilidade

| Caminho | Tipo | Responsabilidade | Situação |
|---|---|---|---|
| `README.md` | doc | visão geral, como rodar, regras | **ativo** (idêntico a `dn/README.md` — duplicado) |
| `dn/README.md` | doc | cópia byte a byte do `README.md` da raiz | **duplicado** |
| `Scorecard_DN_v1.html` (1,5 MB) | HTML | protótipo original com **dados simulados** (UFJ, PENJ, EX3, PLANJ, HERO…) | **órfão**: só referenciado por `template/tools/*` (aposentados). Risco de ser aberto/compartilhado como se fosse o painel |
| `run_fase1.py` | script | ingestão Mtrix + cadastros → `data/dn/curated/` + qualidade | ativo (~3,7 min) |
| `run_fase2.py` | script | métricas DN → `DN_*.parquet` + JSON + HTML | ativo (~1 min) |
| `config/config.yaml` | config | fontes, regras, validação, painel | ativo |
| `dn/` (14 .py) | pipeline | `extract/` (cache, cadastros, sellout), `transform/` (calendario, dimensoes, fato), `load/parquet.py`, `metrics.py`, `painel.py`, `render.py`, `qualidade.py`, `utils/` (config, log, texto) | ativo |
| `dn/**/__pycache__/` | temporário | bytecode | lixo regenerável |
| `src/` (15 .py) | pipeline **gerencial** | sell-in, metas, saneamento, cubos | **fora de escopo**; não é importado por nada do DN |
| `ferramentas/` (4 .py + LEIA-ME) | scripts gerencial | diagnóstico de cobertura, análise bandeira RTM, limpar painéis, comparar painéis | **quebrados aqui**: importam `src.*` e `run_dashboard`/`run_pipeline`, que não existem em `DN/` |
| `template/template.html` (105 KB) | template | **fonte da verdade** do painel (Handlebars) | ativo |
| `template/Scorecard_DN_base.html` | exemplo renderizado | prova byte a byte do renderizador | ativo, mas retrato de jun/26 **sem** receita e **sem** bloco RTM |
| `template/example-data.json` / `.raw.json` | snapshot | dados de exemplo (jun/26, 08/09 20:56) | **desatualizado** (anterior a receita e RTM) |
| `template/data-inventory.json` | contrato | 227 campos (origem: 167 calculado, 36 RTM, 24 M3) | ativo |
| `template/business-rules.md`, `01-analise-prototipo.md` | doc | regras e análise do protótipo | histórico |
| `template/tools/build.py`, `extract_proto.py`, `proto.json` (235 KB) | ferramentas | geraram a 1ª versão do template a partir do protótipo | **aposentados** (README manda não rodar) |
| `data/dn/staging/` (36 arquivos, 105 MB) | cache | Parquet+JSON por arquivo de origem, chave = versão+tamanho+mtime+hash | ativo; cache do RTM e da Hierarquia ficará **obsoleto** na próxima execução (arquivos mudaram) |
| `data/dn/curated/` (19 Parquet + resumo.json) | curated | fato, dimensões e tabelas DN_* | ativo |
| `data/dn/painel/` | saída | `painel_dn.json` (6,9 MB), `painel_dn.raw.json` (6,9 MB), `Scorecard_DN_2026-07.html` (6,1 MB), `Scorecard_DN_2026-06.html` (5,3 MB) | jun/26 é **versão antiga**; `.raw.json` é intermediário |
| `data/dn/quality/` (8 arquivos) | qualidade | relatório + CSVs de exceção | ativo |
| `data/dn/logs/` (21 logs) | log | um por execução, mantém 30 | ativo |
| `data/curated/` (73 MB, `cubos.json` 52 MB), `data/staging/` (35 MB), `data/quality/`, `data/raw/sell_in` (vazio) | saídas **gerencial** | sell-in set/24–set/26, metas FY27 | **fora de escopo** (108 MB) |
| `bases/Sell Out - MTRIX/` (13 xlsx, 497 MB) | base | fonte única da DN | ativo |
| `bases/Bases para tabelas dimensões/` | bases | Produtos, Distribuidores_DePara, Hierarquia_Consolidada, Clusters_DePara (usadas); `Hierarquia_Clientes_Faltando.xlsx` (não usada pelo DN) | ativo |
| `bases/RTM-Transicao/RTM_DePara_Transicao.xlsx` | base | clientes RTM → destino | ativo |
| `bases/Sell In/` (27 xlsx, 93 MB) | base gerencial | usada uma vez para a medição C3 (docs) | **não usada** pelo pipeline DN |
| `bases/Canais/Canais.xlsx` | base gerencial | canal/subcanal por cliente | **não usada** pelo DN |
| `docs/` (6 md) | doc | decisões por rodada, fases 1–3, C3 | ativo |

### 0.1.2 Duplicações, versões antigas, código morto e dependências quebradas

- **Duplicados**: `README.md` = `dn/README.md`; `dn/utils/{config,log,texto}.py` e `dn/extract/cache.py` são cópias adaptadas de `src/utils/*` e `src/extract/cache.py` (duas linhagens do mesmo código na mesma pasta); `painel_dn.json` ≈ `painel_dn.raw.json` (mesmo conteúdo, um formatado).
- **Versões antigas**: `Scorecard_DN_2026-06.html`; `template/example-data*.json` e `Scorecard_DN_base.html` (jun/26, sem RTM); `Scorecard_DN_v1.html` (protótipo).
- **Código morto no template**: 90 funções JS, **35 nunca chamadas** (`acexp, acgo, aclimpa, acpick, acpickd, acqueda, catsup, ddview, dnDraw*, dngo, dnlev, dnlev2, dnview, dohsw, drill, fcat, hexp, offil, ofsort, p20m, p20s, pdcut, pdexp, pdfilt, pdfq, pdlimpa, pdpick, pdsupf, pdt20, setu, sety, showdd, showpane, stcf, toggleAll`; `dnDraw` é chamada por `forEach`, então é viva). Três rotinas de export CSV do protótipo (`historico_*`, `ponderada_top20`, `plano_de_acao_*`) estão mortas; **nenhuma tabela do DN tem exportação hoje**. Stubs `HERO`, `HVK`, `acap`, `pdap` sobrevivem do protótipo. Um comentário HTML `<!-- TODO -->` está **dentro de um `<script>`** (válido, mas frágil). O literal `34.26` (preço fixo R$/kg do protótipo) ainda existe em código morto.
- **Dependências quebradas**: `ferramentas/*.py` → `src.*`, `run_dashboard`, `run_pipeline` (inexistentes em DN). `template/tools/README.md` cita `python tools/extract_proto.py` (aposentado).
- **Bases alteradas depois da última execução** (Fase 1 às 11:48, Fase 2 às 14:28 de 09/09): `RTM_DePara_Transicao.xlsx` (16:18) e `Hierarquia_Consolidada.xlsx` (17:22). Conferi o conteúdo: a RTM continua com 1.762 linhas e 27 destinos; a hierarquia continua com 13.516 clientes e os mesmos 9 distribuidores fora. **O painel publicado não está errado, mas o pipeline não tem como saber disso** (não há verificação de "base mais nova que o curated"). `Hierarquia_Clientes_Faltando.xlsx` também mudou (16:24) — não é lida pelo DN.

---

## 0.2 Auditoria das bases

| Base | Origem | Granularidade | Chave primária | Chaves de junção | Volume | Última atualização | Como é atualizada |
|---|---|---|---|---|---|---|---|
| `Sell Out - MTRIX/ScoreCard_Mtrix_MM.AAAA.xlsx` (aba Sheet1) | extração Mtrix (sell-through) | mês × CNPJ distribuidor × PDV × SKU | (`Ano/Mês`, `CNPJ do AD.`, `Cód. PDV`, `SKU`) — zero duplicados em 5.851.509 linhas | `CNPJ do AD.` → Distribuidores_DePara; `SKU` → Produtos; `Cód. PDV` (CNPJ 14 dígitos / id LGPD negativo / OUTRO) → RTM por CNPJ | 13 arquivos, 497 MB, 382k–523k linhas/mês, jul/25–jul/26 | 07.2026 em 09/09 10:40 (reextraído); demais 12–19/08 | manual: alguém exporta da Mtrix e solta o arquivo na pasta; a competência vem do conteúdo, não do nome |
| `Produtos.xlsx` (aba Produtos) | cadastro de produtos | SKU | `Código Produto` (1.712 SKUs; 287 movimentados) | `SKU` da Mtrix | 72 KB | 18/08/2026 | manual |
| `Distribuidores_DePara.xlsx` (Planilha1) | de-para construído na rodada 3 | CNPJ de filial | `CNPJ DISTRIBUIDOR` (79) | `Cód. Interno Cliente` → Hierarquia; **`Distribuidora Nome Reduzido` → RTM (junção por texto)** | 79 linhas | 09/09/2026 11:41 (coluna `Data de Cadastro` incluída) | manual pelo Douglas |
| `Hierarquia_Consolidada.xlsx` (Planilha1) | estrutura comercial (ERP/BI) | cliente × vendedor (N4) | `CÓDIGO CLIENTE` (13.516 distintos; 1ª linha vence) | ← `Cód. Interno Cliente` | 3,3 MB | 09/09/2026 17:22 (**depois** da última execução) | manual |
| `RTM_DePara_Transicao.xlsx` (aba De-Para RTM) | lista de clientes migrados Dori → distribuidor | cliente | `CNPJ` (1.762, 100% preenchido, 0 duplicados) | `CNPJ` → `Cód. PDV` da Mtrix; `Dsitribuidor Nome Reduzido` → de-para por **nome** | 1.762 linhas, 27 destinos | 09/09/2026 16:18 (**depois** da última execução) | manual. Aba `Descobrir Código` lista "NOVO RIBEIRÃO PRETO" e "NOVO SJRP" = destinos ainda sem cadastro |
| `Clusters_DePara.xlsx` (aba De-Para) | criado na rodada de 09/09 | segmento Mtrix | `SEGMENTO MTRIX` (34 → 12 clusters) | ← `Segmento do PDV` | 40 linhas (34 + apoio) | 09/09/2026 12:06 | manual; lido **diretamente na Fase 2** (não passa pela Fase 1) |
| `Canais.xlsx`, `Hierarquia_Clientes_Faltando.xlsx`, `Sell In/*.xlsx` | gerencial | — | — | — | 94 MB | ago–set/26 | **não usadas pelo DN** |

Observações de integridade:
- **Junção por nome** RTM ↔ de-para (`Dsitribuidor Nome Reduzido` vs `Distribuidora Nome Reduzido`): qualquer grafia diferente vira "sem cobertura" em silêncio. Hoje casa 22 de 27 nomes.
- `Status` do de-para (75 Ativo / 4 Inativo) **não exclui ninguém**; só a ausência na hierarquia exclui (9 distribuidores, 5,4% do kg).
- 32 dos 64 distribuidores com data de cadastro têm 10/12/2013 (carga do ERP, não início real).
- Mtrix: 73 PDVs com chave OUTRO, 17.854 LGPD; PDVs distintos calculados ficam 1–10 abaixo do total da Mtrix em 9 meses (informativo).

---

## 0.3 Rastreabilidade: visual → origem

### 0.3.1 Tudo que aparece no painel (`Scorecard_DN_2026-07.html`)

Legenda de arquivos: **MTX** = `bases/Sell Out - MTRIX/*.xlsx`; **DEP** = `Distribuidores_DePara.xlsx`; **HIE** = `Hierarquia_Consolidada.xlsx`; **RTM** = `RTM_DePara_Transicao.xlsx`; **PRO** = `Produtos.xlsx`; **CLU** = `Clusters_DePara.xlsx`; **CFG** = `config/config.yaml`.

| Visual / métrica | Base | Coluna(s) de origem | Regra (arquivo do pipeline) | Status |
|---|---|---|---|---|
| Cabeçalho: mês de referência, janela da base ativa | MTX | `Ano/Mês` | último mês da série (ou `painel.mes_referencia`); janela = `regras.janela_base_ativa_meses` (5) — `painel.py montar` | OK |
| Gráfico/tabela "Cobertura mês a mês" (PDVs positivados, base atual/novos, LY, Δ%) | MTX + DEP | `# Sell-Out (Quilos)`, `Cód. PDV`, `CNPJ do AD.`, `Data de Cadastro` | positivado = kg>0; contagem distinta de PDV no canal; segmento pela maturidade (>6 meses) — `metrics.serie_nivel`, `_stack`; Δ calculados no **JS** (`dnVar`) a partir da série | OK (fórmulas duplicadas Python/JS) |
| Cards KPI por segmento (base ativa, cobertura, % DN, volume t, kg/PDV, sem compra no mês) + 3 comparativos | MTX | idem | base ativa = PDVs com kg>0 em ≥1 dos 5 meses; DN = cobertura ÷ base ativa; sem compra = base ativa − cobertura — `metrics.serie_nivel/comparativos`, `painel._metricas` | OK |
| Tabela por cluster de loja (×3 segmentos) | MTX + CLU | `Segmento do PDV` → `CLUSTER PAINEL` | mesmo cálculo por cluster; PDV conta uma vez no nível — `metrics.calcular` níveis `cluster`, `cluster_canal` | OK |
| Tabela de supervisores (+ drill série mensal) | MTX + DEP + HIE | `Cód. Interno Cliente` → `(N3) CÓDIGO/SUP./NOME` | rótulo "código - função - nome"; série por SUP — `cadastros._rotulo_concatenado`, `dimensoes.dim_distribuidor` | OK |
| Tabela por categoria (PDVs, % cobertura, penetração, volume, Δ) | MTX + PRO | `SKU` → `Categoria` | cobertura da categoria ÷ base ativa do canal; penetração ÷ positivados do canal — `serie_nivel(cat=True)` | OK |
| Tabela de distribuidores (supervisor, segmento, meses de histórico, KPIs, Δ) + 70 drills | MTX + DEP + HIE | `CNPJ do AD.`, `DESCRIÇÃO DISTRIBUIDOR MTRIX`, `Distribuidora Nome Reduzido`, `Status`, `Data de Cadastro` | maturidade pela data de cadastro, senão 1º mês na Mtrix (censurado, "≥"); exclui sem hierarquia — `metrics.carregar` | OK |
| Tabela "Pontos de venda" (1.400 linhas renderizadas = 20 × 70) + lista completa (124.395 pares via blob) | MTX + RTM + CLU | `Cód. PDV`, `Razão Social PDV`, `UF/Cidade/Bairro PDV`, kg por mês; `CNPJ` da RTM para a coluna RTM | `metrics.pdvs_base_ativa`, `painel.blob_pdvs`; top N = `painel.pdv_top_por_distribuidor` | OK |
| RTM: Base RTM (1.762), rastreáveis (1.309), sem cobertura (453) | RTM + DEP | `CNPJ`, `Dsitribuidor Nome Reduzido` ↔ `Distribuidora Nome Reduzido` | ver 0.6 — `metrics.rtm_aderencia` | OK, regra ambígua (0.6) |
| RTM: aderência, compraram do destino, só de outro, não compraram, ativados, ativados parados, kg no destino/vazados, % vazamento R$ | RTM + MTX + DEP | `CNPJ` → `Cód. PDV`; `CNPJ do AD.` ∈ CNPJs do nome de destino | certo = comprou de qualquer filial do destino no mês; só outro = comprou só de terceiros; ativação = 1º mês com compra certa — `rtm_aderencia` | OK |
| RTM: tabela Evolução (13 meses), Destinos (27), Clientes (1.762: nome = `Bandeira cliente [Antigo]`, cidade/UF da Mtrix) | RTM + MTX | idem | `painel._rtm` | OK (cidade/UF vazias para quem nunca apareceu na Mtrix) |
| Notas da visão (texto) | — | — | texto fixo no template | ver 0.3.2 |

Conclusão: **todo número exibido é rastreável até uma base da pasta**; não há mock nem dado externo renderizado. O que não vem de base são **rótulos e parâmetros fixos**, listados abaixo.

### 0.3.2 Em destaque: o que NÃO vem das bases (não corrigido — aguarda decisão)

| # | Onde | Valor | Origem correta | Impacto de corrigir |
|---|---|---|---|---|
| H1 | `template/template.html` · Notas da visão | texto "**últimos 5 meses**" | `config: regras.janela_base_ativa_meses` (já existe; o texto não lê o config) | baixo: passar como campo do JSON (`periodo.janela_meses`) |
| H2 | idem | "Base atual acima de **6 meses**, Novos até 6" (aparece 3×) | `regras.segmento_novos_meses` | baixo: idem |
| H3 | template · título | "Cobertura mês a mês · **13 meses**" | tamanho real da série (`meta_execucao.meses_serie`) | baixo |
| H4 | template · select de linhas da tabela de PDVs | **50 / 200 / 1000** | config (`painel.tabela.amostra`, `opcoes`) — cai na Fase 3 | baixo |
| H5 | `dn/painel.py` | `"CANAL DISTRIBUIÇÃO"` (nome do canal) | config | baixo |
| H6 | `dn/metrics.py` `SEG_NOMES`; `dn/painel.py` `_EST` (rótulos dos estados RTM), abreviações de mês | rótulos em código | config de rótulos | baixo |
| H7 | `dn/painel.py` `TOP_PDV` fallback `20`; `gzip compresslevel=9` | defaults técnicos | config (o 20 já está lá; o fallback duplica) | nulo |
| H8 | `dn/render.py` `_FMT_EXTRA` | formatos de 4 campos fora do inventário | `template/data-inventory.json` | baixo |
| H9 | template · JS morto | `34.26` (preço R$/kg do protótipo) | remover com o código morto | nulo (não é exibido) |
| H10 | `template/example-data*.json`, `Scorecard_DN_base.html` | snapshot jun/26 sem RTM/receita | regerar a partir de um painel atual | médio: hoje a validação byte a byte valida um exemplo incompleto |
| H11 | `Scorecard_DN_v1.html` (raiz) | painel inteiro com dados simulados | não é fonte de nada | risco de confusão se compartilhado; proposta: mover para `docs/historico/` ou apagar |
| H12 | `data/dn/painel/Scorecard_DN_2026-06.html` | painel de versão anterior | — | apagar/arquivar |
| H13 | JS do gráfico (`dnVar`, `dnMean`) | recalcula vs mês anterior / L3M / LY no navegador | pipeline já entrega `*_var_*` | risco de divergência entre tabela (Python) e gráfico (JS); hoje batem |

---

## 0.4 Pipeline de atualização

### 0.4.1 Rotinas existentes e ordem

```
[manual] soltar ScoreCard_Mtrix_MM.AAAA.xlsx em bases/Sell Out - MTRIX/
[manual] editar de-paras (Distribuidores, Clusters, RTM, Hierarquia, Produtos)
[manual] se mudou um leitor: subir VERSAO_CACHE em dn/extract/cache.py
  1. python run_fase1.py        (~3,7 min: 215 s lendo Excel com cache frio; segundos com cache)
       cadastros → sell-out (cache staging) → fato + dims → conferências → curated → qualidade
  2. python run_fase2.py [AAAA-MM]  (~1 min)
       carrega curated → LÊ DE NOVO Clusters_DePara.xlsx e RTM_DePara_Transicao.xlsx (direto do Excel)
       → métricas DN_* → JSON raw + formatado → valida renderizador byte a byte → HTML
[manual] abrir o HTML com Ctrl+F5; copiar para onde for compartilhado (não há passo de publicação)
```

### 0.4.2 Diagnóstico

| Problema | Evidência | Risco |
|---|---|---|
| **Dois comandos, sem orquestrador** e sem checagem de pré-requisitos | README manda rodar um e depois o outro | rodar só a Fase 2 com curated velho |
| **A Fase 2 fura a camada curated**: `metrics.carregar` chama `ler_clusters()` e `rtm_aderencia` chama `ler_rtm()` lendo Excel | `dn/metrics.py` | `DIM_PDV.ORIGEM_RTM` (Fase 1) e o bloco RTM (Fase 2) podem vir de **versões diferentes** do mesmo arquivo — exatamente o cenário de hoje (RTM alterada às 16:18) |
| **Nenhuma verificação de base desatualizada** | bases com mtime posterior ao curated não geram aviso | painel publicado sem refletir a base |
| **Cache depende de bump manual** (`VERSAO_CACHE`) | documentado como "erro real" no próprio código | dado velho com checagens verdes |
| **Validação byte a byte contra exemplo desatualizado** | `Scorecard_DN_base.html` é jun/26 sem RTM | a prova cobre menos do que o painel real; e editar o template exige regerar o exemplo (passo manual de 8 linhas de Python no README de tools) |
| **Sem publicação** | saída fica em `data/dn/painel/` junto com JSON e versões antigas | cópia manual, versões antigas convivendo |
| **Duplicação de esforço**: JSON gravado duas vezes (raw + formatado, 6,9 MB cada); duas linhagens de utilitários (`src/` e `dn/`); README duplicado | — | manutenção |
| Log: tem início/fim, linhas lidas, avisos e erros; **não tem** linhas rejeitadas por arquivo como número (rejeição aborta) nem um resumo final "o que foi gerado e por quê" | logs em `data/dn/logs/` | parcial em relação ao requisito da Fase 1 |
| Ponto de quebra já ocorrido: caminho da pasta de sell-out errado no config (09/09) | `docs/rodada_2026-09-09.md §2` | falha explícita — bom; mas mostra ausência de validação de config na partida |
| Aborto no meio da gravação deixa curated parcial (a mensagem já avisa) | `log.abortar(situacao=…)` | curated inconsistente entre tabelas |

---

## 0.5 Navegação, layout e performance

### 0.5.1 Mapa de seções (ordem de aparição) e peso no DOM renderizado (jul/26)

| # | Seção | Conteúdo | Linhas `<tr>` | Peso do DOM |
|---|---|---|---|---|
| 1 | Cabeçalho + barra de filtros (categoria ×11 chips, distribuidor select, segmento ×3 chips) | controles | 0 | 0,6% |
| 2 | Cobertura mês a mês · 13 meses | gráfico SVG + tabela (11 painéis: total + 10 categorias) | — | 0,3% |
| 3 | KPIs + "Os mesmos KPIs por cluster de loja" (×3 blocos de segmento) | 6 cards + tabela de 12 clusters × 3 | 42 | 0,6% |
| 4 | Supervisores (×3 segmentos) + 14 drills de série | tabela 14 sup × 3 + gráficos | 64 | 3,6% |
| 5 | Por categoria · detalhe | 10 linhas | 11 | 0,3% |
| 6 | Distribuidores + 70 drills de série | 70 linhas + 70 gráficos ocultos | 72 | 5,4% |
| 7 | **Pontos de venda · base ativa e oportunidade** | 1.400 linhas renderizadas + blob de 124.395 pares | 1.401 | **40%** |
| 8 | Notas da visão | texto | 0 | 0,1% |
| 9 | **RTM · aderência** (5 cards + abas Evolução 13 / Destinos 27 / Clientes 1.762) | | 1.805 | **49%** |

DOM sem script/style: **1,28 MB**; `<tr>` 3.376; `<td>` 36.777; 116 tags `<script>` (uma por série inline `DN_SERIES[...]`).

### 0.5.2 Inventário de tabelas

| Tabela | Origem (Parquet) | Colunas | Linhas renderizadas |
|---|---|---|---|
| Cluster de loja (× 3 segmentos) | `DN_CLUSTER_MES`, `DN_CLUSTER_CANAL_MES` | 18 (9 métricas + 9 Δ) | 12 × 3 |
| Supervisores (× 3 segmentos) | `DN_SUPERVISOR_MES`, `DN_SUPERVISOR_CANAL_MES` | 18 | 14 × 3 |
| Por categoria | `DN_CANAL_CAT_MES` | 8 | 10 |
| Distribuidores | `DN_DISTRIBUIDOR_MES` + `DIM_DISTRIBUIDOR` | 21 | 70 |
| Pontos de venda | `DN_PDV_BASE_ATIVA` + `DIM_PDV` | 13 | 1.400 (+124.395 no blob) |
| RTM · Evolução | `DN_RTM_MES` | 7 | 13 |
| RTM · Destinos | `DN_RTM_DESTINO` | 10 | 27 |
| RTM · Clientes | `DN_RTM_CLIENTE` + `DIM_PDV` | 9 | 1.762 |

Recursos por tabela hoje: ordenação por clique (protótipo, `stcf`/`ofsort` — parcialmente morta), busca só em PDVs (sem debounce; re-renderiza via `innerHTML` a cada tecla) e RTM Clientes (filtro por estado/destino/texto sobre linhas do DOM). **Nenhuma exportação viva.** Sem paginação/virtualização; limite fixo 50/200/1000 só em PDVs.

### 0.5.3 Como os dados chegam ao front

- Tudo **embutido** no HTML pelo renderizador Python (Handlebars mínimo). Zero `fetch`, zero dependência externa.
- Séries dos gráficos: 116 blocos `<script>` inline preenchendo `DN_SERIES`.
- Lista completa de PDVs: `PDV_BLOB` = JSON posicional (13,8 MB) → gzip → base64 (**4,9 MB**, 80% do arquivo), descompactado no navegador com `DecompressionStream`.
- Payload: HTML **6,1 MB** (script 5,07 MB, dos quais 4,9 MB é o blob; DOM 1,28 MB; CSS 27 KB).

### 0.5.4 Tempo de carregamento e gargalos

- Não medido no navegador nesta sessão (o painel embutido não abre `file://`). Medição de referência em Node: base64→bytes 5 ms, gunzip 51 ms, `JSON.parse` de 13,8 MB **171 ms**, gerando ~124 mil arrays em memória (estimativa 40–60 MB de heap).
- Custo dominante esperado no navegador: parse de 6,1 MB de HTML + construção de **36.777 `<td>`** (dois terços em RTM Clientes e PDVs) + 116 scripts inline; estimativa de 1–3 s em desktop, mais em máquinas fracas; abrir pelo OneDrive sincronizado adiciona o download de 6 MB.
- Gargalos de interação: busca de PDVs re-renderiza a tabela inteira por tecla (sem debounce); filtro RTM percorre 1.762 linhas do DOM; ordenação por cabeçalho reordena o DOM.
- Usabilidade/acessibilidade: **nenhuma** persistência (`localStorage` 0), **nenhuma** navegação por teclado ou ARIA (`tabindex`/`aria-`/`role` = 0), tabelas com `min-width` 900–1.000 px (rolagem horizontal em telas pequenas), scroll único longo.

---

## 0.6 Visão RTM: como nasce o "SEM COBERTURA" (453)

**Lógica exata** (`dn/metrics.py → rtm_aderencia`, executada na Fase 2):

1. Base = `bases/RTM-Transicao/RTM_DePara_Transicao.xlsx`, aba `De-Para RTM`, 1.762 linhas, deduplicadas por `CNPJ` (0 duplicados, 0 sem CNPJ).
2. `DESTINO` = coluna `Dsitribuidor Nome Reduzido` (texto, maiúsculas).
3. Conjunto "no painel" = distribuidores da `DIM_DISTRIBUIDOR` com `NO_PAINEL = True` (tem linha na Hierarquia_Consolidada) **e** `TEM_SELLOUT = True` (apareceu na Mtrix) → 70 CNPJs, agrupados por `NOME_REDUZIDO` (de `Distribuidora Nome Reduzido` do de-para).
4. `COBERTO` = o texto do destino **é igual** a algum `NOME_REDUZIDO` desse conjunto.
5. **Sem cobertura = clientes cujo destino não é coberto.** Não há janela de tempo, não há filtro de compra: é um atributo de **cadastro**, constante nos 13 meses (453 em todos).
6. Esses clientes ficam **fora do denominador** da aderência (1.309 = 1.762 − 453) e, na tabela por destino, as quebras vêm nulas.

**Quem compõe os 453**: PELLAH 280 · NOVO RIBEIRÃO PRETO 91 · NOVO SJRP 75 · DIBS 6 · NOVA ENERGIA DISTRIBUIDORA LTDA 1. Conferi contra as bases atuais: **nenhum dos 5 nomes existe no `Distribuidores_DePara.xlsx`** (79 CNPJs) **nem entre os nomes de distribuidor da Mtrix** (13 meses). "NOVO RIBEIRÃO PRETO" e "NOVO SJRP" aparecem na aba `Descobrir Código` da própria base RTM — são **destinos ainda a definir/cadastrar**, não distribuidores. A conta fecha: 453.

**Em linguagem clara**: "sem cobertura" significa *"o distribuidor para onde este cliente foi direcionado não existe na Mtrix nem no de-para; portanto não conseguimos saber se o cliente comprou dele"*. Não significa que o cliente está sem atendimento.

**Avaliação da regra**:
- **Correta** como decisão de não afirmar "não comprou" sem dado (registrado em `docs/rodada_2026-09-09.md §10.1`).
- **Ambígua no nome**: "sem cobertura" no mesmo painel em que "cobertura" = PDVs positivados induz a leitura errada. Sugestão: "destino não mensurável" / "destino fora da Mtrix", com tooltip.
- **Incompleta**: junta três causas distintas num rótulo só — (a) destino não cadastrado no de-para (os 5 de hoje); (b) destino cadastrado mas **excluído do painel** por falta de hierarquia (ex.: KRUPER, RAYO, NORTESUL, MMD, CBX — se um cliente RTM fosse direcionado a eles, a Mtrix tem o dado e mesmo assim ele cairia em "sem cobertura"); (c) destino cadastrado sem sell-out na série. Hoje só (a) ocorre, mas a regra não separa e o painel não explica.
- **Frágil**: junção por **texto livre** entre duas planilhas (coluna com o nome grafado "Dsitribuidor"); um acento ou espaço a mais gera "sem cobertura" silencioso. O caminho robusto é uma coluna de **CNPJ ou código interno do destino** na base RTM.
- Pendência de negócio já registrada (README item 3): confirmar se PELLAH/DIBS/NOVA ENERGIA não reportam à Mtrix ou apenas faltam no de-para. Se for cadastro, 26% da base RTM volta a ser mensurável.

---

## 0.7 Pontos de melhoria (priorizados)

Impacto A/M/B · Esforço em dias úteis (estimativa) · Dep = dependências.

| P | Item | Descrição | Impacto | Esforço | Risco de não corrigir | Dep |
|---|---|---|---|---|---|---|
| 1 | Pipeline · camada curated furada | Fase 2 lê `Clusters_DePara` e `RTM_DePara` direto do Excel; RTM e DIM_PDV podem divergir | A (integridade) | 0,5 | painel com duas versões da mesma base | Fase 1 |
| 2 | Pipeline · orquestrador único + staleness | um comando; verificar mtime/hash das bases vs curated; abortar/avisar | A | 1,5 | painel desatualizado sem ninguém saber (aconteceu hoje) | — |
| 3 | RTM · chave de destino por CNPJ/código | trocar junção por nome por chave; separar causas de "não mensurável" | A (lógica) | 0,5 + coleta | 453 clientes mal explicados; erro silencioso | coluna nova na base RTM (você) |
| 4 | Dados · RTM sem cobertura: confirmar cadastro | PELLAH/DIBS/NOVA ENERGIA no de-para? | A (negócio) | coleta | 26% da base RTM fora | você/cadastro |
| 5 | Arquitetura · retirar o que é do gerencial | `src/`, `ferramentas/`, `data/{curated,staging,quality,raw}`, `Sell In`, `Canais`, `Hierarquia_Clientes_Faltando`, `Scorecard_DN_v1.html` | M (manutenibilidade, 200 MB) | 0,5 | confusão de escopo, scripts quebrados na pasta | sua aprovação (A1) |
| 6 | Performance · RTM Clientes (1.762) e PDVs (1.400) renderizados estáticos | render em JS a partir de dados embutidos, amostra + expandir | M | Fase 3 | 89% do DOM em duas tabelas | Fase 2/3 |
| 7 | UX · abas no topo + persistência + teclado | eliminar scroll longo | M | Fase 2 | — | A5 |
| 8 | Tabelas · componente único (amostra, busca com debounce, ordenação, export filtrado) | hoje cada tabela tem JS próprio; 35 funções mortas | M | Fase 3 | duplicação, bugs | A3, A6 |
| 9 | Config · rótulos e parâmetros fixos (H1–H8) | levar para config/JSON | M | 0,5 | texto do painel desalinhado do config | — |
| 10 | Template · exemplo/validação desatualizados (H10) | regerar snapshot com RTM e receita | M | 0,25 | validação byte a byte cobre menos que o real | — |
| 11 | Pipeline · cache com bump manual | derivar versão do hash do código dos leitores | M | 0,5 | dado velho com checagem verde | — |
| 12 | Segurança · dados sensíveis no HTML | CNPJ, razão social, endereço/bairro de 124k PDVs e 1.762 clientes RTM (com bandeira antiga) embutidos e legíveis no fonte | A (LGPD) | decisão | exposição ao compartilhar | A3 |
| 13 | Fórmulas duplicadas Python × JS (H13) | gráfico recalcula Δ no navegador | B | 0,5 | divergência futura | Fase 3 |
| 14 | Acessibilidade | ARIA, foco, contraste dos Δ (só cor) | M | Fase 2/3 | — | — |
| 15 | Publicação | pasta separada, só o entregável, gerada pelo pipeline | A | Fase 5 | cópia manual, versões antigas | A2 |
| 16 | Receita calculada e não exibida | 5 colunas × 12 tabelas + JSON | B | 0,25 | peso morto | decisão sua (§11 da rodada) |
| 17 | Dados · Status Inativo não exclui; 32 datas 10/12/2013; 6 sem data; 9 sem hierarquia | regras de negócio pendentes | M | coleta | leitura errada de maturidade | você |

---

## Plano proposto · Fases 1 a 5 (sequenciamento e riscos)

**Ordem sugerida: 1 → (2 + 3 juntas no template) → 4 → 5.** A Fase 4 depende da 3 (drill reaproveita o componente de tabela) e a 5 depende da 1 (último passo do orquestrador). Toda fase começa com a proposta escrita e só implementa após o seu "ok".

### Fase 1 · Pipeline único (desenho a apresentar antes)
- `run_dn.py` (um comando): `verificar` (config, bases, mtime/hash vs curated) → `ingerir` (Fase 1 atual) → `calcular` (Fase 2 atual, **lendo clusters e RTM da curated**) → `renderizar` → `validar` (chaves, totais vs Mtrix, bases desatualizadas, placeholders) → `publicar` (Fase 5). Flags `--so-metricas`, `--mes AAAA-MM`, `--sem-publicar`.
- Camadas: `raw` = `bases/` (imutável) → `staging` (cache por arquivo, versão automática) → `curated`. Config-driven (tudo de 0.3.2 vai para `config.yaml` + `config/rotulos.yaml`).
- Log com início/fim, linhas lidas/rejeitadas por arquivo, erros, e `resumo_execucao.json`. Falha explícita, nunca silenciosa.
- Aposentar: `run_fase1.py`, `run_fase2.py` (viram módulos), `template/tools/*`, `painel_dn.raw.json`, `Scorecard_DN_2026-06.html`; mover/remover o que é gerencial (A1).
- Riscos: bump de cache; validação byte a byte precisa do snapshot regerado (H10); primeira execução regrava staging do RTM e da hierarquia (arquivos mudaram hoje).

### Fase 2 · Abas (proposta de agrupamento a validar)
- Sugestão inicial (sem remover nada): **Visão geral** (cabeçalho, cards, gráfico 13 meses, categorias) · **Estrutura** (clusters, supervisores) · **Distribuidores** (tabela + drills) · **Pontos de venda** (tabela + busca) · **RTM** (cards + Evolução/Destinos/Clientes) · **Notas/definições**.
- Aba persistida (`localStorage` + hash na URL), teclado (setas/Home/End, `role=tablist`), filtros globais (categoria, distribuidor, segmento) aplicados a todas, lazy = renderizar tabelas grandes ao abrir a aba (A5).
- Risco: mudar de Handlebars-em-Python para render em JS nas tabelas grandes altera a prova byte a byte (redesenhar a validação).

### Fase 3 · Componente de tabela
- Um componente JS (`DnTable`) para as 8 tabelas: amostra (default sugerido **25** linhas; config), Expandir/Recolher com "mostrando X de Y", busca com debounce (config, ~250 ms), ordenação por cabeçalho, export CSV (e XLSX se A6) do **resultado filtrado**. Virtualização (janela de ~60 linhas) para PDVs e RTM Clientes.
- Dados: cada tabela recebe um JSON compacto embutido (como o blob de PDVs); decisão A3 define o que viaja.

### Fase 4 · RTM drill-down
- 4.1: `regras.rtm.data_migracao: 2026-09-01` em config; toggle "A partir da migração / Histórico completo"; A4 define o comportamento nos meses sem dado.
- 4.2: nota/tooltip com a definição de 0.6; número clicável; **proposta de correção da regra** (chave por CNPJ, três causas separadas) antes de alterar.
- 4.3–4.5: `rtm_aderencia` já sabe **de quem** o cliente comprou (`compras[DIST]`); falta persistir `DIST_ATENDEU` (CNPJ + nome reduzido) em `DN_RTM_CLIENTE` e por mês. Cada número abre o drill.
- 4.6: colunas disponíveis: código antigo ✓, CNPJ ✓, destino ✓, distribuidor que atendeu ✓ (derivável), situação ✓, valor (kg/R$) ✓, última compra = **mês** (A8), razão social = bandeira antiga ou nome Mtrix (A8). Lacunas listadas em A8; nada será estimado.

### Fase 5 · Publicação
- Proposta: `DN/publicacao/` (ou pasta irmã) contendo **só** `Scorecard_DN.html` (nome estável) + `Scorecard_DN_<mês>.html` + `LEIA-ME.txt`; gerada pelo passo `publicar` do orquestrador, com limpeza de versões antigas. Sem JSON, Parquet, scripts ou bases. Depende de A2/A3 (o que pode estar dentro do HTML).

---

## Checklist para você validar esta Fase 0

- [ ] Os números-chave conferem com o que você vê no painel: jul/26 · base ativa 120.817 · positivados 73.185 · DN 60,6% · 1.279,5 t · 70 distribuidores · RTM 1.762 / 1.309 / **453**.
- [ ] Os 5 destinos sem cobertura (PELLAH 280, NOVO RIBEIRÃO PRETO 91, NOVO SJRP 75, DIBS 6, NOVA ENERGIA 1) fazem sentido para você como "ainda sem cadastro/Mtrix".
- [ ] A lista de "fora de escopo" (0.1.1) está certa: nada ali é usado pelo DN.
- [ ] Respostas às ambiguidades A1–A9.
- [ ] Aprovação (ou não) do plano e da ordem das fases.
