# Refino do painel · Etapa E5 · período unificado (Mês, Acumulado do ano, Ano)

13/09/2026. Plano aprovado pelo Douglas: janela dos gráficos segue o período, com "Série completa" como botão dentro do gráfico;
"O que aconteceu no período" nos modos Acumulado e Ano; coluna "Acum. no ano" sai do modo Mês; RTM e Pontos de venda mostram o
mês final do período. Decisões de origem: D8, D21, D25, D26. **Gerada com `--sem-publicar`; checklist único no fim.**

## (a) O que mudou

| Onde | Mudança |
|---|---|
| Lateral | **Período: Mês · Acumulado do ano · Ano**, com o seletor embaixo (meses nos modos Mês e Acumulado; anos fechados no modo Ano). Os chips antigos (Últimos 12 meses, Série completa, anos só para gráfico) saíram |
| Modo Mês | Como antes, sem a coluna "Acum. no ano" nas tabelas |
| Modo Acumulado do ano | Do início do ano (fiscal ou Ano Calendário) até o mês escolhido. Cards: PDVs distintos no período, Volume/Valor acumulado, Frequência acumulada, cada um com Δ vs o mesmo período do ano anterior; a linha de acumulado abaixo dos cards some (os cards já são o acumulado) |
| Modo Ano | Anos fechados do calendário ativo: FY25 e FY26 no fiscal; 2025 no Ano Calendário (2024 incompleto não aparece; o ano em curso fica no Acumulado). Mesmos números do acumulado no último mês do ano |
| Tabelas (Acumulado e Ano) | Categorias, supervisores, distribuidores, clusters e linhas por categoria: PDVs distintos, Δ, Volume/Valor, Δ, Frequência, Δ |
| O que aconteceu no período | Nos modos Acumulado e Ano: maiores quedas e altas vs o mesmo período do ano anterior, em PDVs distintos ou volume/valor |
| Gráficos | Janela: 12 meses até o mês (Mês), do início do ano até o mês (Acumulado), o ano (Ano); botão **Série completa** dentro de cada gráfico (inclusive na janela ao clicar na linha) |
| RTM e Pontos de venda | Sem os modos: mostram o mês final do período (em Ano, o último mês do ano) |
| Linha de filtros ativos | "Acumulado FY26 até mar/26", "FY26", "2025", "Série completa" quando ligada |
| Pipeline | `metrics.acum_pdvs_mensal` com cluster, categoria e linhas por categoria (D25), contagem vetorizada; `painel.montar` preenche em todas as linhas PDVs distintos do período, Δ% e diferença vs o mesmo período do ano anterior e diferença da medida acumulada; as tabelas levam Δ e frequência acumulada em todos os níveis |
| Validação nova | `periodo · acumulado de cada linha = cubo e fato` (t acumulada dos distribuidores = cubo; PDVs distintos do período de clusters e categorias = base de vendas; Δ de PDVs das categorias = recálculo) |
| Config | `painel.rotulos.per_*`; RTM sem o filtro de período |
| Documentos | `docs/regras_negocio.md`: RN-21, RN-25, RN-59 com a nota da E5 |

Backup antes da E5: scratchpad da sessão, pasta `backup_pre_E5`.

## (b) Por quê

O Período mudava só os gráficos e confundia (primeira observação do Douglas no refino). Agora o período escolhido é o que os
números mostram, e o ano e o acumulado respondem "como está o ano" sem tabela à parte.

## (c) Resultado e pendências

| Item | E4b | E5 |
|---|---|---|
| HTML | 13,5 MB | **14,5 MB** (15.244.123 bytes; limite 15 MB, medido em MiB como o pipeline; perto do limite) |
| Validações | 118 ok | **119 ok** |
| Tempo da execução | ~11 min | **~9 min** (a contagem de PDVs distintos do período por códigos inteiros; a primeira versão, com colunas de texto, levava 23 min) |
| Números | — | iguais aos da E4b no modo Mês; FY26 150.453 PDVs distintos (+12,3% vs FY25) e 13.133,5 t (+3,4%); FY25 133.992 (Δ "—", sem FY24); Ano Calendário 2025 136.362 e 12.793,8 t; Acumulado FY26 até mar/26 119.611 (+6,5%) e 7.257,8 t (+1,2%) |

Prova da otimização: a execução com a contagem por códigos gerou pacotes comprimidos, lista de PDVs e cards **idênticos** aos da
versão com texto, e o HTML final saiu com o mesmo md5 da execução anterior (`98aea963198899b07d75c760fbd54dc0`), com o renderizador
validado byte a byte (`resumo_20260913-210248-329f09.json`).

Conferido no navegador, sem erro no console: os três modos em Visão Geral e Supervisores e distribuidores (cards, colunas,
ranking e títulos), troca do calendário no modo Ano (FY25/FY26 ↔ 2025), RTM e Pontos de venda no mês final com o Período escondido,
Voltar guardando o modo, "Série completa" com os 25 meses.

Defeitos achados e corrigidos antes da entrega:
1. O rótulo acima do seletor mostrava "set/26 parcial" em vez de "Mês".
2. A contagem de PDVs distintos do período levava ~14 min (agrupamento por colunas de texto); passou a ~1 min, com o mesmo resultado.

Atenção: com 14,5 MB o arquivo está perto do limite de 15 MB. Se a série crescer (cada mês novo soma ~0,3 MB), a reserva
autorizada (gráficos lendo das tabelas mensais, ~1 MB) ou a revisão do limite entram em decisão.

## (d) Checklist para o Douglas (arquivo `data/dn/painel/Scorecard_DN_2026-09.html`)

1. Lateral: Período com Mês, Acumulado do ano e Ano; o seletor embaixo muda para anos no modo Ano.
2. Mês mar/26: cards como antes (109.319 · 57,2%), sem a coluna "Acum. no ano" nas tabelas.
3. Acumulado do ano com mar/26: "Ano fiscal 2026 (set/25–mar/26)", 119.611 PDVs distintos (+6,5% vs FY25), 7.257,8 t (+1,2%); título "O que aconteceu no período · vs FY25".
4. Ano FY26: 150.453 PDVs distintos (+12,3%), 13.133,5 t (+3,4%). FY25: 133.992, Δ em "—".
5. Ano Calendário → Ano 2025: 136.362 PDVs distintos, 12.793,8 t.
6. Supervisores e distribuidores no Acumulado: colunas PDVs distintos, Volume, Frequência e seus Δ.
7. RTM e Pontos de venda com Acumulado ligado: mostram o mês escolhido; em Ano, o último mês do ano.
8. Gráfico mês a mês: janela segue o período; "Série completa" mostra os 25 meses e desliga no mesmo botão.
