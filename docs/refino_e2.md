# Refino do painel · Etapa E2 · barra lateral e navegação

13/09/2026. Plano aprovado pelo Douglas com as recomendações: abas no topo, Categoria em lista, Segmento e Métrica em chips,
Voltar por troca de aba, conteúdo com até 1.150 px ao lado da lateral, E1 e E2 publicadas juntas depois do checklist completo.
Decisões de origem: D10–D13 de `docs/refino_painel_proposta.md`. **Gerada com `--sem-publicar`.**

## (a) O que mudou

| Onde | Mudança |
|---|---|
| Barra lateral | Os filtros saíram do topo da página para uma lateral fixa à esquerda (250 px, rolagem própria). Ordem: Período · Ano · Segmento · Supervisor · Distribuidor · Categoria · Métrica · Limpar filtros · Voltar |
| Recolher / expandir | Botão « / » no topo da lateral. Recolhida vira uma faixa de 46 px com o número de filtros de recorte ativos. O estado fica lembrado no navegador (`scorecard_dn.lateral.v1`) |
| Categoria | Os 11 chips viraram uma lista (Todas as categorias + 10) |
| Filtro que não vale na aba | Some da lateral (antes ficava apagado com "não se aplica aqui"). Pontos de venda: Supervisor, Distribuidor, Métrica. RTM: Período (só na visão histórico), Supervisor, Métrica. Definições: nenhum filtro |
| Linha de filtros ativos | Abaixo das abas, presa junto com elas ao rolar. Mostra o mês e só o que vale na aba; o que foge do padrão aparece em negrito |
| Limpar filtros | Volta segmento, supervisor, distribuidor e categoria ao padrão; período, ano e métrica não mudam. Desabilitado quando nada está fora do padrão |
| Voltar | Cada troca de aba (clique, teclado ou salto da Penetração para Pontos de venda) vira um passo com aba, filtros e rolagem. O botão Voltar e o botão voltar do navegador restauram o passo anterior; desabilitado na primeira aba. Mudar filtro na mesma aba não cria passo |
| Layout | Cabeçalho e conteúdo deslocados para a direita da lateral; o conteúdo mantém o limite de 1.150 px. Na impressão a lateral some |
| Config | `painel.rotulos.lateral_{titulo, recolher, expandir, limpar, voltar, parcial}` |
| Código | `dn/painel.py` passa `J["lateral"]`; `template/data-inventory.json` +7 campos (`lateral.*`); `dn/pipeline.py` ganha a validação `lateral · filtros, ativos, limpar e voltar no HTML` |
| Documentos | `docs/regras_negocio.md`: RN-44, RN-50 e RN-59 com a nota da E2 |

Backup antes da E2: scratchpad da sessão, pasta `backup_pre_E2`.

## (b) Por quê

Com o scroll longo, quem lia não sabia o que estava filtrado (pedido do Douglas). A lateral deixa os filtros sempre à vista, a
linha de ativos repete o recorte junto das abas, o filtro que não vale some para não confundir, Limpar evita desfazer filtro por
filtro e Voltar resolve o salto de aba sem caminho de volta.

## (c) Resultado e pendências

| Item | E1 | E2 |
|---|---|---|
| Números de ago/26 (base ativa · positivados · DN · t · distribuidores · RTM) | 124.800 · 71.478 · 57,3% · 1.199,9 · 71 · 1.762/1.589/173 | iguais |
| Validações | 108 ok | **109 ok** (+ `lateral · …`) |
| HTML | 11,2 MB | 11,2 MB |
| Avisos | 3 | os mesmos 3 |

Conferido no navegador (servidor local sobre uma cópia do HTML), sem erro no console:
- filtros visíveis por aba conforme a tabela acima;
- sequência Visão geral (supervisor, rolagem) → Distribuidores (segmento Novos) → Penetração (rolagem) → drill para Pontos de venda,
  e três vezes Voltar: cada passo voltou com a aba, os filtros e a rolagem de onde saiu; o Voltar desabilita na primeira aba;
- Limpar filtros zera o recorte e desabilita; a lateral recolhe (46 px) e expande, e o estado fica guardado.

Segunda execução sem `--regerar-exemplo` (`resumo_20260913-171116-e3841d.json`): renderizador validado byte a byte, 109 ok,
mesmos números, HTML idêntico ao da primeira (md5 `ba0ba9ba99b5b87328eb9dfb03bd8700`).

Pendência encontrada, **anterior à E1** (vem da frequência de compra, 13/09): no card "Frequência de compra (estimativa)" aparecem
três números que deveriam estar ocultos (89.160 · 81.806 · 1,14: NFs estimadas, NFs mínimas e frequência mínima). Causa: a regra
de estilo `.k span{display:block}` vence o atributo `hidden`. Correção proposta: uma linha de CSS (`.k [hidden]{display:none}`).
**Não corrigido: aguarda aprovação.**

## (d) Checklist para o Douglas (junto com o da E1, arquivo `data/dn/painel/Scorecard_DN_2026-08.html`)

1. A lateral aparece à esquerda com Período, Ano, Segmento, Supervisor, Distribuidor, Categoria (lista) e Métrica, nessa ordem.
2. O botão « recolhe a lateral; recolhida, mostra o número de filtros ativos; » expande. Fechar e reabrir o arquivo mantém o estado.
3. Em cada aba só aparecem os filtros que valem ali (Pontos de venda: Supervisor, Distribuidor, Métrica; RTM: Período, Supervisor, Métrica; Definições: nenhum).
4. A linha abaixo das abas mostra o recorte atual e fica presa ao rolar; o que foi mudado aparece em negrito.
5. Escolher supervisor, segmento, distribuidor ou categoria: os números mudam como antes; Limpar filtros volta tudo ao padrão e fica desabilitado.
6. Navegar Visão geral → Distribuidores → Penetração e clicar num "sem compra no mês" (vai para Pontos de venda). Voltar três vezes: cada aba volta com os filtros e a posição da tela de onde saiu.
7. O botão voltar do navegador faz o mesmo que o Voltar da lateral.
8. Tabelas largas continuam rolando dentro do próprio bloco; nada fica escondido atrás da lateral.
