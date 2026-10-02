# Refino do painel · Etapa E4b · histórico de todos os meses

13/09/2026. Plano aprovado pelo Douglas: Mês em lista suspensa; gráfico das linhas por categoria montado das tabelas de cada mês
com o LY buscado no mesmo mês do ano anterior; autorizada a reserva (gráficos lendo das tabelas) se passasse de 15 MB (não foi
preciso). Decisões de origem: D24 (histórico), decisão 3 da E4 (Pontos de venda com mês antigo), pendências da E3.
**Gerada com `--sem-publicar`; checklist único no fim.**

## (a) O que mudou

| Onde | Mudança |
|---|---|
| Seletor Mês | Lista suspensa com os **25 meses** da série (set/26 parcial, ago/26, …, set/24), do mais recente ao mais antigo |
| Meses do histórico | Montados no pipeline a partir dos mesmos cubos mensais (`painel.montar(..., leve=True)`: sem séries, Penetração, lista de PDVs, carteira, resumos e memória). Por mês: cards e acumulado, "O que aconteceu no mês", tabelas de categorias, supervisores, distribuidores e clusters, cards e destinos do RTM |
| PDVs distintos do acumulado | Nova função `metrics.acum_pdvs_mensal`: primeiro mês de compra do PDV no ano e soma acumulada, em todos os meses, civil e fiscal, nos níveis canal, segmento, supervisor e distribuidor |
| Meses de histórico do distribuidor | Recontados até cada mês |
| RTM por mês | Destinos do mês calculados a partir da grade cliente × mês e da ativação até o mês; **clientes do mês montados no navegador** a partir da lista cliente × mês (busca, sem conta) em todos os meses, inclusive parcial e fechado |
| set/24 a dez/24 | Base ativa, DN e sem compra em "—" (janela de 5 meses incompleta); volume, R$, positivados e frequência aparecem; "O que aconteceu no mês" vazio em set/24 (sem mês anterior) |
| Carregamento | Ao abrir: tabelas fixas, o mês da URL (ou o parcial) e o mês fechado. Os demais meses abrem quando escolhidos, com "carregando" |
| Pontos de venda com mês antigo | Mostra a lista e a carteira do mês fechado com o aviso "Lista de PDVs de ago/26: a lista só existe para o mês parcial e o mês fechado" |
| Evolução por categoria | Segue o Segmento (séries segmento × categoria); o total diz o recorte ("Total · Novos distribuidores", "Total · supervisor") |
| Gráfico das linhas por categoria | Clicar numa linha por categoria de supervisor, distribuidor ou cluster abre o gráfico mês a mês montado das tabelas de cada mês (abre todos os meses na primeira vez); LY = mesmo mês do ano anterior na tabela daquele mês |
| Pacote por mês | Só as colunas que o template lê (as de acumulado entram por prefixo); clientes RTM fora do pacote |
| Validações | `comprimidos · pacotes = tabelas de cada mes` agora cobre os 25 meses e prova que o **montar leve dá o mesmo que o completo** no mês de referência e no fechado (tabelas, cards, RTM, rótulos do ano) e que os **clientes RTM montados pela lista = tabela do pipeline** nesses dois meses; nova `historico · cards e PDVs distintos acumulados de cada mes` (cards do canal de 23 meses = cubo; PDVs distintos acumulados do canal em 50 mês × perspectiva = base de vendas; 582 linhas de `DN_ACUM_ANO` iguais) |
| Config | `painel.rotulos.pdv_mes_nota` |
| Documentos | `docs/regras_negocio.md`: RN-02, RN-25, RN-26, RN-46, RN-52 com a nota da E4b |

Backup antes da E4b: scratchpad da sessão, pasta `backup_pre_E4b`.

## (b) Por quê

O head precisa ver como estava qualquer mês da série para comparar com hoje (D24), nas mesmas telas e com os mesmos filtros.

## (c) Resultado e pendências

| Item | E4a | E4b |
|---|---|---|
| Meses no arquivo | 2 | **25** |
| HTML | 9,9 MB | **13,5 MB** (limite 15 MB; reserva não usada) |
| Validações | 117 ok | **118 ok** |
| Tempo da execução | ~7 a 14 min | ~10 a 11 min (os 23 meses do histórico somam ~3,5 min) |
| Números | set/26 parcial e ago/26 iguais aos da E4a | iguais; exemplo conferido jun/25: base ativa 106.132 · positivados 58.039 · DN 54,7% (= cubo) |
| Avisos | 9 | 11: os 9 da E4a e 2 informativos "clientes RTM: mesma lista, ordem de desempate diferente da do pipeline" (clientes com mesma situação, destino e nome; a tabela ordena na tela) |

Conferido no navegador, sem erro no console: 25 meses na lista; mar/26 (base ativa 109.319, DN 57,2%, acumulado FY26 set/25–mar/26
7.257,8 t e 119.611 PDVs distintos); nov/24 e set/24 com base ativa e DN em "—"; RTM de mar/26 com aderência 8,1% e os 1.762
clientes; Pontos de venda em mar/26 com o aviso da lista de ago/26; gráfico de PROPEC × Amendoim (15 meses) a partir das tabelas;
evolução por categoria em Novos distribuidores e em supervisor com o total nomeado.

Execução de prova sem `--regerar-exemplo` (`resumo_20260913-194606-a73719.json`): renderizador validado byte a byte, 118 ok, HTML
idêntico ao testado no navegador (md5 `279254fd116cffb33a26626ea65819e8`, 14.138.482 bytes).

Defeitos achados nos testes e corrigidos antes da entrega:
1. A validação da lista de PDVs comparava os meses da lista (2) com os 25 do arquivo.
2. Com Segmento ou Supervisor escolhido, a evolução por categoria chamava o total de "Total do canal".

Regra registrada: nos meses do histórico, segmentação Base atual × Novos e supervisor são os de hoje (RN-15), como nas séries.

## (d) Checklist para o Douglas (arquivo `data/dn/painel/Scorecard_DN_2026-09.html`)

1. Mês: lista com 25 meses, abrindo em set/26 parcial.
2. Escolher mar/26: cards 109.319 · 57,2%; acumulado "Ano fiscal 2026 (set/25–mar/26)"; "O que aconteceu no mês · vs fev/26".
3. Escolher nov/24: base ativa e DN em "—", volume e positivados preenchidos.
4. Supervisores e distribuidores e RTM mudam com o mês; os clientes do RTM aparecem no mês escolhido.
5. Pontos de venda em mês antigo: aviso da lista de ago/26.
6. Escolher uma categoria na lateral e clicar numa linha de distribuidor: o gráfico abre com a evolução daquele distribuidor na categoria.
7. Visão Geral com Segmento Novos: a evolução por categoria mostra "Total · Novos distribuidores".
