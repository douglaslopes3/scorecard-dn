# Evolução · Fase F10 — rastreabilidade por número (11/09/2026)

Executada após a F9 (`docs/evolucao_f9.md`, publicada 11/09 10h49) e a aprovação da proposta da F10 pelo Douglas em 11/09/2026:
P1–P6, a cobertura de 26 fichas, as 8 validações e Q1–Q7 pelas recomendações (Q1 marca **ⓘ** · Q2 modal · Q3 copiar · Q4 memória por
coluna e, linha a linha, nas colunas de oportunidade · Q5 extrato das RN embutido · Q6 piso D1 ≥ 30 PDVs no mês de comparação · Q7 piso
R4 ≥ 20 clientes). Depois do passo 1 (fichas no config, conferidas contra a tela), o Douglas aprovou a lista e a **opção 1 da D-A**.
Regra implementada: **RN-49** (vigente); registros novos em **RN-34** (D-A) e **RN-48** (pisos). Sem regra nova. Última fase da rodada.

**Publicado em 11/09/2026 às 12h42** (execução `20260911-123909-33ceca`, 115 validações ok, md5 `d6ded1fdacb9959cd03c95ca31ac6cdb`, 11.157.101 bytes — o mesmo da prova final `20260911-121229-d1cb59`), após o "checklist ok" do Douglas.

## (a) O que foi alterado

### Config e pipeline

| Arquivo | Mudança |
|---|---|
| `config/config.yaml` | bloco **`painel.memoria`**: `ativo`, `marca: "ⓘ"`, `copiar`, `tabelas.{por_coluna, por_linha}` (7 colunas de oportunidade), `extrato_rn`, `tolerancia` (a da F9), `textos` (título, botões, rótulos das 8 partes, períodos, texto das Definições), `fontes_rotulos` e **26 fichas** — id, RN, título, indicador, abas, período, fórmula, parcelas, `conta`/`conta_rs`, `conta_soma`/`conta_soma_rs` (níveis acima do distribuidor, onde o número é soma), `confere`/`confere_rs` (div100 · sub · div · mul · mul3 · gap), `perspectiva` (toggle de calendário), fonte, curated, `liga` (14 cards e 75 colunas) e nota. **Pisos**: `piso` na D1 (≥ 30 PDVs no mês de comparação) e na R4 (≥ 20 clientes). **D-A**: `painel.rotulos.pen_loja_usado` / `pen_loja_nivel` e `painel.textos.pen_soma` |
| `dn/memoria.py` (novo) | avaliador das conferências (as mesmas 6 operações do navegador), extrato das RN citadas lido de `docs/regras_negocio.md`, fontes do config, linha do RTM, **esperado** no recorte do canal (50 chaves: cards da Visão geral, cards da Penetração × 10 categorias, RTM), lint de termos vetados (o rótulo obrigatório do potencial é permitido) e o JSON embutido `memoria.json` |
| `dn/metrics.py` | **D-A**: no bloco dos níveis de `penetracao`, a linha do distribuidor passa a levar o kg/R$ por loja **usado** no potencial (truncado no P99 ou média do canal abaixo de 30 lojas); acima dele segue a média simples do nível |
| `dn/resumos.py` | tipo `extremo` aceita `piso` (no próprio campo ou na série, no mês de comparação) |
| `dn/painel.py` | `pen_nivel_cat[].n_dist` (distribuidores somados no nível); `penetracao.{sub_loja_usado, sub_loja_nivel, texto_soma}`; `J["memoria"]` (aborta com termo vetado) |
| `dn/pipeline.py` · etapa 4 | **8 validações novas**: `memoria · fichas do config no HTML`, `aritmetica = curated` (17.702 conferências: cards de 3 segmentos em t e R$, 1.050 linhas nível × categoria no grão, RTM, 5 cubos cobertura ÷ base ativa, potencial e regime dos níveis = Σ distribuidores e **D-A nos 710 pares**), `toda parcela existe no inventario`, `RN citada existe e esta vigente`, `fonte = config`, `todo numero marcado tem ficha`, `textos sem termos vetados`, `modal no HTML`. As conferências `resumos · distribuidores` e `resumos · rtm` passaram a aplicar o piso (e a D1 confere também a maior alta). 107 → **115** |
| `template/data-inventory.json` | 717 → **733** campos |

### Template

| Onde | Mudança |
|---|---|
| Modal `#dnmem` | irmão do drill; título com o número, subtítulo com o recorte da linha; **oito partes**: regra (RN e título), período, filtros ativos, fórmula, **conta com os números da tela**, conferência, fonte (base → arquivo → colunas da RN → tabelas curated), data dos dados, observação; extrato da RN (objetivo, definição, fórmula) em `<details>`; botão **Copiar** (as partes em texto) e Fechar |
| Botões ⓘ | 9 por bloco de segmento na Visão geral (6 cards, comparativos, acumulado e variação do acumulado); 4 cards da Penetração; card Aderência do RTM; cabeçalho de toda coluna ligada (não dispara a ordenação, nem pelo teclado); linha a linha nas colunas lojas a positivar, potencial de entrada e em regime (t e R$), a ativar e sem compra no mês; cada frase de resumo |
| Conferência na tela | a conta declarada é refeita com os números exibidos; tolerância = a da F9 + meia unidade de arredondamento de cada número; verde "a conta fecha", laranja com o detalhe se não fecha. Sem filtros, compara também com o esperado do pipeline |
| D-A | subtítulo da coluna kg/R$ por loja: "usado no potencial" no distribuidor, "média do nível" acima (refeito na troca de nível e de grão); legenda do card de potencial e dica da nuvem da Matriz: multiplicação no distribuidor, "soma de N distribuidores do nível" acima |
| Resumos | piso no motor `extremo` (espelho do Python); o piso aparece no tooltip e na memória da frase |
| Definições | parágrafo "Memória de cálculo (F10)" e o extrato das 26 RN citadas |

### Docs

`docs/regras_negocio.md` (RN-49 **vigente**; D-A em RN-34; pisos em RN-48; 51 vigentes · 1 aprovada (RN-12) · 3 declaradas); `README.md`
(changelog, rastreabilidade); `docs/RETOMADA.md` (§1, §5, §6 armadilhas da memória e da D-A, §7, §8); este relatório.

## (b) Por quê

A.14 e §21 do pedido (RN-49): todo número auditável a um clique, com a mesma memória que a F9 deu às frases. O modelo é o da F9 — ficha
declarada no config, motor no navegador, espelho em Python validado na etapa 4 —, para que texto, fórmula e ligação mudem sem código.

A conferência das fichas contra a tela, feita antes do template, achou o **achado A**: o kg/R$ por loja exibido não era o que multiplicava
o potencial. Em ago/26, 316 das 536 linhas distribuidor × categoria com lojas a positivar mostravam um kg/loja diferente do usado, e em 132
(62 nas foco) a conta com o número da tela não reproduzia o potencial — por exemplo, Pellah × Amendoim mostrava 10,3 kg e o cálculo usa
3,8 kg (exclusão das lojas acima do P99). Uma memória de cálculo sobre esse número mostraria uma conta errada. O potencial em si sempre
esteve certo; a D-A corrigiu o que a tela mostra ao lado dele.

Os pisos respondem às duas leituras que a F9 registrou: a D1 premiava a Propec (+7.550%, de 2 para 153 PDVs) e a R4 apontava a VJS
(1 cliente).

## Resultados em ago/26 (recorte do canal, métrica t)

| Onde | Memória (conta como aparece) | Conferência |
|---|---|---|
| Visão geral · DN | 71.478 ÷ 124.600 × 100 = 57,4% | fecha |
| Visão geral · sem compra | 124.600 − 71.478 = 53.122 | fecha |
| Visão geral · kg/PDV | 1.199,9 t ÷ 71.478 PDVs = 16,79 kg/PDV | fecha |
| Visão geral · acumulado | 13.115,8 t e 150.249 PDVs distintos em Ano fiscal 2026 (set/25–ago/26); no civil, 8.841,6 t e 137.389 em Ano 2026 | origem dita |
| Penetração · canal × Amendoim | penetração 39.832 ÷ 71.478 × 100 = 55,7%; potencial "soma de 71 distribuidores do nível = 23,4 t/mês" | fecha / soma |
| Penetração · Pellah × Amendoim | (71,4% − 30,5%) × 766 ÷ 100 = 313 · 313 × 3,8 kg × 34,4% = 0,4 t/mês · 313 × 3,8 kg = 1,2 t/mês · 766 − 234 = 532 · em R$: 313 × 120 × 34,4% = 12.966/mês | todas fecham |
| Matriz · supervisor | "…soma de 5 distribuidores do nível…: Potencial de entrada 3,2 t/mês" (RJ/ES × Amendoim) | soma |
| RTM · aderência | 213 ÷ 1.589 × 100 = 13,4% · de outro 93 · não compraram 1.283 · ativados parados 100 de 313 | fecha |
| Filtro supervisor (Murilo Cunha) · DN | 1.009 ÷ 1.196 × 100 = 84,4% | fecha |
| Resumo D1 (com piso) | maior queda MAM Feira de Santana (−82,5%); maior alta **Francal Imperatriz (+74,1%)** · piso na memória | = curated |
| Resumo R4 (com piso) | **Claumar, 106 de 109 clientes sem compra (97,2%)** | = curated |

## Correções feitas durante a execução

| Sintoma | Causa | Correção |
|---|---|---|
| 4 fichas não fechavam na conferência do passo 1 | fui eu que as escrevi errado: `% cobertura por categoria` citava `lojas` (a linha traz `cobertura_pdv`); RTM dividia por "mensuráveis" sem parcela; DN e sem compra sem o resultado nas parcelas | corrigidas no config antes da lista ir para aprovação; a conferência passou a exigir que toda conta só cite parcelas declaradas |
| exemplo da proposta "12.824 × 9,3 kg × 34,4% = 23,4 t" | no canal o potencial é soma dos distribuidores (kg implícito 5,29 kg); essa conta dá 41,0 t | achado A → D-A; fichas de potencial com `conta_soma` |
| no calendário civil, o modal do acumulado acusava "diferente do esperado" | o esperado é da perspectiva padrão (fiscal) e a tela troca as parcelas para as civis | a comparação pula parcela trocada pelo toggle |
| com filtro no distribuidor, a coluna seguia "média do nível" | o cabeçalho só era refeito na troca de métrica | refeito também na troca de nível da Penetração |

## Prova

| Checagem | Resultado |
|---|---|
| Passo 1 (fichas inertes no config) | md5 do HTML = publicado (`7f5c67a8…`), 107 ok |
| Completa 1 (`20260911-120308-06e45f`, `--regerar-exemplo --sem-publicar`) | byte a byte ok; **115 ok**; HTML 10,6 MB; números iguais (124.600 · 71.478 · 57,4% · 1.199,9 t · 71 · RTM 1762/1589/173) |
| Completa final (`20260911-121229-d1cb59`, `--regerar-exemplo --sem-publicar`) | exemplo regerado; byte a byte ok; **115 ok**; HTML **10,6 MB**; números iguais |
| Navegador (servidor local) | 26 fichas, 26 RN, 50 esperados carregados; contas da tabela acima; ⓘ do cabeçalho não reordena; potencial em R$ fecha; frases D1/R4 com o piso; Matriz com soma no grão supervisor e multiplicação no distribuidor; subtítulo da coluna kg/loja alterna "média do nível" → "usado no potencial" → "média do nível" com o filtro da Pellah; acumulado no calendário civil sem falso alarme; 0 NaN; **console sem erro** |
| Tamanho | 10,5 → **10,6 MB** (+0,1 MB; limite 12) |

## (c) O que ficou pendente

- **RN-12 (conceitos de cliente):** o status "aprovada" foi confirmado pelo Douglas em 11/09/2026; o rodapé do dicionário, que a
  contava como vigente, foi corrigido (51 vigentes · 1 aprovada · 3 declaradas).
- Acumulado e comparativos não têm conta a refazer na tela (o número vem do pipeline); a memória diz a origem, e as validações de
  acumulados e da série já os conferem.
- Depois da rodada: PDVs ponderados (proposta P1–P8/Q1–Q7 adiada, planilha corrigida em 11/09) e F11 Alavancas (candidata). Pendências de
  dado inalteradas (Mtrix set/24 a jun/25, CNPJ do destino RTM, datas de cadastro, 4 destinos RTM sem cadastro).

## (d) Checklist para você

Abra `data/dn/painel/Scorecard_DN_2026-08.html` (Ctrl+F5) — é o gerado, ainda não publicado.

- [ ] Visão geral: o ⓘ ao lado de "% de cobertura (DN)" abre a memória com 71.478 ÷ 124.600 × 100 = 57,4% e "a conta fecha".
- [ ] "Copiar" põe a memória na área de transferência (cole num e-mail).
- [ ] Penetração, categoria Amendoim, sem filtro: o card de potencial diz "soma de 71 distribuidores"; o ⓘ confirma.
- [ ] Filtre o distribuidor Pellah: o card mostra 313 × 3,8 kg/loja × fator 34,4%; a coluna kg/loja diz "usado no potencial".
- [ ] Na tabela por distribuidor, o ⓘ de uma linha (lojas a positivar, potencial, a ativar) abre a conta daquela linha.
- [ ] O ⓘ de um cabeçalho abre a ficha da coluna e não reordena a tabela.
- [ ] Distribuidores: a frase de maior alta aponta Francal Imperatriz; RTM: o destino com maior gap é a Claumar.
- [ ] Definições: o parágrafo "Memória de cálculo (F10)" e o extrato das 26 RN.
- [ ] Console (F12) sem erro.
- [ ] Com o ok: `python run_dn.py --mes 2026-08` publica.
