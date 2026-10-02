# Estabilização do painel · 14/09/2026 · A1, A2, A3, A5, A7, A8 e A9

Etapa aberta após o checklist do refino (`docs/refino_checklist.md`, respondido pelo Douglas em 14/09/2026). Cada item foi
apresentado no formato de aprovação e decidido um a um. **Publicado em 14/09/2026 às 22h03** ("checklist ok, pode publicar" do Douglas):
`python run_dn.py`, execução `20260914-214902` (14 min, sem reingestão), 120 validações ok, renderizador validado byte a byte,
md5 `cffa6784…` (15.600.948 bytes) igual ao da prova, copiado para `Painéis Comerciais/DN/Scorecard_DN.html` (único arquivo da pasta).

## Decisões desta etapa

| Item | Decisão | Origem |
|---|---|---|
| A1 · gráfico "Evolução por categoria" | APROVADO | item 17 do checklist, Fase 2 do pedido |
| A2 · cards Volume do mês / kg por PDV (opção a: regra geral, inclui RTM) | APROVADO | Fase 3 |
| A3 · ocultar Penetração e RTM; temas mantidos nas Definições | APROVADO | Fase 4 |
| A4 · filtro de Gerente Regional | MANTER PARA O BACKLOG (estudo na §5) | Fase 5 |
| A5 · ano em curso no modo Ano (D26 revista) | APROVADO | itens 4, 10 e 19 |
| A6 · RTM "a partir da migração" | NENHUMA ALTERAÇÃO (a resposta do item 29 era só sobre ago/26) | item 29 |
| A7 · seletor de mês da aba Pontos de venda só com os meses com lista | APROVADO | item 26 |
| A8 · janela da base ativa **5 → 6 meses**, para tudo (fator incluído) | APROVADO | regra de negócio nova, pedida pelo Douglas ao iniciar o Bloco 5 |
| Itens 31 e 33 | OK; publicação condicionada ao "checklist ok" | checklist |
| A9 · tabela do bloco Evolução por categoria fora do período (cabeçalho um passo atrasado) | APROVADO | defeito achado pelo Douglas no checklist de tela, 14/09 |

## (a) O que mudou

| Onde | Mudança |
|---|---|
| Visão Geral · Evolução por categoria (A1) | `dnEvoDraw()` procurava `#aba-evolucao` (aba removida na E3); passou a `#aba-visao`. Chips, botões "todas"/"só as foco", linha "Outras categorias" e gráfico voltam a aparecer acima da tabela. Nenhuma outra mudança: motor, dados, cores, config e estado `evo=` são os da F3/F4/E4b |
| Cards (A2) | CSS `.k span` → `.k>span`: a regra do título deixa de alcançar os spans internos. Número e subtítulo de Volume do mês, kg / PDV comprador e dos cards do RTM (Não compraram, Compraram de outro, Ativados parados, subtítulos de Base RTM e Aderência) passam ao padrão (21 px azul / 9,5 px cinza). Formatos numéricos, fórmulas e valores inalterados |
| Abas (A3) | `painel.abas[].oculta: true` em `penetracao` e `rtm`; botão com `hidden` (`.dntabs .tab[hidden]{display:none}`); `DNABAS` ignora botões ocultos (URL `#aba=rtm`/`#aba=penetracao` e setas do teclado caem na Visão Geral); campo `aba.oculta` no JSON e no inventário; validação nova `abas · ocultas = config`. Templates, motores, dados, validações de conteúdo e Definições (temas Penetração e RTM) mantidos. Reversível: `oculta: false` |
| Período · modo Ano (A5) | `dnAnosFechados()` inclui o ano que contém o último mês da série, marcado `curso`; rótulo `painel.rotulos.per_ano_em_curso` ("{ano} · em curso") no seletor e na linha de filtros ativos (`dnPerAnoRot`); números = acumulado até o último mês (nada somado no navegador); anos incompletos no início da série continuam fora (D21). Definições: linha do Ano reescrita |
| Pontos de venda · seletor de mês (A7) | Na aba, o seletor lista só os meses com lista (parcial e fechado) e mostra o mês exibido; `DNE.mes` das outras abas é preservado; aviso da lista mantido |
| Janela da base ativa (A8) | `regras.janela_base_ativa_meses: 6` e `regras.potencial.janela_fator_meses: 6`. Segue automaticamente: base ativa, sem compra, DN, lista de PDVs, carteira (nota "fora da lista"), base elegível, ativação, recorrência, máscara PDV × categoria, cabeçalho, Definições, relatório de qualidade e validações. Textos literais atualizados no config (nota da carteira e 2 fichas da memória desligada). Primeiro mês com DN: fev/25 (era jan/25) |
| Tabela do bloco Evolução por categoria (A9) | `DnTabela.remetrica(id)` aceita remontar uma só tabela; `dnEvoDraw()` chama `remetrica('evo')` (cabeçalho e linhas) em vez de `render('evo')` (só linhas). Antes, ao trocar período, mês ou Série completa, o cabeçalho ficava com os meses do período anterior e as células com os do novo (no Acumulado, 12 colunas × 7 células). Defeito de ordem de execução da E5 |
| Documentos | `docs/regras_negocio.md` (RN-02, RN-46, RN-50, RN-59), `docs/evolucao_etapa1_auditoria.md` (D28), `docs/refino_painel_proposta.md` (D5, D6, D14, D26, andamento), `README.md`, `docs/RETOMADA.md`, este relatório |

Arquivos modificados: `template/template.html`, `config/config.yaml`, `dn/painel.py`, `dn/pipeline.py`, `template/data-inventory.json`
(+2 campos: 819), `template/Scorecard_DN_base.html` e `template/example-data*.json` (regenerados), documentos acima.
Backup pré-Bloco 5: scratchpad da sessão, pasta `backup_pre_B5`. Componentes reaproveitados: motor `dnEvo*` (A1), padrão dos cards
(A2), mecanismo `painel.abas` + fallback de `dnAbaAbrir` (A3), dados do modo Acumulado (A5), `dnPeriodoUI` (A7), chave única da
janela (A8). Nenhum componente novo.

Diferenças entre o aprovado e o implementado: nenhuma. A validação nova da A3 (119 → 120) e o efeito da A2 no RTM estavam na proposta.

## (b) Por quê

Item 17 do checklist e Fase 2: o gráfico sumiu por regressão da E3, não por decisão (A1). Fase 3: dois KPIs centrais ilegíveis por
uma regra de CSS (A2). Fase 4: versão final sem Penetração e RTM na navegação, sem perder o trabalho (A3). Itens 4, 10 e 19: ver o
ano vigente na lista de anos (A5). Item 26: seletor coerente com o que a aba mostra (A7). A8: definição de negócio da base ativa
passa a 6 meses; uma janela só para todos os denominadores (princípio da D28).

## (c) Resultado da execução

Execução `20260914-202306-425633` (`--regerar-exemplo --sem-publicar`), 31 min (reingestão completa de ~1,5 min por mudança de
config; cálculo mais lento nesta máquina que nas execuções de 13/09). **120 validações ok**, 12 avisos (os 11 conhecidos + o aviso
de ingestão do RTM sem CNPJ do destino). HTML **14,9 MB** (15.600.797 bytes; limite 15 MiB = 15.728.640), md5 `c6d89995…`.

| Indicador | Antes (janela 5, 13/09) | Depois (janela 6, 14/09) |
|---|---|---|
| ago/26 · base ativa | 124.800 | **129.595** |
| ago/26 · sem compra no mês | 53.322 | **58.117** |
| ago/26 · positivados | 71.478 | 71.478 |
| ago/26 · DN | 57,3% | **55,2%** |
| ago/26 · volume · distribuidores · frequência | 1.199,9 t · 71 · 1,25 | iguais |
| ago/26 · lista de PDVs (pares) | 129.359 | 134.426 |
| set/26 parcial · base ativa · DN | 120.742 · 13,0% | **125.955 · 12,4%** |
| set/26 parcial · positivados · volume | 15.644 · 201,2 t | iguais |
| RTM (base / mensuráveis / não mensuráveis · aderência ago/26) | 1.762 / 1.589 / 173 · 13,4% | iguais |
| Penetração ago/26 · base elegível (canal) | 124.800 | 129.595 (janela mar/26 a ago/26) |
| Primeiro mês com DN | jan/25 | fev/25 |
| Ano Calendário 2026 até ago/26 · PDVs distintos | 137.592 | 137.592 |
| Validações | 119 | 120 |
| HTML | 14,5 MB | 14,9 MB |

Os números de 6 meses coincidem com a medição prévia feita no staging antes da aprovação da A8 (o mesmo script reproduzia
124.800 · 71.478 · 57,3% com 5 meses).

Conferido no navegador (cópia servida localmente, Chrome, sem erro no console):
- A1: chips das 10 categorias (★ nas 4 foco) + Outras + "todas"/"só as foco"; 7 linhas ao abrir; "só as foco" → 4 linhas + Outras (5 traçados); Σ linhas + Outras = total em set/26 (201,2 t); "todas" → Outras = 0; estado `evo=` gravado.
- A2: os 7 cards da Visão Geral com número 21 px #1E4FA1 (Sem compra em vermelho) e subtítulo 9,5 px sem maiúsculas; os 5 cards do RTM idem.
- A3: 4 botões visíveis; `DNABAS` = visao, distribuidores, pdv, definicoes; `#aba=rtm` abre a Visão Geral; seta → de Pontos de venda vai a Definições; templates de Penetração e RTM no HTML (montam por chamada direta); Definições com os 7 temas.
- A5: modo Ano lista "FY27 · em curso", FY26, FY25 (fiscal) e "2026 · em curso", 2025 (calendário); FY27 = 15.644 PDVs distintos, 201,2 t, vs FY26 −81,7%; linha de filtros ativos com o rótulo; abre em FY27.
- A7: na aba Pontos de venda o seletor mostra só set/26 parcial e ago/26; com mar/26 escolhido na Visão Geral, a aba mostra ago/26 com o aviso e, ao voltar, mar/26 continua.
- A8: cabeçalho "base ativa abr/26 a set/26"; jan/25 com base ativa, sem compra e DN em "—"; fev/25 com 107.176 · 52,0%; Definições com "6 meses" (5 ocorrências); Penetração com base elegível 129.595 e janela mar/26 a ago/26.

**Execução final** `20260914-211557` (`--regerar-exemplo --sem-publicar`, após a A9): 29 min sem reingestão (cálculo ~15 min,
histórico ~6 min, render ~2 min, validação 1,5 min), **120 validações ok**, 11 avisos (os conhecidos), renderizador validado byte a
byte, HTML **14,9 MB** (15.600.948 bytes), md5 **`cffa6784…`**, números idênticos aos da execução anterior. A execução de
conferência sem `--regerar-exemplo` iniciada entre as duas abortou na prova do renderizador porque o template mudou (A9) depois de
ela começar; a prova de reprodução do md5 será a própria execução de publicação (`python run_dn.py`, sem a opção), que valida o
renderizador byte a byte e cujo md5 será comparado ao `cffa6784…` antes de o arquivo ser considerado publicado.
- A9 (navegador): tabela do bloco com o cabeçalho igual aos meses do gráfico em todos os modos: Mês (abr/25 a mar/26, 12 colunas e 12 células), Acumulado (set/25 a mar/26, 7), Ano FY27 (set/26, 1), Série completa (set/24 a set/26, 25) e de volta; console limpo.

**Atenção · tamanho**: 14,9 MB de 15 (folga de 0,12 MB). A janela móvel de 25 meses mantém o arquivo estável a partir de out/26, mas
qualquer campo novo ou crescimento da base ativa pode estourar o limite. Decisão a tomar antes de nov/26: reduzir
`painel.janela_arquivo_meses` (24 meses = −0,3 MB) ou rever `validacao.html_max_mb`. Nada mudado.

> **Correção de 15/09/2026 (pendência 1, medida no arquivo publicado):** a janela móvel **não** estabiliza o arquivo. Os pacotes mensais
> crescem porque os campos vão sendo preenchidos (set/24 tem 61% dos campos da tabela de distribuidores vazios e pesa 86 KiB; ago/26 tem 5% e pesa
> 300 KiB) e porque as linhas aumentam (642 → 747). Em out/26 sai o pacote de 86 KiB e entra um de ~275, set/26 fecha e cresce, e a lista de PDVs
> (8,25 MiB) acompanha a base ativa: saldo de ~+0,3 MB contra folga de 0,12. `janela_arquivo_meses: 24` ganharia só 86 KiB, não 0,3 MB.
> Decisão do Douglas: `validacao.html_max_mb` **15 → 20** (nenhuma restrição técnica medida por trás dos 15; folga passa a ~4,9 MiB, 18 a 24 meses).
> Backlog: lista de PDVs em colunas, com cidade, bairro e último mês por índice, medida em 8,25 → 6,53 MiB (`dn/painel.py`, leitor JS do template,
> validação `pdv · lista combinada = listas de cada mes`).

## Pendências e recomendações futuras (não implementadas)

1. **Gerente Regional com números próprios (A4, backlog)**: campo `GERENTE` (N2) existe e está íntegro (3 gerentes, 14 supervisores, 0 em branco), mas PDV conta uma vez por nível: Sudeste ago/26 = 19.786 PDVs distintos × 19.914 na soma dos supervisores. Exige nível novo no pipeline (cubos, acumulados, PDVs distintos, Penetração, RTM, pacotes, séries, validações). Alternativa sem números (só navegação) foi descartada pelo Douglas.
2. Tamanho do HTML (acima).
3. Card kg / PDV comprador sem comparativos vs mês anterior / L3M / LY (campos `kg_pdv_var_*` não existem no JSON).
4. `_s1.js` e `_s2.js` na raiz do projeto (10/09), não referenciados; nada feito.
5. Pendências anteriores (RETOMADA §5): destinos RTM sem cadastro, datas de cadastro, carteira (124 linhas, 179 × 41, 177), SBM/SBN, Alavancas.

## (d) Checklist de tela (arquivo `data/dn/painel/Scorecard_DN_2026-09.html`, Chrome ou Edge, Ctrl+F5)

1. Abre em set/26 parcial com **4 abas**: Visão Geral, Supervisores e distribuidores, Pontos de venda, Definições. Cabeçalho "base ativa abr/26 a set/26".
2. Cards: 125.955 · 110.311 · 15.644 · 12,4% · 201,2 t · 12,86 kg · 1,03. **Volume do mês e kg / PDV comprador com o número grande azul**, como os vizinhos; em R$ idem.
3. Em ago/26: 129.595 · 58.117 · 71.478 · 55,2% · 1.199,9 t · 16,79 · 1,25.
4. Em jan/25: base ativa, sem compra e DN em "—"; em fev/25 preenchidos (107.176 · 52,0%).
5. Visão Geral, bloco "Evolução por categoria": chips coloridos, ★ nas foco, "Outras categorias", botões "todas" e "só as foco", gráfico de linhas acima da tabela. Ligar/desligar chips redesenha; "só as foco" deixa 4 linhas + Outras; trocar R$, Segmento Novos, um supervisor e Série completa redesenha (total nomeado).
6. Período → Ano: seletor com "FY27 · em curso", FY26, FY25; em Ano Calendário, "2026 · em curso" e 2025. FY27 mostra 15.644 PDVs distintos e 201,2 t (vs FY26 −81,7%).
7. Pontos de venda: seletor de mês só com set/26 parcial e ago/26. Escolha mar/26 na Visão Geral, abra Pontos de venda (ago/26 com o aviso) e volte: continua em mar/26.
8. Digite `#aba=rtm` no fim do endereço e dê Enter: abre a Visão Geral. Setas ← → percorrem só as 4 abas.
9. Definições: 7 temas; "últimos 6 meses" nas linhas de Base ativa, A ativar e Recorrência; linha "Ano" cita o ano em curso.
10. Trocar t/R$, calendário, segmento, supervisor e período em cada aba: nada some nem trava; console sem erro (F12).
11. (A9) Tabela abaixo do gráfico por categoria: os meses do cabeçalho são os do gráfico em qualquer modo; com Acumulado do ano e mar/26, cabeçalho e linhas com set/25 a mar/26 (7 meses); com Série completa, 25 meses.
12. Aprovado → "checklist ok" → `python run_dn.py` publica em `Painéis Comerciais/DN/Scorecard_DN.html`. **Feito em 14/09/2026 22h03.**
