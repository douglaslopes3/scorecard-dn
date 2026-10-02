# Dicionário de regras de negócio · Scorecard DN

**Fonte única** das regras do painel. Criado na fase F0 da evolução (10/09/2026) a partir das regras vigentes
(`config/config.yaml`, `README.md`, docs de rodada) e das decisões da Etapa 1 (`docs/evolucao_etapa1_auditoria.md`, Anexo A).
Última revisão: **16/09/2026 (Etapa 2: RN-60 a RN-64)**.

**Regra de manutenção.** Toda alteração de regra passa por ficha nova ou revisão de ficha, com data e aprovação do Douglas,
**antes** de qualquer mudança em código, config ou template. Ids `RN-nn` são estáveis e nunca renumerados; regra revogada
permanece no arquivo com status "revogada em dd/mm/aaaa" e o motivo. Regra nova recebe o próximo número livre.

**Status.** `vigente` = implementada e em uso no painel publicado · `aprovada` = decidida na Etapa 1, ainda não implementada
(a coluna "Fase" diz onde entra) · `declarada` = registro de ausência de dado ou de escopo (não há cálculo) · `descontinuada` = saiu do painel e do código · `desligada` = código mantido, chave `ativo: false` no config.

**Campos de cada ficha.** Objetivo · Definição · Fórmula · Base de origem · Campos usados · Granularidade · Filtros aplicáveis ·
Exceções · Nulos · Zeros · Duplicidades · Parametrização (chave do config, ou "código: arquivo/função") · Responsável · Status ·
Aprovação (data e origem) · Observações.

Abreviações: **Mtrix** = `bases/Sell Out - MTRIX/ScoreCard_Mtrix_MM.AAAA.xlsx` → `FATO_SELLOUT` · **de-para** =
`bases compartilhadas/Distribuidores_DePara.xlsx` (cadastro único de distribuidores, comum ao Gerencial desde 02/10/2026) · **Hierarquia** = `bases compartilhadas/Hierarquia_AAAAMMDD.xlsx` (a de data mais recente; até 01/10/2026, `Hierarquia_Consolidada.xlsx`) · **Produtos** e **RTM** = `bases compartilhadas/Produtos.xlsx` e `RTM_DePara_Transicao.xlsx` (comuns ao Gerencial desde 02/10/2026) · **A.x** = ficha do Anexo A do doc da Etapa 1 ·
**D.n / Q.n** = decisão/pergunta da Etapa 1.

---

## Bloco 1 · Medidas e populações

### RN-01 · Positivado
| Campo | Conteúdo |
|---|---|
| Objetivo | Definir o que conta como compra no mês |
| Definição | Linha da Mtrix com peso positivo no mês; PDV positivado = tem ≥ 1 linha assim no mês, no nível considerado |
| Fórmula | `PESO_KG > 0` |
| Base de origem | Mtrix |
| Campos usados | `# Sell-Out (Quilos)` → `PESO_KG`, `Cód. PDV`, `CNPJ do AD.`, `Ano/Mês` |
| Granularidade | linha (mês × distribuidor × PDV × SKU); agregada por PDV distinto no nível |
| Filtros aplicáveis | todos (a positivação é avaliada dentro do recorte) |
| Exceções | linha com R$ > 0 e kg ≤ 0 **não** positiva (3 na série) |
| Nulos | kg nulo não ocorre (leitor aborta em coluna obrigatória vazia) |
| Zeros | kg = 0 não positiva |
| Duplicidades | grão único por validação (0 duplicados em 6,42 M linhas; aborta se houver) |
| Parametrização | `regras.positivado` (texto documental); código: `dn/metrics.py` |
| Responsável | Douglas |
| Status | vigente |
| Aprovação | 08/09/2026 · rodada 2 (`docs/mapeamento.md`) |
| Observações | Mesma régua para t e R$ (RN-43): o seletor de métrica não muda quem é positivado |

### RN-02 · Base ativa
| Campo | Conteúdo |
|---|---|
| Objetivo | Denominador da DN: PDVs que compram com alguma regularidade |
| Definição | PDVs positivados em pelo menos um dos últimos **6** meses (janela móvel fechada no mês de referência), no nível. Era 5 até 14/09/2026 (A8) |
| Fórmula | `base_ativa(nível, m) = #{PDV : positivado em algum mês de [m−5, m]}` |
| Base de origem | Mtrix |
| Campos usados | `PESO_KG`, `COD_PDV`, `ANO_MES`, `CNPJ_DISTRIBUIDOR` |
| Granularidade | PDV distinto por nível e mês; par distribuidor × PDV em `DN_PDV_BASE_ATIVA` |
| Filtros aplicáveis | todos |
| Exceções | nula enquanto a janela não está completa (set/24 a jan/25 na série atual, com 6 meses) |
| Nulos | "—" na tela; nada acumula sobre ela nesses meses |
| Zeros | não ocorre |
| Duplicidades | PDV multi-distribuidor conforme RN-10 |
| Parametrização | `regras.janela_base_ativa_meses: 6` (e `regras.potencial.janela_fator_meses: 6`, que acompanha) |
| Responsável | Douglas |
| Status | vigente · **Refino E4a (13/09/2026, gerado sem publicar)**: a base ativa dos PDVs é calculada para o mês parcial e para o mês fechado; a lista embutida é uma só, com as colunas de cada mês (validação `pdv · lista combinada = listas de cada mes`) · **Refino E4b (13/09/2026, gerado sem publicar)**: set/24 a dez/24 ficam sem base ativa (janela de 5 meses incompleta): cards de base ativa, DN e sem compra em "—" · **Estabilização A8 (14/09/2026, gerado sem publicar)**: janela **5 → 6 meses** para tudo (base ativa, base elegível, ativação, recorrência, máscara e fator observado), decisão do Douglas; primeiro mês com DN passa de jan/25 para fev/25; ago/26: base ativa 124.800 → **129.595**, DN 57,3% → **55,2%**, sem compra 53.322 → 58.117; set/26 parcial: 120.742 → 125.955, DN 13,0% → 12,4% |
| Aprovação | 08/09/2026 · rodada 2; reconfirmada 10/09/2026 · A.6 (D28): 5 meses para tudo, inclusive Penetração; **14/09/2026 · A8 da estabilização: 6 meses para tudo (D28 mantém o princípio de uma janela só)** |
| Observações | Medido em ago/26 (bases de 13/09): 5 m → 124.800 e DN 57,3%; 6 m → 129.595 e DN 55,2%, só por definição. É também a **base elegível** (RN-41) |

### RN-03 · Cobertura (PDVs compradores)
| Campo | Conteúdo |
|---|---|
| Objetivo | Numerador da DN |
| Definição | PDVs distintos positivados no mês, no nível |
| Fórmula | `cobertura_pdv(nível, m) = #{PDV : positivado em m}` |
| Base de origem | Mtrix |
| Campos usados | `PESO_KG`, `COD_PDV`, `ANO_MES` |
| Granularidade | PDV distinto por nível e mês |
| Filtros aplicáveis | todos |
| Exceções | — |
| Nulos | — |
| Zeros | nível sem positivado = 0 |
| Duplicidades | RN-10 |
| Parametrização | código: `dn/metrics.py::serie_nivel` |
| Responsável | Douglas |
| Status | vigente |
| Aprovação | 08/09/2026 · rodada 1 |
| Observações | Na tela: "Cobertura · PDVs compradores" |

### RN-04 · % de cobertura (Distribuição Numérica)
| Campo | Conteúdo |
|---|---|
| Objetivo | Indicador principal do painel |
| Definição | Proporção da base ativa que comprou no mês |
| Fórmula | `pct_cobertura = cobertura_pdv ÷ base_ativa × 100` |
| Base de origem | derivada (RN-02, RN-03) |
| Campos usados | — |
| Granularidade | nível × mês |
| Filtros aplicáveis | todos |
| Exceções | "—" quando base ativa nula |
| Nulos | idem |
| Zeros | base ativa 0 não ocorre |
| Duplicidades | RN-10 |
| Parametrização | código: `dn/metrics.py::serie_nivel` |
| Responsável | Douglas |
| Status | vigente |
| Aprovação | 08/09/2026 · rodada 1 |
| Observações | Variações em p.p. (RN-21) |

### RN-05 · Volume (t)
| Campo | Conteúdo |
|---|---|
| Objetivo | Medida física do sell-through |
| Definição | Soma do peso, com sinal, de todas as linhas do recorte, em toneladas |
| Fórmula | `volume_t = Σ PESO_KG ÷ 1000` |
| Base de origem | Mtrix |
| Campos usados | `# Sell-Out (Quilos)` |
| Granularidade | linha; agregada por nível e mês |
| Filtros aplicáveis | todos |
| Exceções | linhas negativas (7 na série, −5,3 kg) entram com sinal |
| Nulos | não ocorre |
| Zeros | entram (não afetam) |
| Duplicidades | — |
| Parametrização | código: `dn/metrics.py::serie_nivel` |
| Responsável | Douglas |
| Status | vigente |
| Aprovação | 08/09/2026 · Fase 2 |
| Observações | Reconciliado contra a linha de total de cada arquivo (aborta se não fechar) |

### RN-06 · Valor do sell-through (R$)
| Campo | Conteúdo |
|---|---|
| Objetivo | Segunda métrica do painel, em reais |
| Definição | Venda do distribuidor ao PDV em R$, **conforme reportado pelo distribuidor à Mtrix**; soma com sinal. **Não é faturamento Dori**; bruto × líquido não determinável (a Mtrix não discrimina impostos, descontos, devoluções) |
| Fórmula | `receita_rs = Σ RECEITA` nas mesmas linhas do volume |
| Base de origem | Mtrix |
| Campos usados | `# Sell-Out (R$)` → `RECEITA` |
| Granularidade | linha; agregada em todos os níveis (já calculada em todos os cubos `DN_*`) |
| Filtros aplicáveis | todos |
| Exceções | 64 linhas negativas (R$ −2,3 mil) entram com sinal; 1.402 linhas com kg > 0 e R$ = 0 contam como compradoras com valor zero, e o recorte avisa quando houver |
| Nulos | não ocorre |
| Zeros | entram |
| Duplicidades | — |
| Parametrização | `regras.metrica.valor_nome`, `valor_definicao`, `sinais`; `painel.rotulos.metrica_*`; cálculo em `dn/metrics.py`; blob de PDVs (`rs_mes`, `rs_ultimo`, `rs_janela`) e do RTM (`rs_certo`, `rs_outro`) em `dn/painel.py` |
| Responsável | Douglas |
| Status | **vigente** (F1, 10/09/2026) |
| Aprovação | 10/09/2026 · A.4 (D1, D30) |
| Observações | Nome na tela "Valor do sell-through (R$)"; colunas "Valor (R$)" e "R$ / PDV". Calculado desde 09/09; nunca exibido (o seletor de 09/09 foi removido por decisão do Douglas, reconhecida como equivocada — Q1) |

### RN-07 · kg / PDV e R$ / PDV
| Campo | Conteúdo |
|---|---|
| Objetivo | Intensidade de compra por loja compradora |
| Definição | Medida do mês dividida pelos PDVs compradores do mês |
| Fórmula | `kg_pdv = volume_kg ÷ cobertura_pdv` · `rs_pdv = receita_rs ÷ cobertura_pdv` |
| Base de origem | derivada (RN-03, RN-05, RN-06) |
| Campos usados | — |
| Granularidade | nível × mês |
| Filtros aplicáveis | todos |
| Exceções | cobertura 0 → nulo |
| Nulos | "—" |
| Zeros | — |
| Duplicidades | RN-10 |
| Parametrização | código: `dn/metrics.py::serie_nivel` |
| Responsável | Douglas |
| Status | vigente (kg e R$ desde a F1, 10/09/2026) |
| Aprovação | 08/09/2026 · Fase 2; R$ 09/09/2026 §9.2 |
| Observações | — |

### RN-08 · Sem compra no mês
| Campo | Conteúdo |
|---|---|
| Objetivo | Oportunidade imediata: quem está na base ativa e não comprou |
| Definição | Base ativa menos cobertura |
| Fórmula | `sem_compra_mes = base_ativa − cobertura_pdv` |
| Base de origem | derivada |
| Campos usados | — |
| Granularidade | nível × mês; lista nominal por par em `DN_PDV_BASE_ATIVA` |
| Filtros aplicáveis | todos; na tabela de PDVs, filtro próprio "Situação" |
| Exceções | "—" com base ativa nula |
| Nulos | idem |
| Zeros | — |
| Duplicidades | RN-10 |
| Parametrização | código: `dn/painel.py` |
| Responsável | Douglas |
| Status | vigente |
| Aprovação | 08/09/2026 · Fase 3 |
| Observações | — |

### RN-09 · Unidades fora do painel
| Campo | Conteúdo |
|---|---|
| Objetivo | Registrar que a terceira medida da Mtrix não é exibida |
| Definição | `# Sell-Out (Und)` é carregada, reconciliada e mantida na fato; não entra em cubo nem em tela |
| Fórmula | — |
| Base de origem | Mtrix |
| Campos usados | `# Sell-Out (Und)` → `UNIDADES` |
| Granularidade | linha |
| Filtros aplicáveis | — |
| Exceções | — |
| Nulos | — |
| Zeros | — |
| Duplicidades | — |
| Parametrização | `regras.metrica.unidades_no_painel: false` |
| Responsável | Douglas |
| Status | **vigente** (F1: seletor tem só t e R$) |
| Aprovação | 10/09/2026 · A.5 (D3) |
| Observações | Motivo: unidade de venda do SKU (caixa, display, pacote) mistura embalagens entre categorias. Pode virar terceira posição do seletor em rodada futura |

### RN-10 · PDV atendido por mais de um distribuidor
| Campo | Conteúdo |
|---|---|
| Objetivo | Evitar dupla contagem sem perder a leitura por distribuidor |
| Definição | O PDV conta **uma vez em cada nível onde aparece**: uma vez por distribuidor, uma vez por supervisor, uma vez por cluster, uma vez no canal e no segmento. A soma dos níveis é maior que o total e isso é declarado na tela |
| Fórmula | contagem distinta de `COD_PDV` dentro de cada chave de nível |
| Base de origem | Mtrix |
| Campos usados | `COD_PDV`, `CNPJ_DISTRIBUIDOR` |
| Granularidade | PDV × nível |
| Filtros aplicáveis | todos |
| Exceções | nenhuma atribuição a um único distribuidor ou supervisor (alternativa rejeitada em A.9) |
| Nulos | — |
| Zeros | — |
| Duplicidades | é a própria regra |
| Parametrização | `regras.pdv_multi_distribuidor` (texto); código: `dn/metrics.py` |
| Responsável | Douglas |
| Status | vigente; **reconfirmada** para a tabela por supervisor |
| Aprovação | 08/09/2026 · rodada 5; 10/09/2026 · A.9 (D35) |
| Observações | ago/26: 796 PDVs em > 1 distribuidor, 146 em > 1 supervisor; linha TOTAL das tabelas por nível = canal, com nota "N PDVs atendidos por mais de um território" |

### RN-11 · Chave do PDV e "cliente"
| Campo | Conteúdo |
|---|---|
| Objetivo | Identificar a loja de forma estável |
| Definição | `Cód. PDV` da Mtrix: CNPJ de 14 dígitos, ou id **LGPD** (negativo, anonimizado pela Mtrix, estável entre meses), ou OUTRO (consumidor final, código interno). Todos entram como PDV. No painel, **"cliente" = PDV** |
| Fórmula | classificação por formato (`dn/extract/sellout.py`) |
| Base de origem | Mtrix |
| Campos usados | `Cód. PDV`, `Razão Social PDV` |
| Granularidade | PDV |
| Filtros aplicáveis | — |
| Exceções | OUTRO acima de `validacao.pdv_outro_max_pct` rejeita o arquivo |
| Nulos | aborta |
| Zeros | — |
| Duplicidades | atributos (razão social, segmento) do mês mais recente vencem (`DIM_PDV`) |
| Parametrização | `regras.pdv_chave_lgpd_prefixo`, `validacao.pdv_outro_max_pct` |
| Responsável | Douglas |
| Status | vigente; "cliente = PDV" **aprovada** |
| Aprovação | 08/09/2026 · rodadas 5/6; 10/09/2026 · A.6 |
| Observações | 144.560 CNPJ · 18.575 LGPD · 77 OUTRO na série. **Revisão 13/09/2026:** a coluna `# PDVs Positivados` deixou de ser obrigatória (saiu das extrações de set/25 em diante); o aviso informativo "PDVs distintos x total da Mtrix" roda só nos arquivos que ainda a trazem (Etapa 1 da frequência, decisão 4) |

### RN-12 · Conceitos de cliente (ativo, inativo, novo, reativado)
| Campo | Conteúdo |
|---|---|
| Objetivo | Vocabulário único da aba de Penetração |
| Definição | **Ativo** = na base ativa (RN-02). **Positivado** = RN-01 no mês. **Inativo** = comprou em algum mês da série e está fora da base ativa. **Novo** = primeiro mês na Mtrix dentro da janela de 6 meses (`regras.janela_base_ativa_meses`). **Reativado** = positivado no mês, sem compra nos 6 meses anteriores e não novo. **Cadastrado, bloqueado, encerrado, mudança de carteira: não existem nas bases** e não são usados |
| Fórmula | por PDV: `PRIMEIRO_MES`, meses positivados na janela, último mês com compra |
| Base de origem | Mtrix; `DIM_PDV.PRIMEIRO_MES`; `DN_PDV_BASE_ATIVA` |
| Campos usados | `COD_PDV`, `ANO_MES`, `PESO_KG` |
| Granularidade | PDV × mês |
| Filtros aplicáveis | todos |
| Exceções | PDV que muda de distribuidor continua o mesmo PDV (o par muda) |
| Nulos | — |
| Zeros | — |
| Duplicidades | RN-10 |
| Parametrização | janela = `regras.janela_base_ativa_meses` |
| Responsável | Douglas |
| Status | **aprovada** · Fase F6/F7 · **15/09/2026**: texto da janela atualizado de 5 para 6 meses (acompanha a A8 de 14/09/2026, RN-02); o cálculo já usava 6 (`dn/metrics.py`, flag `novo` da máscara) |
| Aprovação | 10/09/2026 · A.6 (D24); 15/09/2026 · correção de texto aprovada pelo Douglas |
| Observações | Declarar na aba Definições o que não existe |

## Bloco 2 · Dimensões e hierarquia

### RN-13 · Distribuidor
| Campo | Conteúdo |
|---|---|
| Objetivo | Definir o nível "distribuidor" |
| Definição | Distribuidor = **CNPJ de filial** (`CNPJ do AD.`). Entra no painel só quem tem linha na Hierarquia (via `Cód. Interno Cliente` do de-para). O campo Status do de-para **não** exclui ninguém |
| Fórmula | `NO_PAINEL = NA_HIERARQUIA` |
| Base de origem | Mtrix, de-para, Hierarquia |
| Campos usados | `CNPJ DISTRIBUIDOR`, `Cód. Interno Cliente`, `CÓDIGO CLIENTE` |
| Granularidade | CNPJ |
| Filtros aplicáveis | Distribuidor, Supervisor, Segmento |
| Exceções | distribuidor da Mtrix sem linha no de-para aborta a execução |
| Nulos | — |
| Zeros | — |
| Duplicidades | CNPJ único no de-para (aborta se repetir) |
| Parametrização | `regras.distribuidor_excluir_sem_hierarquia: true` |
| Responsável | Douglas |
| Status | vigente |
| Aprovação | 08/09/2026 · rodadas 2 e 7 |
| Observações | 80 no de-para; 9 fora (5,1% do kg); 71 no painel em ago/26 |

### RN-14 · Segmento do distribuidor (Base atual × Novos × Sem venda)
| Campo | Conteúdo |
|---|---|
| Objetivo | Separar distribuidores maduros de recém-chegados |
| Definição | **Sem venda** (02/10/2026) = nenhum kg > 0 nos últimos 3 meses até o mês de referência; vale antes da maturidade e o histórico dele continua no canal (Todos), para medir a perda e se outro distribuidor a absorve. Base atual = mais de 6 meses de histórico (e não Sem venda); Novos = até 6. Histórico pela `Data de Cadastro` do de-para; sem ela, pelo 1º mês com sell-out na Mtrix, censurado pelo início da série (exibido com "≥") |
| Fórmula | `meses_historico = meses entre a data de cadastro (ou 1º mês) e o mês de referência` |
| Base de origem | de-para; Mtrix |
| Campos usados | `Data de Cadastro`, `PRIMEIRO_MES` |
| Granularidade | distribuidor × mês de referência |
| Filtros aplicáveis | Segmento (global) |
| Exceções | 15 dos 80 sem data; 6 caem no censurado |
| Nulos | censura, nunca inferência |
| Zeros | — |
| Duplicidades | — |
| Parametrização | `regras.segmento_novos_meses: 6`; `regras.segmento_sem_venda_meses: 3`; código `dn/metrics.py::segmento_ids`; `fontes.distribuidores.colunas_opcionais: [Data de Cadastro]` |
| Responsável | Douglas |
| Status | vigente |
| Aprovação | 08/09/2026 · rodada 1; 09/09/2026 · C3; 02/10/2026 · Sem venda (Douglas, critério A: vendas, 3 meses) |
| Observações | 32 dos 64 com data têm 10/12/2013 (carga do ERP). Em set/26: 9 Sem venda (AVANT, CBX, CHUA - Serra ES, IREZ E SIQUEIRA, KRUPER, MDB, MMD, NORTESUL, SBM), todos entre os 10 que ganharam hierarquia em 02/10/2026; 34% dos PDVs deles compraram de outro distribuidor do painel em set/26 |

### RN-15 · Supervisor
| Campo | Conteúdo |
|---|---|
| Objetivo | Nível de território |
| Definição | Supervisor = rótulo "código - nome" do N3 da Hierarquia (desde 02/10/2026; antes "código - função - nome"), casado pelo `Cód. Interno Cliente` do distribuidor com o `Cód. cliente` da Hierarquia. O nome é limpo quando termina com "(código)" igual ao código da linha: sai o "(código)" e o "_" inicial (regra única dos três painéis, 02/10/2026); fora disso entra como veio. Mesmo formato nos níveis N1 e N2 e nos painéis Gerencial e ROTA. **Atributo do distribuidor**; o PDV herda o supervisor de quem o atendeu. A Hierarquia é um retrato atual, aplicado a toda a série, com aviso fixo na tela |
| Fórmula | junção de-para → Hierarquia (1ª linha por código vence) |
| Base de origem | de-para; Hierarquia |
| Campos usados | `Cód. Executivo Vendas (N3)`, `Nome Executivo Vendas (N3)`, `Cód. cliente` (aba `Hierarquia Vendas`) |
| Granularidade | distribuidor |
| Filtros aplicáveis | Supervisor (RN-44), Segmento |
| Exceções | o "Supervisor" textual do de-para não é usado (difere em 71/71) |
| Nulos | não ocorre: 81 de 81 distribuidores com linha na Hierarquia_20261001 (eram 71 na Consolidada) |
| Zeros | — |
| Duplicidades | — |
| Parametrização | `regras.hierarquia.aviso` → JSON `hierarquia.aviso` (com a data da última ingestão), exibido ao lado do select de Supervisor; código: `dn/extract/cadastros.py::arquivo_hierarquia` (arquivo vigente) e `_ler_hierarquia` (rótulo) |
| Responsável | Douglas |
| Status | vigente; aviso **vigente** (F4, 10/09/2026) |
| Aprovação | 08/09/2026 · rodada 6; 10/09/2026 · A.13; 02/10/2026 · troca de base e rótulo "código - nome" (Douglas) |
| Observações | 14 supervisores, 4 rotulados "[VAGO]" em 10/09. Em 02/10/2026: 14 supervisores, 2 "VAGO" (1210 e 1240); 1250 e 1320 com titular novo |

### RN-16 · Retrato mensal da hierarquia
| Campo | Conteúdo |
|---|---|
| Objetivo | Construir histórico de supervisor daqui em diante |
| Definição | A cada ingestão o pipeline grava uma cópia datada de `DIM_DISTRIBUIDOR` |
| Fórmula | `data/dn/curated/historico/DIM_DISTRIBUIDOR_<AAAA-MM-DD>.parquet` |
| Base de origem | curated |
| Campos usados | todos de `DIM_DISTRIBUIDOR` |
| Granularidade | distribuidor × data da ingestão |
| Filtros aplicáveis | — |
| Exceções | não altera nada no painel |
| Nulos | — |
| Zeros | — |
| Duplicidades | uma cópia por data (sobrescreve no mesmo dia) |
| Parametrização | `regras.hierarquia.arquivar_retrato_mensal: true`; código: `dn/pipeline.py::ingerir` grava `curated/historico/DIM_DISTRIBUIDOR_<AAAA-MM-DD>.parquet` a cada ingestão (Q-d) |
| Responsável | Douglas |
| Status | **vigente** (F4, 10/09/2026) |
| Aprovação | 10/09/2026 · A.13 (D20) |
| Observações | Lacuna L9 |

### RN-17 · Categoria
| Campo | Conteúdo |
|---|---|
| Objetivo | Nível "categoria" |
| Definição | Categoria do SKU no cadastro de produtos; SKU sem cadastro entra como "SEM CADASTRO" (nunca inferido) |
| Fórmula | junção `SKU` → `Produtos.xlsx.Categoria` |
| Base de origem | `Produtos.xlsx` |
| Campos usados | `Código Produto`, `Categoria` |
| Granularidade | SKU |
| Filtros aplicáveis | Categoria (global) |
| Exceções | — |
| Nulos | "SEM CADASTRO" com aviso |
| Zeros | — |
| Duplicidades | 1ª linha vence |
| Parametrização | `dimensoes.rotulo_sem_cadastro` |
| Responsável | Douglas |
| Status | vigente |
| Aprovação | 08/09/2026 · rodada 2 |
| Observações | 10 categorias; 288 SKUs movimentados, 0 sem cadastro |

### RN-18 · Cluster de loja
| Campo | Conteúdo |
|---|---|
| Objetivo | Tipo de loja |
| Definição | De-para do `Segmento do PDV` da Mtrix para o cluster do painel; segmento sem linha mantém o próprio nome, com aviso |
| Fórmula | junção `SEGMENTO_MTRIX` → `CLUSTER` |
| Base de origem | `Clusters_DePara.xlsx` (opcional) |
| Campos usados | `SEGMENTO MTRIX`, `CLUSTER PAINEL` |
| Granularidade | segmento (34 → 12) |
| Filtros aplicáveis | — (é linha da tabela de clusters) |
| Exceções | arquivo ausente → clusters = segmentos da Mtrix |
| Nulos | mantém o nome |
| Zeros | — |
| Duplicidades | 1ª linha vence |
| Parametrização | `fontes.clusters` |
| Responsável | Douglas |
| Status | vigente |
| Aprovação | 09/09/2026 · C5 |
| Observações | O de-para de **PDVs ponderados** (`DE-PARA_Ponderada_Clusters.xlsx`) é outra coisa e está fora do config (adiado) |

### RN-19 · Categorias foco
| Campo | Conteúdo |
|---|---|
| Objetivo | Concentrar cards e resumos da Penetração no plano comercial |
| Definição | Lista fixa **Amendoim, Gomas, Gelatina, Regaliz**. "Foco" muda só destaque (estrela), ordenação, cards e resumos calculados sobre as foco; as outras seis aparecem abaixo com o **mesmo cálculo**; total das dez exibido abaixo do total das foco. Nenhuma régua, benchmark ou potencial diferente |
| Fórmula | — |
| Base de origem | config (escolha comercial; critério não está nas bases) |
| Campos usados | `DIM_PRODUTO.CATEGORIA` (ids) |
| Granularidade | categoria |
| Filtros aplicáveis | todos |
| Exceções | — |
| Nulos | — |
| Zeros | — |
| Duplicidades | — |
| Parametrização | `regras.penetracao.categorias_foco`; no painel, `graficos.categorias_foco` (ids) — desde a F3 as foco aparecem com ★ e ligadas por padrão na evolução por categoria |
| Responsável | Douglas |
| Status | **vigente** (F6, 11/09/2026): cards, linha "todas as 10" e ordenação ★ primeiro na aba Penetração; estrela e seleção padrão desde a F3; resumos ficam para a F9 |
| Aprovação | 10/09/2026 · A.8 (D33) |
| Observações | ago/26: 76% do volume e 77% do valor. Alterar a lista muda o painel na execução seguinte; registrar data e responsável aqui |

## Bloco 3 · Tempo e comparativos

### RN-20 · Série calculada e série exibida
| Campo | Conteúdo |
|---|---|
| Objetivo | Separar o que se calcula do que se mostra |
| Definição | Cálculo, cards, base ativa e LY usam **todos** os meses da Mtrix; gráficos, tabelas das séries e evolução do RTM exibem os últimos **12** |
| Fórmula | corte na renderização (`dn/painel.py::_cortar`) |
| Base de origem | Mtrix |
| Campos usados | `ANO_MES` |
| Granularidade | mês |
| Filtros aplicáveis | — |
| Exceções | `null` = série inteira |
| Nulos | — |
| Zeros | — |
| Duplicidades | mesmo mês em dois arquivos aborta |
| Parametrização | `painel.serie_meses_exibidos: 12` |
| Responsável | Douglas |
| Status | vigente; **revista em 13/09/2026**: com `painel.periodo.ativo`, a série inteira vai embutida e os 12 meses passam a ser a janela padrão do seletor "Período" (RN-59) |
| Aprovação | 10/09/2026 · rodada 10/09 §1; 13/09/2026 · Etapa 1 da frequência (decisão 6) e Etapa 2 (decisão 8) |
| Observações | Com mês de referência ago/26, os 12 exibidos coincidem com FY2026. Desde 13/09/2026 a série calculada vai de set/24 a set/26 (25 bases reextraídas) |

### RN-21 · Comparativos (mês anterior, L3M, LY)
| Campo | Conteúdo |
|---|---|
| Objetivo | Leitura de variação sem meta |
| Definição | vs mês anterior; vs média dos 3 meses anteriores (só quando os 3 existem); vs mesmo mês do ano anterior por **junção** em `ANO_MES_LY` (nunca por deslocamento de posição). Contagens e medidas em %; % de cobertura em p.p. Ausência = "—" |
| Fórmula | `var = (v ÷ ref − 1) × 100`; `var_pp = v − ref` |
| Base de origem | `DN_*_MES`, `DIM_CALENDARIO` |
| Campos usados | `ANO_MES_LY` |
| Granularidade | nível × mês |
| Filtros aplicáveis | todos |
| Exceções | mês sem par = "—" (RN-22) |
| Nulos | "—" |
| Zeros | referência 0 → "—" |
| Duplicidades | — |
| Parametrização | código: `dn/metrics.py::comparativos`; desde a F2 os Δ de cada ponto da série vão ao JSON (`*_var_*` por mês) e o gráfico só exibe — `dnVar`/`dnMean` removidos (RK13 fechado) |
| Responsável | Douglas |
| Status | vigente · **Refino E3 (13/09/2026, gerado sem publicar)**: as diferenças absolutas vs mês anterior (PDVs positivados, t, R$) saem do pipeline por supervisor, distribuidor e suas linhas por categoria (mês − mês anterior no cubo da linha; sem linha num dos meses = nulo) e alimentam o bloco "O que aconteceu no mês" da Visão Geral (5 maiores quedas e altas, `painel.mes_ranking.n`); validação `mes · diferencas vs mes anterior = cubos` · **Refino E5 (13/09/2026, gerado sem publicar)**: nos modos Acumulado e Ano, "O que aconteceu no período" ordena as diferenças absolutas vs o mesmo período do ano anterior (PDVs distintos, t, R$), calculadas no pipeline |
| Aprovação | 08/09/2026 · rodada 1; Fase 2 |
| Observações | LY existe só para jul/26, ago/26, set/26 (parcial) até a Mtrix anterior a jul/25 entrar (pendência D5) |

### RN-22 · Mês sem Last Year
| Campo | Conteúdo |
|---|---|
| Objetivo | Não confundir ausência de dado com zero |
| Definição | Mês sem par no ano anterior = **ausência de dado**: sem ponto no gráfico (linha interrompida), Δ "—", legenda "sem LY na série (Mtrix a partir de jul/25)". Nunca zero, nunca preenchido |
| Fórmula | `ly = null` quando `ANO_MES_LY ∉ série` |
| Base de origem | `DIM_CALENDARIO` |
| Campos usados | `ANO_MES_LY` |
| Granularidade | mês |
| Filtros aplicáveis | todos |
| Exceções | — |
| Nulos | é a regra |
| Zeros | proibido como substituto |
| Duplicidades | — |
| Parametrização | `painel.textos.sem_ly` (legenda); template: `dnDraw` (linha LY só entre meses consecutivos com par; marcador só onde há par; Δ "—") |
| Responsável | Douglas |
| Status | **vigente** (F2, 10/09/2026) |
| Aprovação | 10/09/2026 · A.11 (D6) |
| Observações | — |

### RN-23 · Ano fiscal
| Campo | Conteúdo |
|---|---|
| Objetivo | Perspectiva temporal da empresa |
| Definição | Ano fiscal = **setembro a agosto**. `ANO_FISCAL` = ano em que termina (set/25 → 2026). Rótulo longo "Ano fiscal 2026 (set/25–ago/26)" em cabeçalhos e cards; curto "FY26" em colunas e eixos |
| Fórmula | `ANO_FISCAL = ANO + (MES ≥ 9)`; `MES_FISCAL = ((MES − 9) mod 12) + 1` |
| Base de origem | `DIM_CALENDARIO` (já calculada) |
| Campos usados | `ANO_FISCAL`, `MES_FISCAL`, `TRIMESTRE_FISCAL`, `SEMESTRE_FISCAL` |
| Granularidade | mês |
| Filtros aplicáveis | Calendário (RN-24) |
| Exceções | — |
| Nulos | — |
| Zeros | — |
| Duplicidades | — |
| Parametrização | `calendario.fiscal_mes_inicio: 9`, `fiscal_prefixo`, `rotulo_fiscal_longo`, `rotulo_fiscal_curto` (F0) e, desde a F5, `rotulo_civil_longo`, `rotulo_civil_curto`; JSON `calendario.{fiscal,civil}.{rotulo_longo, rotulo_curto, rotulo_anterior_curto, periodo, n_meses, faixas}` (`dn/painel.py`); `{inicio}`/`{fim}` do rótulo longo = período coberto pelo acumulado |
| Responsável | Douglas |
| Status | **vigente** (dimensão desde a rodada 2; rótulos na F5, 10/09/2026) |
| Aprovação | 08/09/2026 · rodada 2; 10/09/2026 · A.10 (D4) |
| Observações | FY2026 completo na série; FY2025 só jul–ago/25; FY2027 desde set/26 |

### RN-24 · Perspectiva padrão e toggle de calendário
| Campo | Conteúdo |
|---|---|
| Objetivo | Deixar o usuário alternar civil × fiscal |
| Definição | Padrão **fiscal**. O toggle muda **só** o eixo temporal (ordem dos meses, agrupamento, acumulado, "mesmo período LY"); não muda base ativa, segmentos, RTM nem o corte de migração. Estado em `localStorage` e URL (`cal=fiscal|civil`) |
| Fórmula | — |
| Base de origem | `DIM_CALENDARIO` |
| Campos usados | `ANO`, `MES`, `ANO_FISCAL`, `MES_FISCAL`, `ORDEM` |
| Granularidade | mês |
| Filtros aplicáveis | combina com todos |
| Exceções | RTM ignora o calendário |
| Nulos | — |
| Zeros | — |
| Duplicidades | — |
| Parametrização | `calendario.perspectiva_padrao: fiscal`; `painel.rotulos.cal_fiscal/cal_civil`; `calendario` em `painel.abas[].filtros` (visao, evolucao, clusters, distribuidores); template: chips `data-cal`, `dnCal()`/`dnCalAplicar()`, faixas de ano `dnFaixasSvg` (mapa `mes:ano` de `calendario.*.faixas`), estado `cal=` |
| Responsável | Douglas |
| Status | **vigente** (F5, 10/09/2026). Q-d: a série exibida continua sendo os últimos 12 meses nas duas perspectivas (RN-20); o toggle muda faixas do eixo, acumulado e "Ano a ano" · **Refino E1 (13/09/2026, gerado sem publicar; D14–D18 de `docs/refino_painel_proposta.md`)**: rótulo "Ano civil" passa a **"Ano Calendário"** (`painel.rotulos.cal_civil`); a tabela "Ano a ano" saiu, o toggle muda faixas e acumulado |
| Aprovação | 10/09/2026 · A.10 (D29) |
| Observações | — |

### RN-25 · Acumulados e comparativo anual
| Campo | Conteúdo |
|---|---|
| Objetivo | YTD civil e fiscal com regra explícita de dado incompleto |
| Definição | Acumulados calculados **no pipeline** e entregues no JSON (YTD civil, YTD fiscal e pares LY quando **todos** os meses do período existirem). Acumulado só é exibido com o período completo na série; mês em andamento leva a etiqueta existente; meses futuros não aparecem; comparativo anual sem par (FY × FY, ano × ano) **bloqueado com nota**; mês sem realizado dentro da série aborta a execução (nunca zera). Na mesma fase, os Δ% do gráfico passam a vir do JSON (fim do recálculo em JS) |
| Fórmula | `ytd(m) = Σ métrica dos meses do período até m`; validação: acumulado = soma da série |
| Base de origem | `DN_*_MES` |
| Campos usados | métricas mensais, `ANO_FISCAL`, `ANO` |
| Granularidade | nível × mês |
| Filtros aplicáveis | todos |
| Exceções | contagens de PDV não se acumulam (um PDV que compra em 3 meses não vira 3); só medidas (t, R$) acumulam; para PDVs o "acumulado" é a base ativa/cobertura do período, a definir na F5 |
| Nulos | "—" |
| Zeros | — |
| Duplicidades | — |
| Parametrização | `dn/metrics.py::acumulados` (colunas `ytd_{civil,fiscal}_{volume_kg, receita_rs, n_meses, volume_ly, receita_ly, volume_var_ly, receita_var_ly}` em todos os `DN_*_MES` e `DN_*_CAT_MES`) e `acum_ano` (`DN_ACUM_ANO`: PDVs distintos, kg, R$ por perspectiva × ano × nível); JSON `acum_*` por entidade e por ponto de série, `ano_a_ano`; `painel.rotulos.acum_ano/acum_col`, `painel.textos.sem_par_anual/ano_completo/ano_em_curso/ano_incompleto`; validações `serie · sem buraco de mes`, `acumulados · soma da serie`, `acumulados · periodo incompleto = nulo`, `acumulados · LY por juncao`, `acumulados · ano a ano = cubos + fato` |
| Responsável | Douglas |
| Status | **vigente** (F5, 10/09/2026). Exceção decidida (Q-a): para PDVs o acumulado é o número de lojas **distintas** que compraram no período, calculado só no mês de referência e por ano (canal, segmentos, supervisores, distribuidores, categorias) · **Refino E1 (13/09/2026, gerado sem publicar; D14–D18 de `docs/refino_painel_proposta.md`)**: tabela "Ano a ano" removida da Evolução (dados de `DN_ACUM_ANO` seguem para os PDVs distintos do acumulado) · **Refino E4b (13/09/2026, gerado sem publicar)**: PDVs distintos do acumulado são contados para cada mês da série (`metrics.acum_pdvs_mensal`: primeiro mês de compra do PDV no ano e soma acumulada), iguais à base de vendas e a `DN_ACUM_ANO` no fim de cada ano · **Refino E5 (13/09/2026, gerado sem publicar)**: nos modos Acumulado e Ano, cards e tabelas passam a PDVs distintos do período, volume/valor acumulado e frequência acumulada, cada um com Δ vs o mesmo período do ano anterior; PDVs distintos do período também para cluster, categoria e linhas por categoria (D25); a coluna "Acum. no ano" saiu do modo Mês |
| Aprovação | 10/09/2026 · A.10 (D31) |
| Observações | Só FY2027 × FY2026 terá par até D5 (Mtrix set/24–jun/25) ser atendida |

### RN-26 · Mês em andamento
| Campo | Conteúdo |
|---|---|
| Objetivo | Acompanhar o mês corrente sem publicá-lo como fechado |
| Definição | O mês de referência é parcial quando é o mesmo mês da última leitura das bases (manifesto). Painel etiquetado ("MÊS EM ANDAMENTO · PARCIAL"); validação de distribuidores vira "≤" com os ausentes nomeados; comparativos mantidos e rotulados (a Mtrix é mensal, não há MTD × MTD); **não publica** |
| Fórmula | `mes_ref == mês de manifesto.gravado_em` |
| Base de origem | manifesto |
| Campos usados | `gravado_em` |
| Granularidade | execução |
| Filtros aplicáveis | — |
| Exceções | `sim`/`nao` forçam |
| Nulos | — |
| Zeros | — |
| Duplicidades | — |
| Parametrização | `regras.mes_em_andamento: auto`, `publicacao.publicar_mes_em_andamento: false` |
| Responsável | Douglas |
| Status | vigente · **Refino E4a (13/09/2026, gerado sem publicar)**: com o mês de referência em andamento, o arquivo leva também o último mês fechado e **é publicado** (`publicacao.publicar_mes_em_andamento: true`, D2); abre no parcial, o seletor Mês da lateral troca para o fechado; o aviso de mês incompleto aparece só no parcial. A segmentação Base atual × Novos dos cubos é a do mês de referência (aviso no log se algum distribuidor mudar de segmento entre os dois meses); meses de histórico e PDVs distintos do acumulado são recontados até o mês fechado · **Refino E4b (13/09/2026, gerado sem publicar)**: o arquivo leva os 25 meses da série (set/24 a set/26) no seletor Mês; os meses que não são o parcial nem o fechado são montados dos mesmos cubos, sem séries; a lista de PDVs e a carteira existem só para o parcial e o fechado (mês antigo mostra a do fechado, com aviso) |
| Aprovação | 10/09/2026 · rodada 10/09 §2 |
| Observações | — |

### RN-27 · Competência da Penetração e da Matriz
| Campo | Conteúdo |
|---|---|
| Objetivo | Evitar gap e potencial inflados por mês incompleto |
| Definição | Penetração, benchmark, gap, lojas a positivar e potencial usam **sempre o último mês fechado**, mesmo com o painel exibindo o mês em andamento; a aba mostra a competência usada |
| Fórmula | `mes_penetracao = último ANO_MES fechado da série` |
| Base de origem | manifesto + série |
| Campos usados | — |
| Granularidade | execução |
| Filtros aplicáveis | todos |
| Exceções | — |
| Nulos | — |
| Zeros | — |
| Duplicidades | — |
| Parametrização | `regras.penetracao.periodo: ultimo_mes_fechado`; `dn/metrics.py::mes_fechado` (mês anterior quando o de referência está em andamento); JSON `penetracao.competencia`/`texto_competencia` (`painel.textos.pen_competencia[_parcial]`); validação `penetracao · competencia = ultimo mes fechado` |
| Responsável | Douglas |
| Status | **vigente** (F6, 11/09/2026) |
| Aprovação | 10/09/2026 · A.3 (D22) |
| Observações | — |

## Bloco 4 · Penetração, benchmark e potencial

### RN-28 · Penetração da categoria (régua oficial)
| Campo | Conteúdo |
|---|---|
| Objetivo | Medir mix: quantas das lojas que já compram levam a categoria |
| Definição | PDVs que compraram a categoria no mês ÷ PDVs positivados do nível no mês |
| Fórmula | `penetracao(nível, cat, m) = positivados(cat) ÷ positivados(nível) × 100` |
| Base de origem | `DN_CANAL_CAT_MES`, `DN_SEGMENTO_CAT_MES`, `DN_DISTRIBUIDOR_CAT_MES`; F4/F6: `DN_SUPERVISOR_CAT_MES`, `DN_CLUSTER_CAT_MES` |
| Campos usados | `positivados`, `positivados_nivel` |
| Granularidade | categoria × nível × mês |
| Filtros aplicáveis | todos; o denominador é o do recorte |
| Exceções | soma das categorias > total (PDV que compra duas conta em cada) |
| Nulos | nível sem positivado → "—" |
| Zeros | — |
| Duplicidades | RN-10 |
| Parametrização | `regras.penetracao.regua_oficial: positivados` (F0); cálculo em `dn/metrics.py::serie_nivel(cat=True)` |
| Responsável | Douglas |
| Status | **vigente** (F6, 11/09/2026) como régua oficial da aba Penetração (coluna "Penetração ÷ positivados"); RN-29 ao lado, rotulada |
| Aprovação | 08/09/2026 · Fase 2; 10/09/2026 · A.2 (D23) |
| Observações | Nunca na mesma coluna que RN-29 sem rótulo |

### RN-29 · % de cobertura da categoria (régua secundária)
| Campo | Conteúdo |
|---|---|
| Objetivo | Alcance da categoria sobre a base ativa |
| Definição | PDVs que compraram a categoria no mês ÷ base ativa do nível (base ativa **não** recortada por categoria) |
| Fórmula | `pct_cobertura(cat) = positivados(cat) ÷ base_ativa(nível) × 100` |
| Base de origem | idem RN-28 |
| Campos usados | `positivados`, `base_ativa` |
| Granularidade | categoria × nível × mês |
| Filtros aplicáveis | todos |
| Exceções | exibida como coluna rotulada ao lado de RN-28 |
| Nulos | base ativa nula → "—" |
| Zeros | — |
| Duplicidades | RN-10 |
| Parametrização | código |
| Responsável | Douglas |
| Status | vigente |
| Aprovação | 10/09/2026 · rodada 10/09 §1 (régua da categoria em Distribuidores); A.2 |
| Observações | — |

### RN-30 · Benchmark de penetração
| Campo | Conteúdo |
|---|---|
| Objetivo | Régua que transforma penetração em gap |
| Definição | Para cada categoria, o **percentil 75** da penetração (RN-28) dos distribuidores do painel com sell-out na categoria no último mês fechado. Universo: todos os distribuidores (não separa segmento). Sem mínimo de observações. **Fixo por categoria**: não é recalculado quando se filtra supervisor, distribuidor ou segmento |
| Fórmula | `benchmark(cat) = P75{ penetracao(d, cat, m_fechado) : d com positivados(cat) > 0 }` |
| Base de origem | `DN_DISTRIBUIDOR_CAT_MES` |
| Campos usados | `penetracao`, `positivados` |
| Granularidade | categoria × mês fechado |
| Filtros aplicáveis | nenhum altera a régua |
| Exceções | distribuidor sem sell-out na categoria não entra |
| Nulos | categoria sem distribuidor comprador → sem benchmark (não ocorre hoje) |
| Zeros | — |
| Duplicidades | — |
| Parametrização | `regras.penetracao.benchmark.{tipo, valor, universo, minimo_observacoes, fixo_por_categoria}`; `dn/metrics.py::penetracao` → `DN_PEN_BENCHMARK`; validações `benchmark · P75 = recalculo` e `benchmark · fixo por categoria` |
| Responsável | Douglas |
| Status | **vigente** (F6, 11/09/2026). ago/26: Amendoim 71,4% · Gomas 60,1% · Gelatina 43,8% · Regaliz 48,4% |
| Aprovação | 10/09/2026 · A.1 (D14, D15, D16, D21) |
| Observações | Riscos aceitos: distribuidor pequeno pode puxar o corte; percentil recalculado a cada mês faz o gap variar sem ação comercial. Na tela: "referência: P75 dos distribuidores na categoria, {mês}" |

### RN-31 · Lojas a positivar
| Campo | Conteúdo |
|---|---|
| Objetivo | Quantificar o gap em lojas |
| Definição | Soma, por distribuidor abaixo do benchmark, de (benchmark − penetração do distribuidor) × positivados do distribuidor. Unidade = **positivações de categoria**; entre categorias nunca vira "PDVs a positivar" (o mesmo PDV aparece em várias). No nível supervisor e canal: agregação por recálculo desse grão, nunca soma de linhas prontas |
| Fórmula | `a_positivar(cat, nível) = Σ_{d ∈ nível, pen_d < P75} (P75 − pen_d) × positivados_d ÷ 100` |
| Base de origem | `DN_DISTRIBUIDOR_CAT_MES` |
| Campos usados | `penetracao`, `positivados` (do distribuidor) |
| Granularidade | distribuidor × categoria × mês fechado |
| Filtros aplicáveis | supervisor, distribuidor, categoria recortam o conjunto de distribuidores; a régua não muda (RN-45) |
| Exceções | distribuidor acima do P75 contribui 0 ("acima da referência") |
| Nulos | — |
| Zeros | exibido como 0 |
| Duplicidades | RN-10; PDVs multi-distribuidor declarados na nota |
| Parametrização | `dn/metrics.py::penetracao` → `DN_PEN_DIST_CAT` (distribuidor × categoria), `DN_PEN_DIST_CLUSTER_CAT` (distribuidor × cluster × categoria, Q-b da F6) e `DN_PEN_NIVEL_CAT` (níveis por soma); validações `a positivar · niveis = Σ distribuidores` e `a positivar · canal = recalculo` |
| Responsável | Douglas |
| Status | **vigente** (F6, 11/09/2026). **Decisão confirmada pelo Douglas (F7, Q-a, 11/09/2026)**: distribuidor do nível **sem venda na categoria** entra com penetração 0 (abaixo da referência), pela letra da regra ("d ∈ nível"); nas 4 foco não muda nada (todos os 71 vendem); afeta Compound, Pirulito, Jubes e Granulado. ago/26: Amendoim 12.824 · Gomas 6.640 · Gelatina 6.111 · Regaliz 6.356 |
| Aprovação | 10/09/2026 · A.7, A.12 (D10, D11); estrutura confirmada contra o print (Anexo C.2) |
| Observações | Não é o gap do canal ((P75 − pen_canal) × positivados_canal daria outro número) |

### RN-32 · Comprador da categoria e "a ativar" (objetivo 1)
| Campo | Conteúdo |
|---|---|
| Objetivo | Ativação: ampliar quem compra a categoria |
| Definição | Comprador da categoria na janela = kg > 0 na categoria em ≥ 1 mês da janela de 5. A ativar = base elegível (RN-41) − compradores da categoria na janela. Lista nominal de PDVs a ativar por distribuidor |
| Fórmula | por PDV × categoria: `Σ PESO_KG(cat, janela) > 0` |
| Base de origem | fato; máscara PDV × categoria (RN-38) |
| Campos usados | `COD_PDV`, `CATEGORIA`, `PESO_KG`, `ANO_MES` |
| Granularidade | PDV × categoria (janela); agregada por nível |
| Filtros aplicáveis | todos |
| Exceções | convive com RN-31 (régua do mês) com nomes distintos: "a ativar (janela)" × "lojas a positivar (mês, vs referência)" |
| Nulos | — |
| Zeros | — |
| Duplicidades | RN-10 |
| Parametrização | janela = `regras.janela_base_ativa_meses` (6 meses que terminam no mês fechado); `dn/metrics.py::_ativacao_recorrencia` → `DN_PEN_NIVEL_CAT` (`base_elegivel`, `compradores_janela`, `a_ativar`, `pct_*`); drill nominal pela máscara (RN-38): select "Situação" da tabela de PDVs com "A ativar em {categoria}"; rótulos `painel.rotulos.pen_ativar`, `pdv_sit_ativar`, texto `painel.textos.pen_ativacao_nota`; validações `ativacao · a ativar = base elegivel − compradores`, `ativacao · canal = recalculo na fato`, `ativacao · distribuidor = pares da mascara` |
| Responsável | Douglas |
| Status | **vigente** (F7, 11/09/2026) · **15/09/2026**: texto da janela atualizado de 5 para 6 meses (acompanha a A8 de 14/09/2026, RN-02); o cálculo já usava 6. ago/26 (canal): a ativar Amendoim 44.145 · Gomas 40.521 · Gelatina 66.590 · Regaliz 60.342 (de 124.600) |
| Aprovação | 10/09/2026 · A.6; 15/09/2026 · correção de texto aprovada pelo Douglas |
| Observações | Depende de RN-38 (máscara) para o drill nominal |

### RN-33 · Recorrência da categoria (objetivo 2)
| Campo | Conteúdo |
|---|---|
| Objetivo | Aumentar a frequência de quem já compra a categoria |
| Definição | Cobertura mensal da categoria = compradores da categoria no mês ÷ compradores da categoria na janela. Frequência = nº de meses com compra da categoria na janela (1 a 5). Sazonalidade sem regra (série curta); comparação com o mesmo mês LY quando existir |
| Fórmula | `cob_mensal(cat) = compradores_mes(cat) ÷ compradores_janela(cat) × 100` |
| Base de origem | fato; máscara PDV × categoria |
| Campos usados | idem RN-32 |
| Granularidade | PDV × categoria × mês |
| Filtros aplicáveis | todos |
| Exceções | bloco separado do objetivo 1, com denominador e nome próprios ("Recorrência mensal") |
| Nulos | — |
| Zeros | — |
| Duplicidades | RN-10 |
| Parametrização | `dn/metrics.py::_ativacao_recorrencia` → `DN_PEN_NIVEL_CAT` (`compradores_mes`, `recorrencia`, `sem_compra_mes`, `freq_1..5`, `meses_medios`, `recorrencia_ly`); bloco "Recorrência mensal" na aba Penetração; drill "Compram {categoria} na janela, sem compra no mês"; rótulo `painel.rotulos.pen_sem_compra`, texto `painel.textos.pen_recorrencia_nota`; validações `recorrencia · = compradores no mes ÷ janela`, `recorrencia · distribuicao de frequencia soma os compradores`, `recorrencia · LY nulo sem par` |
| Responsável | Douglas |
| Status | **vigente** (F7, 11/09/2026). Tela decidida na F7: recorrência, sem compra no mês, distribuição 1–5 meses, média de meses, coluna LY visível com "—" até a D5 (Q-e). ago/26 (canal): Amendoim 49,5% · Gomas 45,5% · Gelatina 46,9% · Regaliz 46,5%; 2,1–2,5 meses de compra em 5 |
| Aprovação | 10/09/2026 · A.6; §18 do doc da Etapa 1 |
| Observações | — |

### RN-34 · Potencial de entrada
| Campo | Conteúdo |
|---|---|
| Objetivo | Traduzir lojas a positivar em t e R$ como **oportunidade calculada** |
| Definição | Lojas a positivar × medida média por comprador do nível na categoria × **fator observado** da categoria. Fator = kg médio das lojas que fizeram a **primeira compra da categoria** (já ativas no canal) no seu 1º mês ÷ kg médio de todos os compradores da categoria, medido na janela de 6 meses (`regras.potencial.janela_fator_meses`) e recalculado a cada mês. Média por distribuidor só com ≥ 30 lojas compradoras na categoria (senão média do canal, marcada). Média truncada no P99 da categoria. Em R$, mesma fórmula com R$/loja |
| Fórmula | `potencial_entrada = a_positivar × media_truncada(kg_loja, nível, cat) × fator(cat)` |
| Base de origem | fato; `DN_DISTRIBUIDOR_CAT_MES`; `DIM_PDV.PRIMEIRO_MES` |
| Campos usados | `PESO_KG`, `RECEITA`, `COD_PDV`, `CATEGORIA`, `ANO_MES` |
| Granularidade | distribuidor × categoria; agregado por recálculo |
| Filtros aplicáveis | recorte recalcula no nível; régua não muda |
| Exceções | categoria sem loja nova na janela → fator indisponível → "—" com nota (nunca 50% de fallback) |
| Nulos | "—" |
| Zeros | — |
| Duplicidades | RN-10 |
| Parametrização | `regras.potencial.{fator, janela_fator_meses, minimo_lojas_distribuidor, percentil_corte_outliers, rotulo_entrada, aviso}`; `dn/metrics.py::penetracao` (fator em `DN_PEN_BENCHMARK`, kg/R$ por loja e potencial em `DN_PEN_DIST_CAT`); validações `potencial · = a positivar × kg/loja × fator`, `kg/loja · truncado P99 e minimo de lojas`, `fator · observado > 0 ou nulo sem lojas novas`. Fator observado > 1 é **mantido como observado**, com aviso no log (decisão do Douglas, F7 Q-b, 11/09/2026; teto em 100% rejeitado) · **F10 (D-A, aprovada em 11/09/2026):** na linha do distribuidor, as colunas kg/loja e R$/loja passam a mostrar o valor **usado** no potencial (média truncada no P99 ou média do canal abaixo de 30 lojas), subtítulo `painel.rotulos.pen_loja_usado`; nos níveis acima, a média simples do nível (volume ÷ lojas), só descritiva, subtítulo `pen_loja_nivel`; legenda do card e dica da nuvem da Matriz citam a soma dos distribuidores (`painel.textos.pen_soma`). Código: `dn/metrics.py::penetracao` (bloco dos níveis) |
| Responsável | Douglas |
| Status | **vigente** (F6, 11/09/2026) · **15/09/2026**: texto da janela atualizado de 5 para 6 meses (acompanha a A8 de 14/09/2026, RN-02); o cálculo já usava 6. Fator na janela abr–ago/26: Amendoim 34%, Gomas 49%, Gelatina 54%, Regaliz 48% ("1ª compra da categoria" observada desde jul/25 — censura declarada em Definições) |
| Aprovação | 10/09/2026 · A.7 (D25); 15/09/2026 · correção de texto aprovada pelo Douglas |
| Observações | Medido em ago/26: fator Amendoim 30%, Gomas 48%, Gelatina 53%, Regaliz 46% (o "50%" do print era premissa) · **Achado A (11/09/2026, F10):** até a F9, a coluna ao lado do potencial mostrava a média simples em todos os níveis — em ago/26, 316 das 536 linhas distribuidor × categoria com lojas a positivar exibiam um kg/loja diferente do usado, e em 132 a conta com o número da tela não reproduzia o potencial. O potencial em si sempre esteve certo |

### RN-35 · Potencial em regime e nomenclatura
| Campo | Conteúdo |
|---|---|
| Objetivo | Separar oportunidade de teto teórico e de previsão |
| Definição | Potencial em regime = a positivar × média dos compradores (sem fator): teto teórico. Nome próprio; **nunca somado** ao de entrada. Todo potencial leva o rótulo "oportunidade calculada, não previsão" e memória de cálculo no tooltip. Nunca "meta", "previsão", "ganho garantido" |
| Fórmula | `potencial_regime = a_positivar × media_truncada(kg_loja)` |
| Base de origem | derivada |
| Campos usados | — |
| Granularidade | idem RN-34 |
| Filtros aplicáveis | idem |
| Exceções | exibição opcional; se exibido, ao lado do de entrada |
| Nulos | — |
| Zeros | — |
| Duplicidades | — |
| Parametrização | `regras.potencial.rotulo_regime`, `aviso`; coluna "Potencial em regime" ao lado da de entrada (Q-c), card na Visão da categoria, linha "todas as 10" |
| Responsável | Douglas |
| Status | **vigente** (F6, 11/09/2026) |
| Aprovação | 10/09/2026 · A.7 |
| Observações | — |

### RN-36 · Cores por distância ao benchmark
| Campo | Conteúdo |
|---|---|
| Objetivo | Leitura rápida nas tabelas por supervisor e distribuidor |
| Definição | Verde quando penetração ≥ 95% do benchmark; vermelho quando < 70%; neutro entre. Régua escrita na nota da tabela |
| Fórmula | `pct_bench = penetracao ÷ benchmark × 100` |
| Base de origem | derivada (RN-28, RN-30) |
| Campos usados | — |
| Granularidade | nível × categoria |
| Filtros aplicáveis | todos |
| Exceções | sem benchmark → sem cor |
| Nulos | sem cor |
| Zeros | — |
| Duplicidades | — |
| Parametrização | `regras.penetracao.cor_verde_pct: 95`, `cor_vermelho_pct: 70` → `DN_PEN.verde/vermelho` no template (classes `.pen-v`/`.pen-r`); validação `penetracao · cores e competencia no HTML` |
| Responsável | Douglas |
| Status | **vigente** (F6, 11/09/2026); revisável após ver a distribuição |
| Aprovação | 10/09/2026 · A.14 (D34) |
| Observações | Com P75 de Amendoim em 71,4%, 95% equivale a 67,8% de penetração |

### RN-37 · Cubos supervisor × categoria e cluster × categoria
| Campo | Conteúdo |
|---|---|
| Objetivo | Penetração por território e por tipo de loja |
| Definição | `DN_SUPERVISOR_CAT_MES` e `DN_CLUSTER_CAT_MES`, derivados da fato, com as mesmas colunas dos cubos de categoria existentes (positivados, volume, receita, base ativa, penetração, % cobertura, comparativos) |
| Fórmula | mesma de `DN_DISTRIBUIDOR_CAT_MES` com a chave do nível |
| Base de origem | fato, `DIM_DISTRIBUIDOR`, `DIM_CLUSTER` |
| Campos usados | — |
| Granularidade | nível × categoria × mês |
| Filtros aplicáveis | todos |
| Exceções | — |
| Nulos | — |
| Zeros | — |
| Duplicidades | RN-10 |
| Parametrização | `dn/metrics.py::calcular` — `DN_SUPERVISOR_CAT_MES` (SEG × SUP × CAT), `DN_SUPERVISOR_CANAL_CAT_MES` (SUP × CAT), `DN_CLUSTER_CAT_MES` (SEG × CLUSTER × CAT), `DN_CLUSTER_CANAL_CAT_MES` (CLUSTER × CAT); validações `categorias x supervisor/cluster · volume` (kg fecha com o nível em todos os meses; cobertura da categoria nunca acima do nível) |
| Responsável | Douglas |
| Status | **vigente** (F4, 10/09/2026). Expostos como linhas por categoria na aba Clusters e supervisores (Q-c) e na tabela de categorias da Visão geral filtrada por supervisor |
| Aprovação | 10/09/2026 · A.13 (D20) |
| Observações | Categoria × cluster é calculável direto da fato (SKU e Segmento do PDV na mesma linha); o print de referência a estimava (Anexo C.4) |

### RN-38 · Máscara PDV × categoria
| Campo | Conteúdo |
|---|---|
| Objetivo | Drill nominal até os PDVs a ativar e recorrência por categoria |
| Definição | Um inteiro de 10 bits por par distribuidor × PDV (bit = comprou a categoria na janela), embutido no blob de PDVs **se** a medição ficar ≤ 1 MB adicional no HTML; acima disso volta a decisão |
| Fórmula | `mascara = Σ 2^i · [comprou cat_i na janela]` |
| Base de origem | fato |
| Campos usados | `COD_PDV`, `CNPJ_DISTRIBUIDOR`, `CATEGORIA`, `PESO_KG` |
| Granularidade | par |
| Filtros aplicáveis | todos |
| Exceções | — |
| Nulos | — |
| Zeros | — |
| Duplicidades | — |
| Parametrização | `painel.pdv_categoria.{embutir_mascara: medir, limite_mb: 1}` (F0) |
| Responsável | Douglas |
| Status | **vigente** (F7, 11/09/2026): **embutida** no blob de PDVs (colunas `mascara` e `novo`), **20 bits** por par (0–9 comprou a categoria na janela · 10–19 comprou no mês; Q-c), 0,29 MB em gzip+base64 (limite 1 MB); `painel.pdv_categoria.embutir_mascara: sim`; abre as situações por categoria da tabela de PDVs e os drills da Penetração (Q-d); validação `mascara · embutida = curated` |
| Aprovação | 10/09/2026 · A.14 (D32) |
| Observações | Estimativa +0,1 a 0,3 MB |

### RN-39 · Drop (declaração de ausência)
| Campo | Conteúdo |
|---|---|
| Objetivo | Registrar que não existe |
| Definição | As bases não têm pedido, entrega, nota nem dia (Mtrix é mensal, agregada por distribuidor × PDV × SKU). Drop **não é calculável** e **nenhum proxy** (kg/PDV-mês, meses na janela) recebe esse nome |
| Fórmula | — |
| Base de origem | — |
| Campos usados | — |
| Granularidade | — |
| Filtros aplicáveis | — |
| Exceções | reabre só com base nova com grão de pedido |
| Nulos | — |
| Zeros | — |
| Duplicidades | — |
| Parametrização | — |
| Responsável | Douglas |
| Status | **declarada** |
| Aprovação | 10/09/2026 · A.14 (D26) |
| Observações | Lacuna L2 |

### RN-40 · Faturamento Dori (declaração de escopo)
| Campo | Conteúdo |
|---|---|
| Objetivo | Não confundir com RN-06 |
| Definição | Faturamento Dori (sell-in) **não está** nas bases deste projeto. Se vier, entra como base e regra próprias, com outro nome, nunca na mesma coluna que o sell-through |
| Fórmula | — |
| Base de origem | — |
| Campos usados | — |
| Granularidade | — |
| Filtros aplicáveis | — |
| Exceções | — |
| Nulos | — |
| Zeros | — |
| Duplicidades | — |
| Parametrização | — |
| Responsável | Douglas |
| Status | **declarada** |
| Aprovação | 10/09/2026 · A.4; L10 |
| Observações | Regra de escopo do projeto (não misturar com o Gerencial) |

### RN-41 · Base elegível
| Campo | Conteúdo |
|---|---|
| Objetivo | Denominador do objetivo 1 (ativação) |
| Definição | Base elegível = **base ativa do nível** (RN-02). Cadastro de PDVs elegíveis independente de compra **não existe** nas bases; o painel declara isso na aba Definições |
| Fórmula | = RN-02 |
| Base de origem | `DN_PDV_BASE_ATIVA` |
| Campos usados | — |
| Granularidade | PDV × nível |
| Filtros aplicáveis | todos |
| Exceções | — |
| Nulos | — |
| Zeros | — |
| Duplicidades | RN-10 |
| Parametrização | `regras.janela_base_ativa_meses` (sem chave própria, por decisão D28) |
| Responsável | Douglas |
| Status | **vigente** (F7, 11/09/2026) como denominador da ativação (coluna "Base elegível = base ativa"); **declarada** a ausência de cadastro em Definições |
| Aprovação | 10/09/2026 · A.6 (D24, D28) |
| Observações | Lacuna L1 |

## Bloco 5 · Matriz, filtros, resumos, apresentação

### RN-42 · Matriz de Oportunidades
| Campo | Conteúdo |
|---|---|
| Objetivo | Responder "onde atuar primeiro" |
| Definição | Unidade elementar = par **distribuidor × categoria** no último mês fechado; supervisor e canal por recálculo. Eixo X = lojas a positivar (RN-31); Y = distância ao benchmark em p.p.; bolha = potencial de entrada na métrica ativa. Um ponto por par; filtros recortam os pontos. **Sem quadrantes** na 1ª entrega (2ª entrega: mediana de X e Y do recorte, se aprovada). **Sem score único** |
| Fórmula | — |
| Base de origem | `DN_DISTRIBUIDOR_CAT_MES`, RN-30, RN-31, RN-34 |
| Campos usados | — |
| Granularidade | distribuidor × categoria |
| Filtros aplicáveis | supervisor, distribuidor, categoria, métrica |
| Exceções | totais entre categorias = "positivações de categoria"; potencial soma (é volume) |
| Nulos | par sem benchmark ou fator → fora da nuvem, listado na tabela com "—" |
| Zeros | oportunidade 0 exibida como 0; negativa = "acima da referência" |
| Duplicidades | RN-10, RN-31 |
| Parametrização | `regras.matriz.{unidade, eixo_x, eixo_y, bolha, quadrantes, score}` — lidos e conferidos em `dn/painel.py` (valor diferente do implementado, ou `quadrantes`/`score` ligados, **aborta**); a aba lê `pen_nivel_cat` (campos novos `gap_pp`, `positivados_nivel`), sem tabela própria; `painel.rotulos.matriz_grao_dist/sup`, `pdv_sit_pos_sem`, `painel.textos.matriz_nota`; template `dnMx*` (nuvem SVG, chips de grão e categoria, tabela `matriz`, estado `mxg=`/`mxc=`); validações `matriz · gap = referencia − penetracao`, `matriz · positivados do distribuidor = cubo`, `matriz · config lido e aba no HTML` |
| Responsável | Douglas |
| Status | **vigente** (F8, 11/09/2026): 1ª entrega — dois grãos (distribuidor × categoria; supervisor × categoria por soma), nuvem X = lojas a positivar (linear) · Y = referência − penetração (p.p.) · bolha = potencial na métrica, só as foco ligadas ao abrir, tabela rastreável com CSV, drill "Positivados no mês sem {categoria}" (bit do mês da máscara); **sem quadrantes e sem score** · **Refino E1 (13/09/2026, gerado sem publicar; D14–D18 de `docs/refino_painel_proposta.md`)**: **descontinuada**: aba, motor JS, `J["matriz"]`, `regras.matriz`, regras de resumo M1–M3 e ficha `gap_pp` removidos; o drill "Positivados no mês sem {categoria}" continua na tabela de PDVs (`penetracao.sit_pos_sem`) |
| Aprovação | 10/09/2026 · A.12 (D10–D13) |
| Observações | Saídas: tabela rastreável ordenável com CSV; drill até os PDVs (RN-38); nuvem; memória de cálculo no tooltip |

### RN-43 · Seletor de métrica (Volume × Valor)
| Campo | Conteúdo |
|---|---|
| Objetivo | Ler o painel em t ou em R$ |
| Definição | Toggle global, padrão **t**. Alterna medidas (volume/valor, kg/R$ por PDV, Δ de medida, séries, potencial, RTM kg/R$, PDVs); **contagens nunca alternam** (base ativa, cobertura, DN, penetração, aderência, ativados). Formatos: cards "R$ x,x mi" (1 decimal); tabelas inteiro com milhar; R$/PDV 2 decimais; eixos "R$ mi"; CSV com valor cheio e métrica no nome (`_t`/`_rs`). Estado em `localStorage` e URL (`met=t|rs`) |
| Fórmula | — |
| Base de origem | RN-05, RN-06, RN-07 |
| Campos usados | — |
| Granularidade | — |
| Filtros aplicáveis | combina com todos |
| Exceções | recorte com kg > 0 e R$ = 0 avisa |
| Nulos | — |
| Zeros | — |
| Duplicidades | — |
| Parametrização | `regras.metrica.{padrao, formato_*}`, `painel.rotulos.metrica_t/metrica_rs`; template: `dnMet()`, `dnAplicarMetrica()`, classes `m-kg`/`m-rs`, `DN_COLS_KPI()`; validação `metrica · pares t/R$ no HTML` |
| Responsável | Douglas |
| Status | **vigente** (F1, 10/09/2026) |
| Aprovação | 10/09/2026 · A.4, A.5 |
| Observações | Resíduos do protótipo (`RKG=34.26`, `applyUnit`, `UMODE`, `YMODE`, `setu`, `sety`, `PCL`, cartões HERO, aba Histórico, exportadores mortos) **removidos na F1**; o R$ vem só de `receita_rs` |

### RN-44 · Filtro por Supervisor
| Campo | Conteúdo |
|---|---|
| Objetivo | Recorte por território |
| Definição | Seleção **única** com "Todos". Age em Visão geral, Evolução, Clusters e supervisores (destaca a linha), Distribuidores, Pontos de venda, Penetração, Matriz e, **desde 13/09/2026 (D18 revista), RTM pelo supervisor do destino** (cards, série, destinos, clientes e drills só com os clientes cujo destino é do supervisor; clientes com destino não mensurável não têm supervisor e saem do recorte, com nota); **não** em Definições. Escolher supervisor restringe a lista de distribuidores; escolher distribuidor de outro supervisor limpa o supervisor. Chip esmaecido onde não age. Estado em `localStorage` e URL (`sup=`). Aviso fixo de hierarquia vigente (RN-15) |
| Fórmula | `distribuidores(sup) = {d : SUPERVISOR(d) = sup}` |
| Base de origem | `DIM_DISTRIBUIDOR` |
| Campos usados | `SUPERVISOR` |
| Granularidade | supervisor |
| Filtros aplicáveis | combina com segmento, distribuidor, categoria, métrica, calendário |
| Exceções | supervisor sem distribuidor do segmento → "sem distribuidores deste segmento" |
| Nulos | — |
| Zeros | — |
| Duplicidades | — |
| Parametrização | `painel.abas[].filtros` (visao, evolucao, clusters, distribuidores, pdv), `painel.rotulos.supervisor_todos`; JSON `supervisores_lista`, `distribuidor.supervisor_id`, `categorias_sup`, `evo_sup_json`; template `dnSup()`, `dnCardsAplicar()`, `DN_DIST_SUP`, estado `sup=` |
| Responsável | Douglas |
| Status | **vigente** (F4, 10/09/2026). Com supervisor: cards da Visão geral mostram o supervisor no segmento ativo (Q-a); tabela de categorias vira supervisor × categoria; Evolução usa a série do supervisor e o recorte por categoria fica desabilitado com nota (Q-b); evolução por categoria com as séries do supervisor; Distribuidores e PDVs restritos; RTM não age · **Refino E2 (13/09/2026, gerado sem publicar)**: o select de supervisor mora na barra lateral; na aba Pontos de venda e no RTM só aparecem os filtros que valem ali · **Refino E3 (13/09/2026, gerado sem publicar)**: na aba Supervisores e distribuidores, clicar no nome do supervisor filtra os distribuidores dele; na visão Cluster os filtros Supervisor e Distribuidor somem (a tabela de clusters não tem esses recortes) · **22/09/2026 (Douglas, gerado sem publicar)**: o filtro **Distribuidor** passa a agir na Visão Geral (`painel.abas[].filtros`): cards do mês e do acumulado vêm do registro do distribuidor em `tabelas_json.distribuidores` (categoria "Todas"; o distribuidor está num único segmento, então "Todos" usa esse registro e outro segmento dá "Sem dado"); o gráfico mês a mês usa a série `dist-<id>` (sem a linha "mesmo mês LY", RN-22); o ranking "O que aconteceu no mês" fica **oculto** com distribuidor selecionado (decisão do Douglas: uma linha só não tem o que comparar); evolução e tabela por categoria seguem o canal ou o supervisor, com nota; template `dnVgDist()`, `dnDistReg()`. Só navegador, nenhum número ou campo do JSON muda |
| Aprovação | 10/09/2026 · A.13 (D18, D19) · 22/09/2026 · Douglas (distribuidor na Visão Geral, ranking oculto) |
| Observações | Multi-seleção não; o nível gerente (N2) seria o caminho para territórios juntos |

### RN-45 · Filtros × referências
| Campo | Conteúdo |
|---|---|
| Objetivo | Não mover a régua a cada clique |
| Definição | Benchmark (RN-30) e fator (RN-34) são calculados no total e **não** mudam com filtro; lojas a positivar, potencial, rankings e resumos são recalculados no recorte, no nível, nunca por soma |
| Fórmula | — |
| Base de origem | — |
| Campos usados | — |
| Granularidade | — |
| Filtros aplicáveis | todos |
| Exceções | — |
| Nulos | recorte vazio → "sem dado" |
| Zeros | — |
| Duplicidades | — |
| Parametrização | `regras.penetracao.benchmark.fixo_por_categoria: true`; na aba Penetração o nível ativo (canal, segmento, supervisor, distribuidor) escolhe linhas pré-calculadas — nada é somado no template; nota "no recorte selecionado (referência e fator não mudam)" |
| Responsável | Douglas |
| Status | **vigente** (F6, 11/09/2026) na Penetração · Refino E1 (13/09/2026): a Matriz saiu, a regra vale só na Penetração |
| Aprovação | 10/09/2026 · A.1; §23 do doc da Etapa 1 |
| Observações | Rótulo "no recorte selecionado" nos números recalculados |

### RN-46 · Evolução por categoria
| Campo | Conteúdo |
|---|---|
| Objetivo | Ver categorias crescendo ou caindo |
| Definição | Gráfico de linhas com **Top N** (padrão 5, config) na métrica do seletor mais a linha "Outras categorias" agregada; seleção manual de quais exibir, foco (RN-19) ligadas por padrão. A tabela de categorias ganha participação % na métrica ativa, Δ participação vs LY (quando houver) e sparkline. Sem regra de "aceleração" nesta rodada |
| Fórmula | `participacao(cat) = medida(cat) ÷ medida(canal) × 100` |
| Base de origem | `DN_CANAL_CAT_MES` (séries já embutidas) |
| Campos usados | `volume_kg`, `receita_rs` por mês |
| Granularidade | categoria × mês |
| Filtros aplicáveis | métrica, período, segmento e supervisor (séries `EVO_SUP`, desde a F4); distribuidor e categoria **não** (série por categoria × distribuidor descartada por tamanho em 10/09) |
| Exceções | — |
| Nulos | — |
| Zeros | — |
| Duplicidades | — |
| Parametrização | `painel.graficos.{categorias_top_n, categorias_outras_rotulo}`, `painel.rotulos.evo_*`; JSON `graficos.*`, `categoria.{participacao_*, spark_*}`, `segmento.supervisor.spark_*`, `distribuidor.spark_*`; template `dnEvo*`, `dnSpark`, tabela `evo`; estado `evo=` |
| Responsável | Douglas |
| Status | **vigente** (F3, 10/09/2026). "Outras categorias" = soma das **não selecionadas** (Q-a); eixo em valor absoluto na métrica do seletor (Q-c); sparkline também em supervisores e distribuidores (Q-b; nas linhas por categoria do distribuidor fica "—", sem série por categoria) · **Refino E1 (13/09/2026, gerado sem publicar; D14–D18 de `docs/refino_painel_proposta.md`)**: mini-linhas (sparkline) removidas das tabelas; o gráfico ao clicar na linha entra na E3 · **Refino E3 (13/09/2026, gerado sem publicar)**: a evolução por categoria passou para a Visão Geral; o gráfico mês a mês segue Segmento e Categoria da lateral (séries do canal por segmento e segmento × categoria embutidas); a evolução por categoria em linhas segue sem recorte de segmento até a E4; clicar na linha de categorias, supervisores, distribuidores ou clusters abre o gráfico em janela · **Refino E4b (13/09/2026, gerado sem publicar)**: a evolução por categoria em linhas segue o Segmento (séries segmento × categoria) e o total diz o recorte; o gráfico das linhas por categoria de supervisor, distribuidor e cluster é montado das tabelas de cada mês, com o LY buscado na tabela do mesmo mês do ano anterior · **Estabilização A1 (14/09/2026, gerado sem publicar)**: corrigida a regressão da E3: `dnEvoDraw()` procurava a aba `aba-evolucao` (removida na fusão) e por isso chips e gráfico não apareciam desde a E3, só a tabela; passou a `aba-visao`. Nenhuma outra mudança · **A9 (14/09/2026)**: a tabela do bloco é remontada inteira (`DnTabela.remetrica('evo')`) a cada redesenho, para o cabeçalho ter os mesmos meses do gráfico ao trocar período, mês ou Série completa |
| Aprovação | 10/09/2026 · A.11 (D8, D9); correção A1 aprovada em 14/09/2026 |
| Observações | Validações: `categorias · participacao (vol/rs) soma 100`, `categorias · participacao vs LY = recalculo`, `sparklines = series` |

### RN-47 · Gráfico de evolução com Last Year
| Campo | Conteúdo |
|---|---|
| Objetivo | Comparar cada mês com o mesmo mês do ano anterior |
| Definição | Coluna = realizado do mês; linha com marcador = mesmo mês LY (só onde existir, RN-22); Δ% vs LY escrito sob o mês quando houver; tooltip com atual, LY e Δ. Chave "PDVs · Volume/Valor": em PDVs mantém empilhado por segmento e linha da base ativa; em métrica, coluna única na métrica ativa e linha LY da mesma métrica. Campos novos `volume_ly` e `receita_ly` por ponto, por junção no pipeline |
| Fórmula | `x_ly(m) = x(ANO_MES_LY(m))` |
| Base de origem | `DN_*_MES`, `DIM_CALENDARIO` |
| Campos usados | `cobertura_ly` (existe), `volume_ly`, `receita_ly` (novos) |
| Granularidade | nível × mês |
| Filtros aplicáveis | todos |
| Exceções | RN-22 |
| Nulos | RN-22 |
| Zeros | — |
| Duplicidades | — |
| Parametrização | `painel.graficos.{evolucao_ly, chave_padrao}`, `painel.rotulos.graf_pdv`, `painel.textos.sem_ly`; JSON `graficos.*`; série com `volume_ly`, `receita_ly` e 12 Δ por ponto; template `dnDraw` (duas chaves), `dnGraf()`, estado `graf=` |
| Responsável | Douglas |
| Status | **vigente** (F2, 10/09/2026) |
| Aprovação | 10/09/2026 · A.11 (D6, D7) |
| Observações | Validações: `serie · LY = mes correspondente` (canal + 5 distribuidores) e `serie · Δ do JSON = curated = recalculo`. Na chave PDVs o Δ% vs LY fica na tabela e no tooltip (Q-c); na chave medida vai sob o mês |

### RN-48 · Resumos executivos dinâmicos
| Campo | Conteúdo |
|---|---|
| Objetivo | Dizer onde olhar, com rastreabilidade |
| Definição | Cada frase é uma **regra declarada no config** (`painel.resumos.regras[]`), avaliada no navegador sobre os dados embutidos e os filtros ativos, com seis partes: o que · onde · quanto · contra o quê · por que merece atenção (limiar da regra) · próximo nível (link que aplica o filtro). Só fatos numéricos; sem adjetivo, causa, prescrição ou responsabilização. Sem dado no recorte → "sem dado suficiente para X". O pipeline valida cada regra contra o dado do mês em um recorte por aba. **Limiares** aprovados item a item na F9, com exemplos reais |
| Fórmula | por regra |
| Base de origem | dados embutidos no HTML |
| Campos usados | por regra |
| Granularidade | aba × recorte |
| Filtros aplicáveis | todos |
| Exceções | Definições não tem resumo |
| Nulos | "sem dado suficiente" |
| Zeros | — |
| Duplicidades | — |
| Parametrização | `painel.resumos.{ativo, termos_vetados, regras[]}` — **24 regras** (id, aba, rn, indicador, tipo, parâmetros, texto com `{campo}` formatado pelo sufixo, limiar, link); `painel.textos.resumo_*`; avaliador `dn/resumos.py` (um tipo = uma operação: dn_mes, delta_serie_extremo, extremo, pdv_sem_compra, pdv_maior_sem_compra, pdv_concentracao, novos, abaixo_p75, sem_venda_mes, rtm_aderencia, rtm_vazamento, rtm_parados) e motor JS `dnRs*` (espelho); JSON `resumos.regras_json/esperado_json`, `kpi_json`; validações `resumos · {aba} = curated` (8), `resumos · regras do config no HTML`, `resumos · textos sem termos vetados` · **F10 (Q6, Q7, 11/09/2026):** campo `piso` no tipo `extremo` — D1 só ranqueia distribuidores com ≥ 30 PDVs no mês de comparação; R4 só ranqueia destinos com ≥ 20 clientes; o piso aparece na memória da frase |
| Responsável | Douglas |
| Status | **vigente** (F9, 11/09/2026). Limiares aprovados em 11/09/2026: V1 \|Δ DN\| ≥ 1,0 p.p. · V2 \|Δ PDVs do distribuidor\| ≥ 100 · V3 queda de % cobertura ≥ 1,0 p.p. · V4 ≥ 30% da base sem compra · E1 \|Δ da categoria\| ≥ 10 t / R$ 300 mil · C1 \|Δ DN do cluster\| ≥ 2,0 p.p. · C2 \|Δ PDVs do supervisor\| ≥ 100 · C3 DN ≥ 5,0 p.p. abaixo do recorte · D1 \|Δ cobertura\| ≥ 20% · D2 informativa · D3 ≥ 25% dos distribuidores abaixo do P75 nas 4 foco · D4 ≥ 1 (só mês em andamento) · P1 informativa · P2 ≥ 70% do volume nos 10% maiores (N = 1.000) · R1 \|Δ aderência\| ≥ 1,0 p.p. · R2 vazamento ≥ 5% dos mensuráveis · R3 ≥ 50% dos ativados parados · R4 ≥ 50% sem compra no destino · N1 informativa · N2 < 70% da referência · N3 ≥ 50% sem compra no mês (ranking pelo nº absoluto) · M1/M2/M3 informativas. A frase aparece sempre; o limiar só marca "atenção" (Q-b) · Pisos desde a F10: em ago/26 a maior alta da D1 passou de Propec (+7.550%, de 2 para 153 PDVs) para Francal Imperatriz (+74,1%), e o destino da R4 passou de VJS (1 cliente) para Claumar (106 de 109 sem compra) · **Refino E1 (13/09/2026, gerado sem publicar; D14–D18 de `docs/refino_painel_proposta.md`)**: **desligada** (`painel.resumos.ativo: false`): blocos fora da tela e validações puladas; código e regras mantidos (M1–M3 e A1–A3 saíram com Matriz e Alavancas) |
| Aprovação | 10/09/2026 · A.14 (D17, D27) |
| Observações | Lista de frases por aba na ficha A.14. Não existe resumo hoje |

### RN-49 · Rastreabilidade
| Campo | Conteúdo |
|---|---|
| Objetivo | Todo número e frase auditáveis na tela |
| Definição | Tooltip (ou modal do drill) por frase de resumo e por número de oportunidade com: indicador, período, filtros ativos, base de origem, id da regra (RN), valor de comparação, benchmark, memória de cálculo, data dos dados (carimbo do manifesto) |
| Fórmula | — |
| Base de origem | — |
| Campos usados | — |
| Granularidade | — |
| Filtros aplicáveis | — |
| Exceções | — |
| Nulos | — |
| Zeros | — |
| Duplicidades | — |
| Parametrização | `painel.memoria.{ativo, marca, copiar, tabelas.{por_coluna, por_linha}, extrato_rn, tolerancia, textos, fontes_rotulos, fichas[]}` — **26 fichas** (id, rn, título, indicador, abas, período, fórmula, parcelas, conta e conta_rs, conta_soma e conta_soma_rs nos níveis acima do distribuidor, confere e confere_rs com as operações div100 · sub · div · mul · mul3 · gap, perspectiva, fonte, curated, liga, nota); avaliador `dn/memoria.py` (conferência, extrato das RN lido deste dicionário, esperado no recorte do canal, JSON `memoria.json`); motor `dnMem*` no template (modal `#dnmem`, botão ⓘ nos cards da Visão geral, da Penetração e do RTM, no cabeçalho de 75 colunas ligadas, por linha nas 7 colunas de oportunidade, e nas frases de resumo; botão copiar; auto-conferência da conta com a meia unidade de arredondamento de cada número; comparação com o esperado sem filtros); extrato das RN citadas nas Definições; validações `memoria · fichas do config no HTML`, `aritmetica = curated`, `toda parcela existe no inventario`, `RN citada existe e esta vigente`, `fonte = config`, `todo numero marcado tem ficha`, `textos sem termos vetados`, `modal no HTML` |
| Responsável | Douglas |
| Status | **vigente** (F10, 11/09/2026): memória de cálculo a um clique em todo número de card, em toda coluna ligada e nas colunas de oportunidade linha a linha, com as oito partes (indicador · RN · período · filtros ativos · fórmula · conta com os números da tela · fonte até a coluna · data dos dados). Q1–Q5 aprovadas em 11/09/2026: marca ⓘ, modal, copiar, coluna + linha, extrato das RN embutido · **Refino E1 (13/09/2026, gerado sem publicar; D14–D18 de `docs/refino_painel_proposta.md`)**: **desligada** (`painel.memoria.ativo: false`): botões ⓘ e modal fora da tela e validações puladas; código e fichas mantidos (fichas de Matriz e Alavancas saíram) |
| Aprovação | 10/09/2026 · A.14; §21 do pedido · proposta F10 (P1–P6, 26 fichas, 8 validações, Q1–Q7) aprovada em 11/09/2026; lista de fichas conferida e aprovada em 11/09/2026 |
| Observações | A conferência das fichas contra a tela revelou o **achado A** (ver RN-34): o kg/R$ por loja exibido não era o que multiplicava o potencial. Corrigido pela D-A antes de a memória entrar |

### RN-50 · Abas do painel
| Campo | Conteúdo |
|---|---|
| Objetivo | Estrutura de navegação após a evolução |
| Definição | Visão geral (foto do mês) · **Evolução** (nova: gráfico LY, categorias, série e acumulados, calendário) · Clusters e supervisores · Distribuidores · Pontos de venda · **Penetração** (nova) · **Matriz** (nova) · RTM · Definições. Ordem final confirmada em cada fase (F3, F6, F8). Alavancas: **não** nesta rodada (candidata F11) |
| Fórmula | — |
| Base de origem | config |
| Campos usados | — |
| Granularidade | — |
| Filtros aplicáveis | por aba (`painel.abas[].filtros`) |
| Exceções | `painel.abas` só muda na fase que cria a aba (validação template = config) |
| Nulos | — |
| Zeros | — |
| Duplicidades | — |
| Parametrização | `painel.abas` (por fase). F3: `{id: evolucao, rotulo: "Evolução", filtros: [categoria]}` na 2ª posição |
| Responsável | Douglas |
| Status | abas **Evolução** (F3), **Penetração** (F6), **Matriz de oportunidades** (F8, entre Penetração e RTM) e **Alavancas** (F11, 11/09/2026, entre Evolução e Clusters e supervisores; RN-57) **vigentes** — regra completa · **Refino E1 (13/09/2026, gerado sem publicar; D14–D18 de `docs/refino_painel_proposta.md`)**: abas Alavancas e Matriz de oportunidades **removidas**; ficam Visão geral · Evolução · Clusters e supervisores · Distribuidores · Pontos de venda · Penetração · RTM · Definições · **Refino E2 (13/09/2026, gerado sem publicar)**: filtros em barra lateral recolhível (ordem: Período · Ano · Segmento · Supervisor · Distribuidor · Categoria em lista · Métrica); o filtro que não vale na aba some; linha de filtros ativos presa com as abas; Limpar filtros (segmento, supervisor, distribuidor, categoria); Voltar = cada troca de aba é um passo (aba, filtros e rolagem), também pelo botão do navegador · **Refino E3 (13/09/2026, gerado sem publicar)**: abas passam a 6: Visão Geral (Visão geral + Evolução) · Supervisores e distribuidores (Clusters e supervisores + Distribuidores, id `distribuidores`, seletor Ver por Supervisor · Distribuidor · Cluster) · Pontos de venda · Penetração (tabelas por supervisor, cluster e distribuidor num bloco com Ver por) · RTM · Definições · **Estabilização A3 (14/09/2026, gerado sem publicar)**: **Penetração e RTM ocultas** da navegação (`painel.abas[].oculta: true`): botão `hidden`, fora da lista de abas do navegador (URL `#aba=rtm`/`#aba=penetracao` e setas do teclado caem na Visão Geral); templates, dados, motores e validações mantidos; reversível pelo config; validação `abas · ocultas = config`. Reverte D5/D6/D14 do refino por decisão do Douglas. Definições mantêm os temas Penetração e RTM. Usuário final vê 4 abas |
| Aprovação | 10/09/2026 · A.16 (Q3) |
| Observações | — |

### RN-51 · Carimbo e publicação
| Campo | Conteúdo |
|---|---|
| Objetivo | Saber de quando são os dados e proteger o publicado |
| Definição | "atualizado em dd/mm/aaaa" = data da última ingestão (manifesto), não do relógio. Publicação só do HTML, nome estável, cópia atômica com md5, após todas as validações; mês em andamento não publica |
| Fórmula | — |
| Base de origem | manifesto |
| Campos usados | `gravado_em` |
| Granularidade | execução |
| Filtros aplicáveis | — |
| Exceções | — |
| Nulos | — |
| Zeros | — |
| Duplicidades | — |
| Parametrização | `publicacao.*` |
| Responsável | Douglas |
| Status | vigente |
| Aprovação | 09/09/2026 · Fase 5 |
| Observações | — |

## Bloco 6 · RTM (vigentes; sem mudança na Etapa 1)

### RN-52 · Aderência ao direcionamento
| Campo | Conteúdo |
|---|---|
| Objetivo | Medir se o cliente migrado compra do destino |
| Definição | Aderiu quem comprou do destino do de-para (qualquer filial) no mês; comprou só de outro = vazamento, medido à parte e nunca somado; não comprou = sem sell-out de ninguém. **Destino (13/09/2026, decisão 8b):** `Cód. Cliente [Distribuidor]` da planilha RTM → filial no de-para (`Cód. Interno Cliente`) → nome reduzido do de-para; "do destino" continua valendo para qualquer filial desse nome (confirmado em 02/10/2026). O **supervisor do destino** é o da **filial do código**, não o do grupo de filiais do mesmo nome (02/10/2026, Douglas: a CHUA passou a ter filiais de dois supervisores); no painel por usuário, o cliente entra se a filial do código é do usuário. Sem código ou com código fora do de-para = destino sem cadastro (RN-53), mesmo que o nome da planilha case; nome da planilha diferente do nome do código = só aviso |
| Fórmula | `pct_aderencia = certo ÷ mensuráveis × 100` |
| Base de origem | `RTM_DePara_Transicao.xlsx`, Mtrix, de-para |
| Campos usados | `CNPJ`, `Cód. Cliente [Distribuidor]`, `Dsitribuidor Nome Reduzido` (conferência), `CNPJ do AD.`; de-para `Cód. Interno Cliente`, `Distribuidora Nome Reduzido` |
| Granularidade | cliente × mês; recorte por supervisor do destino (RN-44) |
| Filtros aplicáveis | próprios do bloco (estado, destino, visão temporal); supervisor da barra pelo supervisor do destino (D18 revista, 13/09/2026); período (RN-59) só na visão histórico completo |
| Exceções | até 01/10/2026: destino com filiais de supervisores diferentes abortava. Desde 02/10/2026 o supervisor vem da filial do código; aborta só cliente mensurável cuja filial do código não está no painel, ou código com mais de uma filial no de-para |
| Nulos | — |
| Zeros | — |
| Duplicidades | CNPJ único na base RTM |
| Parametrização | `regras.rtm_destino_chave: codigo`; código: `dn/metrics.py::rtm_aderencia` → `DN_RTM_MES`, `DN_RTM_SUP_MES` |
| Responsável | Douglas |
| Status | vigente; **revista em 13/09/2026** (chave por código e recorte por supervisor do destino) · **Refino E4a (13/09/2026, gerado sem publicar)**: cards, destinos e clientes do RTM seguem o mês escolhido; na visão "a partir da migração", um mês anterior ao corte volta para histórico completo · **Refino E4b (13/09/2026, gerado sem publicar)**: clientes RTM de cada mês montados no navegador a partir da lista cliente × mês (busca, sem conta), conferidos contra a tabela do pipeline no parcial e no fechado; destinos do mês calculados no pipeline a partir da grade cliente × mês |
| Aprovação | 09/09/2026 · rodada 09/09 §10; 13/09/2026 · Etapa 2 da frequência (decisões 8a e 8b) |
| Observações | Medido em 13/09/2026: código e nome casam os mesmos 1.589 clientes (1.589 de 1.589 com o mesmo nome); 173 não mensuráveis por qualquer das duas chaves (NOVO RIBEIRÃO PRETO 91 e NOVO SJRP 75 sem código; DIBS 6 e NOVA ENERGIA 1 com código fora do de-para). A coluna opcional `CNPJ Distribuidor Destino` deixa de ser necessária. Por supervisor do destino (ago/26): 10 supervisores; Σ = canal (1.589 · 213 · 93 · 1.283); 54 dos 93 "só de outro" atendidos por distribuidor de outro supervisor |

### RN-53 · Destino não mensurável
| Campo | Conteúdo |
|---|---|
| Objetivo | Não afirmar "não comprou" sem dado |
| Definição | Cliente cujo destino não existe no de-para (sem cadastro), existe mas está fora do painel, ou está no painel sem sell-out na série. Fora do denominador; nunca "não comprou"; atributo de cadastro, igual em todos os meses. Destino por CNPJ quando a coluna `CNPJ Distribuidor Destino` existir, senão por nome com aviso |
| Fórmula | três causas exibidas separadamente |
| Base de origem | RTM, de-para, Hierarquia |
| Campos usados | — |
| Granularidade | cliente |
| Filtros aplicáveis | próprios do bloco |
| Exceções | — |
| Nulos | — |
| Zeros | — |
| Duplicidades | — |
| Parametrização | `painel.rotulos.rtm_motivos`, `painel.textos.rtm_nao_mensuravel`, `fontes.rtm.colunas_opcionais` |
| Responsável | Douglas |
| Status | vigente |
| Aprovação | 09/09/2026 · Fase 4 |
| Observações | 173 clientes em 4 destinos sem cadastro (10/09) |

### RN-54 · Corte temporal e ativação do RTM
| Campo | Conteúdo |
|---|---|
| Objetivo | Ler a migração a partir da data oficial |
| Definição | Corte 01/09/2026; visão "a partir da migração" vira padrão automaticamente quando a série alcança o corte; ativação (1ª compra no destino) em duas réguas: histórico completo e desde o corte |
| Fórmula | — |
| Base de origem | config, Mtrix |
| Campos usados | — |
| Granularidade | cliente × mês |
| Filtros aplicáveis | chip de visão |
| Exceções | o calendário civil/fiscal (RN-24) **não** afeta o RTM |
| Nulos | — |
| Zeros | — |
| Duplicidades | — |
| Parametrização | `regras.rtm.{data_migracao, visao_padrao}` |
| Responsável | Douglas |
| Status | vigente |
| Aprovação | 09/09/2026 · Fase 4 (A4) |
| Observações | — |

### RN-55 · Valor no RTM
| Campo | Conteúdo |
|---|---|
| Objetivo | Aplicar o seletor de métrica ao bloco RTM |
| Definição | kg no destino / em outros alternam para R$ no destino / em outros (`rs_certo`, `rs_outro`, já calculados) sob a regra RN-06; contagens (clientes, aderência, ativados) não alternam |
| Fórmula | — |
| Base de origem | `DN_RTM_MES`, `DN_RTM_DESTINO`, `DN_RTM_CLIENTE_MES` |
| Campos usados | `rs_certo`, `rs_outro` |
| Granularidade | idem RN-52 |
| Filtros aplicáveis | métrica + próprios do bloco |
| Exceções | — |
| Nulos | — |
| Zeros | — |
| Duplicidades | — |
| Parametrização | `regras.metrica` (alcance total); blob do RTM cols 8–9 |
| Responsável | Douglas |
| Status | **vigente** (F1, 10/09/2026) |
| Aprovação | 10/09/2026 · A.4 |
| Observações | Decisão de 09/09 (só kg) revogada pela A.4 |

### RN-56 · Carteira de PDVs ponderados (PRIME / DESTAQUE)
| Campo | Conteúdo |
|---|---|
| Objetivo | Acompanhar PDVs específicos escolhidos pelo comercial (carteira ponderada), separados em DESTAQUE e PRIME |
| Definição | Carteira = pares distribuidor × PDV da planilha `DE-PARA_Ponderada_Clusters.xlsx` com cluster PRIME ou DESTAQUE. Um par entra no painel se (1) o CNPJ do distribuidor está no de-para e no painel, (2) o CNPJ do PDV existe na Mtrix e não é CNPJ de distribuidor e (3) esse distribuidor vendeu para o PDV (kg > 0) em pelo menos um mês da série. Razão social diferente da Mtrix é só aviso |
| Fórmula | `valida(par) = dist ∈ painel ∧ pdv ∈ DIM_PDV ∧ pdv ∉ distribuidores ∧ Σ kg(dist, pdv, série) > 0` |
| Base de origem | planilha ponderada; Mtrix; de-para; Hierarquia |
| Campos usados | `CNPJ DISTRIBUIDOR`, `CNPJ PDV`, `RAZÃO SOCIAL VAREJO`, `CLUSTER`; Mtrix `CNPJ do AD.`, `Cód. PDV`, `# Sell-Out (Quilos)`, `Ano/Mês` |
| Granularidade | par distribuidor × PDV (linha da planilha) |
| Filtros aplicáveis | na aba Pontos de venda, combina com distribuidor, supervisor e Situação; botões Destaque · Prime · Todos os PDVs |
| Exceções | linha inválida não aborta: fica fora, com o número da linha do Excel e o motivo no log e em `data/dn/quality/carteira_pdv.md` (Q2); nome diferente da Mtrix = aviso (Q4); os atalhos de outras abas para Pontos de venda abrem em "Todos" |
| Nulos | planilha ausente = painel sem a carteira (fonte opcional) |
| Zeros | par sem compra na série = inválido |
| Duplicidades | par repetido ou PDV em dois clusters: as linhas envolvidas ficam fora, com aviso (Q5) |
| Parametrização | `fontes.pdv_ponderada`; `regras.carteira.{clusters_validos, exige_compra_na_serie, nome_aviso_minimo, nome_palavras_ignoradas}`; `painel.pdv_carteira.{ativo, padrao, rotulo, opcoes, textos}`; código `dn/extract/cadastros.py::ler_pdv_ponderada`, `dn/metrics.py::carteira` → `DN_PDV_CARTEIRA` |
| Responsável | Douglas |
| Status | **vigente** (11/09/2026): botões Destaque · Prime · Todos na aba Pontos de venda, abrindo em Destaque (**desde 16/09/2026 abre em Todos os PDVs, RN-64**; no painel por usuário só pares do recorte, RN-63); 57 linhas válidas em ago/26 (DESTAQUE 6, PRIME 51); validações `carteira · …` · **Refino E4a (13/09/2026, gerado sem publicar)**: a carteira (pares válidos na base ativa) é calculada para cada mês do arquivo |
| Aprovação | 10/09/2026 · pedido; 11/09/2026 · proposta "PDVs ponderados" (P1–P9, Q1–Q6) aprovada como recomendado |
| Observações | Em 11/09/2026: 181 linhas; 58 válidas (DESTAQUE 7 de 9; PRIME 51 de 172), todas na base ativa de ago/26 |

### RN-57 · Decomposição da variação (alavancas)
| Campo | Conteúdo |
|---|---|
| Objetivo | Mostrar de onde veio a variação da medida (t ou R$) entre dois meses, sem premissa e sem causa |
| Definição | Identidades exatas: medida = base ativa × DN ÷ 100 × medida por PDV comprador; medida por PDV = categorias por loja × SKUs por categoria × medida por SKU (níveis sem categoria); com categoria: medida da categoria = base ativa do nível × % de cobertura da categoria ÷ 100 × medida por comprador da categoria (régua RN-29). A contribuição de cada fator é a média do efeito de trocar só aquele fator do mês de comparação para o mês, em todas as ordens de troca (valor de Shapley); as contribuições somam a variação. Base RTM: clientes mensuráveis × aderência ÷ 100 × medida por cliente que comprou do destino (subconjunto do canal, não soma) |
| Fórmula | `c_i = (1/n!) Σ_ordens [f(x com os fatores até i trocados) − f(x com os fatores antes de i trocados)]`, `Σ c_i = f(x1) − f(x0)` |
| Base de origem | cubos `DN_*_MES` e `DN_*_CAT_MES` (canal, segmento, supervisor, supervisor × segmento, distribuidor); fato (pares PDV × categoria e PDV × SKU com kg > 0); `DN_RTM_MES` |
| Campos usados | `base_ativa`, `pct_cobertura`, `positivados`, `volume_kg`, `receita_rs`, `kg_pdv`, `rs_pdv`; fato `COD_PDV`, `CAT`, `COD_PRODUTO`, `PESO_KG`; RTM `certo`, `so_outro`, `sem_compra`, `pct_aderencia`, `kg_certo`, `rs_certo` |
| Granularidade | nível × categoria × comparação (mês anterior, mesmo mês do ano anterior) |
| Filtros aplicáveis | segmento, categoria, supervisor, distribuidor, métrica; calendário não age |
| Exceções | quem não vendeu em um dos meses é **entrada** ou **saída**, sem decomposição (a variação dele entra no total); PDV em mais de um distribuidor conta em cada um (RN-10) |
| Nulos | mês de comparação sem base ativa (janela de 6 meses incompleta) = "sem par": a comparação não é decomposta |
| Zeros | contribuição zero exibida como zero |
| Duplicidades | RN-10 |
| Parametrização | `regras.alavancas.{metodo, comparacoes, mix, rtm}`; `painel.alavancas.{textos, rotulos}`; aba em `painel.abas`; resumos A1–A3; fichas de memória `alav_*`; código `dn/metrics.py::alavancas` → `DN_ALAVANCAS` |
| Responsável | Douglas |
| Status | **vigente** (F11, 11/09/2026; ficha escrita antes do código) · **15/09/2026**: texto da janela atualizado de 5 para 6 meses (acompanha a A8 de 14/09/2026, RN-02); o cálculo já usava 6 · **Refino E1 (13/09/2026, gerado sem publicar; D14–D18 de `docs/refino_painel_proposta.md`)**: **descontinuada**: aba, `metrics.alavancas`, `DN_ALAVANCAS`, `painel.alavancas`, regras A1–A3 e fichas `alav_*` removidos. A aba volta em outro formato (plano por alavanca, como o print do Douglas) quando existir a fonte do plano |
| Aprovação | 10/09/2026 · A.16; 11/09/2026 · proposta F11 (P1–P8, Q1–Q8) aprovada como recomendado; 15/09/2026 · correção de texto aprovada pelo Douglas |
| Observações | É decomposição aritmética, não causa: "o DN contribuiu −67,5 t" não diz por que o DN caiu. ago/26 × jul/26 (canal): −79,7 t = base ativa +38,2 · DN −67,5 · kg por PDV −50,4 (categorias por loja −35,4 · SKUs por categoria −6,2 · kg por SKU −8,8). A comparação com o ano anterior só existe a partir do mês de referência nov/26 (a base ativa de ago/25 é nula) ou com a Mtrix de set/24 a jun/25 |

### RN-58 · Frequência de compra (atendimentos por PDV)
| Campo | Conteúdo |
|---|---|
| Objetivo | Medir quantas vezes, em média, o PDV comprador foi atendido no mês |
| Definição | Atendimento = uma NF do distribuidor para o PDV no mês; devolução não conta. Frequência de compra = atendimentos ÷ PDVs positivados do recorte. No distribuidor conta as NFs daquele distribuidor; do supervisor para cima soma as NFs de todos os distribuidores do PDV, e o PDV conta uma vez (RN-10). A Mtrix entrega a frequência por SKU: as NFs de cada par distribuidor × PDV são **estimadas** (valor verdadeiro entre a maior frequência de SKU e a soma); exato quando o par tem uma linha |
| Fórmula | Par com frequências de SKU f₁…fₙ (linhas kg > 0): `atend = D·(1 − Π(1 − fᵢ/D))`, `D = α_mês × max fᵢ`, nunca abaixo de `max fᵢ`. α_mês calibrado para Σ dos pares (todas as linhas do arquivo) = `freq_total × Cód. PDV distintos` da linha de total. `frequencia(nível) = Σ atend ÷ positivados(nível)`. Categoria: a mesma conta só com os SKUs da categoria, com o mesmo α. Mínimo sem estimativa: `Σ max fᵢ ÷ positivados`. Acumulado: `Σ atendimentos dos meses ÷ Σ positivados dos meses` |
| Base de origem | Mtrix (`# Frequência de compra` por linha e na linha de total); `Produtos.xlsx` (categoria) |
| Campos usados | `# Frequência de compra`, `# Sell-Out (Quilos)`, `Cód. PDV`, `CNPJ do AD.`, `SKU`, `Ano/Mês` |
| Granularidade | par distribuidor × PDV (× categoria) × mês; agregada por nível |
| Filtros aplicáveis | segmento, categoria, distribuidor, supervisor; período (RN-59) nas séries |
| Exceções | Estimativa abaixo do canal Mtrix, com erro não mensurável; o canal do painel exclui os distribuidores sem hierarquia e por isso não é o número da Mtrix. Por PDV (aba Pontos de venda) nada: a coluna "NFs mín. no mês" e o campo `nf_min` do blob saíram em 22/09/2026 (ver Status) |
| Nulos | sem positivados = "—"; linha com frequência vazia ou < 1, linha de total sem frequência, total × PDVs longe de inteiro ou nenhum α que feche o total = a execução aborta |
| Zeros | não ocorre (frequência ≥ 1 em 100% das linhas medidas) |
| Duplicidades | RN-10 |
| Parametrização | `fontes.sellout.colunas_obrigatorias`; `regras.frequencia.{regra, populacao, alfa_busca_max}`; `validacao.frequencia_{tolerancia_inteiro, tolerancia_total, alfa_min, alfa_max}`; `painel.rotulos.{frequencia, frequencia_col, graf_freq}` (`frequencia_pdv` removido em 22/09/2026); `painel.textos.{frequencia_nota, frequencia_definicao}`; ficha de memória `frequencia`; código `dn/metrics.py::{frequencia_calibrar, frequencia_alocar, serie_nivel}` → `DN_FREQ_CALIBRACAO`, colunas `atendimentos`, `frequencia`, `atendimentos_min`, `frequencia_min` dos cubos `DN_*` |
| Responsável | Douglas |
| Status | **vigente** (Etapa 3 da frequência, 13/09/2026; ficha escrita antes do código; publicação só depois do checklist) · **Refino E1 (13/09/2026, gerado sem publicar; D14–D18 de `docs/refino_painel_proposta.md`)**: rótulos passam a sinalizar **estimativa**: card "Frequência de compra (estimativa)", coluna "Freq. compra (est.)", chave do gráfico "Frequência (estimativa)" · **22/09/2026 (Douglas, gerado sem publicar)**: a coluna **"NFs mín. no mês"** (decisão 2) **sai da tabela de Pontos de venda** ("não faz sentido pra gente"); na mesma tarde, a pedido do Douglas ("pode tirar o nf_min do blob também"), **`nf_min` saiu do blob de PDVs** (`metrics.pdvs_base_ativa` não calcula mais `nf_min_mes`; `painel.blob_pdvs` não grava a coluna), o rótulo `painel.rotulos.frequencia_pdv` e o campo `frequencia.rotulo_pdv` foram removidos do config, do JSON e do `data-inventory.json`, e a validação "freq · NFs min. no mes (blob) = fato" deu lugar a "freq · blob de PDVs sem nf_min". `NF_MIN` continua nos cubos (`frequencia_min`, `atendimentos_min`). Cards, colunas e gráfico da frequência estimada não mudam |
| Aprovação | 13/09/2026 · Etapa 1 (respostas R1–R9) e Etapa 2 (decisões 1–8b) da frequência |
| Observações | Medido em 25 meses: α de 1,088 a 1,134 nos meses fechados (1,013 no parcial set/26); com o α do mês anterior, erro no canal de 1,01% em média e 2,14% no pior mês; o mínimo subestima o canal em 6,6% a 9,7%; a união proporcional acerta 100% dos pares de uma linha (19% a 22% dos pares) e nunca sai da faixa [maior; soma]. α fora de `frequencia_alfa_min/max` = aviso (mês em andamento não é checado). Linha kg > 0 pode conter NF de devolução (não mensurável). Documentos: `docs/frequencia_etapa1_medicao.md`, `docs/frequencia_etapa2_proposta.md` |

### RN-59 · Seletor de período das séries
| Campo | Conteúdo |
|---|---|
| Objetivo | Ver os meses anteriores aos 12 exibidos sem mudar nenhum cálculo |
| Definição | Chip "Período" na barra: Últimos N meses (padrão, `painel.serie_meses_exibidos`) · Série completa · cada ano do calendário ativo (fiscal ou civil, RN-23/RN-24). Age nos gráficos de evolução, nas tabelas das séries, nas mini-linhas, na evolução por categoria e na série do RTM (só na visão histórico completo) |
| Fórmula | nenhuma: a série inteira vai embutida (compacta) e o navegador só escolhe os pontos desenhados |
| Base de origem | séries `DN_*` já calculadas |
| Campos usados | `ANO_MES`; faixas do calendário |
| Granularidade | mês |
| Filtros aplicáveis | combina com todos; o ano incompleto aparece com os meses que existem |
| Exceções | não se aplica a cards, Alavancas, Pontos de venda, Penetração, Matriz e Ano a ano (chip inativo com dica); no RTM, a visão "a partir da migração" fixa o período no corte |
| Nulos | ano sem ponto no recorte = "sem série mensal para este recorte" |
| Zeros | — |
| Duplicidades | — |
| Parametrização | `painel.serie_meses_exibidos`, `painel.periodo.{ativo, rotulo, rotulo_ultimos, rotulo_tudo, nota}`; filtro `periodo` em `painel.abas[].filtros`; `validacao.html_max_mb` |
| Responsável | Douglas |
| Status | **vigente** (Etapa 3 da frequência, 13/09/2026; publicação só depois do checklist) · **Refino E2 (13/09/2026, gerado sem publicar)**: os chips do Período ficam na barra lateral · **Refino E4a (13/09/2026, gerado sem publicar)**: o seletor Mês (parcial e fechado) entra na lateral antes do Período; o Período segue escolhendo só os meses dos gráficos até a E5 · **Refino E5 (13/09/2026, gerado sem publicar)**: o seletor de período vira **Mês · Acumulado do ano · Ano** e muda os números (D8, D26): Mês = o mês escolhido; Acumulado do ano = do início do ano (fiscal ou Ano Calendário) até o mês; Ano = anos fechados (FY25, FY26; 2025), iguais ao acumulado no último mês do ano. Janela dos gráficos: 12 meses até o mês, o acumulado ou o ano, com o botão "Série completa" dentro do gráfico. RTM e Pontos de venda mostram o mês final do período · **Refino E6 (13/09/2026, gerado sem publicar)**: o arquivo leva só os últimos `painel.janela_arquivo_meses` (25) meses da série (seletor de mês, gráficos, pacotes por mês e série do RTM); cálculo, base ativa, LY e acumulados seguem com todos os meses. Mantém o HTML estável em ~14,5 MB · **Estabilização A5 e A7 (14/09/2026, gerado sem publicar)**: modo Ano passa a listar também o **ano em curso** (o que contém o último mês da série; rótulo `painel.rotulos.per_ano_em_curso`, "FY27 · em curso", "2026 · em curso"), com os números do acumulado até o último mês; anos incompletos no início da série continuam fora (D21); **D26 revista** a pedido do Douglas (itens 4, 10 e 19 do checklist). Na aba Pontos de venda o seletor de mês lista só os meses com lista (parcial e fechado); o mês das outras abas é preservado (A7, item 26) |
| Aprovação | 13/09/2026 · Etapa 1 da frequência (decisão 6) e Etapa 2 (decisões 4 e 8) · janela do arquivo: plano da E6 aprovado pelo Douglas (opção c) |
| Observações | Revisa RN-20. Custo medido na Etapa 2: +346 KB com 24 meses antes da compactação; a série compacta omite campos nulos e aspas de números. `validacao.html_max_mb` passou de 12 para 15 (decisão 4) |

## Bloco 7 · Painéis por usuário e aba Pontos de venda (Etapa 2, 16/09/2026)

### RN-60 · Painel por usuário (recorte pela hierarquia)
| Campo | Conteúdo |
|---|---|
| Objetivo | Cada usuário do canal Distribuição recebe, na pasta dele em `Painéis Comerciais/Gerencial`, um Scorecard DN só com os dados que pode ver, no modelo dos painéis Gerenciais |
| Definição | Usuário = rótulo distinto de cada nível da Hierarquia entre os distribuidores do painel: N1 = HEAD, N2 = GERENTE, N3 = SUPERVISOR (`DIM_DISTRIBUIDOR`). O painel do usuário é o painel do canal calculado sobre a **fato recortada aos distribuidores dele** antes de qualquer cubo, JSON ou HTML; o "canal" do painel passa a ser o recorte, e o nome do canal vira o rótulo do usuário. O N1 recebe cópia byte a byte do painel do canal. Postos vagos (`[VAGO]`) também recebem painel (Q3) |
| Fórmula | `fato_u = fato[DIST ∈ distribuidores(u)]`; cubos, base ativa, acumulados, Penetração, RTM e carteira recalculados sobre `fato_u` com o mesmo código |
| Base de origem | Hierarquia (via de-para → `DIM_DISTRIBUIDOR`); Mtrix |
| Campos usados | `HEAD`, `GERENTE`, `SUPERVISOR`, `CNPJ_DISTRIBUIDOR` |
| Granularidade | usuário (rótulo) × painel completo |
| Filtros aplicáveis | dentro do painel do usuário, os filtros de sempre; o select de supervisor lista só os do recorte |
| Exceções | rótulos em `distribuicao.ignorar_rotulos` e "SEM HIERARQUIA" não geram painel; recorte sem venda até certo mês recebe o bloco do calendário da `DIM_CALENDARIO`; erro em um usuário não interrompe os demais (`distribuicao.em_erro`: continuar = publica os que passaram e sai com exit 1; abortar_publicacao = gera todos e não publica nenhum; parar) |
| Nulos | PDVs distintos não somam entre usuários (o mesmo PDV atendido por dois supervisores conta uma vez no canal); kg, R$ e NFs somam |
| Zeros | recorte sem venda no mês: cards nulos (nunca zero) |
| Duplicidades | distribuidor pertence a exatamente um supervisor, um gerente e um head |
| Parametrização | `distribuicao.{ativo, destino, niveis, prefixo, ignorar_rotulos, criar_pasta, em_erro, rotulo_canal, gravar_json}`; pasta = rótulo com `/`→`-`; arquivo `Scorecard_DN_N<n>_<slug>.html`; código `dn/distribuicao.py`, etapa 6 de `pipeline.executar`; `--usuario`, `--sem-usuarios` |
| Responsável | Douglas |
| Status | **vigente** (16/09/2026 07h21): 18 painéis publicados (1 head, 3 gerentes, 14 supervisores), md5 conferido |
| Aprovação | 16/09/2026 · plano da Etapa 2 aprovado com as recomendações Q1–Q5; política de erro `continuar` escolhida após as alternativas |
| Observações | Validações: soma N2 e N3 = canal em kg, R$ e NFs (mês a mês e por categoria) com diferença zero; vazamento (rótulo, nome, código, slug de outros usuários; CNPJ e nome Mtrix de distribuidores fora da carteira) = zero ocorrências em 18/18; painel do canal inalterado. Relatório: `docs/distribuicao_etapa2.md` |

### RN-61 · Penetração no painel por usuário: referência do canal
| Campo | Conteúdo |
|---|---|
| Objetivo | "Acima da referência" significar o mesmo no painel do head e no do supervisor |
| Definição | No recorte, o benchmark P75 por categoria (RN-30), os cortes P99 de kg/R$ por loja, o kg/R$ por loja do canal usado abaixo do mínimo de lojas (RN-34) e o fator observado (RN-34) são os do **canal inteiro**, guardados pela execução do canal; só o que é do distribuidor (lojas, penetração, kg/loja próprio, a positivar, potencial) é recalculado no recorte |
| Fórmula | as de RN-30, RN-31, RN-34 e RN-35 com `benchmark`, `corte`, `kg_loja_canal`, `fator` = valores do canal |
| Base de origem | `DN_PEN_BENCHMARK` do canal (em memória, `c["pen_canal"]`) |
| Campos usados | os de RN-30/RN-34 |
| Granularidade | categoria (referência) × distribuidor do recorte |
| Filtros aplicáveis | os da aba Penetração (oculta desde 14/09/2026) |
| Exceções | a execução de um único usuário (`--usuario`) calcula o canal antes, para ter a referência |
| Nulos | categoria sem venda no recorte no mês fechado não entra na tabela do recorte |
| Zeros | — |
| Duplicidades | — |
| Parametrização | código `dn/metrics.py::penetracao` (`c["pen_canal"]`, só com `c["recorte"]`) |
| Responsável | Douglas |
| Status | **vigente** (16/09/2026) |
| Aprovação | 16/09/2026 · Q1 da Etapa 2, recomendação aceita |
| Observações | alternativa descartada: referência da própria carteira (cada supervisor com uma régua diferente) |

### RN-62 · RTM no painel por usuário: só clientes com destino no recorte
| Campo | Conteúdo |
|---|---|
| Objetivo | Não embutir no arquivo de um supervisor clientes RTM de outros supervisores nem os sem destino cadastrado |
| Definição | No recorte, a base RTM (RN-52) fica só com os clientes cujo destino, resolvido pela chave do código do distribuidor (`regras.rtm_destino_chave: codigo`), é um distribuidor do recorte. Os 173 clientes sem destino cadastrado (RN-53) aparecem só no painel do canal. "Só de outro" passa a significar "comprou de outro distribuidor do próprio recorte": comprar de um distribuidor de outro supervisor não é visível no painel do supervisor |
| Fórmula | `base_u = base[destino_por_chave ∧ destino ∈ distribuidores(u)]`; estados como RN-52 sobre `fato_u` |
| Base de origem | `DIM_RTM`; de-para; `fato_u` |
| Campos usados | `Cód. Cliente [Distribuidor]` → `NOME_REDUZIDO`; `COD_PDV` |
| Granularidade | cliente RTM × mês, dentro do recorte |
| Filtros aplicáveis | os da aba RTM (oculta desde 14/09/2026) |
| Exceções | recorte sem cliente RTM: série do RTM com zeros e aderência nula |
| Nulos | não mensuráveis = 0 em todo recorte |
| Zeros | — |
| Duplicidades | — |
| Parametrização | código `dn/metrics.py::rtm_aderencia` (bloco `c["recorte"]`) |
| Responsável | Douglas |
| Status | **vigente** (16/09/2026) |
| Aprovação | 16/09/2026 · Q2 da Etapa 2, recomendação aceita |
| Observações | validação por usuário: estados somam os rastreáveis, não mensuráveis = 0, destinos só do recorte |

### RN-63 · Carteira de PDVs ponderados no painel por usuário
| Campo | Conteúdo |
|---|---|
| Objetivo | A carteira (RN-56) de cada usuário só com os pares dos distribuidores dele |
| Definição | No recorte, uma linha da planilha ponderada é válida pela regra de RN-56 com "painel" = distribuidores do recorte; linhas de outros distribuidores são inválidas por definição, sem aviso e sem relatório (o relatório `quality/carteira_pdv.md` é só da execução do canal) |
| Fórmula | `valida_u(par) = valida(par) ∧ dist ∈ distribuidores(u)` |
| Base de origem | planilha ponderada; `fato_u` |
| Campos usados | os de RN-56 |
| Granularidade | par distribuidor × PDV |
| Filtros aplicáveis | botões Destaque · Prime · Todos os PDVs |
| Exceções | usuário sem par válido: botões Destaque e Prime vazios |
| Nulos | — |
| Zeros | — |
| Duplicidades | — |
| Parametrização | código `dn/metrics.py::carteira` (retorno antecipado com `c["recorte"]`) |
| Responsável | Douglas |
| Status | **vigente** (16/09/2026) |
| Aprovação | 16/09/2026 · Q5 da Etapa 2, recomendação aceita |
| Observações | só os pares válidos entram no HTML: CNPJ e razão social das linhas de outros distribuidores não viajam no arquivo do usuário |

### RN-64 · Aba Pontos de venda: abertura e filtro Situação
| Campo | Conteúdo |
|---|---|
| Objetivo | Aba mais direta: abrir na lista completa e reduzir o filtro Situação ao que se usa |
| Definição | A aba Pontos de venda abre com o botão **Todos os PDVs** ativo em todos os painéis (canal e usuários), "por enquanto". O filtro **Situação** tem só quatro opções: Todos da base ativa · Sem compra no mês · Positivados no mês · Clientes RTM. As opções por categoria de RN-38 (a ativar · na janela sem compra no mês · no mês · positivados sem a categoria, 4 × 10 categorias) saem do select; a máscara PDV × categoria continua embutida e o drill da aba Penetração (oculta) continua funcionando |
| Fórmula | nenhuma: só quais opções o select mostra e qual botão abre ativo |
| Base de origem | — |
| Campos usados | `PDV_ROT.sit_cat` (JSON `penetracao.situacoes_por_categoria`) |
| Granularidade | painel |
| Filtros aplicáveis | combina com distribuidor, supervisor, mês e carteira |
| Exceções | `painel.pdv_situacoes_por_categoria: true` volta a mostrar as opções por categoria; `painel.pdv_carteira.padrao: destaque` volta a abrir em Destaque |
| Nulos | — |
| Zeros | — |
| Duplicidades | — |
| Parametrização | `painel.pdv_carteira.padrao` (todos), `painel.pdv_situacoes_por_categoria` (false); template `template.html` (`dnPdvSituacoes`, `PDV_ROT.sit_cat`), `template/data-inventory.json` (`penetracao.situacoes_por_categoria`); exemplo regerado em 16/09/2026 |
| Responsável | Douglas |
| Status | **vigente** (16/09/2026 07h16, publicado com o canal e os 18 usuários) |
| Aprovação | 16/09/2026 · Douglas: "na aba de Pontos de Vendas pode abrir em todos os PDVs por enquanto" e "deixar apenas Sem compra, positivado no mês, clientes RTM e Todos" |
| Observações | Revisa RN-56 (abertura em Destaque) e a exibição de RN-38 no select. Motivo: o usuário sem PDV ponderado abria a aba vazia e as 44 opções confundiam |

### RN-65 · Média do PDV por mês com compra (tabela de Pontos de venda)
| Campo | Conteúdo |
|---|---|
| Objetivo | Ler o tamanho médio do PDV sem depender de quantos meses da janela ele comprou |
| Definição | Coluna **"kg médio · por mês com compra"** (métrica t) ou **"R$ médio · por mês com compra"** (métrica R$) na tabela de Pontos de venda, entre "na janela" e "no mês" |
| Fórmula | `media = medida_na_janela ÷ meses_na_janela`, com `medida_na_janela` = kg (ou R$) somados nos meses da janela em que o par distribuidor × PDV teve kg > 0 e `meses_na_janela` = quantidade desses meses (RN-02) |
| Base de origem | blob de PDVs (`dn/painel.py::blob_pdvs`, colunas `kg_janela`, `rs_janela`, `meses_janela`, já existentes) |
| Campos usados | colunas 13 (kg janela), 17 (R$ janela) e 10 (meses na janela) do blob |
| Granularidade | par distribuidor × PDV, no mês da lista (parcial ou fechado) |
| Filtros aplicáveis | os da aba (mês, distribuidor, supervisor), Situação e carteira; segue a métrica (RN-43); ordenável; sai no CSV |
| Exceções | por atendimento (ticket médio) **não é calculável**: a Mtrix é mensal e o número de NFs só existe como mínimo estimado do mês (RN-58) |
| Nulos | medida na janela vazia = "—" |
| Zeros | `meses_na_janela` ≥ 1 em toda a base ativa (medido em 22/09/2026: 132.470 pares, mínimo 1, máximo 6, nenhum zero); a divisão nunca é por zero |
| Duplicidades | RN-10 |
| Parametrização | nenhuma; calculada no navegador (`template/template.html`, `dnPdvMedia`), sem campo novo no JSON nem no `data-inventory.json` |
| Responsável | Douglas |
| Status | **vigente** (22/09/2026, gerado sem publicar) |
| Aprovação | 22/09/2026 · Douglas: média por **meses com compra** (não pelos 6 meses fixos da janela) |
| Observações | Pedido de 22/09/2026 ("senti falta de uma coluna com valor médio ou peso médio, dependendo da métrica"). Nas tabelas de Supervisores e distribuidores a leitura equivalente já existe ("kg / PDV" e "R$ / PDV", medida do mês ÷ PDVs compradores) |

---

*65 fichas (22/09/2026: + RN-65 média do PDV por mês com compra; revisões anotadas em RN-44 (distribuidor na Visão Geral) e RN-58 (coluna "NFs mín." retirada da tabela de PDVs); CSV das tabelas sem tags HTML, só template):*
*64 fichas (16/09/2026: + RN-60 painel por usuário, RN-61 referência da Penetração no recorte, RN-62 RTM no recorte, RN-63 carteira no recorte, RN-64 aba Pontos de venda; revisões anotadas em RN-56 e, por referência, RN-38):*
*59 fichas (13/09/2026: + RN-58 frequência de compra e RN-59 seletor de período; revisões em RN-11, RN-20, RN-44 e RN-52):*
*57 fichas: 53 vigentes · 1 aprovada, não implementada (RN-12 conceitos de cliente — status "aprovada" confirmado pelo Douglas em 11/09/2026) · 3 declaradas (F1: RN-06, RN-07, RN-09, RN-43, RN-55; F2: RN-22, RN-47; F3: RN-46; F4: RN-16, RN-37, RN-44 e o aviso de RN-15; F5: RN-23 (rótulos), RN-24, RN-25; F6: RN-19, RN-27, RN-28 (régua oficial), RN-30, RN-31, RN-34, RN-35, RN-36, RN-45; F7: RN-32, RN-33, RN-38, RN-41; F8: RN-42, RN-50 completa; F9: RN-48; F10: RN-49, com registros da D-A em RN-34 e dos pisos D1/R4 em RN-48; carteira de PDVs ponderados: RN-56; F11: RN-57 e a aba Alavancas em RN-50). Nenhuma regra foi inventada nesta fase; cada ficha cita
a decisão de origem. Próxima revisão: ao fim de cada fase F1–F10, marcando as fichas implementadas como vigentes.*
