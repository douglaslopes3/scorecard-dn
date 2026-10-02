# Refino do painel · Etapa E1 · limpeza

13/09/2026. Aprovada pelo Douglas (plano da E1; Alavancas e Matriz apagadas; resumos e memória desligados; publicação a cada
etapa). Decisões de origem: D14–D18 e D23 de `docs/refino_painel_proposta.md`. **Gerada com `--sem-publicar`; publica só depois
do checklist abaixo.**

## (a) O que mudou

| Onde | Mudança |
|---|---|
| Abas | Saem **Alavancas** e **Matriz de oportunidades**. Ficam 8: Visão geral · Evolução · Clusters e supervisores · Distribuidores · Pontos de venda · Penetração · RTM · Definições |
| Resumos automáticos (RN-48) | `painel.resumos.ativo: false`. Blocos fora da tela; validações `resumos · …` puladas. Código e regras mantidos (regras M1–M3 e A1–A3 apagadas) |
| Memória de cálculo ⓘ (RN-49) | `painel.memoria.ativo: false`. Botões ⓘ, modal e texto nas Definições fora da tela; validações `memoria · …` puladas. Código e fichas mantidos (fichas `gap_pp` e `alav_*` apagadas; ligações a colunas removidas) |
| Evolução | Tabela **Ano a ano** removida |
| Tabelas | **Mini-linhas** removidas (Visão geral, Clusters e supervisores, Distribuidores) |
| Visão geral | Coluna **Penetração** removida da tabela de categorias |
| Textos | Parágrafos explicativos das abas removidos; títulos encurtados; notas da barra de filtros removidas (hierarquia, Comparativos, Métrica, Ano, Período); legenda de cores da Penetração em uma linha; notas das sub-abas do RTM removidas; travessões tirados dos textos exibidos |
| Rótulos | "Ano civil" → **"Ano Calendário"**; frequência sinalizada: **"Frequência de compra (estimativa)"**, coluna "Freq. compra (est.)", chave do gráfico "Frequência (estimativa)" |
| Aviso de mês em andamento | Encurtado: "{mês} parcial, atualizado em {data}. Os comparativos confrontam um mês incompleto com meses cheios." |
| Definições | Parágrafos de Matriz e Alavancas removidos; Período e Calendário reescritos sem citar o que saiu |
| Código apagado | `metrics.alavancas` e `_shapley` · `painel._alavancas` e bloco `J["matriz"]` · campo `gap_pp` · tipos de resumo de alavancas · validações de Matriz (3) e Alavancas (5) · validação das mini-linhas · tabela `ano_a_ano` (painel, tabelas, validação) · motor JS da Matriz, das Alavancas e das mini-linhas · `data/dn/curated/DN_ALAVANCAS.parquet` |
| Mantido | `penetracao · positivados do distribuidor = cubo` (era da Matriz, confere dado da Penetração); situação "Positivados no mês sem {categoria}" na tabela de PDVs (agora em `penetracao.sit_pos_sem`); `DN_ACUM_ANO` (PDVs distintos do acumulado) |
| Inventário | `template/data-inventory.json`: 810 → 755 campos (saem `matriz.*`, `alavancas.*`, `ano_a_ano.*`, `*.spark_*`, `pen_nivel_cat.gap_pp`; entra `penetracao.sit_pos_sem`) |
| Documentos | `docs/regras_negocio.md`: RN-42 e RN-57 descontinuadas; RN-48 e RN-49 desligadas; RN-24, RN-25, RN-45, RN-46, RN-50 e RN-58 com a nota do refino; legenda de status ganha `descontinuada` e `desligada` |

Backup dos arquivos antes da E1: scratchpad da sessão, pasta `backup_pre_E1` (dn/, config/, run_dn.py, template.html,
data-inventory.json, regras_negocio.md, RETOMADA.md).

## (b) Por quê

Painel gerencial com foco no head: menos informação e texto, só o medido (D1, D23). Matriz não respondia pergunta (D14);
Alavancas atuais não são as alavancas do negócio e voltam quando houver a fonte do plano (D14); resumos e ⓘ poluíam a leitura
(D18); Ano a ano repetia o que o novo seletor de período vai mostrar (D16); mini-linhas só fariam sentido ampliáveis (D15);
coluna Penetração duplicava a aba Penetração (D16).

## (c) Resultado da execução e pendências

| Item | ago/26 antes (13/09 13h55) | ago/26 depois da E1 |
|---|---|---|
| Base ativa | 124.800 | 124.800 |
| Positivados | 71.478 | 71.478 |
| DN | 57,3% | 57,3% |
| Volume | 1.199,9 t | 1.199,9 t |
| Distribuidores | 71 | 71 |
| RTM (base / mensuráveis / não mensuráveis) | 1.762 / 1.589 / 173 | 1.762 / 1.589 / 173 |
| Aderência | 13,4% (213 · 93 · 1.283) | 13,4% (213 · 93 · 1.283) |
| Frequência de compra | 1,25 | 1,25 (1,2474 = curated = recálculo) |
| Validações | 138 ok (RETOMADA; 137 nomes distintos no resumo) | **108 ok**, todas: saem 30 nomes (11 de resumos, 8 de memória, 3 de Matriz, 5 de Alavancas, 1 de mini-linhas, 2 da tabela Ano a ano) e entra 1 (`penetracao · positivados do distribuidor = cubo`, a antiga conferência da Matriz renomeada) |
| HTML | 12,8 MB | 11,2 MB |
| Avisos | 3 (RTM sem cadastro, carteira ×2) | os mesmos 3 |

Conferido no navegador (servidor local sobre uma cópia do HTML): as 8 abas montam, t/R$, Ano fiscal/Ano Calendário, supervisor
e período funcionam, sem erro no console, nenhum ⓘ nem bloco de resumo na tela.

Segunda execução sem `--regerar-exemplo` (`resumo_20260913-164507-e81d84.json`): renderizador validado byte a byte, 108 ok,
mesmos números, HTML idêntico ao da primeira (md5 `408feddeae63de8ae09a348193f81bfe`).

Pendências: nenhuma de código. A publicação espera o checklist.

## (d) Checklist para o Douglas (arquivo `data/dn/painel/Scorecard_DN_2026-08.html`)

1. As abas são 8, sem Alavancas e sem Matriz de oportunidades.
2. Não há bloco "Resumo do recorte" em nenhuma aba nem botão ⓘ ao lado dos números.
3. Barra de filtros: sem as notas cinzas (hierarquia, Comparativos, Métrica, Ano, Período); o chip diz "Ano Calendário".
4. Visão geral: cards com os mesmos números de antes (124.800 · 53.322 · 71.478 · 57,3% · 1.199,9 t · 16,79 kg/PDV · 1,25); o card da frequência diz "(estimativa)".
5. Visão geral: tabela de categorias sem a coluna Penetração e sem mini-linha; sem o parágrafo "Duas réguas".
6. Evolução: gráfico e evolução por categoria funcionam; não existe mais a tabela "Ano a ano".
7. Clusters e supervisores e Distribuidores: tabelas sem a coluna de mini-linha; clicar na linha ainda abre a evolução abaixo.
8. Penetração: números iguais aos de antes; legenda de cores em uma linha; sem parágrafos.
9. Pontos de venda: carteira Destaque/Prime/Todos e a situação "Positivados no mês sem {categoria}" no filtro.
10. RTM: cards, Evolução, Destinos e Clientes funcionam; sem o parágrafo introdutório e sem as notas das sub-abas.
11. Trocar t/R$, Ano fiscal/Ano Calendário, supervisor e Período em cada aba: nada some nem trava.
12. Aprovado → publicar (`python run_dn.py --mes 2026-08`).
