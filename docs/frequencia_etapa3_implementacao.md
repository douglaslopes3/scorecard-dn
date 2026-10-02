# Frequência de compra · Etapa 3 · Implementação

**Data:** 13/09/2026 · **Base:** Etapa 1 (`docs/frequencia_etapa1_medicao.md`, respostas R1–R9) e Etapa 2
(`docs/frequencia_etapa2_proposta.md`, decisões 1–8b). **Nada foi publicado:** todas as execuções usaram `--sem-publicar`; o
painel no ar continua sendo o de 11/09/2026 16h53. Antes de mexer, o código, o config, o template e os docs foram copiados para o
scratchpad (`…\scratchpad\bk0\`, 70 arquivos).

## 1. O que mudou (a) e por quê (b)

| Arquivo | O que mudou | Por quê |
|---|---|---|
| `config/config.yaml` | `# Frequência de compra` passou a ser coluna **obrigatória** e `# PDVs Positivados` virou opcional · `regras.frequencia` (regra, população, busca do α) · `regras.rtm_destino_chave: codigo` · `validacao.html_max_mb: 15` e `validacao.frequencia_*` (tolerâncias e faixa do α) · `painel.periodo` · rótulos e textos da frequência e do RTM por supervisor · filtros `periodo` nas abas com série e `supervisor` + `periodo` no RTM · ficha de memória `frequencia` | R4, decisões 1–8b; nada hardcoded |
| `dn/extract/sellout.py` | Lê a frequência de cada linha (`FREQ`) e a da linha de total (`freq_total`); a coluna PDVs Positivados virou opcional; frequência vazia ou menor que 1 rejeita o arquivo | RN-58 |
| `dn/transform/fato.py` | `FATO_SELLOUT` ganha `FREQ`; a reconciliação confere, arquivo a arquivo, que frequência do total × PDVs distintos dá um inteiro (senão aborta) | Decisão 6 |
| `dn/pipeline.py` | Grava `SELLOUT_GABARITO` (linha de total de cada arquivo) na curated · **13 validações novas** (§3) · contagem da tabela `rtm_serie` com as linhas por supervisor | Calibração lida da curated, nunca do Excel |
| `dn/metrics.py` | `frequencia_calibrar` (α do mês por bisseção sobre todas as linhas do arquivo) · `frequencia_alocar` (estimativa por par distribuidor × PDV e por par × categoria; mínimo sem estimativa) · `atendimentos`, `frequencia`, `atendimentos_min`, `frequencia_min`, variações % e acumulado (Σ NFs ÷ Σ positivados) em todos os cubos `DN_*` · `nf_min_mes` na base ativa · RTM: destino pelo código do distribuidor e série por supervisor do destino (`DN_RTM_SUP_MES`; aborta se um destino tiver filiais de supervisores diferentes) · tabela `DN_FREQ_CALIBRACAO` | RN-58, RN-52, RN-44 |
| `dn/painel.py` | Frequência nos KPIs, nas tabelas, nas séries (só o valor) e no acumulado · série inteira embutida em formato compacto (`serie_js`: chaves curtas, números sem aspas, nulos omitidos) · coluna `nf_min` no blob de PDVs · blocos `periodo_sel` e `frequencia` · RTM com `sup_id`, `serie_sup`, `por_supervisor_json` e as notas | Decisões 2–5, 8, 8a |
| `dn/tabelas.py` | `serie_js` fora das linhas de tabela · frequência acumulada só na tabela de supervisores · `rtm_serie` = canal + supervisores | Tamanho do HTML |
| `template/template.html` | Card **Frequência de compra** (7º card) com Δ mês anterior, L3M e LY · frequência no acumulado do ano · coluna **Freq. compra** e grupo **Δ Frequência** nas tabelas de clusters, supervisores e distribuidores · 3ª chave do gráfico **Frequência** · coluna **NFs mín. no mês** em Pontos de venda · chip **Período** (Últimos 12 meses · Série completa · anos fiscais ou civis) aplicado a gráficos, tabelas das séries, mini-linhas, evolução por categoria e série do RTM (esta só na visão histórico completo) · RTM: cards, série, destinos, clientes, drills, resumos e memória recortados pelo supervisor do destino, com nota · textos da aba Definições · **exemplo regerado** (`--regerar-exemplo`) | Decisões 2–8a |
| `template/data-inventory.json` | 60 campos novos | Contrato de formato |
| `docs/regras_negocio.md` | RN-58 e RN-59 novas; revisões em RN-11, RN-20, RN-44 e RN-52 | Ficha antes do código |

## 2. Números (execução `--mes 2026-08 --sem-publicar`, 13/09/2026 13h35–13h40)

Também rodei sem `--mes` (set/26 em andamento, 13h41–13h45): 138 validações ok, α de set/26 = 1,0133 (fora da faixa, sem aviso
porque o mês está em andamento, decisão 6), HTML de 11,7 MB, não publicado. Essa foi a última execução, então a curated está em set/26.

| Item | Publicado (11/09) | Agora | Motivo |
|---|---:|---:|---|
| Meses na série calculada | 14 (jul/25–ago/26) | **24** (set/24–ago/26; set/26 em andamento) | 25 bases reextraídas |
| Base ativa ago/26 | 124.600 | **124.800** | Linhas novas DIERO e PELLAH (aceito na pergunta 7) |
| DN ago/26 | 57,4% | **57,3%** | Idem |
| Positivados · volume · distribuidores | 71.478 · 1.199,9 t · 71 | 71.478 · 1.199,9 t · 71 | Sem mudança |
| RTM clientes · mensuráveis · não mensuráveis · aderência | 1.762 · 1.589 · 173 · 13,4% | iguais | A chave por código dá o mesmo resultado |
| RTM "já compraram algum dia" | 313 | **324** | Histórico mais longo (desde set/24) |
| Alavancas canal ago × jul/26 | −79,7 t (DN −67,5) | **−84,0 t** (DN −72,0) | Base ativa de jul e ago/26 com DIERO e PELLAH |
| **Frequência de compra ago/26 (canal do painel)** | — | **1,25** (89.160 NFs estimadas ÷ 71.478 PDVs); mínimo sem estimativa 1,14 | RN-58 |
| α ago/26 · faixa nos 24 meses | — | 1,1165 · 1,0879 a 1,1336 | Calibração fecha com a Mtrix (erro 0,0000 NF) |
| Frequência por distribuidor · supervisor · categoria (ago/26) | — | 1,07–1,67 · 1,16–1,38 · 1,04–1,20 | — |
| HTML | 11,0 MB | **12,2 MB** (limite 15 MB) | Série inteira compacta + frequência + RTM por supervisor |
| Validações | 124 | **138** | 13 novas + a contagem de `rtm_serie` ajustada |

Frequência do canal do painel (1,2474) × Mtrix (1,2489): a Mtrix inclui os 10 distribuidores sem hierarquia, que ficam fora do
painel (RN-13), e as linhas com kg ≤ 0.

## 3. Validações novas (todas ok)

`freq · total x PDVs inteiro` (25 arquivos, maior distância 4,4e-11) · `freq · Σ estimativa = total Mtrix` (24 meses) ·
`freq · minimo <= estimativa <= soma (pares)` (1.450.330 pares) · `freq · par de uma linha = frequencia da linha` (300.389) ·
`freq · categoria <= par` (3.924.706) · `freq · card canal = curated = recalculo` · `freq · Σ distribuidores = canal (NFs)` ·
`freq · NFs min. no mes (blob) = fato` · `periodo · serie inteira embutida` · `periodo · serie compacta = serie do JSON` ·
`RTM · Σ supervisores do destino = canal` (10 supervisores × 24 meses) · `RTM · 1 supervisor por destino mensuravel` (23 destinos) ·
`RTM · destino pela chave do codigo` (1.589). Mais o aviso (não aborta) de α fora da faixa, que não disparou.

Conferência no navegador, no HTML gerado e servido localmente pelo scratchpad: nenhum erro no console; nenhum gráfico com NaN nos 4
períodos × 3 chaves; o seletor desenha 12, 24 e 12 (FY25) pontos; ao trocar para ano civil, os chips viram 2024 · 2025 · 2026;
RTM com o supervisor MURILO CUNHA dá 280 clientes · 19 do destino · 11 de outro · 250 sem compra, igual à medição da Etapa 2;
drill "Comprou do destino" com esse supervisor = 19 clientes; memória de cálculo da frequência: "a conta fecha com os números da
tela".

## 4. Pendências (c)

1. **Publicar:** ao aprovar o checklist, rodar `python run_dn.py --mes 2026-08`. A última execução foi com set/26 em andamento, e ela não publica sozinha.
2. **Nome reduzido da SBM** está "SBN" no de-para (você corrige). Não altera nenhum número: a SBM fica fora do painel.
3. **Aviso desatualizado no log da ingestão:** `RTM_DePara_Transicao.xlsx: sem coluna de CNPJ do destino — destino casado por NOME` continua saindo do leitor de cadastros, mas o destino agora é casado pelo código (o log do cálculo diz isso). Corrigir o texto invalida o cache dos leitores e força 12 minutos de reingestão; ficou para a próxima vez que o leitor mudar.
4. Pendências anteriores do RETOMADA seguem valendo.

## 5. Checklist para você testar antes de publicar (d)

Abrir `data/dn/painel/Scorecard_DN_2026-08.html` (gerado às 13h40 com `--mes 2026-08`).

**Frequência**
- [ ] Visão geral: 7º card "Frequência de compra" = **1,25**, com a nota "estimativa calibrada no total Mtrix" e Δ vs mês ant. **−3,0%** · vs L3M · vs LY **−0,9%**.
- [ ] ⓘ do card: conta "89.160 NFs estimadas ÷ 71.478 PDVs = 1,25 · mínimo sem estimativa: 81.806 ÷ 71.478 = 1,14" e "a conta fecha".
- [ ] Linha "Acumulado no ano" mostra a frequência acumulada (FY26 **1,25**) e o Δ vs FY25.
- [ ] Escolher um supervisor: o card muda (ex.: 1110 MURILO CUNHA).
- [ ] Distribuidores: colunas "Freq. compra" e "Δ Frequência"; ordenar pela frequência (1,07 a 1,67).
- [ ] Clusters e supervisores: as mesmas colunas.
- [ ] Gráfico de evolução: 3º chip "Frequência" desenha as colunas e a tabela "Frequência · NFs por PDV comprador".
- [ ] Pontos de venda: última coluna "NFs mín. no mês", vazia para quem não comprou no mês.
- [ ] Definições: parágrafo da frequência com o parâmetro de ago/26 (1,1165) e a faixa (1,0879 a 1,1336).

**Período**
- [ ] Barra: "Período · Últimos 12 meses · Série completa (set/24–ago/26) · FY25 · FY26".
- [ ] Evolução: "Série completa" mostra 24 meses; FY25 mostra set/24 a ago/25; o título do bloco acompanha.
- [ ] Trocar para "Ano civil": os chips viram 2024 · 2025 · 2026; "2024" mostra só set a dez/24.
- [ ] Mini-linhas das tabelas e o cabeçalho da coluna acompanham o período.
- [ ] Penetração, Matriz, Alavancas e Pontos de venda: chip Período esmaecido ("não se aplica aqui").
- [ ] Recarregar a página: o período escolhido fica salvo.

**RTM**
- [ ] Sem supervisor: números iguais aos de hoje (1.762 · 1.589 · 13,4% · 213 · 93 · 1.283).
- [ ] Escolher 1110 MURILO CUNHA: Base 280 · aderência 6,8% · 19 do destino · 11 de outro · 250 não compraram · nota dos 173 sem supervisor.
- [ ] Série, destinos e clientes só desse supervisor; clicar em "compraram do destino" abre 19 clientes, com o supervisor no título.
- [ ] Supervisor sem cliente RTM (1130 FABIO MONTEIRO, 1210 [VAGO], 1310 ARLINDO NASCIMENTO ou 1320 [VAGO - OLIVEIRA]): cards com "—" e a nota "sem clientes RTM com destino deste supervisor".
- [ ] Visão "Histórico completo" + "Série completa": série de 24 meses; visão "A partir da migração": chip Período esmaecido.

**Publicação**
- [ ] Rodar `python run_dn.py --mes 2026-08` (publica): esperar 138 validações ok e "publicado", com o HTML de 12,2 MB.
