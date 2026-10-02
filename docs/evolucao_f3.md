# Evolução · Fase F3 — aba Evolução e evolução por categoria (10/09/2026, noite)

Executada após a F2 (`docs/evolucao_f2.md`, publicada 21h49) e a aprovação item a item da proposta da F3 (P1–P8; Q-a "Outras" =
soma das não selecionadas; Q-b mini-linhas também em supervisores e distribuidores; Q-c eixo em valor absoluto; Q-d o gráfico de
cobertura sai inteiro da Visão geral) pelo Douglas em 10/09/2026. Regras implementadas: **RN-50** (aba Evolução; Visão geral =
foto do mês, A.16), **RN-46** (evolução por categoria, participação, Δ participação vs LY, sparkline) e a estrela das foco de
**RN-19**.

**Publicado em 10/09/2026 às 22h22** (execução `20260910-221447-e950e2`, 50 validações ok, md5 `4876737e253beda27b41d165df6b2807`, 8.381.774 bytes), após o ok do Douglas no checklist (d).

## (a) O que foi alterado

### Pipeline

| Arquivo | Mudança |
|---|---|
| `dn/painel.py` | por categoria: `participacao_vol`, `participacao_rs` (medida da categoria ÷ medida do canal no mês) e `participacao_var_ly_vol/rs` (p.p. vs mesmo mês LY, por junção; nulo sem par); `spark_t`/`spark_rs` (os 12 pontos da série exibida) em categorias, supervisores e distribuidores; bloco `graficos` ganhou `categorias_top_n`, `categorias_outras_rotulo`, `categorias_foco` (ids), rótulos dos botões e `meses` (rótulos exibidos) |
| `dn/tabelas.py` | nas linhas por categoria da tabela de distribuidores, `spark_*` vai nulo (não há série por categoria: decisão A de 10/09) |
| `dn/pipeline.py` · etapa 4 | **4 validações novas**: `categorias · participacao (vol) soma 100`, `(rs) soma 100` (±0,05 p.p.), `categorias · participacao vs LY = recalculo` (recálculo independente na curated) e `sparklines = series` (112 mini-linhas). 46 → **50** |
| `config/config.yaml` | `painel.abas` ganhou `{id: evolucao, rotulo: "Evolução", filtros: [categoria]}` na 2ª posição; `painel.rotulos.evo_todas/evo_foco/evo_total`; `categorias_top_n` (5) e `categorias_outras_rotulo` da F0 passam a ser lidos |
| `template/data-inventory.json` | 351 → **368** campos (participação ×4, spark ×6, `graficos.*` ×7) |

### Template

| Onde | Mudança |
|---|---|
| Abas | `tpl-aba-evolucao` novo, entre Visão geral e Clusters; o bloco "Cobertura mês a mês" (chips da chave, gráfico com LY, select Recorte, tabela da série, séries embutidas) **saiu inteiro** da Visão geral para lá |
| Visão geral | fica com a tarja de mês em andamento, os cards e a tabela "Por categoria · detalhe", que ganhou **Participação** (no volume ↔ no valor), **Δ part. vs LY** (p.p.) e **Últimos 12 meses** (mini-linha SVG com tooltip mês a mês; no CSV, os 12 valores) |
| Evolução por categoria | bloco novo: chips por categoria (★ nas foco), "Outras categorias" (soma das não selecionadas), botões "todas" e "só as foco"; gráfico de linhas na métrica do seletor com tooltip (categoria, mês, valor, % do canal); tabela categoria × 12 meses com "Outras" e "Total do canal", no componente padrão, com CSV. Padrão ao abrir: Top 5 do mês de referência + foco ligadas |
| Mini-linhas | também nas tabelas de supervisores e distribuidores (linhas por categoria do distribuidor: "—") |
| Estado | `DNE.evo` (ids selecionados; `-outras` quando desligada) em `localStorage` e URL (`&evo=`); valor inexistente volta ao padrão |
| `DnTabela` | colunas podem definir `csv()` (a mini-linha exporta os 12 valores) |
| JS novo | `dnSpark`, `dnColSpark`, `dnEvoInit/Padrao/LerEstado/Gravar/Toggle/Set/Linhas/Draw`; `dnAplicarMetrica` redesenha o gráfico de categorias; `dnAbaMontar` inicializa a Evolução |

### Docs

`docs/regras_negocio.md` (RN-46 → **vigente**; RN-50 aba Evolução vigente; RN-19 anota a estrela; 31 vigentes · 21 aprovadas ·
3 declaradas); `README.md` (changelog, parâmetros, navegação com 7 abas); `docs/RETOMADA.md` (§1, §4 abas, §5 pendência 9 →
publicar a F3 e propor a F4, §6 armadilha da Evolução, §7); este relatório.

## (b) Por quê

A.16 (Q3): a Visão geral estava acumulando cards, gráfico e tabela; separar o temporal numa aba própria deixa a abertura como
foto do mês. A.11 (D8, D9): ver categorias crescendo ou caindo sem 10 linhas ilegíveis, com Top N e "outras" que fecham com o
total, e participação/sparkline na tabela para leitura rápida.

## Prova

| Checagem | Resultado |
|---|---|
| Pipeline (`20260910-215626-7bc23d`, sem template) | 50 validações ok; participação soma 99,99% (t) e 100,01% (R$); Δ vs LY = recálculo nas 10 categorias; 112 mini-linhas = séries; HTML 7,97 MB |
| Completa (`20260910-220334-d2f933`, `--regerar-exemplo --sem-publicar`) | exemplo regerado; byte a byte ok; **50 ok**; abas template = config (7); 0 campos fora do inventário; HTML **7,99 MB**; números iguais (124.600 · 71.478 · 57,4% · 1.199,9 t · 71 · RTM 1762/1589/173) |
| Navegador (servidor local) | Visão geral só com a tabela de categorias (Participação 31,0% em Amendoim, Δ part. −3,9 p.p., 10 mini-linhas com tooltip "set/25: 383,7 · out/25: 413,3 · …"); aba Evolução com os dois blocos: gráfico de cobertura igual ao publicado (chips PDVs / Volume · t) e evolução por categoria com Top 5 + foco ligadas (★ Amendoim, ★ Gomas, ★ Regaliz, ★ Gelatina, Bala) e "Outras", 6 linhas e 72 pontos, tooltip "Amendoim · set/25: 383,7 t · 35,0% do canal"; tabela com Outras 161,2 e Total 1.199,9 (selecionadas + outras = total); desligar Amendoim: 5 linhas e Outras 533,3; "só as foco" e "todas" funcionam; em R$: eixo em mi, tooltip "R$ 13.525.070 · 38,2% do canal", tabela em R$; URL `evo=GOMAS,REGALIZ,GELATINA,BALA`; nota "não se aplica aqui: segmento, distribuidor" com chips esmaecidos; mini-linhas em 14 supervisores e nas 71 linhas totais de distribuidores ("—" nas linhas por categoria); CSV de categorias `scorecard-dn_categorias_2026-08_t.csv`; teclado → da Visão geral leva a Evolução; 375 px sem rolagem; **console sem erro** |
| Tamanho | 7,93 → **7,99 MB** (+0,06 MB) |

## (c) O que ficou pendente

- Resumos da aba Evolução (D17) ficam para a F9; acumulados e calendário para a F5.
- Próxima fase: **F4** (filtro por Supervisor; cubos `DN_SUPERVISOR_CAT_MES` e `DN_CLUSTER_CAT_MES`; retrato mensal da hierarquia).

## (d) Checklist para você

Abra `data/dn/painel/Scorecard_DN_2026-08.html` (Ctrl+F5) — é o gerado, ainda não publicado.

- [ ] Sete abas; a Visão geral abre só com cards e a tabela de categorias.
- [ ] Tabela de categorias: "Participação" (Amendoim 31,0%), "Δ part. vs LY" (−3,9 p.p.), mini-linha com tooltip mês a mês; em "Valor · R$" a participação vira 34,0%.
- [ ] Aba Evolução: o gráfico de cobertura está igual ao publicado (chaves, LY, recorte por categoria).
- [ ] Evolução por categoria: 5 chips ligados (as 4 ★ e Bala) mais "Outras"; a tabela fecha com o total do canal; desligar uma categoria a move para "Outras"; "só as foco" e "todas"; trocar para R$ redesenha; passar o mouse nos pontos mostra a participação.
- [ ] Copiar a URL com `evo=` e abrir em outra aba: mesma seleção.
- [ ] Chips Segmento e Distribuidor esmaecidos em Evolução, com a nota ao lado das abas.
- [ ] Clusters e supervisores e Distribuidores: mini-linhas na última coluna; nas linhas por categoria de Distribuidores aparece "—".
- [ ] Console (F12) sem erro; setas ←/→ passam pela aba nova.
- [ ] Com o ok: `python run_dn.py --mes 2026-08` publica.
