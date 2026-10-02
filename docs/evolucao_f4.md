# Evolução · Fase F4 — filtro por Supervisor, cubos supervisor × categoria e cluster × categoria, retrato da hierarquia (10/09/2026, noite)

Executada após a F3 (`docs/evolucao_f3.md`, publicada 22h22) e a aprovação item a item da proposta da F4 (P1–P8; Q-a os cards da
Visão geral passam a mostrar o supervisor; Q-b recorte por categoria do gráfico de cobertura desabilitado com nota; Q-c expor já
os cubos como linhas por categoria em "Clusters e supervisores"; Q-d retrato da hierarquia a cada ingestão) pelo Douglas em
10/09/2026. Regras implementadas: **RN-44** (filtro global por Supervisor, seleção única, escopo por aba), **RN-37** (cubos
supervisor × categoria e cluster × categoria), **RN-16** (retrato mensal da hierarquia) e o aviso de **RN-15** ("hierarquia
vigente em {data}"). Sem regra nova.

**Publicado em 10/09/2026 às 23h04** (execução `20260910-230326-443d55`, 58 validações ok, md5 `e8e53049b3c20e5fd68b4eeec30ae247`, 9.102.712 bytes), após o ok do Douglas no checklist (d). Prova final antes da publicação: execução `20260910-224653-3a0b17`.

## (a) O que foi alterado

### Pipeline

| Arquivo | Mudança |
|---|---|
| `dn/metrics.py` | `calcular` gera os cubos de categoria também para `("supervisor", [SEG, SUP])`, `("supervisor_canal", [SUP])`, `("cluster", [SEG, CLUSTER])` e `("cluster_canal", [CLUSTER])` → `DN_SUPERVISOR_CAT_MES` (1.907 linhas), `DN_SUPERVISOR_CANAL_CAT_MES` (1.838), `DN_CLUSTER_CAT_MES` (1.978), `DN_CLUSTER_CANAL_CAT_MES` (1.675); mesma função dos cubos existentes, com `positivados_nivel` e `penetracao` do nível |
| `dn/pipeline.py` · etapa 1 | **retrato da hierarquia** (RN-16, Q-d): quando `regras.hierarquia.arquivar_retrato_mensal` é verdadeiro, a ingestão grava `data/dn/curated/historico/DIM_DISTRIBUIDOR_<AAAA-MM-DD>.parquet` (a dimensão inteira, com supervisor) e registra no log. Só roda quando há ingestão (bases alteradas ou `--forcar`) |
| `dn/painel.py` | `supervisores_lista` (id, rótulo, distribuidores), `distribuidor.supervisor_id`, `categorias_sup` (14 × 10 linhas: mesmos campos da tabela de categorias, participação = categoria ÷ total do supervisor no mês, Δ participação vs LY, mini-linha), `evo_sup_json` (`{sup: {cat: {t: [12], rs: [12]}}}`), `hierarquia.aviso` com a data da última ingestão e `hierarquia.rotulo_sup_todos`; `_cats_por` monta as categorias de clusters e supervisores a partir dos cubos novos; mini-linhas passam a ser **alinhadas pelo rótulo do mês** (`_spark(serie, meses_exib)`), não pela posição |
| `dn/tabelas.py` | tabela `categorias_sup`; `_por_categoria` gera, nas tabelas de clusters e supervisores, uma linha total (`cat_id = "__all__"`) e uma por categoria, no mesmo padrão de Distribuidores (Q-c) |
| `dn/pipeline.py` · etapa 4 | **8 validações novas**: `categorias x supervisor · volume`, `categorias x supervisor (canal) · volume`, `categorias x cluster · volume`, `categorias x cluster (canal) · volume` (kg por categoria fecha com o cubo do nível em todos os meses e nenhuma categoria tem cobertura acima do nível), `supervisores · select no HTML` (15 opções = 14 + Todos), `evo_sup · series supervisor x categoria` (140 séries = 140 pares na curated, 12 pontos), `tabela categorias_sup · registros` (140 = curated), `tabela categorias_sup · host no HTML`; a validação de sparklines passou a comparar por mês; o `esperado` de clusters e supervisores soma as linhas por categoria. 50 → **58** |
| `config/config.yaml` | `supervisor` nos `filtros` das abas visao, evolucao, clusters, distribuidores e pdv; `categoria` em clusters; `painel.rotulos.supervisor_todos`; `regras.hierarquia.aviso` e `arquivar_retrato_mensal` (F0) passam a ser lidos |
| `template/data-inventory.json` | 368 → **386** campos (`supervisores_lista[]`, `distribuidor.supervisor_id`, `categoria_sup.*`, `evo_sup_json`, `hierarquia.*`, `cat_id`/`cat_nome` em clusters e supervisores) |

### Template

| Onde | Mudança |
|---|---|
| Barra | select **Supervisor** (`#fsel-sup`, seleção única) ao lado do de Distribuidor, com o aviso da hierarquia; escolher um supervisor restringe o select de Distribuidor aos dele; escolher um distribuidor de outro supervisor limpa o supervisor; `dnFiltrosAplicabilidade` ganhou `supervisor` (chip esmaecido com nota em RTM e Definições) |
| Visão geral | `dnCardsAplicar()`: com supervisor, os 6 cards (`data-k`) mostram o registro do supervisor no segmento ativo (tabela `supervisores`, linha `__all__`); o valor do canal fica em `data-orig` e volta ao limpar; se a aba Clusters ainda não montou, monta-a escondida para ler os dados. A tabela de categorias troca para `categorias_sup` filtrada (participação sobre o total do supervisor; tooltip "% do supervisor"); nota `#vg-sup-nota` |
| Evolução | gráfico de cobertura usa `DN_SERIES['sup-<seg>-<id>']` (definidas na carga, fora dos `<template>`) no pane `dnc2-__canal__-sup`; o select "Recorte por categoria" fica **desabilitado com nota** (Q-b); a evolução por categoria lê `EVO_SUP[sup]` (t e R$) e o total vem da série do supervisor, **alinhado por mês** (`dnEvoTotal`) |
| Clusters e supervisores | coluna **Categoria** e filtro por `cat_id` nas duas tabelas (linhas totais destacadas, `linhaClasse hl`); o filtro global Categoria passa a agir nesta aba |
| Distribuidores | `supervisor_id` no filtro externo |
| Pontos de venda | filtro por distribuidor ∈ supervisor via `DN_DIST_SUP` (nome do distribuidor → id do supervisor) |
| CSV / estado | nome do CSV ganha `sup-<id>`; `DNE.sup` em `localStorage` e URL (`&sup=`) |
| Gráficos | guardas `v == null` e filtro `isNaN` no gráfico de categorias e nas mini-linhas (níveis com meses sem venda) |

### Docs

`docs/regras_negocio.md` (RN-16, RN-37, RN-44 e o aviso de RN-15 → **vigente**; 34 vigentes · 18 aprovadas · 3 declaradas);
`README.md` (changelog, parâmetros, rotina: o retrato em `curated/historico/` não se apaga); `docs/RETOMADA.md` (§1, §4 filtros,
§5 pendência 9 → publicar a F4 e propor a F5, §6 armadilha do supervisor, §7); este relatório.

## (b) Por quê

A.13 (D18–D20): o supervisor é a unidade de gestão comercial e não havia como olhar o painel por ele; a seleção única evita
somas de bases ativas entre supervisores (o PDV conta uma vez por nível, RN-05). Os cubos por categoria (D20) já ficam prontos
para a Penetração por supervisor e cluster (F6). O retrato datado (RN-16) é a única forma de construir histórico de supervisor,
porque a Hierarquia é um retrato sem datas (RN-15), daí o aviso fixo ao lado do select.

## Correções feitas durante a prova

| Sintoma | Causa | Correção |
|---|---|---|
| validação "host no HTML" falhava para `categorias_sup` | o host usa `id="dados-categorias_sup"` | a checagem aceita o id |
| mini-linhas e total da evolução do supervisor deslocados | níveis com meses sem venda têm série mais curta; o alinhamento era por posição | alinhamento por rótulo de mês em `_spark`, na validação e em `dnEvoTotal` |
| cards "—" ao escolher supervisor antes de abrir Clusters | tabela de supervisores ainda não montada | `dnAbaMontar('clusters')` escondida sob demanda |
| `<path d="NaN">` / `<circle cy="NaN">` no gráfico de categorias | pontos nulos entravam na escala | guardas de nulo e filtro `isNaN` |

## Prova

| Checagem | Resultado |
|---|---|
| Passo 1 (cubos + retrato + validações) | os 4 cubos fecham com os cubos de nível (maior diferença 0,0000 kg; 192 · 185 · 201 · 168 células; 0 categorias com cobertura acima do nível) |
| Passo 2 (JSON, tabelas, inventário) | `categorias_sup` 140 = curated; 140 séries supervisor × categoria; 0 campos fora do inventário |
| Completa (`20260910-224653-3a0b17`, `--regerar-exemplo --sem-publicar`) | exemplo regerado; byte a byte ok; **58 ok**; abas template = config (7); HTML **8,7 MB** (9.102.712 bytes); tabelas embutidas: clusters 382, supervisores 340, categorias 10, categorias_sup 140, distribuidores 747; números iguais (124.600 · 71.478 · 57,4% · 1.199,9 t · 71 · RTM 1762/1589/173) |
| Navegador (servidor local, recarga limpa) | select com 14 supervisores + Todos; Murilo Cunha: cards 1.196 / 1.009 / 14,0 t e volta ao canal (124.600 / 53.122 / 71.478) ao limpar; BA/SE: 10.967 / 5.516 / 78,4 t; tabela supervisor × categoria com tooltip "31,7% do supervisor"; Evolução com a série do supervisor, recorte desabilitado com nota, evolução por categoria dele com total correto ("— … 2,3 2,3 1,2 2,7 14,0"); Distribuidores e PDVs restritos; RTM inalterado com chip esmaecido; URL com `sup=`; 0 elementos SVG com NaN em todas as abas, sem supervisor e com 6 supervisores testados (inclusive os "vago"); **console sem erro** |
| Retrato da hierarquia | prova com `--forcar --sem-publicar` (ingestão completa, execução `20260910-225511-6a7c0c`, 58 validações ok, 13 avisos informativos já conhecidos da ingestão, HTML idêntico em tamanho e números): gravado `curated/historico/DIM_DISTRIBUIDOR_2026-09-10.parquet` (80 distribuidores = a dimensão inteira, inclusive os 9 fora do painel; 16,9 KB); nas execuções sem ingestão não grava |
| Tamanho | 8,0 → **8,7 MB** (+0,7 MB, dentro do estimado em P4: +0,75 com Q-c; limite 12) |

## (c) O que ficou pendente

- Penetração por supervisor e cluster (usa os cubos novos): F6. Resumos com supervisor: F9. Histórico de supervisor no painel:
  só quando houver retratos acumulados em `curated/historico/`. Cluster × supervisor: não aprovado.
- Próxima fase: **F5** (calendário civil × fiscal: toggle, ordem fiscal, acumulados no pipeline, comparativo anual bloqueado
  sem par, rótulos "Ano fiscal 2026 (set/25–ago/26)" / FY26).

## (d) Checklist para você

Abra `data/dn/painel/Scorecard_DN_2026-08.html` (Ctrl+F5) — é o gerado, ainda não publicado.

- [ ] Barra: select "Supervisor" com 14 nomes e o aviso "hierarquia vigente em …".
- [ ] Escolher um supervisor: os 6 cards da Visão geral mudam para ele; a tabela vira supervisor × categoria; limpar volta ao canal (124.600 · 71.478 · 57,4%).
- [ ] O select de Distribuidor mostra só os dele; escolher um distribuidor de outro supervisor limpa o supervisor.
- [ ] Evolução com supervisor: gráfico com a série dele, "Recorte por categoria" desabilitado com nota, evolução por categoria com o total dele.
- [ ] Clusters e supervisores: coluna Categoria; o filtro Categoria age; linhas totais destacadas.
- [ ] Distribuidores e Pontos de venda restritos ao supervisor; RTM com chip esmaecido e nota.
- [ ] Copiar a URL com `sup=` e abrir em outra aba: mesma seleção.
- [ ] Console (F12) sem erro; 375 px sem rolagem horizontal.
- [ ] Com o ok: `python run_dn.py --mes 2026-08` publica.
