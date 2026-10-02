# Frequência de compra · Etapa 2 · Proposta

**Data:** 13/09/2026 · **Base:** medições da Etapa 1 (`docs/frequencia_etapa1_medicao.md`) e as respostas da §12, mais as medições
novas desta etapa. **Nada foi implementado**: não mexi em `dn/`, `config/`, `template/`, `bases/` nem `data/`. Os testes rodaram em
scripts somente leitura e numa **cópia** do projeto no scratchpad (`…\scratchpad\sb\`). Essa cópia lê as bases originais e grava
tudo dentro dela, sem publicar nada.
Cada número traz o que foi **MEDIDO**. O que for **ESTIMADO** está marcado como tal.

## 0. Resumo

1. **Frequência do canal:** dá para ter o número **exato** todo mês, porque sai da linha de total da Mtrix. Frequência do total × PDVs distintos = total de atendimentos (NFs), um inteiro nos 25 arquivos.
2. **Frequência do PDV, do distribuidor, do supervisor, do cluster e da categoria:** **não dá para calcular com exatidão.** A base vem por SKU e a Mtrix não entrega outro grão. Em cada par distribuidor × PDV, o valor verdadeiro fica entre o **maior** valor de SKU e a **soma** dos valores de SKU. Essa faixa é larga: no distribuidor, a soma fica, em mediana, 460% acima do maior valor.
3. **Regras testadas:** 6 regras de estimativa, contra o único gabarito que existe (o total do canal) e contra os casos de valor conhecido (par com uma só linha = 19% a 22% dos pares).
   - **Recomendada: "união proporcional" (MA).** Fecha exatamente com o total da Mtrix em todo mês, acerta 100% dos casos conhecidos, nunca sai da faixa [maior; soma] e tem o parâmetro mais estável (varia 1,1% entre meses).
   - **Fora da amostra** (parâmetro de um mês aplicado ao mês seguinte), ela erra o total em **1,01% em média e 2,14% no pior mês**.
   - **Alternativa sem hipótese: "mínimo de atendimentos" (M0).** Nunca exagera, mas subestima o canal em **6,6% a 9,7%**.
4. **Limite que não se remove:** o erro por PDV, distribuidor e categoria **não é mensurável** com as bases. Só o do canal é. A proposta declara isso na tela e na ficha.
5. **Pipeline:** com as bases novas e as decisões da Etapa 1, a cópia rodou com **24 meses** e **passou as 125 checagens de validação**.
   - A cópia deixou set/24 de fora, porque a SBM ainda não está no de-para.
   - HTML com 12 meses exibidos: **11,5 MB** (limite 12 MB).
   - HTML com a série completa exibida (o custo do seletor): **11,8 MB**, com **folga de 161 KB**.
   - A frequência vai somar **cerca de 50 a 160 KB (ESTIMADO)**. Por isso **o tamanho do HTML precisa de uma decisão** (pergunta 4).

---

## 1. Definições (respostas da Etapa 1, §12)

| Item | Definição |
|---|---|
| Atendimento | **Uma NF** do distribuidor para o PDV no mês (R1) |
| Devolução | Não conta (R1); na prática, **só linhas com kg > 0** entram (R8) |
| Frequência do PDV no distribuidor | Número de NFs daquele distribuidor para o PDV no mês (R3) |
| Frequência do PDV no canal | Soma das NFs de todos os distribuidores do PDV; o PDV conta uma vez no nível (R3, RN-10) |
| Mês em andamento | Etiquetado como parcial, igual às outras medidas (R9, RN-26) |

**Consequência medida:** como uma NF é de um só distribuidor, as NFs do PDV no canal são a soma das NFs dos pares distribuidor × PDV.
Por isso a mesma conta serve para todos os níveis: **atendimentos do nível = Σ atendimentos dos pares do nível** e
**frequência = atendimentos ÷ PDVs positivados do nível**. No distribuidor, os positivados são os daquele distribuidor; do supervisor
para cima, cada PDV conta uma vez.

## 2. O que as bases permitem (MEDIDO)

| Nível | Exato? | Por quê |
|---|---|---|
| Canal (todos os distribuidores Mtrix) | **Sim**, todo mês | Frequência do total × PDVs distintos = NFs do mês (inteiro, 25 de 25 arquivos) |
| Canal no painel (sem os 9 distribuidores fora da Hierarquia) | Não | O total da Mtrix inclui esses distribuidores, e não há total por distribuidor |
| Par distribuidor × PDV | Só quando o par tem **1 linha** (19,2% a 22,1% dos pares) | Com 2 ou mais SKUs, as NFs ficam entre o maior valor e a soma |
| Distribuidor, supervisor, cluster, segmento | Não | Soma de pares estimados |
| PDV × categoria | Só quando a categoria tem 1 linha no par (em ago/26, de 33% a 97% dos grupos, conforme a categoria) | Mesma faixa, dentro da categoria |

Faixa verdadeira no distribuidor (ago/26 e meses fechados, kg > 0): a soma fica **243% a 867% acima do maior valor** (p10 a p90).
Com isso, a faixa sozinha não serve como número de painel. É preciso uma regra.

## 3. Regras candidatas e o erro de cada uma (MEDIDO)

Para cada par distribuidor × PDV, com as frequências de SKU f₁…fₙ, cada regra estima as NFs. Calibrar uma regra significa escolher,
todo mês, o parâmetro que faz **Σ estimativas = NFs da linha de total** daquele mês.

| Regra | Como estima as NFs do par | Parâmetro (24 meses fechados) | Fecha com o total do mês? | Casos conhecidos (1 linha) | Fica em [maior; soma]? | Fora da amostra: parâmetro do mês anterior (erro médio · pior) | Qualquer mês → qualquer mês (médio · pior) |
|---|---|---|---|---|---|---|---|
| **M0 · mínimo** | maior fᵢ | — | não (−6,6% a −9,7%) | acerta | sim | 7,74% · 9,65% | 7,75% · 9,65% |
| M1 · máximo | Σ fᵢ | — | não (+470% a +518%) | acerta | sim | — | — |
| Mc · fator | c × maior fᵢ | c = 1,070 a 1,107 (variação 0,9%) | sim | **erra 100%** (soma ~1.000–1.500 NFs a mais por mês nos pares de 1 linha) | **não**: acima da soma em todos os pares de 1 linha | 1,03% · 2,16% | 1,03% · 3,45% |
| Ml · interpolação | maior + λ(Σ − maior) | λ = 0,0126 a 0,0190 (**variação 11,6%**) | sim | acerta | sim | 1,05% · 2,23% | 1,05% · 3,32% |
| MD · ocasiões fixas | D(1 − Π(1 − fᵢ/D)), mínimo = maior | D = 1,11 a 1,19 (variação 1,9%) | sim | acerta | sim | 1,27% · 2,61% | 1,29% · 4,73% |
| **MA · união proporcional** | Dₚ(1 − Π(1 − fᵢ/Dₚ)), com Dₚ = α × maior fᵢ | **α = 1,088 a 1,134 (variação 1,1%)** | **sim** | **acerta** | **sim** | **1,01% · 2,14%** | **1,02% · 3,32%** |

*"Fecha com o total": a regra é calibrada na população da linha de total (todas as linhas). Aplicada só às linhas com kg > 0 (R8),
a frequência do canal difere da Mtrix em no máximo 0,00024.*

**Como ler a MA em linguagem de negócio.** Supõe que as compras de cada SKU caem em datas ao acaso dentro de um "calendário" de
tamanho α vezes a maior frequência do par. Quando dois SKUs caem na mesma data, contam como a mesma NF. Com α perto de 1 (o que os
dados mostram), quase todas as compras de SKUs diferentes saem juntas, na mesma NF. O α do mês é o que faz o total bater com a Mtrix.
Par com 1 SKU fica exatamente com a frequência da linha.

**Sensibilidade no distribuidor (MEDIDO, 1.728 pares distribuidor × mês, 24 meses fechados):**

| Comparação | p10 | mediana | p90 | pior |
|---|---:|---:|---:|---:|
| Ml contra MA (%) | −2,72 | −0,89 | +3,20 | +21,69 |
| M0 contra MA (%) | −9,38 | −7,57 | −5,81 | −11,50 |

A ordem dos distribuidores quase não muda entre M0 e MA: correlação de postos de 0,968 a 0,988.
Em ago/26, a frequência por distribuidor vai de **1,07 a 1,67** pela MA e de 1,00 a 1,51 pela M0.

**Categoria (ago/26, média por comprador da categoria no par distribuidor × PDV, kg > 0):**

| Categoria | M0 | **MA** | Soma (M1) | Grupos exatos (1 linha) |
|---|---:|---:|---:|---:|
| AMENDOIM | 1,116 | **1,196** | 3,189 | 36,6% |
| BALA | 1,080 | **1,152** | 2,687 | 40,6% |
| CHOCOLATE | 1,047 | **1,093** | 1,814 | 59,7% |
| COMPOUND | 1,037 | **1,040** | 1,069 | 97,4% |
| GELATINA | 1,072 | **1,154** | 3,312 | 33,1% |
| GOMAS | 1,096 | **1,154** | 2,360 | 52,5% |
| GRANULADO | 1,073 | **1,126** | 1,924 | 55,0% |
| JUBES FRUIT SNACKS | 1,119 | **1,155** | 1,655 | 69,6% |
| PIRULITO | 1,056 | **1,083** | 1,376 | 75,6% |
| REGALIZ | 1,080 | **1,161** | 3,211 | 33,3% |

Coerência medida: com o α do mês, a estimativa **da categoria nunca passa a do par** (0 casos em 25 meses).
Não há gabarito para a categoria. O α é o do par, e isso é uma hipótese declarada.

**Canal em ago/26 (kg > 0):** Mtrix 1,2489 · MA 1,2489 · M0 1,1457.

**Recomendação: MA.** É a única que junta as quatro propriedades medidas: fecha com o total, acerta os casos conhecidos, fica dentro da
faixa e tem o parâmetro mais estável, com o menor erro fora da amostra. A Mc sai por inventar NFs em PDVs de 1 SKU. A Ml tem erro
parecido, mas o parâmetro é 10 vezes mais instável e diverge até 21,7% da MA num distribuidor. A M0 é a opção "sem suposição", ao
custo de ficar sempre abaixo.

## 4. Limitações (entram na ficha e na aba Definições)

1. **Erro não mensurável abaixo do canal.** O número por distribuidor, supervisor, cluster e categoria é estimado; o valor verdadeiro está entre M0 e M1 e não há como medir o erro. Só o canal Mtrix tem gabarito.
2. **Canal do painel ≠ canal Mtrix.** O painel exclui 9 distribuidores sem Hierarquia (RN-13). A frequência do canal no painel é a soma dos pares estimados, não o número da Mtrix.
3. **Devolução dentro de uma linha com kg > 0.** Se houver NF de devolução nesse SKU no mês, ela entra na contagem e não dá para separar (R8).
4. **O α depende da linha de total de cada arquivo.** Arquivo sem linha de total ou com frequência do total nula = não há calibração naquele mês. Proposta: abortar, como a reconciliação de kg já faz.
5. **Mês em andamento:** o α de set/26 foi 1,013 (a frequência cai porque há poucos dias). O número sai etiquetado como parcial (R9) e não é comparável com meses fechados.
6. **Por PDV individual** a estimativa é a menos confiável (a faixa é a do par). Ver a pergunta 2.

## 5. Proposta de cálculo

**Métrica nova:** *Frequência de compra* = atendimentos estimados ÷ PDVs positivados do recorte. Rótulo final: pergunta 7.

| Passo | Onde | O quê |
|---|---|---|
| 1 | leitura | `# Frequência de compra` → `FREQ` por linha; frequência da linha de total → gabarito `freq_total`; `K = round(freq_total × Cód. PDV distintos)`. Aborta se `|freq_total × N − K| > tolerância` (config) |
| 2 | calibração | Para cada mês, α tal que Σ MA dos pares (todas as linhas) = K. Tabela `DN_FREQ_CALIBRACAO` (mês, freq_total, N, K, α, Σ maior, Σ soma, erro final) |
| 3 | por par | `atend_par = MA(linhas kg > 0 do par, α do mês)`; por par × categoria, a mesma regra só com os SKUs da categoria |
| 4 | por nível | `atendimentos = Σ atend_par` do nível; `frequencia = atendimentos ÷ positivados` (distribuidor: pares do distribuidor; acima: PDV uma vez). Por categoria: `Σ atend_par_cat ÷ positivados na categoria` |
| 5 | comparativos | `frequencia_var_mes_anterior / _l3m / _ly` em % (mesma regra das outras medidas, RN-21/RN-22) |
| 6 | acumulado | A frequência não se soma entre meses: pergunta 5 |

Parâmetros no config (nada hardcoded): `regras.frequencia.regra: uniao_proporcional` (ou `minimo`), `regras.frequencia.populacao: kg_positivo`,
`validacao.frequencia_tolerancia_total`, `validacao.frequencia_alfa_min/max` (faixa de alerta, hoje medida entre 1,088 e 1,134).

## 6. Seletor de período (decisão 6 da Etapa 1)

Proposta: um chip na barra de filtros, **"Período: Últimos 12 meses (padrão) · Série completa · [anos]"**. Os anos seguem o toggle
fiscal/civil que já existe. O pipeline embute a série inteira, e o navegador só escolhe quais pontos desenhar; nada é recalculado em JS
(mantém a F2).
Com as bases atuais, ficam: fiscal set/24–ago/25 · set/25–ago/26 · set/26–(parcial); civil 2024 (4 meses) · 2025 · 2026.

| Onde se aplica | Onde não se aplica (não têm eixo de meses) |
|---|---|
| Gráficos e tabelas de série: Visão geral (evolução), Evolução (incluindo por categoria), Clusters e supervisores, Distribuidores (drill), mini-linhas das tabelas, evolução do RTM | Cards (mês de referência), Penetração e Matriz (mês fechado, RN-27), Pontos de venda, Alavancas (dois meses), tabela Ano a ano (já é anual) |

**MEDIDO (cópia):** a série completa custa **+346 KB** no HTML (11,5 → 11,8 MB com 24 meses). Os blocos de série embutidos vão de 418 KB para 705 KB.

## 7. Impacto no pipeline

| Parte | Mudança | Medido / estimado |
|---|---|---|
| `config.yaml · fontes.sellout` | Tirar `# PDVs Positivados` das obrigatórias (R4); `# Frequência de compra` passa a **obrigatória** (proposta); `arquivos_ignorados` continua vazio quando a SBM entrar no de-para (R5) | MEDIDO na cópia: sem a coluna obrigatória, as 13 bases de set/25 em diante são lidas |
| `dn/extract/sellout.py` | `DESTINO` ganha `FREQ`; o gabarito tolera a falta de `# PDVs Positivados` (hoje daria `KeyError`); o gabarito ganha `freq_total` | O cache invalida sozinho (hash do código dos leitores) → ingestão completa |
| `dn/transform/fato.py` | `FATO_SELLOUT` ganha a coluna `FREQ` (float); novas validações: K inteiro e α calibrável | Tamanho da fato: +1 coluna numérica em ~10,8 M linhas (ESTIMADO +5 a 10 MB em Parquet, fora do HTML) |
| `dn/metrics.py` | Calibração α por mês; `atendimentos`/`frequencia` em `serie_nivel` (níveis e categoria), `comparativos`; tabela `DN_FREQ_CALIBRACAO` | Tempo de cálculo MEDIDO na cópia com 24 meses **sem** frequência: 240 s (hoje 138 s). A frequência soma o ajuste de α (MEDIDO no script: poucos segundos por mês) |
| `dn/painel.py`, `dn/tabelas.py` | Campos novos nos pontos de série e nas linhas das tabelas; série completa embutida para o seletor | — |
| `template/template.html` | Colunas/cards conforme a pergunta 3; chip Período; nota de estimativa; faixa de ano da série completa; **exige `--regerar-exemplo`** | — |
| `template/data-inventory.json` | Uma entrada por campo novo (frequência, 3 variações, atendimentos, período) em cada caminho (`segmento.kpi`, `cluster`, `supervisor`, `distribuidor`, `categoria`, séries) | Sem a entrada, só aviso no log |
| Memória de cálculo (F10) e resumos (F9) | Ficha nova da frequência (fórmula, parcelas, nota de estimativa, link RN-58); resumo opcional | — |
| Cache e manifesto | As 25 bases mudaram → ingestão completa na primeira rodada | MEDIDO na cópia: 24 arquivos lidos em ~12 min da 1ª vez (sem cache) |
| Validações novas (propostas) | (1) `freq · K inteiro por arquivo`; (2) `freq · Σ MA = K` (tolerância); (3) `freq · maior ≤ estimativa ≤ soma` em todos os pares; (4) `freq · pares de 1 linha = FREQ`; (5) `freq · categoria ≤ par`; (6) `freq · α dentro da faixa do config` (aviso); (7) `freq · canal do JSON = curated = recálculo`; (8) `período · série completa embutida = meses da série` | As 125 checagens atuais **passaram** na cópia com 24 meses |
| **Tamanho do HTML** | Série completa + frequência | MEDIDO: 11,85 MB com a série completa (12.420.547 bytes; limite 12.582.912; folga 164.759 bytes). ESTIMADO para a frequência: ~27 KB (só o valor em cada ponto) a ~95 KB (valor + LY + 3 variações nos 2.339 pontos), mais ~20 a 60 KB nas tabelas → **pode passar do limite**. Com set/24 entra mais 1 mês (ESTIMADO ~+15 KB) |
| `docs/RETOMADA.md` §1 | Números de referência de ago/26 | MEDIDO na cópia: base ativa 124.800 · positivados 71.478 · DN 57,3% · 1.199,9 t · 71 distribuidores · RTM 1.762/1.589/173 |

**Mitigações de tamanho (MEDIDO na série completa):** os blocos de série têm **161.563 bytes só de campos vazios** (`x:""`) e
42.677 números entre aspas. Omitir campos vazios e tirar as aspas dos números **recuperaria mais do que a frequência custa**,
sem perder informação. Alternativa: subir `validacao.html_max_mb`. Decisão na pergunta 4.

## 8. RN novas (rascunho para `docs/regras_negocio.md`)

### RN-58 · Frequência de compra (atendimentos por PDV)
| Campo | Conteúdo |
|---|---|
| Objetivo | Medir quantas vezes, em média, o PDV positivado foi atendido no mês |
| Definição | Atendimento = uma NF do distribuidor para o PDV no mês; devolução não conta. Frequência = atendimentos ÷ PDVs positivados do recorte. No distribuidor, conta as NFs daquele distribuidor; do supervisor para cima, soma as NFs de todos os distribuidores do PDV, e o PDV conta uma vez (RN-10) |
| Fórmula | Par distribuidor × PDV com frequências de SKU f₁…fₙ (linhas kg > 0): `atend = Dₚ·(1 − Π(1 − fᵢ/Dₚ))`, `Dₚ = α_mês × max fᵢ`, nunca abaixo de `max fᵢ`. α_mês é calibrado para que Σ dos pares (todas as linhas) = `round(freq_total × PDVs distintos)` da linha de total do arquivo. `frequencia(nível) = Σ atend ÷ positivados(nível)`. Categoria: a mesma conta, só com os SKUs da categoria, com o mesmo α |
| Base de origem | Mtrix (`# Frequência de compra` por linha e na linha de total); `Produtos.xlsx` (categoria) |
| Campos usados | `# Frequência de compra`, `# Sell-Out (Quilos)`, `Cód. PDV`, `CNPJ do AD.`, `SKU`, `Ano/Mês` |
| Granularidade | par distribuidor × PDV (× categoria) × mês; agregada por nível |
| Filtros aplicáveis | todos (segmento, categoria, distribuidor, supervisor); seletor de período (RN-59) |
| Exceções | **Estimativa** abaixo do canal Mtrix: o valor verdadeiro do par está entre max fᵢ e Σ fᵢ, e o erro não é mensurável. Exato quando o par (ou a categoria no par) tem uma linha |
| Nulos | Sem positivados no recorte = "—"; arquivo sem linha de total ou sem frequência no total = aborta |
| Zeros | Não ocorre (frequência ≥ 1 medida em 100% das linhas) |
| Duplicidades | RN-10 |
| Parametrização | `regras.frequencia.*`, `validacao.frequencia_*`; código: `dn/metrics.py` |
| Responsável | Douglas |
| Status | proposta (Etapa 2 de 13/09/2026) |
| Aprovação | — |
| Observações | Medido em 25 meses: α de 1,088 a 1,134; erro fora da amostra no canal de 1,01% em média e 2,14% no pior mês; M0 (mínimo) subestima o canal em 6,6% a 9,7%. Linha com kg > 0 pode conter NF de devolução (não mensurável) |

### RN-59 · Seletor de período das séries
| Campo | Conteúdo |
|---|---|
| Objetivo | Ver os meses anteriores aos 12 exibidos sem mudar o cálculo |
| Definição | Chip "Período" em todas as abas com eixo de meses: Últimos 12 meses (padrão, `painel.serie_meses_exibidos`) · Série completa · cada ano do calendário ativo (fiscal ou civil, RN-23/RN-24) |
| Fórmula | Nenhuma: o navegador filtra os pontos da série embutida; nada é recalculado |
| Base de origem | Séries `DN_*` já calculadas |
| Granularidade | mês |
| Filtros aplicáveis | combina com todos; o ano incompleto é rotulado ("4 de 12") |
| Exceções | Não se aplica a cards, Penetração, Matriz, Pontos de venda, Alavancas e Ano a ano |
| Parametrização | `painel.serie_meses_exibidos` (padrão), `painel.periodo.*` (rótulos) |
| Status | proposta (Etapa 2 de 13/09/2026) |
| Observações | Revisa RN-20 (hoje a série exibida é fixa). Custo medido: +346 KB com 24 meses |

**Revisões propostas em fichas existentes:** RN-20 (série exibida → seletor, com remissão à RN-59); RN-11 (a coluna `# PDVs Positivados` deixa de ser obrigatória; o aviso informativo só onde ela existir).

## 9. Perguntas para o Douglas (para fechar a Etapa 2)

1. **Regra:** MA (recomendada: estimativa calibrada que bate com a Mtrix no canal) ou M0 (mínimo garantido, sempre 6,6% a 9,7% abaixo)? Ou mostrar a MA com o M0 na memória de cálculo?
2. **Por PDV individual (aba Pontos de venda):** mostrar a frequência estimada de cada PDV, mostrar só a faixa (mínimo–máximo) ou não mostrar por PDV?
3. **Onde exibir** (marque): cards da Visão geral · tabelas de Clusters/Supervisores · tabela de Distribuidores · evolução (gráfico/série) · Evolução por categoria · categoria nas tabelas de Distribuidores.
4. **Tamanho do HTML** (série completa + frequência pode passar de 12 MB): (a) compactar as séries (omitir campos vazios e aspas dos números; recupera ~160 KB ou mais); (b) subir `html_max_mb` (para quanto?); (c) as duas.
5. **Acumulado do ano da frequência:** (a) não mostrar; (b) média ponderada = Σ atendimentos do período ÷ Σ positivados mês a mês; (c) atendimentos do período ÷ PDVs distintos do período.
6. **Validação α fora da faixa:** só aviso, ou aborta?
7. **Nome na tela:** "Frequência de compra", "Atendimentos por PDV" ou outro? A tela sempre traria a nota "estimativa calibrada no total Mtrix".
8. **Seletor:** confirma que ele não se aplica às abas da coluna da direita da §6?

**Paro aqui e aguardo o seu ok na Etapa 2.**

---

## Anexo · Arquivos de apoio (scratchpad `…\scratchpad\freq\` e `…\scratchpad\sb\`)

`s10_estimadores.py` → `out/est_por_mes.csv`, `out/est_por_distribuidor.csv`, `out/est_por_categoria.csv`, `out/est_fora_amostra.csv`, `out/est_resumo.json` ·
`s11_exatos.py` → `out/est_exatos.csv` · cópia do pipeline: `sb/run1.log` (24 meses, 12 exibidos), `sb/run2.log` (série completa), `sb/run1_12m.html`, `sb/d/painel/Scorecard_DN_2026-08.html`.
Diferenças da cópia em relação ao projeto (só para medir): caminhos das bases absolutos; `# PDVs Positivados` fora das obrigatórias;
leitura do gabarito tolerante à coluna ausente; set/24 em `arquivos_ignorados` (SBM ainda fora do de-para); publicação desviada para dentro da cópia; pastas de dados encurtadas (limite de 260 caracteres do Windows).

---

## 10. Decisões do Douglas sobre a Etapa 2 (13/09/2026)

| # | Tema | Decisão | Consequência para a Etapa 3 |
|---|---|---|---|
| 1 | Regra | **MA (união proporcional) no painel e M0 (mínimo garantido) na memória de cálculo** | Ficha da memória com "estimativa" e "mínimo garantido: X" |
| 2 | Por PDV (Pontos de venda) | **Só o mínimo garantido** (M0, inteiro), coluna "NFs mín. no mês" | MEDIDO: +62.464 bytes no blob de PDVs (129.359 pares; 72.279 com valor em ago/26) |
| 3 | Onde exibir | **Cards da Visão geral · tabelas de Clusters/Supervisores · tabela de Distribuidores (total e por categoria) · chave nova "Frequência" no gráfico de evolução.** Séries levam **só o valor**; LY e variações nos cards e tabelas. Evolução por categoria e Penetração/Matriz ficam fora | — |
| 4 | Tamanho do HTML | **Compactar as séries** (omitir campos vazios e aspas dos números; MEDIDO ~161 KB de campos vazios) **e subir o limite** para um valor confortável: `validacao.html_max_mb: 15` | Validação "série compacta = série do JSON" |
| 5 | Acumulado do ano | **Σ atendimentos ÷ Σ positivados** dos meses do período (civil e fiscal); nulo com mês faltando (RN-25) | — |
| 6 | Calibração | **Não calibra** (sem linha de total, freq do total vazia, T × PDVs não inteiro, nenhum α fecha) → **aborta**; **α fora de `validacao.frequencia_alfa_min/max`** (início 1,05–1,20) → **aviso**; **mês em andamento** → sem checagem de faixa | — |
| 7 | Nome na tela | **"Frequência de compra"** (card/título) · "Freq. compra" (coluna) · "Frequência" (chave do gráfico) · "NFs mín. no mês" (lista de PDVs); nota "estimativa calibrada no total Mtrix" | — |
| 8 | Seletor de período | Só nas abas com série mensal; nas demais o chip fica **inativo com dica**. **No RTM**, age na série **só na visão "histórico completo"** | RN-59 |
| 8a | **Revisão da D18** (filtro Supervisor no RTM) | **Aprovada:** o filtro age no RTM pelo **supervisor do destino** (cards, série, destinos, clientes, drills); indicadores e série por supervisor calculados no pipeline; não mensuráveis fora do recorte, com nota; supervisor sem cliente com aviso | MEDIDO: 0 destinos com filiais de supervisores diferentes; Σ supervisores = canal (1.589 · 213 · 93 · 1.283); 54 dos 93 "só de outro" atendidos por distribuidor de outro supervisor. Validações: Σ supervisores = canal; 1 supervisor por destino (aborta). Revisa RN-44 e RN-52 |
| 8b | **Chave do destino RTM** | **Opção a:** casar por `Cód. Cliente [Distribuidor]` → filial no de-para → destino = nome reduzido da filial no de-para; "do destino" continua sendo qualquer filial (RN-52) | MEDIDO: resultado idêntico ao atual (1.589 mensuráveis; 213 do destino em ago/26); 173 não mensuráveis continuam (NOVO RIBEIRÃO PRETO 91 e NOVO SJRP 75 sem código; DIBS 6 e NOVA ENERGIA 1 com código fora do de-para). Fecha a pendência 5 (coluna `CNPJ Distribuidor Destino` deixa de ser necessária). **Item separado na Etapa 3**, com revisão da RN-52 e aviso "código × nome da planilha" |

### Rascunhos de revisão de fichas (entram em `docs/regras_negocio.md` na Etapa 3, após o ok)

- **RN-58 (nova) · Frequência de compra:** como na §8, com: memória de cálculo mostra também o mínimo garantido (M0); lista de PDVs mostra só "NFs mín. no mês" (M0); acumulado = Σ atendimentos ÷ Σ positivados; calibração ausente aborta, α fora da faixa avisa.
- **RN-59 (nova) · Seletor de período:** como na §8, e no RTM age só na visão "histórico completo".
- **RN-44 (revisão) · Filtro por Supervisor:** passa a agir no RTM pelo supervisor do destino (D18 revista em 13/09/2026).
- **RN-52 (revisão) · Aderência ao direcionamento:** destino pela chave `Cód. Cliente [Distribuidor]` → filial → nome reduzido do de-para; o casamento por nome da planilha passa a ser só conferência (aviso); recorte por supervisor do destino.
- **RN-20 (revisão):** série exibida padrão de 12 meses com seletor (RN-59). **RN-11 (revisão):** `# PDVs Positivados` deixa de ser obrigatória.
- **Config:** `fontes.sellout.colunas_obrigatorias` (− `# PDVs Positivados`, + `# Frequência de compra`), `regras.frequencia.*`, `validacao.frequencia_*`, `validacao.html_max_mb: 15`, `painel.periodo.*`.

### Pré-requisito do Douglas antes da Etapa 3 rodar

- SBM COMÉRCIO (01026770000176) no `Distribuidores_DePara.xlsx` (R5). Sem ela, a execução aborta (set/24).
