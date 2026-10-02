# Adequação e evolução do Painel de Alavancas DN
## Etapa 1 — auditoria, mapeamento e proposta (sem implementação) · versão consolidada

**Projeto auditado:** Scorecard DN · Distribuição Numérica (`Documentos\Painéis - Alavancas\DN`)
**Data:** 10/09/2026 (duas auditorias no mesmo dia, consolidadas à noite) · **Mês de referência do painel:** ago/26 (set/26 na pasta, em andamento)
**Natureza desta entrega:** somente leitura. Nenhum arquivo do projeto foi executado, alterado, criado ou apagado. Gravado em `docs/` em 10/09/2026 com aprovação do Douglas.

**Origem:** consolida `Downloads\Auditoria_Painel_DN_Etapa1.md` (documento-base, numeração mantida: D1–D27, R1–R10, RK1–RK12, L1–L9,
F0–F10, Anexo A com decisões já tomadas) e `evolucao_fase0_auditoria` (segunda auditoria, mesma noite), que acrescentou medições
executadas sobre a fato e a curated, correções de fato, cinco decisões novas (D28–D32) e quatro ambiguidades entre os dois textos
(AMB1–AMB4). A correspondência entre as duas numerações está no Anexo B. Desde a F0 (10/09/2026), cada ficha A.x aponta para a regra `RN-nn` de `docs/regras_negocio.md`, que é a fonte única; este anexo é o histórico das decisões. Os quatro prints de referência da aba de Penetração,
recebidos na noite de 10/09, estão lidos no **Anexo C** (o que cada um afirma, o que é dado, premissa ou estimativa, e o que se
reproduz na curated).

Legenda: **[FATO]** encontrado nas bases/código · **[REGRA]** confirmada e documentada · **[LACUNA]** dado que não existe · **[RISCO]** ·
**[HIPÓTESE]** a validar · **[SUGESTÃO]** · **[DECISÃO]** decisão necessária do Douglas · **[DECIDIDO]** já decidido (Anexo A).

---

## 1. Resumo executivo do entendimento

O pedido é evoluir o painel DN de um **scorecard de acompanhamento** (o que aconteceu) para um **instrumento de direcionamento
comercial** (onde atuar primeiro): seletor Volume/Valor, seletor Ano Calendário/Ano Fiscal, Last Year explícito no gráfico, evolução
por categoria, aba de Penetração com dois objetivos separados (ativação × recorrência), Matriz de Oportunidades com benchmark e
potencial de ganho, resumos executivos dinâmicos em todas as abas, filtro por Supervisor e rastreabilidade de cada insight.

O que a auditoria mostra, em uma frase por bloco:

1. **Volume × Valor é o item mais barato de todos.** R$ e unidades já estão na fato; a receita já é calculada em todos os cubos e já
   chega ao JSON do painel com os três comparativos. Só não é exibida. **[FATO]**
2. **Valor não é faturamento Dori.** O `# Sell-Out (R$)` da Mtrix é a venda do distribuidor ao PDV. Chamar isso de "faturamento"
   nos resumos ou na matriz induz leitura errada; a decisão D1 precisa fixar o nome, não só bruto/líquido. **[FATO][DECISÃO]**
3. **Ano Fiscal já existe na dimensão calendário** (set–ago, `FY2026`), mas **não há histórico para comparar um ano fiscal com o
   anterior**: a série começa em jul/25. **[FATO][LACUNA]**
4. **Last Year já existe** para PDVs positivados (`cobertura_ly`, por junção, nunca por deslocamento) e **não existe** para volume e
   receita na série. LY disponível só em jul/26, ago/26 e set/26 (parcial). **[FATO][LACUNA]**
5. **Penetração já é calculada** por categoria em três níveis (canal, segmento, distribuidor) com duas réguas; a régua oficial
   **já foi decidida** (÷ positivados; Anexo A.2). Não existe categoria × supervisor, categoria × cluster nem categoria × PDV. **[FATO][DECIDIDO]**
6. **O objetivo 1 (aumentar cadastros/ativações) não tem base elegível.** Tudo nasce de compra (Mtrix sell-out); não há cadastro de
   PDVs "que poderiam comprar". Além disso o pedido fala em janela de **6 meses** e a regra vigente da base ativa é **5**. **[LACUNA crítica][DECISÃO D24, D28]**
7. **Drop não é calculável**: a Mtrix é mensal, sem pedido, sem nota, sem dia, sem vendedor. **[LACUNA]**
8. **Benchmark já decidido**: percentil 75 por categoria, todos os distribuidores, sem mínimo, fixo por categoria, último mês
   fechado (Anexo A.1). Nada existe ainda no pipeline. **[DECIDIDO]**
9. **Divergência com a premissa do pedido:** não existem resumos executivos no painel, nem na Visão geral. As abas "Alavancas" e
   "Evolução" citadas no pedido não existem neste painel. **[FATO]**
10. **Risco concreto de número errado** se o toggle R$ for religado sem cuidado: o template ainda carrega `RKG=34.26` (preço médio
    único do protótipo) e `applyUnit()`, que multiplica kg por essa constante. **[RISCO alto]**
11. **Dupla contagem é real e medida**: 804 PDVs em ago/26 são atendidos por mais de um distribuidor; 129.148 pares para 124.600
    PDVs. Nada pode ser somado de distribuidor para canal. **[FATO][RISCO]**

**Conclusão da etapa:** o painel está tecnicamente saudável, versionado, validado (40 validações por execução) e rastreável campo a
campo. A evolução é viável em partes, mas depende de decisões de negócio antes de qualquer linha de código: o que é Valor (D1),
base elegível e janela (D24, D28), premissa de conversão (D25) e cubo supervisor × categoria (D20). Benchmark, régua e período já
estão decididos.

---

## 2. Escopo solicitado (como entendido)

| # | Bloco do pedido | Situação após a auditoria |
|---|---|---|
| 1 | Auditoria e diagnóstico | entregue nesta etapa |
| 2 | Seletor Volume (t) / Valor (R$) | viável; dado pronto em todos os cubos; falta o conceito e o nome de Valor (D1, D30) |
| 3 | Seletor Ano Calendário / Ano Fiscal | viável como recorte; comparação FY vs FY LY **inviável hoje** |
| 4 | Gráfico de evolução com Last Year | parcial hoje (só PDVs); volume/receita exigem campo novo |
| 5 | Evolução geral por categoria | viável sem cálculo novo (dados já embutidos) |
| 6 | Nova aba de Penetração | viável em parte; 5 das 15 perguntas sem dado (§18) |
| 7 | Dois objetivos (ativação × recorrência) | objetivo 2 viável; objetivo 1 sem base elegível |
| 8 | Desdobramento hierárquico | Supervisor → Distribuidor → Categoria: **falta o cubo Supervisor × Categoria** (D20) |
| 9 | Drop e Faturamento | Valor do sell-through pronto; **Drop não existe**; faturamento Dori fora destas bases |
| 10 | Matriz de Oportunidades | viável sobre distribuidor × categoria, com regra de dupla contagem |
| 11 | Benchmark | **decidido** (P75; Anexo A.1) |
| 12 | Potencial de ganho | viável com premissas explícitas e aprovadas (D25) |
| 13 | Classificação de oportunidades | depende de 10, 11 e 12 |
| 14 | Resumos executivos dinâmicos | **não existem hoje**; construção nova |
| 15 | Filtro por Supervisor | viável em 3 abas sem cálculo novo; nas demais exige cubo novo |
| 16 | Interação entre filtros | mapeada (§23) |
| 17 | Rastreabilidade dos insights | há base (inventário de 280 campos + logs + carimbo) |
| 18 | Estados especiais | mapeados (§23) |
| 19 | Dicionário de regras | proposto (§25, Anexo A é o modelo de ficha) |

Fora do escopo desta rodada: PDVs ponderados (`DE-PARA_Ponderada_Clusters.xlsx`, planilha com colunas desalinhadas, adiada até a
correção); compartilhamento da pasta; pendências antigas de dado (RETOMADA §5).

---

## 3. Situação atual identificada

### 3.1 Arquitetura

**[FATO]** ETL em Python → Parquet → **um HTML offline único**, por um comando (`run_dn.py`) em seis etapas: `verificar → ingerir →
calcular → renderizar → validar → publicar`. A ingestão só roda quando alguma base muda (manifesto por tamanho, data e hash).
Qualquer falha aborta e **nada é publicado**. Manifesto conferido em 10/09 à noite: bases inalteradas.

**[FATO]** Publicação: `Painéis Comerciais\DN\Scorecard_DN.html`, nome estável, cópia atômica com md5, limite de 12 MB; 6,9 MB hoje.

**[FATO]** Template Handlebars editado à mão; o pipeline **aborta se o renderizador não reproduzir byte a byte** o exemplo. Toda
edição exige `--regerar-exemplo`. Contrato de campos em `template/data-inventory.json` (280 campos: 208 calculado, 36 RTM, 19 M3,
17 config); campo fora do inventário gera aviso.

### 3.2 Abas, visuais e filtros (inventário)

| Aba | Filtros que agem | Filtros próprios | Componentes |
|---|---|---|---|
| **Visão geral** | Segmento, Categoria | — | 6 cards por segmento (Base ativa, Sem compra no mês, Cobertura, % de cobertura (DN), Volume do mês, kg/PDV; Δ vs mês ant./L3M/LY); gráfico "Cobertura mês a mês · 12 meses" (positivados empilhados Base atual × Novos, linha base ativa, linha tracejada LY, % DN); tabela da série com Δ; tabela "Por categoria · detalhe" (PDVs compradores, % cobertura, penetração, volume t, Δ) |
| **Clusters e supervisores** | Segmento | — | tabela por cluster (12 × 3 segmentos); tabela por supervisor (14 × 3) + série mensal ao clicar |
| **Distribuidores** | Segmento, Distribuidor, Categoria | — | tabela (71 linhas totais + 676 por categoria) com supervisor, segmento, meses de histórico, KPIs, Δ; série mensal ao clicar |
| **Pontos de venda** | Distribuidor | Situação (todos / sem compra / positivados / RTM) | tabela nominal sobre blob gzip+base64 com 129.148 pares distribuidor × PDV |
| **RTM** | — | Estado, Destino, busca, visão temporal | 5 cards clicáveis, Evolução (12 meses), Destinos (27), Clientes (1.762), drills em modal |
| **Definições** | — | — | notas parametrizadas pelo config |

**[FATO]** Componente único de tabela (`DnTabela`): busca, ordenação, amostra 25, expansão em passos de 200 até 2.000, CSV do
filtrado. Estado (aba, seg, cat, dist, rtm) em `localStorage` + URL.

### 3.3 Métricas e cálculos existentes

| Métrica | Fórmula implementada | Onde | Exibida? |
|---|---|---|---|
| Positivado | linha com `PESO_KG > 0` no mês | `metrics.py` | sim |
| Cobertura (`cobertura_pdv`) | PDVs distintos positivados no mês | `serie_nivel` | sim |
| Base ativa | PDVs positivados em ≥ 1 dos últimos **5** meses; **nula** enquanto a janela não fecha (jul a out/25) | `serie_nivel` | sim |
| % de cobertura (DN) | cobertura ÷ base ativa | `serie_nivel` | sim |
| Volume (t) | soma de `PESO_KG` ÷ 1000 (**todas** as linhas, inclusive kg ≤ 0) | `serie_nivel` | sim |
| kg/PDV | volume ÷ cobertura | `serie_nivel` | sim |
| **Receita (R$)** | soma de `RECEITA` (mesmas linhas do volume) | `serie_nivel` | **não** |
| **R$/PDV** | receita ÷ cobertura | idem | **não** |
| Penetração (categoria) | positivados na categoria ÷ **positivados do nível** (régua oficial, A.2) | `serie_nivel(cat=True)` | sim (Visão geral) |
| % de cobertura da categoria | positivados na categoria ÷ **base ativa do nível** | idem | sim |
| Sem compra no mês | base ativa − cobertura | `painel.py` | sim |
| Comparativos | vs mês anterior, vs média L3M, vs LY (**junção** por `ANO_MES_LY`); % para cobertura, volume e receita; **p.p.** para % de cobertura | `comparativos` | sim, exceto receita |
| RTM | aderência, vazamento, ativação em duas réguas; `rs_certo`/`rs_outro` calculados | `rtm_aderencia` | sim (kg); R$ não |
| Δ% do gráfico | recalculados em **JS** (`dnVar`, `dnMean`) a partir da série | template | sim |

**[FATO]** Cubos existentes: canal, segmento, supervisor (× segmento), cluster (× segmento), supervisor no canal, cluster no canal,
distribuidor; **com categoria, apenas** canal, segmento e distribuidor (`DN_DISTRIBUIDOR_CAT_MES`, 8.623 linhas). Mais
`DN_PDV_BASE_ATIVA` (par distribuidor × PDV; sem categoria, sem R$) e quatro tabelas de RTM. Nada por trimestre/semestre/ano.

### 3.4 Cálculos e parâmetros fixos encontrados (conferidos no template atual)

| Item | Ocorrências | Situação |
|---|---|---|
| `RKG = 34.26` (R$/kg médio) e `applyUnit()` | 1 / 3 | **[RISCO alto]** converte kg → R$ por preço médio único. Inerte hoje; é o caminho que um toggle "R$" mal ligado usaria |
| `PCL = 0.47` (proporção de mês corrido) | 1 | inerte; resquício do protótipo |
| `UMODE='t'`, `YMODE='cal'`, `setu()`, `sety()` | 3 / 2 / 1 / 1 | os dois toggles do **protótipo** foram removidos da visão base (08/09); o esqueleto de JS continua |
| Seletor **"Peso · t / Receita · R$"** de 09/09 (`dnMet`, `.m-kg/.m-rs`) | **0** | construído no template reformado em 09/09 (`docs/rodada_2026-09-09.md` §9.2) e **não existe mais**; nenhuma decisão de remoção registrada em docs. **[FATO a esclarecer: Q1]** |
| `HERO`, `PLANJ`, `HISTDATA`, `UFJ`, `PENJ` | 3 (HISTDATA) | stubs vazios |
| `TODO: meta/projeção — input manual via Excel` | **13** | toda meta/projeção foi removida do protótipo |
| `kg/11604.63` (linha 844) | 1 | código morto |
| Classes CSS `.pauta`, `.callout`, `.dnbul` | 0 usos na marcação | resíduo |
| Janela 5, corte 6, rótulos, abas, tolerâncias, série de 12 | config | **corretamente parametrizados** |
| "13 meses" nos textos | — | já parametrizado (`periodo.n_meses_serie`) |
| Fórmulas Δ em JS (`dnVar`, `dnMean`) | — | duplicam o Python (H13 da auditoria de 09/09, ainda aberto) |

**[FATO]** Regra do projeto cumprida: regras de negócio no config, não no código. As exceções acima são resíduos, não regras ativas.

**[RISCO]** Inconsistência **documental**: campos do inventário aparecem como 242 (README), 275 (RETOMADA) e 280 (rodada de 10/09).
Só o último é o atual.

### 3.5 Níveis hierárquicos disponíveis

Canal → Segmento → Supervisor (N3, **14**; 0 distribuidores sem supervisor; **4** rotulados "[VAGO]": 1210 PR, 1240 DF/GO/TO,
1250 AC/MS/MT/RO, 1320 BA/SE) → Distribuidor (71) → PDV (129.148 pares; 124.600 PDVs). Em paralelo: Cluster de loja (12) e Categoria
(10). Acima do supervisor: Gerente (N2, 3) e Head (N1, 1), não usados. **Supervisor é atributo do distribuidor**, não do PDV. O
"Supervisor" textual do de-para difere do rótulo da hierarquia em 71/71 (formatos diferentes); a regra aprovada usa a hierarquia.

### 3.6 Resumos executivos existentes

**[FATO] Nenhum**, em nenhuma aba. A premissa do pedido ("concentrados na Visão geral") descreve provavelmente o Painel Gerencial.

---

## 4. Bases e estruturas encontradas

| Base | Arquivo | Grão | Colunas usadas | Observação |
|---|---|---|---|---|
| Sell-out Mtrix | `bases/Sell Out - MTRIX/ScoreCard_Mtrix_MM.AAAA.xlsx` — **15 arquivos** (jul/25 a set/26) | SKU × distribuidor × PDV × mês | CNPJ do AD., Cód. PDV, Razão Social/UF/Cidade/Bairro/Endereço/CEP PDV, Segmento do PDV, SKU, Ano/Mês, **# Sell-Out (R$)**, **# Sell-Out (Und)**, **# Sell-Out (Quilos)**, # PDVs Positivados, # Total SKUs | 6.420.954 linhas em 15 meses; competência vem da coluna; a linha de total vira gabarito de reconciliação (fecha em R$, Und e kg). **Não tem** dia, pedido, entrega, nota, vendedor, preço de tabela, imposto, marcação de devolução |
| Produtos | `Produtos.xlsx` | SKU | Código, Descrição, **Categoria**, Marca | 288 SKUs movimentados, 0 fora do cadastro |
| Distribuidores | `Distribuidores_DePara.xlsx` (80) | CNPJ de filial | CNPJ, Descrição Mtrix/BI, Cód. Interno Cliente, Status, Supervisor, Nome Reduzido, *Data de Cadastro* | 15 sem data; Status não exclui |
| Hierarquia | `Hierarquia_Consolidada.xlsx` | Código Cliente | N1 Head, N2 Gerente, **N3 Sup./Exec.** | retrato atual, **sem datas**; 9 distribuidores sem linha ficam fora |
| RTM | `RTM_DePara_Transicao.xlsx` | cliente | CNPJ, Cód. Cliente [Antigo], Distribuidor Nome Reduzido | 1.762; destino casado por nome; `CNPJ Distribuidor Destino` ausente |
| Clusters | `Clusters_DePara.xlsx` | Segmento do PDV | Segmento Mtrix → Cluster painel (34 → 12) | opcional |
| PDVs ponderados | `DE-PARA_Ponderada_Clusters.xlsx` | distribuidor × PDV (181) | CLUSTER (PRIME 172 / DESTAQUE 9) | **fora do config; colunas desalinhadas nas linhas 2–33; adiado** |

**[FATO]** Curated: `FATO_SELLOUT` (ANO_MES × CNPJ_DISTRIBUIDOR × COD_PDV × COD_PRODUTO, com **RECEITA, UNIDADES, PESO_KG**),
`DIM_PDV` (163.212), `DIM_DISTRIBUIDOR` (80), `DIM_PRODUTO` (288), `DIM_CALENDARIO` (15), `DIM_RTM` (1.762), `DIM_CLUSTER` (34).

**[FATO] `DIM_CALENDARIO` já traz o ano fiscal pronto:** `ANO_FISCAL`, `ANO_FISCAL_ROTULO` (`FY` + ano de fechamento: set/25 → FY2026),
`MES_FISCAL` (set = 1), `TRIMESTRE_FISCAL`, `SEMESTRE_FISCAL`, mais trimestre/semestre civis e `ANO_MES_LY`. Nenhuma flag de YTD é
gravada, por decisão (YTD depende do período escolhido na tela).

**[FATO] Cobertura temporal real:** série jul/25–ago/26 (14 meses) + set/26 parcial. Base ativa só a partir de nov/25. LY só para
jul/26, ago/26 e set/26 (parcial). FY2025: só jul e ago/25. **FY2026: completo.** FY2027: set/26 parcial. Calendário 2026: jan–set.

**[FATO] Sinais dos valores** (medido na fato, 10/09 à noite):

| Situação | Linhas | Efeito |
|---|---|---|
| `RECEITA < 0` | 64 (R$ −2.276 no total) | devolução/ajuste sem marcação; já reduz totais hoje (soma com sinal) |
| `PESO_KG < 0` | 7 (−5,3 kg) | idem |
| `PESO_KG > 0` e `RECEITA = 0` | **1.402** | positiva em volume, vale zero em valor |
| `PESO_KG > 0` e `RECEITA < 0` | 53 | idem, negativo |
| `RECEITA > 0` e `PESO_KG ≤ 0` | 3 | valor sem volume; **não positiva** pela regra atual |

**[FATO] R$/kg**: canal 31,48 (jul/25) → 34,88 (jan/26) → 33,71 (ago/26). Por categoria em ago/26: BALA 21,56 · GOMAS 22,47 ·
PIRULITO 26,36 · COMPOUND 29,54 · GRANULADO 32,40 · JUBES 32,89 · AMENDOIM 37,04 · REGALIZ 44,02 · GELATINA 48,12 · CHOCOLATE 80,12.
A troca t → R$ **reordena** categorias, distribuidores e clusters.

**[FATO] Multi-distribuidor**: 804 PDVs positivados em ago/26 com mais de um distribuidor (de 72.251); 129.148 pares × 124.600 PDVs.

**[FATO] Categorias por PDV** na janela abr–ago/26: média 3,46 de 10; distribuição 1: 27.671 · 2: 22.965 · 3: 19.407 · 4: 20.075 ·
5: 14.806 · 6: 10.671 · 7: 6.630 · 8: 3.565 · 9: 1.498 · 10: 217.

---

## 5. Regras de negócio confirmadas

Todas em `config/config.yaml` e `docs/`, confirmadas pelo Douglas em rodadas anteriores:

1. **Positivado** = `PESO_KG > 0` no mês.
2. **Base ativa** = PDVs positivados em ≥ 1 dos últimos 5 meses; nula sem janela completa.
3. **DN / % de cobertura** = positivados ÷ base ativa.
4. **PDV multi-distribuidor** conta em cada distribuidor e **uma vez** no canal/segmento/supervisor/cluster.
5. **Distribuidor = CNPJ de filial**; sem hierarquia fica fora; Status não exclui.
6. **Segmento**: Base atual > 6 meses de histórico, Novos até 6 (data de cadastro, senão 1º mês na Mtrix, "≥").
7. **Supervisor** = "código - função - nome" do N3 da hierarquia, via Cód. Interno Cliente.
8. **Categoria** = cadastro de produtos, por SKU. **Cluster** = de-para do Segmento do PDV.
9. **Categoria em Distribuidores**: positivados na categoria ÷ base ativa do distribuidor (não recortada por categoria).
10. **RTM**: aderiu quem comprou do destino; comprar de outro é vazamento; "destino não mensurável" fora do denominador; corte 01/09/2026.
11. **Comparativos** vs mês anterior, L3M e LY, **sem meta**; LY por junção; ausência = "—", nunca zero.
12. **Mês em andamento** entra etiquetado e não é publicado; comparativos mantidos e rotulados.
13. **Série exibida** (12 meses) corta só a exibição.
14. **Ano fiscal** = setembro a agosto, prefixo `FY` (config); presente na dimensão, não exibido.
15. **Meta e projeção** virão por Excel, formato ainda não definido.
16. **[DECIDIDO 10/09]** Benchmark P75 (A.1) · régua da penetração ÷ positivados (A.2) · último mês fechado (A.3).

---

## 6. Regras de negócio NÃO confirmadas (o pedido depende delas)

| # | Regra ausente | Impacto | Decisão |
|---|---|---|---|
| R1 | **O que é "Valor"**: o R$ da Mtrix é a venda do distribuidor ao PDV; bruto/líquido, impostos, descontos e devoluções são desconhecidos; não é faturamento Dori | bloqueia o seletor e o nome na tela | D1, D30 |
| R2 | **Base elegível / cliente cadastrado** | bloqueia o objetivo 1 e "lojas a positivar" | D24 |
| R3 | **Cliente ativo, inativo, novo, reativado** (o painel só conhece positivado, base ativa, sem compra no mês, meses na janela, último mês, primeiro mês) | bloqueia classificação | D24 |
| R4 | ~~Benchmark~~ | **decidido** (A.1) | D14–D16, D21 |
| R5 | **Premissa de conversão** do potencial (referência usava 50% do kg médio) | bloqueia o "quanto vale" | D25 |
| R6 | **Drop** | bloqueia drop em qualquer visual | D26 |
| R7 | **Frequência mínima / cobertura mensal** (objetivo 2); "cobertura" hoje já é o nome da régua da DN | bloqueia o objetivo 2 | D24 |
| R8 | **Nomenclatura do ano fiscal** e perspectiva padrão | bloqueia o seletor de calendário | D4, D29 |
| R9 | **Mudança de carteira/supervisor no tempo** | bloqueia comparação histórica por supervisor | D18, L9 |
| R10 | **Dupla contagem** ao somar oportunidades | bloqueia totais da matriz | D11 |
| R11 | **Janela da base elegível: 5 (regra vigente) × 6 (pedido)** | bloqueia denominadores da penetração | **D28** |
| R12 | **Mês sem LY = ausência de dado, nunca zero** (é o comportamento do código, nunca formalizado) | gráfico LY | D6 (confirmar) |

---

## 7. Lacunas de dados

| # | O que falta | Consequência | O que seria necessário | Alternativa (fato / hipótese / sugestão) |
|---|---|---|---|---|
| L1 | **Cadastro de PDVs elegíveis** por distribuidor | "quantos poderiam comprar" sem resposta; denominador = quem já comprou | cadastro dos distribuidores (ERP deles) ou Mtrix com PDVs sem venda | SUGESTÃO: base elegível = base ativa, declarado na tela (D24) |
| L2 | **Pedido / nota / dia** | **Drop não é calculável**; frequência só como "meses com compra na janela" | Mtrix ou outra base com grão de pedido | FATO: kg/PDV-mês e meses na janela são proxies, **não** drop; não usar o nome |
| L3 | **Meta comercial** | sem benchmark oficial nem "% da meta" | plano comercial formal (Excel de meta, formato a definir) | benchmark estatístico já decidido (A.1) |
| L4 | **Categoria × supervisor** e **categoria × cluster** | "supervisores com maiores gaps por categoria" sem resposta | cubo novo (cálculo, não base) | decisão de projeto (D20) |
| L5 | **CNPJ do destino na base RTM** | destino por nome; 173 clientes não mensuráveis | coluna `CNPJ Distribuidor Destino` | pendência antiga |
| L6 | **Data de cadastro de 6 distribuidores** | histórico "≥" | preencher o de-para | pendência antiga |
| L7 | **Mtrix anterior a jul/25** | sem LY para set/25–jun/26; sem FY2025; sem acumulado 2026 × 2025 | `ScoreCard_Mtrix` de set/24 a jun/25 (10 arquivos) | D5 |
| L8 | **Preço/mix por SKU no painel** | não separa efeito preço × volume no Valor | já está na fato; é cubo novo | |
| L9 | **Histórico de hierarquia** | supervisor atual aplicado à série inteira | hierarquia com vigência, ou retrato mensal arquivado pelo pipeline | SUGESTÃO: pipeline passa a guardar o retrato a partir de agora |
| L10 | **Faturamento Dori** (sell-in) | "faturamento" da penetração/matriz | base do projeto Gerencial, fora do escopo (regra 2) | FATO: o R$ da Mtrix mede outra coisa |
| L11 | **PDV × categoria** | ativação e recorrência por categoria no PDV nominal | cubo novo (deriva da fato) | ver AMB2 (dimensionamento) |
| L12 | ~~Print de referência da Penetração~~ | — | **recebido** (4 prints, 10/09 à noite); leitura no Anexo C | resolvida; sobra a pergunta Q5 (existe print da "Frente 2"?) |

---

## 8. Dúvidas e ambiguidades

1. ~~Régua da penetração~~ **decidida** (A.2).
2. **"Lojas a positivar"** pressupõe base elegível. Sem L1, só pode ser "PDVs da base ativa que não compram a categoria". É o mesmo? **[D24]**
3. **Resumos executivos "existentes"**: não há nenhum. **[D27: confirmar]**
4. **Valor no RTM**: `rs_certo`/`rs_outro` existem; o seletor age ali? **[D1]**
5. **Unidades (Und)** na fato, não usadas em nenhum cubo. Terceira métrica? **[D3]**
6. ~~Mês em andamento na penetração~~ **decidido** (A.3: último mês fechado).
7. **Janela 5 × 6 meses** (pedido §8 × regra vigente). **[D28]**
8. **"Cliente" no desdobramento** = PDV da Mtrix (CNPJ ou id LGPD). Confirmar. **[D24]**
9. **Abas "Alavancas" e "Evolução"** citadas no pedido §18 não existem aqui. Ignorar ou criar? **[Q3]**
10. **Remoção do seletor t/R$ de 09/09** sem registro: foi decisão? **[Q1]**
11. **Devoluções**: só há sinal negativo, sem marcação. Manter soma com sinal (como hoje) ou excluir? **[D30]**
12. **Reabrir decisões fechadas** do RETOMADA §4: proposta é nenhuma sem pedido explícito. **[Q4]**

### Ambiguidades entre as duas auditorias (resolvidas aqui ou deixadas para decisão)

| # | Ponto | Auditoria 1 | Auditoria 2 | Consolidado |
|---|---|---|---|---|
| AMB1 | "Faturamento" | "Faturamento pronto" (= R$ Mtrix) | R$ Mtrix ≠ faturamento Dori | **texto corrigido**: usar "Valor do sell-through (R$)" até D1/D30 fixarem o nome; faturamento Dori é L10 |
| AMB2 | PDV × categoria embutido | inviável (~1,2 M linhas) | viável como máscara de 10 bits por par (129 mil inteiros, +0,1 a 0,3 MB) | duas hipóteses de dimensionamento; **medir antes de descartar** (D32) |
| AMB3 | Filtro Supervisor no RTM | inclui (supervisor do destino já no JSON) | exclui (aderência é por cliente e destino) | fica para **D18** |
| AMB4 | Evolução por categoria | Top N + "outras" | small multiples em índice + tabela de participação | fica para **D8** |
| — | Supervisores "VAGO" | 2 | 3 | **4** (conferido) |
| — | Marcações TODO | 12 | — | **13** (conferido) |
| — | LY disponível | jul e ago/26 | + set/26 parcial | **3 meses**, um parcial |
| — | Linhas negativas | "verificação não executada" | executada | tabela em §4 |

---

## 9. Riscos identificados

| # | Risco | Severidade | Mitigação proposta |
|---|---|---|---|
| RK1 | **`RKG=34.26` + `applyUnit()`**: religar o toggle R$ pelo JS herdado produz receita fictícia | **Alta** | usar só `receita_rs` da fato; remover `RKG`, `applyUnit`, `PCL`, `UMODE/YMODE/setu/sety` na mesma fase |
| RK2 | **Dupla contagem**: 804 PDVs multi-distribuidor; PDV em várias categorias (média 3,46) | **Alta** | unidade elementar = par distribuidor × categoria; nunca somar níveis nem categorias como PDVs; total sempre no nível |
| RK3 | **Benchmark lido como meta** | **Alta** | régua escrita ao lado do número ("referência: P75 dos distribuidores na categoria, ago/26") |
| RK4 | **Potencial lido como previsão** | **Alta** | nomenclatura fixa (Realizado / Oportunidade calculada / Potencial teórico) + memória de cálculo |
| RK5 | **Divergência Volume × Valor**: 1.402 linhas kg > 0 com R$ = 0; R$/kg 21→80 entre categorias; sinais opostos de variação | Média | positivado segue por kg; duas variações lado a lado; aviso "R$ = 0 com volume > 0 em N linhas" no recorte; nunca converter uma na outra |
| RK6 | **Temporalidade da hierarquia**: supervisor atual aplicado à série inteira; 4 VAGO | Média | rótulo "hierarquia vigente em {mês}"; arquivar retrato mensal (L9) |
| RK7 | **Ano fiscal sem LY**: FY2026 completo, FY2025 inexistente; calendário 2026 idem | Média | recorte fiscal sim; comparativo anual **bloqueado com nota**, não número parcial |
| RK8 | **Base ativa nula** jul–out/25 | Média | manter "—"; não acumular nada que dependa dela nesse trecho |
| RK9 | **Tamanho do HTML** (6,9 de 12 MB) | Média | medir antes (§12); teto no config |
| RK10 | **Mês em andamento** contaminar gap e potencial | Média | **resolvido por A.3** (último mês fechado) |
| RK11 | Distribuidor fora do painel distorcer totais | Baixa | régua atual + contagem excluída exibida |
| RK12 | **Manutenção**: cada campo novo = inventário + `--regerar-exemplo` + validação | Baixa | previsto nas fases |
| RK13 | **Fórmulas duplicadas Python × JS** (Δ do gráfico); toggles ampliam o que o JS recalcula | Média | decidir onde mora o cálculo (D31); validação por amostragem no pipeline |
| RK14 | **Resumo dinâmico** inventando causa/adjetivo | Média | gerador por regras declaradas; só fatos numéricos rastreáveis |
| RK15 | **Escopo**: drop e faturamento puxam para o sell-in (Gerencial) | Média | decisão explícita (D26, L10) |

---

## 10. Impactos técnicos

| Frente | Pipeline | JSON / inventário | Template | Validação |
|---|---|---|---|---|
| Volume × Valor | nada novo nos cubos; falta R$ no blob de PDVs (`DN_PDV_BASE_ATIVA`) e nas séries dos drills | campos já existem; faltam `rs_mes`, `rs_janela` no blob e formatos | toggle global (`DNE.met`), pares de colunas nas 8 tabelas, gráfico, cards, CSV nomeado; limpeza RK1 | card canal · receita = recálculo; R$ do blob = série |
| Calendário | `DIM_CALENDARIO` pronta; expor `ano_fiscal`/`mes_fiscal`/`ordem` na série; acumulados YTD (civil e fiscal) com LY quando houver par | campos novos por ponto | toggle, ordenação/agrupamento, rótulos | acumulado = soma da série |
| Gráfico LY | `cobertura_ly` existe; criar `volume_ly`, `receita_ly` | +2 campos por ponto | redesenho de `dnDraw` | JS × Python |
| Evolução por categoria | nada | nada | gráfico novo + seleção | — |
| Supervisor | nada (atributo do distribuidor); cubo supervisor × categoria se D20 | lista + mapa dist → sup no blob | chip/select global; `filtroExterno` | abas × config |
| Penetração | cubos novos: supervisor × categoria (D20); PDV × categoria (D32); benchmark P75 no config | bloco novo | aba nova | soma por categoria = cubo; benchmark reproduzido |
| Matriz | cubo de oportunidade por (distribuidor × categoria) com gap, P75, potencial | bloco novo | aba/bloco novo | memória de cálculo reproduzível |
| Resumos | motor de regras (config) em JS sobre dados embutidos; pipeline valida em um recorte por aba | regras | bloco por aba | cada frase → campo |

---

## 11. Impactos analíticos

- R$ **muda o ranking** (jul/26: receita +16,9% vs LY com volume +9,9%; mix Chocolate × Bala). Rótulo da métrica em todo visual e no CSV.
- Ano fiscal muda a leitura de tendência (set = mês 1) e deixa FY2027 com um mês parcial; único acumulado com par: FY2027 × FY2026.
- Separar os dois objetivos evita somar "a ativar" com "a recuperar".
- Régua oficial (÷ positivados, A.2) mede **mix** de quem já compra; a secundária (÷ base ativa) mede alcance. O gap e "lojas a
  positivar" são na principal (A.2). Se D28 mudar a janela para 6, a régua secundária e a DN mudam de denominador.
- Potencial = aritmética simples com três escolhas (população, benchmark, média) que mudam o resultado em ordem de grandeza: cenário, nunca previsão.
- Multi-distribuidor impede somar oportunidades de distribuidor para canal.

## 12. Impactos de performance

| Item | Hoje | Acréscimo estimado [HIPÓTESE, medir] | Base |
|---|---|---|---|
| HTML | 6,9 MB (limite 12) | | |
| R$ no blob de PDVs (2 números × 129.148) | — | +0,3 a 0,5 MB | registro de série de 14 pontos ≈ 2 KB; número curto ≈ 8 B antes do gzip |
| PDV × categoria como **máscara** (1 inteiro por par) | — | +0,1 a 0,3 MB | AMB2 |
| PDV × categoria como **linhas** (~1,2 M) | — | inviável embutido | AMB2 |
| Séries R$ e LY | já no JSON | ~0 | |
| Cubo supervisor × categoria (14 × 10 × 12) | — | < 50 KB | |
| Série por categoria × distribuidor (71 × 10) | — | +1,3 a 1,8 MB (medido em 10/09, descartado) | |
| Matriz (distribuidor × categoria) | — | < 100 KB | |
| Resumos pré-calculados | — | < 50 KB | |
| Toggles em JS | — | redesenho de gráficos e re-render das tabelas visíveis: ordem do filtro de segmento hoje | load 197 ms (Fase 2) |

Abas só viram DOM na primeira abertura; aba nova segue o padrão.

## 13. Impactos de usabilidade

- Dois seletores globais novos + três filtros + chip do RTM: barra precisa separar **recorte** (segmento, supervisor, distribuidor,
  categoria) de **modo de leitura** (métrica, calendário), com o estado escrito ao lado dos títulos e chip esmaecido onde não age.
- Seletores novos entram na mesma chave de `localStorage`/URL (`met`, `cal`) para o link compartilhado reproduzir a tela.
- LY explícito em 12 meses com 9 vazios: legenda "sem LY na série (Mtrix a partir de jul/25)", não zeros.
- 10 linhas de categoria: ilegível em 375 px; alternativas em §17.
- Matriz e resumos com memória de cálculo a um clique (tooltip ou o `<dialog>` do drill).
- Filtro por supervisor reduz 71 distribuidores a 2–9: útil ao supervisor, redundante ao head.

---

## 14. Análise: Volume versus Valor

**[FATO]** `RECEITA` na fato desde a origem; somada em todos os cubos (`receita_rs`, `rs_pdv`) com três variações; RTM tem
`rs_certo`, `rs_outro`. Exibida em lugar nenhum. Ausente no blob de PDVs e nas séries dos drills. Seletor construído em 09/09 e
removido sem registro (Q1); esqueleto do protótipo (`UMODE`, `setu`, `applyUnit`, `RKG`) ainda no arquivo.

**Onde alterna:** volume do mês ↔ valor; kg/PDV ↔ R$/PDV; Δ de volume ↔ de valor; séries dos gráficos; rankings; potencial (sempre
as duas colunas); RTM (kg ↔ R$ no destino/em outros), se D1 incluir; PDVs (kg mês/último/janela ↔ R$) após incluir no blob.

**Onde NÃO alterna:** base ativa, cobertura, % de cobertura (DN), penetração, aderência, ativados, meses de histórico, sem compra:
são **contagens**. Trocar ali criaria a impressão de duas DNs.

**[LACUNA]** Mtrix não informa devolução, cancelamento, desconto, imposto. **[HIPÓTESE]** o R$ é o valor de venda do distribuidor ao
PDV, com sinal (estornos negativos), sem separar impostos. **[FATO]** volume e receita somam **todas** as linhas com sinal; positivado
só `kg > 0`; 1.402 linhas positivam sem R$.

**[SUGESTÃO]** Nome na tela: "Valor do sell-through (R$)". Formatos: t com 1 decimal; R$ inteiro com milhar, "R$ mil" a partir de 6
dígitos nos cards, R$/PDV com 2 decimais; métrica no cabeçalho de coluna e no nome do CSV. Toggle global, `met=t|rs` na URL, padrão
**t**. Sinais negativos: manter soma com sinal (líquido), que é o que reconcilia com a Mtrix.

**[DECISÃO]** D1 conceito e alcance (inclui RTM?) · D2 formato · D3 Unidades · **D30** nome na tela e tratamento de sinais.

---

## 15. Análise: Ano Fiscal versus Ano Calendário

**[FATO]** `calendario.fiscal_mes_inicio: 9`, `fiscal_prefixo: FY`; dimensão calcula ano, mês, trimestre, semestre fiscais como
**colunas** (não tabela paralela). Nada exibido.

**[FATO] Cobertura por perspectiva:**

| Perspectiva | Mês × mesmo mês LY | Acumulado × acumulado LY |
|---|---|---|
| Calendário 2026 | só jul/26, ago/26 (set/26 parcial) | jan–ago/26 **sem par** (jan–jun/25 não existem) |
| Fiscal FY2026 (set/25–ago/26, completo) | idem | **sem par** (FY2025 só tem jul–ago/25) |
| Fiscal FY2027 | set/26 × set/25 ✓ | set/26 YTD × set/25 YTD ✓ (parcial) |

**Nomenclatura [DECISÃO D4]**: (a) `FY2026` (config; ano em que termina) · (b) `FY25/26` · (c) `Safra 25/26` · (d) "AF 2026
(set/25–ago/26)" no cabeçalho e `FY26` nas colunas.

**Regras a formalizar [SUGESTÃO]**: acumulado só quando **todos** os meses do período estão na série; período com mês em andamento
recebe a etiqueta existente; meses futuros não aparecem (não há meta); mês sem realizado dentro da série aborta (validação "meses
sem arquivo: nenhum"), nunca zera. O calendário muda **só** o eixo temporal (ordem, agrupamento, acumulado, "mesmo período LY"); não
muda base ativa, segmentos nem RTM (corte de migração é data absoluta).

**[SUGESTÃO]** implementar como **recorte e rótulo** com acumulado do período, e **suprimir** o comparativo anual com nota. Acumulados
calculados no **pipeline** (fonte única) em vez de JS (RK13).

**[DECISÃO]** D4 nomenclatura · D5 carregar Mtrix set/24–jun/25 · **D29** perspectiva padrão (sugestão: fiscal; a série de 12 meses
exibida coincide com FY2026 quando o mês de referência é ago/26) · **D31** acumulados no pipeline ou em JS.

---

## 16. Análise: gráfico de evolução e Last Year

**[FATO]** O gráfico já embute, por mês: base ativa, positivados (empilhados por segmento), % de cobertura, **`cobertura_ly`** (por
junção; mês sem LY fica **nulo**, não zero, e a linha se interrompe) e volume (só na tabela). Δ% da tabela em JS.

**[LACUNA]** `volume_ly` e `receita_ly` não existem na série.

**Avaliação** (12 meses, t e R$, telas pequenas):

| Opção | Leitura | Comparabilidade | Mobile | Meses sem LY |
|---|---|---|---|---|
| 1 coluna atual + coluna LY | boa | direta | fraca (24 barras) | par vazio evidente |
| 2 linha + linha | tendência | boa | boa | linha interrompida |
| **3 coluna atual + linha LY** | **nível no mês e referência sem competir** | boa | razoável | linha só onde existe (comportamento atual) |
| 4 = 3 + Δ% sob o eixo | idem + número | melhor | razoável | "—" |

**[SUGESTÃO]** Opção 3 (ou 4), tooltip com atual, LY e Δ (% ou p.p.), legenda "sem LY na série" enquanto L7 não for resolvida. PDVs
e métrica (t/R$) em chaves separadas do gráfico, para não sobrepor três escalas.

**[DECISÃO]** D6 formato e regra "sem LY = ausência" (R12) · D7 campos `volume_ly`/`receita_ly`.

---

## 17. Análise: evolução por categoria

**[FATO]** 10 categorias com série mensal completa embutida (`DN_SERIES['cat-<id>']`), exibidas uma por vez. Participação muito
desigual em ago/26: AMENDOIM 378 t, GOMAS 321 t, REGALIZ 127 t, BALA 125 t, GELATINA 98 t, GRANULADO 79 t, CHOCOLATE 31 t, JUBES 30 t,
PIRULITO 17 t, COMPOUND 7 t. Nenhum cálculo novo para a visão consolidada.

**[RISCO]** 10 linhas na mesma escala absoluta: as quatro menores viram ruído; com R$ a ordem muda. "Aceleração" exige regra
numérica (ex.: Δ% do mês − Δ% L3M) que não existe.

**Alternativas** (AMB4; escolher em D8):

| Alternativa | Responde | Observação |
|---|---|---|
| a Top N dinâmico (4–5) + "outras" agregada, com seleção manual | comparação direta das grandes | escala absoluta esconde as pequenas |
| b Small multiples (10 mini-gráficos, índice base 100) | ritmo por categoria | melhor leitura; ocupa altura |
| c Índice base 100 num gráfico só | ritmo relativo | perde tamanho; combinar com participação |
| d Tabela de categorias + participação % + Δ participação vs LY + sparkline | tudo numa tabela | formato já usado no painel |
| e Categoria selecionada × total do canal | foco | é o que existe hoje |

Filtro de distribuidor/supervisor **não** funciona nessa visão (série por categoria só em canal, segmento e distribuidor; por
distribuidor custaria +1,3 a 1,8 MB, descartado em 10/09).

**[DECISÃO]** D8 alternativa (auditoria 1: a; auditoria 2: b + d) · D9 métrica padrão da visão (% cobertura, penetração, volume ou valor).

---

## 18. Proposta conceitual da aba de Penetração

**Régua [DECIDIDO A.2]**: principal = PDVs que compraram a categoria no mês ÷ positivados do nível; secundária = ÷ base ativa,
rotulada. **Período [DECIDIDO A.3]**: último mês fechado. **Benchmark [DECIDIDO A.1]**: P75 por categoria.

**O que a aba responde com os dados existentes:**

| # | Pergunta | Resposta possível |
|---|---|---|
| 1 | Quantos clientes compram cada categoria? | **Sim** (canal, segmento, distribuidor) |
| 2 | Quantos poderiam comprar? | **Não** como cadastro; só "PDVs da base ativa (ou positivados) que não compraram a categoria" [L1, D24, D28] |
| 3 | Penetração atual? | **Sim** (A.2) |
| 4 | Gap? | **Sim** (A.1) |
| 5 | Maior oportunidade? | **Sim**, por categoria e distribuidor |
| 6 | Categorias com maior potencial? | **Sim**, com D25 |
| 7 | Supervisores com maiores gaps? | **Não por categoria** até D20 |
| 8 | Distribuidores com maiores gaps? | **Sim** |
| 9–10 | Impacto em Volume / Valor? | **Sim**, como cenário (`kg_pdv`, `rs_pdv` do nível) com D25 |
| 11 | Frequência de compra? | **Parcial**: "meses com compra na janela de 5" por par; por categoria só com L11 |
| 12 | Drop? | **Não** [L2] |
| 13 | Faturamento × penetração? | só como "valor do sell-out" (AMB1); faturamento Dori não [L10] |
| 14 | Ativação? | **Sim** com L11: base ativa sem compra da categoria na janela |
| 15 | Recorrência? | **Sim** com L11: comprou a categoria na janela mas não no mês |

**Dois objetivos [HIPÓTESE para validação, D24]:**

- **Ativação** (ampliar quem compra): população = base ativa do nível (janela N, D28). Comprador da categoria = kg > 0 na categoria
  em ≥ 1 mês da janela. A ativar = base ativa − compradores na janela. "Novo" = 1º mês na Mtrix dentro da janela (`PRIMEIRO_MES`).
  Não existem "cadastrado", "bloqueado", "reativado" (L1). Mudança de distribuidor: o par muda, o PDV não; canal mede no PDV, distribuidor no par (RK2).
- **Recorrência** (cobertura mensal): população = compradores da categoria na janela. Comprou no mês = kg > 0 na categoria no mês.
  Cobertura mensal da categoria = compradores no mês ÷ compradores na janela. Frequência = meses com compra na janela. Sazonalidade
  sem regra (14 meses); comparar com o mesmo mês LY quando existir.

Blocos separados, denominadores e nomes distintos ("Ativação da categoria", "Recorrência mensal").

**Desdobramento**: Geral → Supervisor → Distribuidor → Categoria → PDV. Supervisor único por distribuidor; PDV pode ter mais de um
distribuidor; categoria é atributo do SKU (PDV × categoria é matriz de flags); cliente sem hierarquia não ocorre; distribuidor sem
hierarquia já está fora; "duplicidade de cadastro" não se aplica (a DIM_PDV guarda a razão social mais recente por CNPJ).

**Sobre os prints de referência** (Anexo C): a estrutura "penetração × P75 × lojas a positivar × ganho t/mês" **se reproduz na
curated** (jun/26: 2,72 categorias por loja, 11,3 kg por loja compradora de Amendoim, ganho = a positivar × kg por loja × 50%); os
absolutos diferem porque o print usou outra leitura de jun/26 (65.527 positivados, 67 → 71 distribuidores hoje). "Loja nova entra a
50% do kg médio" é **premissa** (D25). "Lojas a positivar" do print é a **soma dos gaps por distribuidor** abaixo do P75 (não o gap do
canal), coerente com a unidade distribuidor × categoria (D10). O print de categoria × cluster está marcado como **estimado** (canal ×
multiplicador fixo por cluster): **desnecessário** — a fato tem SKU e Segmento do PDV na mesma linha, o cruzamento real é calculável
e dá valores diferentes da estimativa (Anexo C.4). O print usa **4 categorias foco** (Amendoim, Gomas, Gelatina, Regaliz) e cores por
limiar (verde ≥ 95% do benchmark, vermelho < 70%): ambos viram decisão (D33, D34).

**Estrutura proposta [SUGESTÃO]:** cabeçalho com recorte, régua e competência (último mês fechado) → 4 cards (categorias por PDV;
PDVs a positivar nas categorias foco; potencial em t e R$; maior oportunidade) → bloco Ativação: tabela por categoria (compradores,
população, penetração, P75, % do P75, a positivar, kg/R$ por comprador, potencial) com drill supervisor → distribuidor → PDVs (lista
nominal, busca, CSV) → bloco Recorrência: tabela por categoria (compradores na janela, no mês, cobertura mensal, distribuição de
frequência, sem compra no mês) com os mesmos drills → gráfico penetração × P75 → resumo dinâmico e memória de cálculo por número.
Drop e faturamento Dori de fora até L2/L10.

---

## 19. Proposta conceitual da Matriz de Oportunidades

**Unidade elementar [SUGESTÃO, D10]: par distribuidor × categoria no último mês fechado**, agregado no nível (supervisor, canal)
por recálculo, nunca por soma.

**Dupla contagem [RK2, D11]:** dentro de uma categoria, somar entre distribuidores é válido ressalvado o multi-distribuidor (804);
entre categorias, o mesmo PDV aparece em várias: o total só pode ser "soma de oportunidades por categoria", **nunca** "PDVs a
positivar"; duas leituras separadas, com a régua escrita.

**Potencial (cenário):** `a positivar × média por comprador do próprio nível na categoria × fator de conversão aprovado (D25)`, em t
e R$, com limites: população mínima, média truncada por percentil (outliers), mesma competência para todos. Memória de cálculo em
cada número.

**Eixos [SUGESTÃO, D12]:** X = PDVs a positivar; Y = distância ao P75 (p.p.); bolha = potencial na métrica ativa. Quadrantes: muitos
PDVs + gap pequeno (**ganho rápido**), muitos + gap grande (**estrutural**), poucos + grande (**foco pontual**), poucos + pequeno
(**manutenção**). Faixas só com exemplos reais aprovados.

**Comparação entre tamanhos diferentes:** normalizar pela base do distribuidor; absoluto e relativo lado a lado. **Score único:** não
nesta etapa (D13); se pedido, proposta com fórmula, pesos e sensibilidade antes de código.

**Saídas:** uma tabela ordenável cobre os quatro rankings; agrupamento por supervisor/distribuidor/categoria na mesma tabela; scatter
SVG com quadrantes após regra; tabela rastreável + tooltip de memória **obrigatórios**; drill até o PDV (blob); destaques via resumos;
realizado × potencial com nomes distintos.

**[DECISÃO]** D10 unidade · D11 dupla contagem · D12 eixos e quadrantes · D13 score (recomendo não) · D25 conversão.

---

## 20. Benchmark — decidido (A.1); alternativas registradas para histórico

| Alternativa | Regra | Vantagem | Limitação / sensibilidade a outliers |
|---|---|---|---|
| **Percentil 75 dos distribuidores na categoria [DECIDIDO]** | 3º quartil da penetração, mês de referência, todos os distribuidores com sell-out na categoria, sem mínimo, fixo por categoria | régua da referência; "praticada na própria operação" | sensível a distribuidores pequenos; recalculado a cada mês → gap varia sem ação comercial (riscos aceitos em A.1) |
| Mediana | P50 | estável | ambição baixa |
| Melhor observado | máximo | ambicioso | outlier vira meta |
| Média histórica do próprio distribuidor | L6M/L12M | evolução | não indica potencial |
| Percentil no grupo comparável (segmento/cluster/supervisor) | P75 por grupo | mais justo | grupos pequenos instáveis |
| Meta comercial formal | externa | ideal | não existe (L3) |

Implementação prevista: `regras.penetracao.benchmark` no config (percentil, universo, mínimo = 0), calculado em
`DN_DISTRIBUIDOR_CAT_MES`, régua escrita ao lado do número.

---

## 21. Proposta de resumos executivos dinâmicos

**[FATO]** Não existem. Componente novo.

**Princípio:** cada frase é uma **regra declarada** no config, avaliada **no navegador** sobre os dados embutidos e os filtros ativos,
e produz: o que (indicador) + onde (nível/nome) + quanto (valor e variação) + contra o quê (comparação) + por que merece atenção
(limiar objetivo da regra) + próximo nível (link que aplica o filtro). Sem adjetivos, causas, verbos prescritivos ou
responsabilização. Dado insuficiente → "sem dado suficiente para X no recorte" (base ativa incompleta, mês sem LY, categoria sem
observações). O pipeline valida cada regra contra o dado do mês em pelo menos um recorte por aba (reprodutibilidade).

**Por aba [SUGESTÃO]:**

| Aba | Regras candidatas |
|---|---|
| Visão geral | resultado do mês na métrica ativa; Δ vs mês anterior/L3M/LY (quando houver); maior contribuição positiva e negativa à variação de cobertura por distribuidor (Δ absoluto de PDVs); categoria com maior queda de % cobertura; PDVs sem compra no mês e t/R$ vendidos a eles na janela |
| Clusters e supervisores | cluster com maior Δ p.p.; supervisor com maior Δ absoluto de PDVs (+ e −); supervisor com menor DN vs canal, sempre com base equivalente |
| Distribuidores | maior queda/alta de cobertura; distribuidores novos e seu peso; abaixo do P75 (por categoria); sem venda no mês (mês em andamento) |
| Pontos de venda | PDVs sem compra com maior kg/R$ na janela; concentração: % do volume nos N maiores |
| RTM | aderência e Δ; vazamento; ativados parados; destino com maior gap |
| Penetração | categoria com maior nº a positivar; nível mais distante do P75; maior oportunidade de recorrência |
| Matriz | maior oportunidade em t e em R$ do recorte; principal gap de cobertura mensal; principal oportunidade de mix; próximo drill |

**Rastreabilidade (§21 do pedido):** tooltip por frase com indicador, período, filtros ativos, base, id da regra, valor de comparação,
benchmark, memória de cálculo e data dos dados (carimbo existente).

**[DECISÃO]** D17 aprovar o conjunto de frases (cada uma é regra) e os limiares, com exemplos reais · D27 confirmar que não há resumo hoje.

---

## 22. Avaliação do filtro por Supervisor

**[FATO]** Atributo do distribuidor (N3). Cubos `DN_SUPERVISOR_MES` e `DN_SUPERVISOR_CANAL_MES`; supervisor já em cada distribuidor e
cada cliente RTM no JSON. 14 supervisores, 4 "[VAGO]", 0 distribuidores sem supervisor, 1 supervisor → N distribuidores (2 a 9).
Hierarquia sem histórico (L9, RK6).

| Aba | Filtro por supervisor | Custo | Observação |
|---|---|---|---|
| Visão geral | cards e gráfico via `DN_SUPERVISOR_CANAL_MES`; tabela de categorias **exige cubo novo** (D20) | médio | |
| Clusters e supervisores | já é a dimensão da tabela | — | redundante |
| **Distribuidores** | sim, sem cálculo novo | baixo | maior ganho imediato |
| **Pontos de venda** | sim, via distribuidor (mapa dist → sup no blob) | baixo | |
| RTM | possível (supervisor do destino no JSON); **AMB3**: a aderência é por cliente e destino, o filtro pode confundir | baixo | D18 |
| Penetração / Matriz | depende de D20 | médio | |

**[SUGESTÃO]** seleção única com "Todos", na barra global, chip esmaecido onde não age, aviso "hierarquia vigente em {mês}";
supervisor × distribuidor: escolher supervisor restringe a lista de distribuidores; distribuidor de outro supervisor limpa o
supervisor. Pipeline passa a arquivar o retrato mensal da hierarquia (L9).

**[DECISÃO]** D18 escopo por aba (inclui RTM?) · D19 única/múltipla · D20 criar `DN_SUPERVISOR_CAT_MES`.

---

## 23. Mapa de interação entre filtros e estados especiais

Controles previstos: **Métrica** (t/R$), **Calendário** (civil/fiscal), **Período/série**, **Segmento**, **Supervisor**,
**Distribuidor**, **Categoria**, **Visão RTM**, filtros próprios das tabelas.

| Combinação | Comportamento esperado | Regra | Conflito / estado vazio | Aviso |
|---|---|---|---|---|
| Métrica × visual de contagem | contagens não mudam; só colunas de medida | positivado por kg | recorte com kg > 0 e R$ = 0 | "R$ = 0 com volume > 0 em N linhas" |
| Calendário × série exibida (12) | corte por nº de meses, não por ano | | ano fiscal parcial no início | rótulo do período coberto |
| Calendário × LY | mês a mês válido; acumulado × acumulado **bloqueado** sem par | | | nota, não número |
| Calendário × janela 5/6 | não interage (janela móvel) | | | |
| Supervisor × Distribuidor | supervisor restringe distribuidores | | incoerente → lista vazia com mensagem | limpar um dos dois |
| Supervisor × Categoria | independentes; na Visão geral exige D20 | | | |
| Distribuidor × Categoria | já funciona | soma das categorias > total | | nota existente |
| Segmento × Supervisor | supervisor pode não ter distribuidor do segmento | | vazio | "sem distribuidores deste segmento" |
| Período × janela | base ativa sempre a janela fechada no mês | | | explicitar |
| Filtros × benchmark | **fixo por categoria no total** [DECIDIDO A.1] | | | régua escrita |
| Filtros × potencial | recalculado no recorte, no nível, nunca somado | RK2 | | "no recorte selecionado" |
| Filtros × resumos | recalculados; "sem dado" quando vazio | | | |
| Filtros × rankings | dentro do recorte; empate = mesma posição, ordem alfabética | | | |
| Mês em andamento × tudo | etiqueta; Penetração/Matriz no último mês fechado [A.3] | | | |
| Visão RTM × calendário / métrica | RTM ignora calendário; métrica conforme D1 | | | chip esmaecido |

**Estados especiais (§22 do pedido):** nenhum filtro = canal · supervisor único = seus distribuidores · vários supervisores = fora
(seleção única, D19) · distribuidor único = já existe · período sem dados = "—" · parcial = etiqueta · mês sem LY = "—" ·
categoria sem benchmark = não ocorre (sem mínimo, A.1) · cliente sem hierarquia = não ocorre · volume sem valor = aviso (1.402
linhas) · valor sem volume (3 linhas) = não positiva, valor entra no total · drop = ausente · oportunidade negativa = "acima da
referência", potencial 0 · oportunidade zero = exibida como 0 · empate = mesma posição · alteração de hierarquia = aviso ·
divergência entre bases = pipeline aborta/avisa · total ≠ soma das partes = declarado na tela (multi-distribuidor).

---

## 24. Recomendação de priorização

| Ordem | Item | Dependência | Custo | Valor |
|---|---|---|---|---|
| 1 | **Decisões de negócio** abertas (D1, D24, D25, D28 em especial) + dicionário de regras | Douglas | — | destrava tudo |
| 2 | **Seletor Volume/Valor** + remoção dos resíduos (RK1) | D1–D3, D30 | baixo | alto |
| 3 | **Last Year no gráfico** (volume/receita) | D6, D7 | baixo | alto |
| 4 | **Evolução por categoria** | D8, D9 | baixo | médio-alto |
| 5 | **Filtro por Supervisor** (abas de custo baixo) | D18, D19 | baixo | médio-alto |
| 6 | **Seletor de calendário** | D4, D5, D29, D31 | médio | médio (limitado pela falta de LY) |
| 7 | **Aba de Penetração** (recorrência primeiro; ativação quando D24/D28 destravarem) | D20, D24, D28, D32 | médio-alto | alto |
| 8 | **Matriz de Oportunidades** | 7 + D10–D13, D25 | alto | alto |
| 9 | **Resumos executivos** | 7 e 8 + D17 | alto | alto |
| 10 | **Rastreabilidade** (tooltip com memória) | 9 | médio | médio |

Racional: 2 a 5 usam dados que já existem, com risco baixo; 6 depende de nomenclatura e vale menos sem histórico; 7 a 9 são o
coração do pedido e dependem das definições.

---

## 25. Checklist de decisões necessárias

| # | Decisão | Bloqueia | Estado |
|---|---|---|---|
| D1 | Conceito oficial de **Valor** | seletor | **decidida** (A.4: sell-through da Mtrix, "Valor do sell-through (R$)", soma com sinal, alcance total) |
| D2 | Formato de exibição do Valor | seletor | **decidida** (A.5) |
| D3 | **Unidades (Und)** como métrica? | seletor | **decidida** (A.5: não entra agora) |
| D4 | Nomenclatura do ano fiscal | calendário | **decidida** (A.10: "Ano fiscal 2026 (set/25–ago/26)" + `FY26`) |
| D5 | Carregar Mtrix set/24 a jun/25 | comparativo anual | **decidida** (A.10: pedir à Mtrix; pendência de dado L7) |
| D6 | Formato do gráfico com LY | gráfico | **decidida** (A.11: coluna + linha LY + Δ%; sem LY = ausência) |
| D7 | Criar `volume_ly` / `receita_ly` | gráfico | **decidida** (A.11: sim, no pipeline) |
| D8 | Evolução por categoria | gráfico | **decidida** (A.11: Top N + "outras" com seleção, mais tabela com participação e sparkline) |
| D9 | Métrica padrão da evolução por categoria | gráfico | **decidida** (A.11: a métrica do seletor, t ou R$) |
| D10 | Unidade elementar da oportunidade | matriz | **decidida** (A.12: distribuidor × categoria, último mês fechado) |
| D11 | Regra de dupla contagem | matriz | **decidida** (A.12) |
| D12 | Eixos e quadrantes | matriz | **decidida** (A.12: nuvem X × Y × bolha, sem quadrantes na 1ª entrega) |
| D13 | Score único | matriz | **decidida** (A.12: não criar) |
| D14 | Benchmark: alternativa | penetração/matriz | **decidida** (P75, A.1) |
| D15 | Universo do benchmark | penetração | **decidida** (todos, A.1) |
| D16 | Mínimo de observações | penetração | **decidida** (sem mínimo, A.1) |
| D17 | Resumos executivos: modelo e frases | resumos | **decidida** (A.14: modelo e lista; limiares na F9 com exemplos reais) |
| D18 | Escopo do filtro de Supervisor por aba | filtro | **decidida** (A.13: todas menos RTM e Definições) |
| D19 | Seleção única ou múltipla | filtro | **decidida** (A.13: única) |
| D20 | Cubos supervisor × categoria e cluster × categoria | penetração | **decidida** (A.13: os dois, mais retrato mensal da hierarquia) |
| D21 | Benchmark fixo ou recalculado no recorte | matriz | **decidida** (fixo, A.1) |
| D22 | Penetração/matriz no último mês fechado | tudo novo | **decidida** (A.3) |
| D23 | **Régua oficial da penetração** | penetração | **decidida** (÷ positivados, A.2) |
| D24 | **Base elegível** e conceitos de cliente | objetivo 1 | **decidida** (A.6) |
| D25 | Conversão do potencial | potencial | **decidida** (A.7: fator observado por categoria, sem premissa fixa) |
| D26 | Drop | drop | **decidida** (A.14: não existe; sem proxy) |
| D27 | Resumo executivo hoje | resumos | **decidida** (A.14: não há; construção nova) |
| **D28** | Janela da base elegível | penetração, DN | **decidida** (A.6: 5 meses para tudo) · **revista em 14/09/2026 (A8 da estabilização): 6 meses para tudo** |
| **D29** | Perspectiva padrão do calendário | calendário | **decidida** (A.10: fiscal) |
| **D30** | Nome do Valor na tela e sinais negativos | seletor | **decidida** (absorvida pela A.4) |
| **D31** | Acumulados: pipeline ou JS | calendário | **decidida** (A.10: pipeline; Δ% do gráfico também migram para o JSON) |
| **D32** | PDV × categoria | penetração | **decidida** (A.14: medir a máscara por par; volta a decisão se passar de 1 MB) |
| **D33** | Categorias foco | penetração, matriz, resumos | **decidida** (A.8: Amendoim, Gomas, Gelatina, Regaliz, no config) |
| **D34** | Limiares de cor | penetração | **decidida** (A.14: 95% / 70% como parâmetros no config, revisáveis) |
| **D35** | PDV multi-distribuidor na tabela por supervisor | penetração por supervisor, RK2 | **decidida** (A.9: regra vigente, soma > total declarada) |

Sobre D25, o print fixa a estrutura: `ganho (t/mês) = lojas a positivar × kg por loja compradora da categoria × 50%`, com "lojas a
positivar" = Σ por distribuidor abaixo do P75 de `(P75 − penetração_d) × positivados_d`. Falta aprovar o **50%**, o mês da média
(mês de referência ou janela), e limites (D25).

**Perguntas (não são decisões):** Q1 a remoção do seletor t/R$ de 09/09 foi decisão sua? · ~~Q2 print~~ recebido · Q3 abas
"Alavancas"/"Evolução" do pedido: ignorar? · Q4 nenhuma decisão fechada do RETOMADA §4 é reaberta sem pedido explícito: confirma? ·
**Q5** o print 1 fala em "duas fontes de ganho" (categorias por loja × SKUs por categoria × kg por SKU) e só mostra a Frente 1; existe
uma Frente 2 (SKUs por categoria) a considerar nesta rodada?

---

## 26. Plano de fases futuras (nada executado)

| Fase | Conteúdo | Entregável | Pré-requisito |
|---|---|---|---|
| **F0** | Registro das decisões D1–D32 e criação do dicionário de regras (ficha como no Anexo A) | `docs/regras_negocio.md` + entradas no `config.yaml` | aprovação item a item |
| **F1** | Seletor Volume/Valor; R$ no blob de PDVs (e RTM se D1); limpeza de `RKG`, `applyUnit`, `PCL`, `UMODE/YMODE/setu/sety` | métrica alternável; validação t × R$ | D1–D3, D30 |
| **F2** | LY explícito no gráfico (PDVs, volume, receita) | campos novos + inventário + validação | D6, D7 |
| **F3** | Evolução por categoria | bloco novo na Visão geral | D8, D9 |
| **F4** | Filtro por Supervisor nas abas de custo baixo; pipeline arquiva retrato mensal da hierarquia | filtro global | D18, D19 |
| **F5** | Seletor de calendário (recorte fiscal, acumulados, sem comparativo anual) | seletor + rótulos | D4, D5, D29, D31 |
| **F6** | Aba de Penetração, objetivo 2 (recorrência) primeiro; cubos supervisor × categoria e PDV × categoria | aba nova + P75 no config + validações | D20, D32, D28 |
| **F7** | Objetivo 1 (ativação) — **só se D24 destravar** | extensão da aba | D24, D28 |
| **F8** | Matriz de Oportunidades e classificação | aba/bloco novo + memória de cálculo | D10–D13, D25 |
| **F9** | Resumos executivos dinâmicos | componente novo | D17 |
| **F10** | Rastreabilidade (tooltip: indicador, período, filtros, base, regra, benchmark, memória, data) | componente + inventário | F9 |

Cada fase: proposta escrita → ok item a item → implementação → `--regerar-exemplo` quando o template mudar → `--sem-publicar` com
prova de que os números de kg não mudaram → relatório (a) alterado, (b) por quê, (c) pendências, (d) checklist → publicação com ok.

---

## 27. Gate de aprovação

**Compreendido.** Evoluir o Scorecard DN de acompanhamento para direcionamento: duas métricas, dois calendários, LY explícito,
evolução por categoria, penetração com dois objetivos, matriz com benchmark e potencial, resumos dinâmicos, filtro por supervisor e
rastreabilidade — sem inventar dado e sem implementar antes da aprovação.

**Encontrado.** Projeto saudável, parametrizado e validado; **Valor calculado e não exibido** (e um seletor de 09/09 removido sem
registro); **ano fiscal pronto na dimensão**; **LY correto por junção, só para PDVs e só em 3 meses**; **penetração em três níveis com
régua já decidida**; resíduos de protótipo, um perigoso (`RKG=34.26`); dupla contagem medida (804 PDVs); 1.402 linhas positivadas sem
R$; hierarquia sem histórico com 4 territórios vagos; nenhum resumo executivo hoje.

**A validar.** Nada aberto desta etapa: R1–R12 (§6), AMB1–AMB4 e as dúvidas (§8) e Q1–Q5 foram resolvidos pelas fichas A.4–A.16. Pendências de dado seguem em §7 (L1, L2, L5, L6, L7, L10).

**Regras a definir.** Nenhuma pendente: D1 a D35 decididas em 10/09/2026 (Anexo A, fichas A.1–A.16). Restam os limiares dos resumos (F9, com exemplos reais) e os quadrantes da matriz (2ª entrega), ambos por aprovação item a item quando chegarem.

**Riscos a aceitar ou mitigar.** RK1 (preço médio herdado), RK2 (dupla contagem), RK3/RK4 (benchmark e potencial lidos como meta e
previsão), RK5 (Volume × Valor), RK7 (ano fiscal sem LY), RK9 (HTML), RK13 (fórmulas em JS).

**Etapas recomendadas.** F0 a F10 (§26), uma por vez, cada uma com aprovação escrita item a item.

**Nada foi feito além de ler.** Sem código, sem alteração de arquivo, sem execução do pipeline, sem publicação, sem correção de
problemas encontrados. Gravado em `docs/evolucao_etapa1_auditoria.md` com o seu ok (10/09/2026).

**ANÁLISE E MAPEAMENTO CONCLUÍDOS. NENHUMA ALTERAÇÃO FOI EXECUTADA. AGUARDANDO A APROVAÇÃO DE DOUGLAS PARA DEFINIÇÃO DO PRÓXIMO PASSO.**

---

## Anexo A — decisões registradas (10/09/2026, Douglas) — transcritas sem alteração

### A.1 · Benchmark de penetração (D14, D15, D16, D21)

*Regra(s) no dicionário: RN-30 (`docs/regras_negocio.md`, F0).*

| Campo da ficha | Conteúdo |
|---|---|
| **Nome da regra** | Benchmark de penetração por categoria |
| **Objetivo** | Dar a régua de comparação que transforma a penetração observada em gap e em oportunidade |
| **Definição** | Para cada categoria, a penetração dos distribuidores naquela categoria é ordenada e o **percentil 75** vira o benchmark da categoria |
| **Fórmula** | `benchmark(cat) = percentil_75( penetracao(distribuidor, cat, mês de referência) )` |
| **Universo** | **Todos os distribuidores do painel** com sell-out na categoria no mês (71 em ago/26). Não separa Base atual × Novos |
| **Mínimo de observações** | **Sem mínimo** — toda categoria recebe benchmark |
| **Comportamento com filtros** | **Fixo por categoria**, calculado no total; não é recalculado quando se filtra supervisor, distribuidor ou segmento |
| **Base de origem** | `DN_DISTRIBUIDOR_CAT_MES` (derivada da Mtrix) |
| **Granularidade** | categoria × mês de referência |
| **Período** | último mês fechado; **não** calculado no mês em andamento (D22, aprovado) |
| **Tratamento de nulos** | distribuidor sem sell-out na categoria não entra no cálculo |
| **Régua da penetração usada** | penetração ÷ PDVs positivados (A.2) — o benchmark é o percentil 75 **dessa** régua |
| **Responsável pela validação** | Douglas |
| **Status** | **aprovado** (régua, universo, mínimo, comportamento com filtros e período) |
| **Riscos aceitos** | sem mínimo de observações, um distribuidor pequeno com penetração alta pode puxar o corte de uma categoria; percentil recalculado a cada mês faz o gap variar sem ação comercial |
| **Data** | 10/09/2026 |

*Decisão registrada. Nada foi implementado: o benchmark ainda não existe no pipeline, no config nem no painel.*

### A.2 · Régua oficial da penetração (D23)

*Regra(s) no dicionário: RN-28, RN-29 (`docs/regras_negocio.md`, F0).*

| Campo da ficha | Conteúdo |
|---|---|
| **Nome da regra** | Penetração de categoria (régua oficial) |
| **Objetivo** | Medir mix — quantas categorias a loja que já compra da gente leva |
| **Definição (principal)** | **Penetração = PDVs que compraram a categoria no mês ÷ PDVs positivados do nível no mês** |
| **Definição (secundária)** | **% de cobertura da categoria = PDVs que compraram a categoria ÷ base ativa do nível**, exibida como coluna rotulada ao lado |
| **Fórmula** | `penetracao = positivados(cat) / positivados(nivel) * 100` · `pct_cobertura = positivados(cat) / base_ativa(nivel) * 100` |
| **Base de origem** | `DN_CANAL_CAT_MES`, `DN_SEGMENTO_CAT_MES`, `DN_DISTRIBUIDOR_CAT_MES` — **ambas já calculadas hoje** |
| **Granularidade** | categoria × nível × mês |
| **Nível do denominador** | o do recorte: canal no total, distribuidor quando filtrado por distribuidor |
| **Período** | último mês fechado (D22) |
| **Gap e lojas a positivar** | calculados **na régua principal**, contra o benchmark do percentil 75 (A.1) |
| **Exceções** | as duas réguas nunca aparecem sem rótulo na mesma coluna; a soma das categorias é maior que o total (PDV que compra duas categorias conta em cada uma) |
| **Responsável pela validação** | Douglas |
| **Status** | **aprovado** |
| **Data** | 10/09/2026 |

### A.3 · Período da aba de Penetração e da Matriz (D22)

*Regra(s) no dicionário: RN-27 (`docs/regras_negocio.md`, F0).*

Penetração, benchmark, gap e potencial usam **sempre o último mês fechado**, mesmo quando o painel estiver exibindo o mês em
andamento. Com mês parcial, a aba mostra o mês fechado com rótulo explícito da competência usada, em vez de gap e potencial inflados
por mês incompleto.

### A.4 · Conceito e nome de "Valor" (D1, D30) — decidido por Douglas em 10/09/2026

*Regra(s) no dicionário: RN-06, RN-55 (`docs/regras_negocio.md`, F0).*

| Campo da ficha | Conteúdo |
|---|---|
| **Nome da regra** | Valor do sell-through |
| **Objetivo** | Segunda métrica do painel, ao lado do Volume (t), para leitura em reais |
| **Definição** | Valor = **sell-through** reportado pelo distribuidor à Mtrix: venda do distribuidor ao PDV, em R$, conforme reportado (sem separar impostos, descontos ou devoluções — a Mtrix não os discrimina). **Não é faturamento Dori** |
| **Nome na tela** | **"Valor do sell-through (R$)"**; nas colunas, "Valor (R$)" e "R$ / PDV"; a métrica em kg permanece "Volume (t)" e "kg / PDV". Definição completa na aba Definições e no tooltip da métrica |
| **Fórmula** | `receita_rs = Σ RECEITA` nas mesmas linhas do volume (já calculado em todos os cubos); `rs_pdv = receita_rs ÷ cobertura_pdv` |
| **Base de origem** | Mtrix, coluna `# Sell-Out (R$)` → `FATO_SELLOUT.RECEITA` |
| **Granularidade** | mês × distribuidor × PDV × SKU (fato); agregada em todos os níveis |
| **Sinais negativos** | **soma com sinal** (líquido de estornos), como já ocorre e como reconcilia com a linha de total da Mtrix; nada é excluído |
| **Positivado** | continua sendo `kg > 0`; linha com kg > 0 e R$ = 0 (1.402 na série) conta como compradora com valor zero; o recorte avisa quando houver |
| **Alcance do seletor** | **total**: cards, gráficos, tabelas, PDVs (após incluir R$ no blob), RTM (`rs_certo` / `rs_outro`), potencial, resumos. Contagens de PDV nunca alternam |
| **Bruto × líquido** | não determinável pelas bases; o painel declara "conforme reportado pelo distribuidor" e não afirma nenhum dos dois |
| **Faturamento Dori** | fora deste projeto; se vier, entra como base e regra próprias, com outro nome, nunca na mesma coluna que o sell-through |
| **Responsável pela validação** | Douglas |
| **Status** | **aprovado** (conceito, nome, sinais, alcance) |
| **Data** | 10/09/2026 |

*Decisão registrada. Nada foi implementado: o seletor não existe no template e o R$ segue fora da tela.*

### A.5 · Formato do Valor e Unidades (D2, D3) — decidido por Douglas em 10/09/2026

*Regra(s) no dicionário: RN-09, RN-43 (`docs/regras_negocio.md`, F0).*

| Campo da ficha | Conteúdo |
|---|---|
| **Nome da regra** | Formato de exibição do Valor do sell-through; Unidades fora do seletor |
| **Cards** | valor do mês em "R$ x,x mi" (1 decimal); "R$ / PDV" com 2 decimais |
| **Tabelas** | inteiro com separador de milhar (ex.: 40.891.388); R$ / PDV com 2 decimais; cabeçalho "Valor (R$)" |
| **Séries e gráficos** | eixo em "R$ mi" com 1 decimal; tooltip com o valor cheio |
| **CSV** | valor cheio sem abreviação, como exibido na tabela; métrica no nome do arquivo (`_t` / `_rs`) |
| **Variações** | % com sinal e cor, como as de volume; % de cobertura continua em p.p. |
| **Unidades (`# Sell-Out (Und)`)** | **não entra** como métrica nesta rodada: a unidade da Mtrix é a unidade de venda do SKU (caixa, display, pacote) e mistura embalagens entre categorias. Continua na fato (`UNIDADES`), reconciliada, disponível para rodada futura como terceira posição do mesmo seletor |
| **Base de origem** | `FATO_SELLOUT.RECEITA`; formatos em `template/data-inventory.json` e `config/config.yaml` (rótulos) |
| **Responsável pela validação** | Douglas |
| **Status** | **aprovado** |
| **Data** | 10/09/2026 |

### A.6 · Janela e base elegível; conceitos de cliente (D24, D28) — decidido por Douglas em 10/09/2026

*Regra(s) no dicionário: RN-02, RN-12, RN-32, RN-41 (`docs/regras_negocio.md`, F0).*

| Campo da ficha | Conteúdo |
|---|---|
| **Nome da regra** | Base elegível e conceitos de cliente da aba de Penetração |
| **Janela (D28)** | **5 meses para tudo**, inclusive Penetração (opção a). A DN publicada não muda. O "6 meses" do pedido foi lido como aproximação. Medido em ago/26: 5 m → base ativa 124.600, DN 57,4%; 6 m daria 129.393 e 55,2% só por definição (+4.793 PDVs que compraram em mar/26 e em nenhum dos 5 últimos) |
| **Base elegível** | = base ativa do nível: PDVs com kg > 0 em ≥ 1 dos últimos 5 meses (`DN_PDV_BASE_ATIVA`) |
| **Cliente cadastrado** | **não existe** nas bases; o painel não usa o termo |
| **Cliente ativo** | = na base ativa |
| **Cliente positivado** | kg > 0 no mês de referência (regra atual) |
| **Cliente inativo** | comprou em algum mês da série e está fora da base ativa (sem compra na janela) |
| **Cliente novo** | primeiro mês na Mtrix (`DIM_PDV.PRIMEIRO_MES`) dentro da janela |
| **Cliente reativado** | positivado no mês, sem compra nos 5 meses anteriores, e não novo |
| **"Cliente" no desdobramento** | = PDV da Mtrix, inclusive id LGPD (anonimizado, estável entre meses) |
| **Comprador da categoria** | kg > 0 na categoria em ≥ 1 mês da janela (cubo PDV × categoria, D32) |
| **A ativar na categoria** | base elegível − compradores da categoria na janela (objetivo 1); o print e a régua A.2 medem penetração sobre positivados do mês — os dois números convivem com nomes distintos |
| **Bloqueado / encerrado / mudança de carteira / vendedor** | sem dado; não tratados; declarado na aba Definições |
| **Base de origem** | Mtrix (fato), `DIM_PDV`, `DN_PDV_BASE_ATIVA` |
| **Responsável pela validação** | Douglas |
| **Status** | **aprovado** |
| **Data** | 10/09/2026 |

### A.7 · Potencial de ganho: fator de conversão e limites (D25) — decidido por Douglas em 10/09/2026

*Regra(s) no dicionário: RN-34, RN-35 (`docs/regras_negocio.md`, F0).*

| Campo da ficha | Conteúdo |
|---|---|
| **Nome da regra** | Potencial de entrada por categoria |
| **Objetivo** | Traduzir "lojas a positivar" em t e R$ como oportunidade calculada, nunca como previsão |
| **Fórmula** | `potencial_entrada(nível, cat) = lojas_a_positivar(nível, cat) × kg_medio_compradores(nível, cat) × fator(cat)` |
| **Lojas a positivar** | Σ, por distribuidor abaixo do P75 da categoria, de `(P75 − penetração_d) × positivados_d` (estrutura do print, C.2), na régua A.2, no último mês fechado (A.3) |
| **Fator (opção b)** | **observado, por categoria**: kg médio das lojas que fizeram a **primeira compra da categoria** (já ativas no canal) no seu 1º mês ÷ kg médio de todos os compradores da categoria, medido na **janela de 5 meses** e recalculado a cada mês. Sem premissa fixa. Medido em ago/26 (só o mês): Amendoim 30%, Gomas 48%, Gelatina 53%, Regaliz 46% — o "50%" do print era razoável em três e otimista em uma |
| **kg médio por distribuidor** | usado quando o distribuidor tem **≥ 30** lojas compradoras na categoria; abaixo disso, média do canal, com marcação na tabela |
| **Outliers** | média truncada no **P99** da categoria (por nível) |
| **Em R$** | mesma fórmula com R$ por loja (`rs_pdv`), sob a mesma régua do sell-through (A.4) |
| **Potencial em regime** | teto = a positivar × kg médio dos compradores (sem fator); se exibido, com o nome "potencial em regime" e **nunca somado** ao de entrada |
| **Nomes na tela** | "Potencial de entrada (t/mês)" e "(R$/mês)"; rótulo fixo "oportunidade calculada, não previsão"; memória de cálculo no tooltip (a positivar × kg médio × fator, com os três números) |
| **Período** | a positivar e médias: último mês fechado (A.3); fator: janela de 5 meses |
| **Base de origem** | fato (kg por PDV × categoria × mês), `DN_DISTRIBUIDOR_CAT_MES`, `DIM_PDV.PRIMEIRO_MES` |
| **Tratamento de nulos** | categoria sem loja nova na janela → fator indisponível → potencial "—" com nota (nunca 50% de fallback silencioso) |
| **Responsável pela validação** | Douglas |
| **Status** | **aprovado** (opção b e complementos 1–5) |
| **Data** | 10/09/2026 |

### A.8 · Categorias foco (D33) — decidido por Douglas em 10/09/2026

*Regra(s) no dicionário: RN-19 (`docs/regras_negocio.md`, F0).*

| Campo da ficha | Conteúdo |
|---|---|
| **Nome da regra** | Categorias foco do plano de penetração |
| **Lista** | **Amendoim, Gomas, Gelatina, Regaliz** (as quatro do print). Em ago/26 somam 76% do volume e 77% do valor do canal. Bala (10,4% do volume, penetração 20%) fica fora por decisão comercial, apesar de ser a maior oportunidade de entrada em t entre as não foco |
| **Onde fica** | `config/config.yaml` → `regras.penetracao.categorias_foco` (lista de ids de categoria), alterável sem código; a mudança registra data e responsável nesta ficha e no changelog |
| **Quem define** | Douglas (comercial). Critério não está nas bases: é escolha de plano |
| **O que "foco" muda na tela** | estrela e ordenação primeiro nas tabelas; cards e resumos da aba calculados sobre as foco ("a positivar nas 4 foco", "potencial nas 4 foco"); as outras seis visíveis logo abaixo com o **mesmo cálculo**; total das dez exibido abaixo do total das foco. **Nada** de benchmark, régua ou potencial diferente: a régua é igual para as dez |
| **Vigência** | a lista vale para toda a série exibida (não há histórico de foco); alterar a lista muda o painel inteiro na execução seguinte |
| **Base de origem** | `DIM_PRODUTO.CATEGORIA` (ids) + config |
| **Responsável pela validação** | Douglas |
| **Status** | **aprovado** (lista e itens 2–4) |
| **Data** | 10/09/2026 |

### A.9 · PDV multi-distribuidor por supervisor (D35) — decidido por Douglas em 10/09/2026

*Regra(s) no dicionário: RN-10 (`docs/regras_negocio.md`, F0).*

| Campo da ficha | Conteúdo |
|---|---|
| **Nome da regra** | Contagem do PDV multi-distribuidor nos níveis da penetração |
| **Definição** | **Regra vigente mantida** (rodada 5, 08/09): o PDV conta **uma vez em cada nível onde aparece** — uma vez por distribuidor, uma vez por supervisor, uma vez no canal. Nenhuma atribuição a um único supervisor |
| **Consequência na tela** | a linha TOTAL da tabela por supervisor é o canal, não a soma das linhas; nota fixa: "N PDVs atendidos por mais de um território; a soma das linhas excede o total" (N calculado, exibido) |
| **Medição ago/26** | 796 PDVs em mais de um distribuidor; 650 deles dentro do mesmo supervisor; **146** em mais de um supervisor (0,2% do canal); soma por supervisor 71.624 × total 71.478 |
| **Lojas a positivar e potencial** | não afetados: calculados por distribuidor × categoria (D10) e agregados no nível por recálculo, nunca por soma |
| **Alternativas rejeitadas** | atribuir ao supervisor de maior kg no mês (o print fechava a soma assim) ou na janela: criaria regra nova, instável mês a mês, e faria a penetração do "perdedor" cair sem perder a loja |
| **Base de origem** | fato + `DIM_DISTRIBUIDOR.SUPERVISOR` |
| **Responsável pela validação** | Douglas |
| **Status** | **aprovado** |
| **Data** | 10/09/2026 |

### A.10 · Calendário: nome do ano fiscal, histórico, padrão e acumulados (D4, D5, D29, D31) — decidido por Douglas em 10/09/2026

*Regra(s) no dicionário: RN-23, RN-24, RN-25 (`docs/regras_negocio.md`, F0).*

| Campo da ficha | Conteúdo |
|---|---|
| **Nome da regra** | Perspectiva temporal do painel |
| **Ano fiscal** | setembro a agosto (regra vigente, `calendario.fiscal_mes_inicio: 9`); `ANO_FISCAL` = ano em que termina (set/25 → 2026), como já está na `DIM_CALENDARIO` |
| **Nomenclatura (D4, opção d)** | cabeçalhos e cards: **"Ano fiscal 2026 (set/25–ago/26)"**; colunas e eixos: **`FY26`**. Rótulos no config (`calendario.rotulo_longo`, `rotulo_curto`), não em código |
| **Perspectiva padrão (D29)** | **fiscal**. Toggle na barra global (Ano fiscal · Ano civil), estado em `localStorage` e URL (`cal=fiscal|civil`). O calendário muda só o eixo temporal (ordem dos meses, agrupamento, acumulado, "mesmo período LY"); não muda base ativa, segmentos, RTM nem o corte de migração |
| **Acumulados (D31)** | calculados **no pipeline** e entregues no JSON: YTD civil, YTD fiscal e seus pares LY quando todos os meses existirem; validados como soma da série. Na mesma fase, os Δ% do gráfico (hoje recalculados em JS por `dnVar`/`dnMean`) passam a vir do JSON — fecha o risco RK13 |
| **Regras de exibição** | acumulado só quando **todos** os meses do período estão na série; período com mês em andamento leva a etiqueta existente; meses futuros não aparecem; comparativo anual (FY × FY, ano × ano) **bloqueado com nota** enquanto não houver par; mês sem realizado dentro da série aborta (validação), nunca zera |
| **Histórico (D5)** | **pedir à Mtrix** a extração de set/24 a jun/25 (10 arquivos, ~400 MB, ~6 min de ingestão, nenhuma mudança de código). Com eles: LY em toda a série exibida e FY2026 × FY2025. Enquanto não vier: "sem LY antes de jul/26" declarado; não bloqueia nenhuma fase. Registrado como pendência de dado (L7) |
| **Base de origem** | `DIM_CALENDARIO`, `DN_*_MES` (soma), config |
| **Responsável pela validação** | Douglas |
| **Status** | **aprovado** |
| **Data** | 10/09/2026 |

### A.11 · Gráficos: Last Year explícito e evolução por categoria (D6, D7, D8, D9) — decidido por Douglas em 10/09/2026

*Regra(s) no dicionário: RN-22, RN-46, RN-47 (`docs/regras_negocio.md`, F0).*

| Campo da ficha | Conteúdo |
|---|---|
| **Gráfico de evolução (D6)** | **coluna** = realizado do mês; **linha com marcador** = mesmo mês do ano anterior, só onde existir; **Δ% vs LY** escrito sob o mês quando houver; tooltip com atual, LY e Δ (% ou p.p. conforme a métrica). Segunda chave do gráfico, "PDVs · Volume/Valor": em PDVs mantém o empilhado por segmento e a linha da base ativa; em métrica, coluna única na métrica ativa e linha LY da mesma métrica (nunca três escalas no mesmo eixo) |
| **Regra "sem LY"** | mês sem par no ano anterior = **ausência de dado**: sem ponto, linha interrompida, Δ "—", legenda "sem LY na série (Mtrix a partir de jul/25)". Nunca zero. Formaliza o comportamento atual do código (R12) |
| **Campos novos (D7)** | `volume_ly` e `receita_ly` em cada ponto das séries (canal, categoria, supervisor, distribuidor), por junção em `ANO_MES_LY` no pipeline, com os Δ% já calculados (coerente com D31); entram no inventário e na validação (LY da série = valor do mês correspondente) |
| **Evolução por categoria (D8, opção a + d)** | gráfico de linhas com **Top N** (padrão 4 ou 5, parâmetro no config) mais a linha "outras categorias" agregada, e **seleção manual** de quais categorias exibir (as foco marcadas com estrela e ligadas por padrão); a tabela de categorias ganha **participação %** na métrica ativa, **Δ participação vs LY** (quando houver) e **sparkline** da série por linha |
| **Métrica (D9)** | a do seletor global (t ou R$); as réguas de PDV (penetração e % de cobertura da categoria) continuam nas colunas da tabela |
| **Aceleração / desaceleração** | sem regra nesta rodada; volta quando houver LY na série inteira (D5) |
| **Base de origem** | `DN_CANAL_MES`, `DN_CANAL_CAT_MES` e demais `DN_*_MES` (séries), `DIM_CALENDARIO.ANO_MES_LY` |
| **Responsável pela validação** | Douglas |
| **Status** | **aprovado** |
| **Data** | 10/09/2026 |

### A.12 · Matriz de Oportunidades (D10, D11, D12, D13) — decidido por Douglas em 10/09/2026

*Regra(s) no dicionário: RN-31, RN-42 (`docs/regras_negocio.md`, F0).*

| Campo da ficha | Conteúdo |
|---|---|
| **Unidade elementar (D10)** | o par **distribuidor × categoria** no último mês fechado (A.3), em `DN_DISTRIBUIDOR_CAT_MES`. Supervisor e canal são agregações por **recálculo** nesse grão, nunca soma de linhas |
| **Dupla contagem (D11)** | dentro de uma categoria, "lojas a positivar" soma entre distribuidores como **positivações de categoria** (PDVs multi-distribuidor declarados na nota: 796 em >1 distribuidor, 146 em >1 supervisor em ago/26); entre categorias, o total é "positivações de categoria", **nunca** "PDVs a positivar" — os dois nomes aparecem separados; potencial em t e R$ soma entre categorias e distribuidores (é volume, não loja), e o "potencial de entrada" nunca soma ao "potencial em regime"; total do canal = recálculo no canal |
| **Eixos (D12)** | X = lojas a positivar; Y = distância ao P75 em p.p.; bolha = potencial de entrada na métrica ativa (t ou R$); um ponto por par distribuidor × categoria; filtros de supervisor, distribuidor e categoria recortam os pontos; tooltip com a memória de cálculo |
| **Quadrantes** | **não na primeira entrega**. Segunda entrega, se aprovada, com fronteiras na mediana de X e de Y do recorte e nomes "ganho rápido / estrutural / foco pontual / manutenção", validados com exemplos reais |
| **Score único (D13)** | **não criar**. A tabela ordenável cobre os rankings (lojas a positivar, gap, potencial t, potencial R$) sem esconder a régua. Se vier a ser pedido: proposta com fórmula, pesos e sensibilidade antes de código |
| **Saídas da 1ª entrega** | tabela rastreável (distribuidor, supervisor, categoria, positivados, compradores, penetração, P75, gap p.p., lojas a positivar, kg/loja, fator, potencial t, potencial R$) com ordenação, busca e CSV; drill da linha até a lista de PDVs a positivar (blob, D32); nuvem X × Y × bolha; destaques via resumos (D17) |
| **Nomes na tela** | "Oportunidade calculada", "Potencial de entrada", "Referência: P75 dos distribuidores na categoria" — nunca "meta", "previsão" ou "ganho garantido" |
| **Base de origem** | `DN_DISTRIBUIDOR_CAT_MES`, fato (fator A.7), `DIM_DISTRIBUIDOR` (supervisor), config (P75, foco) |
| **Responsável pela validação** | Douglas |
| **Status** | **aprovado** |
| **Data** | 10/09/2026 |

### A.13 · Filtro por Supervisor e cubos novos (D18, D19, D20) — decidido por Douglas em 10/09/2026

*Regra(s) no dicionário: RN-15, RN-16, RN-37, RN-44 (`docs/regras_negocio.md`, F0).*

| Campo da ficha | Conteúdo |
|---|---|
| **Nome da regra** | Filtro global por Supervisor |
| **Definição** | Supervisor = N3 da hierarquia via código interno do distribuidor (regra vigente); atributo do distribuidor, herdado pelo PDV que ele atende |
| **Escopo por aba (D18)** | **Visão geral** (cards e gráfico via `DN_SUPERVISOR_CANAL_MES`; tabela de categorias via `DN_SUPERVISOR_CAT_MES`) · **Clusters e supervisores** (destaca a linha do supervisor; clusters não recortados) · **Distribuidores** · **Pontos de venda** (mapa distribuidor → supervisor no blob) · **Penetração** · **Matriz**. **Fora**: RTM (aderência é do cliente ao destino; o bloco já filtra por destino) e Definições |
| **Seleção (D19)** | **única**, com "Todos", como o Distribuidor. Sem multi-seleção; o nível gerente (N2) é o caminho para ver territórios juntos, se um dia for pedido |
| **Interação** | escolher supervisor restringe a lista de distribuidores aos dele; escolher distribuidor de outro supervisor limpa o supervisor; chip esmaecido onde não age; estado em `localStorage` e URL (`sup=`) |
| **Aviso** | fixo: "hierarquia vigente em {data da carga}, aplicada a toda a série" (4 territórios "[VAGO]" hoje) |
| **Cubos novos (D20)** | **`DN_SUPERVISOR_CAT_MES`** (14 × 10 × meses) e **`DN_CLUSTER_CAT_MES`** (12 × 10 × meses), derivados da fato sem dado novo, com as mesmas colunas dos cubos de categoria existentes (positivados, volume, receita, base ativa, penetração, % cobertura, comparativos); validados como o de distribuidor × categoria (volume por categoria = cubo do nível) |
| **Retrato mensal da hierarquia (L9)** | a cada ingestão o pipeline grava uma cópia datada de `DIM_DISTRIBUIDOR` (`data/dn/curated/historico/DIM_DISTRIBUIDOR_<AAAA-MM-DD>.parquet`) para construir histórico de supervisor daqui em diante; nada muda no painel agora |
| **Base de origem** | `Hierarquia_Consolidada.xlsx` (N3), `Distribuidores_DePara.xlsx`, fato |
| **Responsável pela validação** | Douglas |
| **Status** | **aprovado** |
| **Data** | 10/09/2026 |

### A.14 · Resumos executivos, Drop, PDV × categoria, limiares de cor (D17, D26, D27, D32, D34) — decidido por Douglas em 10/09/2026

*Regra(s) no dicionário: RN-36, RN-38, RN-39, RN-48, RN-49 (`docs/regras_negocio.md`, F0).*

| Campo da ficha | Conteúdo |
|---|---|
| **Resumos executivos (D17, D27)** | **Não existem hoje** (D27 confirmado); construção nova. **Modelo aprovado**: cada frase é uma regra no config (`resumos.<aba>.<id>`), avaliada no navegador sobre os dados embutidos e os filtros ativos, com seis partes: o que · onde · quanto · contra o quê · por que merece atenção (limiar da regra) · próximo nível (link que aplica o filtro). Só fatos numéricos; sem adjetivo, causa, prescrição ou responsabilização; sem dado no recorte → "sem dado suficiente para X". O pipeline valida cada regra contra o dado do mês em um recorte por aba. Tooltip por frase: indicador, período, filtros, base, id da regra, comparação, benchmark, memória de cálculo, data dos dados |
| **Lista de frases da 1ª entrega (D17)** | **Visão geral**: DN do mês vs mês anterior e vs LY · distribuidor com maior contribuição positiva e negativa à variação de PDVs · categoria com maior queda de % cobertura · PDVs sem compra no mês e t/R$ vendidos a eles na janela. **Clusters e supervisores**: cluster com maior Δ p.p. (+/−) · supervisor com maior Δ absoluto de PDVs (+/−) · supervisor com menor DN vs canal. **Distribuidores**: maior queda e maior alta de cobertura · novos e seu peso · abaixo do P75 nas foco · sem venda no mês (mês em andamento). **Pontos de venda**: sem compra com maior kg/R$ na janela · % do volume nos N maiores. **RTM**: aderência e Δ · vazamento · ativados parados · destino com maior gap. **Penetração**: categoria com maior nº a positivar · nível mais distante do P75 · maior oportunidade de recorrência. **Matriz**: maior oportunidade em t e em R$ · principal gap de cobertura mensal · principal oportunidade de mix |
| **Limiares** | **não fixados agora**: vêm na fase F9 com exemplos reais, aprovados item a item antes de ligar cada frase |
| **Drop (D26)** | **não existe** nas bases (Mtrix sem pedido, entrega ou dia); nenhum proxy recebe esse nome; reabre só com base nova |
| **PDV × categoria (D32)** | **medir** a máscara por par (um inteiro de 10 bits por par distribuidor × PDV, estimativa +0,1 a 0,3 MB) antes de embutir; é o que dá o drill até os PDVs a positivar e a recorrência por categoria; se a medição passar de **1 MB**, volta a decisão |
| **Limiares de cor (D34)** | verde a partir de **95%** do benchmark, vermelho abaixo de **70%**, neutro entre — como **parâmetros no config** (`regras.penetracao.cor_verde_pct`, `cor_vermelho_pct`), régua escrita na nota da tabela; revisar depois de ver a distribuição real (com P75 de Amendoim em 71,4%, 95% equivale a penetração de 67,8%) |
| **Responsável pela validação** | Douglas |
| **Status** | **aprovado** |
| **Data** | 10/09/2026 |

### A.15 · Respostas às perguntas Q1, Q4, Q5 — Douglas, 10/09/2026

*Regra(s) no dicionário: RN-06 (Q1), RN-50 (Q5) (`docs/regras_negocio.md`, F0).*

| # | Pergunta | Resposta | Consequência |
|---|---|---|---|
| Q1 | A remoção do seletor "Peso · t / Receita · R$" de 09/09 foi decisão sua? | **Sim, decisão do Douglas, reconhecida como equivocada** | o seletor volta na fase F1 sob a regra A.4 (sell-through), sem o JS herdado do protótipo (RK1); registrado para não se repetir |
| Q4 | Nenhuma decisão fechada do RETOMADA §4 é reaberta sem pedido explícito | **Confirmado** | base ativa 5 m, multi-distribuidor, segmentos, RTM, série de 12, mês em andamento permanecem |
| Q5 | Existe uma "Frente 2" (SKUs por categoria) nesta rodada? | **Não, só a Frente 1** | a decomposição kg/loja = categorias × SKUs/categoria × kg/SKU pode aparecer como leitura de apoio, sem frente própria; profundidade de SKU fica para rodada futura |
| Q3 | Abas "Alavancas" e "Evolução" do pedido: ignorar ou criar? | **Evolução: criar (F3); Alavancas: fase candidata F11** | ficha A.16 |

### A.16 · Abas "Evolução" e "Alavancas" (Q3) — decidido por Douglas em 10/09/2026

*Regra(s) no dicionário: RN-50 (`docs/regras_negocio.md`, F0).*

| Campo da ficha | Conteúdo |
|---|---|
| **Evolução** | **criar** a aba, como reorganização sem cálculo novo: recebe tudo o que é temporal — gráfico de evolução com LY (A.11), evolução por categoria Top N (A.11), tabela da série com acumulados e o toggle de calendário (A.10). A Visão geral fica como foto do mês (cards, resumo dinâmico, tabela de categorias). Entra na fase **F3**. `painel.abas` do config ganha a aba; os resumos de "Evolução" do pedido (D17) passam a viver nela |
| **Alavancas** | **não criar nesta rodada**. Registrada como fase candidata **F11**: decomposição da variação do resultado em fatores, por identidades aritméticas sem premissa — `volume = base ativa × DN × kg por PDV comprador` e `kg por loja = categorias por loja × SKUs por categoria × kg por SKU` (print 1) — com a contribuição de cada fator vs mês anterior e vs LY (efeito de cada termo com os demais fixos). Só será proposta depois que Penetração e Matriz estiverem publicadas. "Categoria com maior contribuição e maior retração" já cabe nos resumos da aba Evolução |
| **Responsável pela validação** | Douglas |
| **Status** | **aprovado** (opção a) |
| **Data** | 10/09/2026 |

**Etapa 1 encerrada em 10/09/2026:** D1–D35 decididas (fichas A.1–A.16); Q1–Q5 respondidas. Próximo passo: fase F0 (dicionário de regras e config), mediante proposta escrita e aprovação item a item.

---

## Anexo B — correspondência com a segunda auditoria (`evolucao_fase0_auditoria`)

| Segunda auditoria | Este documento |
|---|---|
| N1 Valor · D-V1 · D-V2 sinais · D-V3 padrão t · D-V4 R$ no blob/RTM | D1 · D30 · D2 · D1 |
| N2/N3 base elegível, ativo/novo · D-P1 janela 5×6 · D-P3 cliente = PDV | D24 · **D28** · D24 |
| N4 cobertura mensal · N5/D-P2 régua | R7/D24 · D23 (decidida) |
| N6 drop · N7 faturamento | D26/L2 · L10 (AMB1) |
| N8/D-B1 benchmark (mediana) | superado por A.1 (P75) |
| N9/D-C1 nome FY · D-C2 padrão · D-C3 acumulados · D-C4 sem par | D4 · **D29** · **D31** · RK7 |
| N10/D-L1 sem LY = ausência · D-L2 chaves do gráfico | D6 · D6 |
| N11 remoção do seletor de 09/09 | Q1 |
| D-E1 categorias | D8/D9 (AMB4) |
| D-M1..M3 matriz | D10–D13 |
| D-R1/R2 resumos | D17 |
| D-S1 supervisor | D18–D20 (AMB3) |
| D-X1 drop/faturamento fora · D-X2 Mtrix antiga · D-X3 print · D-X4 abas · D-X5 reabrir decisões | D26 · D5 · Q2 · Q3 · Q4 |
| L1–L10 (segunda) | L7, L2, L10, L1, L9, L3, L8, sinais (§4), L5, L12 |
| R1–R12 (segunda) | RK2, RK5, RK7, RK6, RK3, RK4, RK14, RK13, RK9, item resíduos (§3.4), RK15, armadilha OneDrive (RETOMADA) |
| máscara PDV × categoria | **D32** (AMB2) |
| F1–F7 (segunda) | F0–F10 |

---

## Anexo C — leitura dos prints de referência (recebidos em 10/09/2026 à noite)

Quatro prints de um painel anterior (leitura Mtrix **jun/26**, 65.527 PDVs positivados, 12 linhas de supervisor). Servem como
conceito; nada foi copiado. Para cada um: o que afirma, o que é dado / premissa / estimativa, e o que se reproduz na curated de hoje
(teste feito em jun/26 e ago/26, só leitura).

### C.1 · Print 1 — "Mix tem duas fontes de ganho" (ficha da Frente 1)

| Linha do print | Conteúdo | Classificação | Na curated |
|---|---|---|---|
| Decomposição | kg por loja = categorias que ela compra × SKUs por categoria × kg por SKU | **FATO calculável**: os três termos existem na fato (categoria via SKU, SKUs distintos por PDV, kg por SKU) | reproduzível |
| O que é | loja não compra a categoria e passa a comprar (primeira venda) | definição = objetivo "ativação da categoria" (§18) | — |
| KPI | % de lojas que compram a categoria | = régua oficial A.2 (÷ positivados) | existe |
| Onde estamos | 2,7 das 10 categorias por loja | média de categorias distintas por PDV positivado **no mês** | **2,72** em jun/26; 2,70 em ago/26 (na janela de 5 meses seria 3,46: régua diferente, não misturar) |
| Onde dá para chegar | P75 dos distribuidores, categoria a categoria | = A.1 | — |
| O que falta | 34.822 positivações de categoria nas 4 foco | soma de "lojas a positivar" das 4 foco | estrutura reproduzida (C.2) |
| Quanto vale | 123,3 t/mês nas 4 foco | soma dos ganhos das 4 foco, com **premissa de 50%** | idem |
| Quem executa | negociação de espaço com o dono da loja | texto prescritivo | **fora** (resumos não prescrevem ação sem regra, §21) |
| "A frente 1 mexe no primeiro termo, a fr…" | texto cortado; sugere Frente 2 = SKUs por categoria | — | **Q5** |

### C.2 · Print 2 — cards e tabela da Frente 1

Cards: Categorias por loja 2,7 de 10 · Lojas a positivar 34.822 · Ganho de volume 123,3 t/mês · Maior oportunidade Amendoim
60% → 76%, +63,1 t/mês. Texto: "Isto é mix, não cobertura — o PDV já está dentro dos 65.527 cobertos".

Tabela (categoria · lojas que compram · penetração · benchmark · % do benchmark · lojas a positivar · kg por loja que compra · ganho t/mês):

| Categoria | Print (jun/26) | Reprodução na curated, jun/26 | Reprodução, ago/26 |
|---|---|---|---|
| Amendoim | 39.471 · 60,2% · P75 75,9% · 79% · +11.216 · 11,3 kg · 63,1 t | 40.051 · 61,0% · 74,3% · 10.388 · **11,3 kg** · 58,7 t | 39.832 · 55,7% · 71,4% · 12.824 · 9,3 · 59,9 |
| Gomas | 35.256 · 53,8% · 66,7% · 81% · +9.039 · 7,6 · 34,6 | 35.523 · 54,1% · 61,8% · 6.643 · 7,7 · 25,5 | 38.242 · 53,5% · 60,1% · 6.640 · 8,3 · 27,7 |
| Gelatina | 23.527 · 35,9% · 46,6% · 77% · +8.136 · 3,2 · 12,9 | 23.746 · 36,1% · 44,8% · 7.460 · **3,2** · 11,8 | 27.223 · 38,1% · 43,8% · 6.111 · 3,6 · 10,9 |
| Regaliz | 27.054 · 41,3% · 49,5% · 83% · +6.431 · 4,0 · 12,7 | 27.323 · 41,6% · 48,7% · 6.092 · 3,9 · 12,0 | 29.877 · 41,8% · 48,4% · 6.356 · 4,2 · 13,4 |

Leitura:
- **Fórmulas confirmadas na estrutura**: penetração = lojas ÷ positivados do canal (A.2); % do benchmark = penetração ÷ P75;
  kg por loja = kg da categoria ÷ lojas compradoras (bate ao decimal); **ganho = lojas a positivar × kg por loja × 50%** (fecha nas
  quatro linhas do print: 11.216 × 11,3 × 0,5 = 63,4; 9.039 × 7,6 × 0,5 = 34,3; 8.136 × 3,2 × 0,5 = 13,0; 6.431 × 4,0 × 0,5 = 12,9).
- **"Lojas a positivar" não é o gap do canal** ((75,9 − 60,2)% × 65.527 daria 10.288, o print mostra 11.216): é a **soma, por
  distribuidor abaixo do P75, de (P75 − penetração do distribuidor) × positivados do distribuidor**. Reproduzido aqui com essa fórmula.
  Coerente com a unidade distribuidor × categoria (D10) e com a regra "somar dentro da categoria, nunca entre categorias" (D11): os
  34.822 são "positivações de categoria", não PDVs.
- **Diferenças de absolutos** (39.471 × 40.051 lojas; P75 75,9 × 74,3): o print usou outra leitura de jun/26 (65.527 positivados
  contra 65.709 na curated de então e 66.788 na reingestão de 10/09, com 67 → 72 distribuidores na fato). Não é erro de fórmula; é
  base diferente. A implementação sairá dos números da curated atual e será validada contra `DN_DISTRIBUIDOR_CAT_MES`.
- **Premissa de 50%** declarada no rodapé do print: entra como D25; o painel novo a exibe ao lado do número, nunca escondida.
- **Nota de competência** ("leitura real da Mtrix jun/26"): coerente com A.3 (último mês fechado).
- **Gráfico**: barras pareadas penetração hoje × P75 por categoria, foco com estrela, outras em cinza, ganho em t sobre cada par:
  formato reproduzível com o SVG do painel; as 4 foco viram D33.
- **"ver as outras 6 categorias"**: o mesmo padrão de amostra + expandir do componente atual.

### C.3 · Print 3 — Penetração das 4 foco por supervisor

Tabela supervisor × (PDVs, penetração nas 4 foco, ganho t/mês), cores verde ≥ 95% do benchmark e vermelho < 70%, TOTAL 65.527 PDVs
e 123,6 t (o card diz 123,3: pequena inconsistência interna do print, provavelmente arredondamento por linha).

- **Prova da necessidade do cubo supervisor × categoria** (L4, D20): sem ele esta tabela não existe.
- **Soma das linhas = total do canal** (6.126 + … + 89 = 65.527, exato). Na regra do DN o PDV multi-distribuidor conta em cada
  distribuidor, e a soma por supervisor ficaria **acima** do total (804 PDVs em ago/26). O print atribuiu cada PDV a um supervisor só,
  ou a base da época não tinha o caso. Vira **D35**.
- **Hierarquia do print é a de jun/26**: 12 supervisores, nomes "Alcindo" e "Oliveira" como titulares; hoje são 14 rótulos, com
  "Oliveira" já vago e "Alcindo" ausente. Confirma RK6/L9: a tabela muda de cara a cada retrato da hierarquia, sem histórico.
- **Rótulo por primeiro nome**: o painel atual usa "código - função - nome"; rótulo curto é decisão de exibição (config `rotulos`).
- **Limiares de cor** 95% / 70%: não existem no projeto; viram D34 (parâmetros no config, nunca no código).
- **"Clique não precisa"**: no painel atual toda linha abre drill; manter o padrão é decisão de UX na fase.

### C.4 · Print 4 — Categoria dentro do cluster (SKUs/PDV e Ganho t/mês)

O print declara "**abertura por cluster estimada** até a Mtrix abrir categoria × segmento" e mostra SKUs/PDV por categoria × cluster.
Os valores são o número do canal multiplicado por um fator fixo por cluster (Amendoim 3,1 → 4,3 / 3,9 / 3,4 / 2,2 / 1,6 / 1,8; Gomas 2,1
→ 2,9 / 2,7 / 2,3 / 1,5 / 1,1 / 1,2: mesmas razões 1,39 / 1,26 / 1,10 / 0,71 / 0,52 / 0,58 em todas as linhas).

- **A estimativa é desnecessária aqui**: cada linha da Mtrix traz SKU (→ categoria) e Segmento do PDV (→ cluster). O cruzamento real
  é calculável da fato sem dado novo. Calculado em ago/26 (SKUs distintos por PDV comprador da categoria, média por cluster):

| Categoria | Canal | AS 20+ | AS 10-19 | AS 05-09 | AS 01-04 | Mercearia | Outros |
|---|---|---|---|---|---|---|---|
| Amendoim | 3,0 | 5,0 | 4,5 | 3,9 | 2,9 | 2,5 | 2,8 |
| Gomas | 2,2 | 3,1 | 3,1 | 3,2 | 2,3 | 1,9 | 2,3 |
| Regaliz | 3,0 | 3,9 | 4,3 | 4,1 | 3,1 | 2,7 | 2,7 |
| Bala | 2,5 | 3,3 | 3,1 | 2,9 | 2,6 | 2,2 | 2,6 |
| Gelatina | 3,1 | 3,5 | 3,6 | 3,5 | 3,3 | 3,0 | 2,7 |
| Granulado | 1,8 | 1,9 | 2,0 | 2,1 | 1,8 | 1,6 | 1,9 |
| Jubes | 1,5 | 2,2 | 1,6 | 1,7 | 1,6 | 1,5 | 1,5 |
| Chocolate | 1,7 | 2,2 | 2,1 | 2,0 | 1,7 | 1,7 | 1,8 |
| Pirulito | 1,3 | 1,0 | 1,5 | 1,4 | 1,3 | 1,3 | 1,3 |
| Compound | 1,0 | — | 1,0 | 1,0 | 1,0 | 1,0 | 1,0 |

- **A estimativa do print estava errada em forma e valor**: os multiplicadores reais não são uniformes (Gelatina quase não varia por
  cluster: 3,5 → 2,7; Amendoim varia muito: 5,0 → 2,5), e "AS 01-04" não fica abaixo do canal como o print supunha. É o caso
  concreto da regra de ouro: estimar quando o dado existe produz uma tabela plausível e falsa.
- O toggle "SKUs/PDV · Ganho t/mês" do print é a Frente 2 (profundidade de SKU dentro da categoria): **Q5**.
- Cores verde/vermelho por célula sem régua declarada no print: se entrar, régua e limiar no config (D34).

### C.5 · O que muda no documento por causa dos prints

| Onde | Antes | Depois |
|---|---|---|
| L12 / Q2 | print ausente | recebido; conceito e fórmulas lidos |
| D25 | "premissa de conversão (referência: 50%)" | estrutura fixada: ganho = a positivar × kg por loja × 50%; a positivar = Σ gaps por distribuidor abaixo do P75; falta aprovar 50%, mês/janela da média e limites |
| D10/D11 | unidade e dupla contagem em aberto | o print corrobora distribuidor × categoria e "positivações de categoria" (não PDVs) como unidade do total |
| L4 / D20 | cubo supervisor × categoria "decisão de projeto" | print 3 prova o uso; cubo categoria × cluster também calculável (print 4) sem estimativa |
| Novas | — | D33 categorias foco · D34 limiares de cor · D35 atribuição do PDV multi-distribuidor por supervisor · Q5 Frente 2 |
| §18 | estrutura proposta | acrescentar cards do print (categorias por loja, a positivar, ganho, maior oportunidade), coluna "% do benchmark", gráfico pareado, e a decomposição kg/loja em três termos como leitura de apoio |

*Documento de análise consolidado. Nenhum arquivo do projeto DN foi executado, alterado, criado ou apagado.*
