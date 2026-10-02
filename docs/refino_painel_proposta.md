# Refino do painel DN · proposta consolidada

Iniciado em 13/09/2026 com o Douglas. Nada implementado. Este arquivo registra as decisões e o que ainda está aberto.
Regra de trabalho: nada é executado sem aprovação item a item (ver `docs/RETOMADA.md` §2).

## 1. Objetivo

Painel gerencial mais objetivo: menos informação, menos texto, só o que é medido. Público do head ao supervisor do canal,
com foco no head. Uso no computador. As abas conversam entre si e levam à ação por rankings clicáveis.

## 2. Decisões fechadas

| # | Tema | Decisão |
|---|---|---|
| D1 | Público e uso | Head ao supervisor, foco no head; computador |
| D2 | Mês exibido | Mês fechado e mês parcial no mesmo arquivo; parcial publicado; abre no parcial quando existir |
| D3 | Comparativos do parcial | Mantidos (mês anterior, L3M, LY) com aviso de mês incompleto |
| D4 | Data de corte do parcial | Não existe na base; rótulo "parcial · atualizado em dd/mm" (data de leitura das bases) |
| D5 | Parcial nas abas | Em todas as abas, exceto Penetração · 14/09/2026 (A3): Penetração e RTM ocultas da navegação |
| D6 | Penetração | Mantida (referência P75, lojas a positivar, potencial), sempre no mês fechado com a etiqueta do mês · **revista em 14/09/2026 (A3)**: aba oculta da navegação, código e dados mantidos |
| D7 | Visão detalhada do mês | Bloco "O que aconteceu no mês": maiores quedas e altas por supervisor e distribuidor, em PDVs positivados e volume, clicáveis |
| D8 | YTD e ano | Todos os indicadores que já existem |
| D9 | Calendário | Fica; "Ano civil" passa a "Ano Calendário" |
| D10 | Filtros | Barra lateral que expande e recolhe; linha fixa no topo com o que está filtrado |
| D11 | Filtro que não vale na aba | Some |
| D12 | Limpar filtros | Limpa só o recorte (segmento, supervisor, distribuidor, categoria) |
| D13 | Voltar | Botão Voltar e botão do navegador restauram aba, filtros e rolagem |
| D14 | Abas | Visão geral + Evolução juntas; Clusters e supervisores + Distribuidores juntas; Matriz sai; Alavancas sai por enquanto (volta quando existir a fonte do plano: baseline, metas, definição de cada alavanca) · **14/09/2026 (A3)**: Penetração e RTM ocultas; usuário final vê 4 abas |
| D15 | Gráfico por linha | Mini-linhas saem; clicar na linha abre o gráfico mês a mês em janela sobreposta |
| D16 | Redundância | Fundir onde houver; tabela "Ano a ano" sai; coluna Penetração sai da tabela de categorias da aba principal |
| D17 | Frequência de compra | Fica, sinalizada como estimativa (RN-58) |
| D18 | Resumos automáticos (RN-48) e memória de cálculo ⓘ (RN-49) | Removidos |
| D19 | Evolução por categoria (linhas com chips) | Fica na aba principal |
| D20 | Penetração por supervisor / cluster / distribuidor | Fundir numa tabela com "Ver por", se reduzir redundância |
| D21 | Anos incompletos no início da série | 2024 do Ano Calendário (set a dez) não aparece |
| D22 | Arquivo | Um arquivo único: lista de PDVs combinada (os dois meses) e tabelas comprimidas (gzip+base64) |
| D23 | Texto | Sem parágrafos explicativos; no máximo um título curto por bloco; sem travessões |
| D24 | Histórico | Qualquer mês da série em Visão Geral, Supervisores e distribuidores e RTM; Pontos de venda com mês parcial e mês fechado; Penetração no mês fechado (D6). DN existe de jan/25 em diante |
| D25 | PDVs distintos do cluster | Calcular no pipeline por período (acumulado e ano), contagem medida |
| D26 | Ano × Acumulado do ano | Acumulado vai até o mês escolhido; "Ano" lista só anos fechados (FY25, FY26; 2025); ano em curso só no Acumulado · **revista em 14/09/2026 (A5)**: o ano em curso também entra no modo Ano, rotulado "· em curso" |
| D27 | Nome da aba principal | Visão Geral |

## 3. Medições que sustentam as decisões (13/09/2026, dados de ago/26 e set/26 parcial)

| Medição | Resultado |
|---|---|
| HTML publicado (ago/26) | 12,84 MB; limite 15 MB |
| Lista de PDVs: ago/26 + set/26 separadas | 12,48 MB |
| Lista de PDVs combinada | 8,30 MB (130.560 pares; 5.696 só em ago/26, 1.201 só em set/26; cadastro idêntico nos pares comuns) |
| Tabelas embutidas hoje (texto) após remoções | 4,34 MB; comprimidas 0,56 MB |
| Arquivo com os dois meses (estimativa por blocos) | ~10,5 MB |
| Tabelas mensais de todos os níveis, 24 meses, todas as colunas (curated `*_MES`), comprimidas | 4,63 MB |
| Coluna Penetração da Visão geral × aba Penetração (ago/26, canal) | números idênticos nas 10 categorias |
| DN do canal | nula de set/24 a dez/24 (janela de 5 meses incompleta); existe de jan/25 em diante |
| Acumulados já calculados na curated | `ytd_*` com Δ vs LY por mês em todos os níveis `*_MES` (inclui distribuidor e cluster); PDVs distintos por ano em `DN_ACUM_ANO` para canal, segmento, supervisor, categoria e distribuidor (cluster não) |
| Histórico por aba | Tabelas de nível: 24 meses na curated; RTM: 24 meses já embutidos no HTML; Pontos de venda: só o mês de referência (`DN_PDV_BASE_ATIVA`); Penetração: só o mês fechado (`DN_PEN_*`) |
| Troca de aba hoje | `history.replaceState`: não empilha histórico, por isso não há voltar |

## 4. Estrutura proposta

### Barra lateral
1. Período: Mês · Acumulado do ano · Ano
2. Calendário: Ano fiscal · Ano Calendário
3. Recorte: Segmento › Supervisor › Distribuidor › Categoria
4. Métrica: t · R$
5. Botões: Limpar filtros · Voltar · Recolher/expandir

### Abas (de 10 para 6)
1. Visão Geral (nome a confirmar): aviso de parcial · cards · gráfico mês a mês · evolução por categoria · o que aconteceu no mês · categorias
2. Supervisores e distribuidores: uma tabela com "Ver por: Supervisor · Distribuidor · Cluster"
3. Pontos de venda
4. Penetração (mês fechado)
5. RTM
6. Definições (uma linha de fórmula por indicador)

## 5. Impactos em regras, validações e documentos

| Item | Efeito |
|---|---|
| RN-57 Alavancas, RN-42 Matriz | Descontinuadas; saem 6 + 3 validações |
| RN-48 Resumos, RN-49 Memória | Descontinuadas; saem 10 + 8 validações |
| RN-59 Período, RN-24/25 Calendário | Reescritas (período muda os números; "Ano Calendário") |
| RN-58 Frequência | Rótulo "estimativa" |
| Publicação do mês em andamento | `publicar_mes_em_andamento` passa a true |
| Validações novas | Dois meses no arquivo; lista combinada = listas separadas; tabelas comprimidas = originais |
| Barra, Voltar, Limpar | Comportamento de navegador: checklist de uso |
| `regras_negocio.md`, `data-inventory.json`, `RETOMADA.md` | Atualizados ao fim de cada etapa |

## 6. Etapas

| Etapa | O quê |
|---|---|
| E1 | Limpeza: remover abas, blocos, resumos, ⓘ e textos (números iguais aos de hoje) |
| E2 | Barra lateral, linha de filtrado, Limpar e Voltar |
| E3 | Fusão das abas e gráfico em janela |
| E4 | Dados: compressão, lista combinada, dois meses, publicação do parcial |
| E5 | Período unificado (Mês, Acumulado, Ano) mudando os números |
| E6 | Definições enxutas, documentação e checklist final |

Cada etapa: gerar com `--sem-publicar`, checklist, aprovação do Douglas, publicação.

Com D24: E4 passa a embutir as tabelas mensais de todos os meses (estimativa do arquivo ~14,4 MB; ~13,7 MB se os gráficos
lerem das tabelas, a medir) e E5 inclui D25 e D26.

## 7. Em aberto

A1–A3 fechadas em D24–D27 (13/09/2026). Publicação: a cada etapa, depois do checklist (o time ainda não tem acesso).
Alavancas e Matriz: código apagado. Resumos e memória: código mantido, desligados no config.

## 8. Andamento

| Etapa | Estado |
|---|---|
| E1 | Executada em 13/09/2026, gerada sem publicar; aguarda checklist (`docs/refino_e1.md`) |
| E2 | Executada em 13/09/2026, gerada sem publicar (`docs/refino_e2.md`); E1 e E2 publicam juntas após o checklist completo |
| E3 | Executada em 13/09/2026, gerada sem publicar (`docs/refino_e3.md`); inclui a correção do card da frequência. Checklist único no fim do refino |
| E4a | Executada em 13/09/2026, gerada sem publicar (`docs/refino_e4a.md`): set/26 parcial + ago/26 no arquivo, 9,9 MB, 117 validações |
| E4b | Executada em 13/09/2026, gerada sem publicar (`docs/refino_e4b.md`): 25 meses no arquivo, 13,5 MB, 118 validações |
| E5 | Executada em 13/09/2026, gerada sem publicar (`docs/refino_e5.md`): Mês · Acumulado do ano · Ano, 14,5 MB, 119 validações |
| E6 | Executada em 13/09/2026, gerada sem publicar (`docs/refino_e6.md`): Definições em tabelas por tema, janela móvel de 25 meses, README e RETOMADA reescritos, checklist consolidado em `docs/refino_checklist.md` |

Refino E1–E6 concluído sem publicar. Checklist respondido em 14/09/2026; ajustes decorrentes (A1, A2, A3, A5, A7) e a regra nova A8 (janela de 6 meses) estão em `docs/estabilizacao_2026-09-14.md`. Publicação com `python run_dn.py` após o checklist de tela.
