# Evolução · Fase F6 — aba Penetração: benchmark, lojas a positivar, fator observado, potencial (11/09/2026, madrugada)

Executada após a F5 (`docs/evolucao_f5.md`, publicada 10/09 23h44) e a aprovação da proposta da F6 (P1–P9; Q-a recorrência fica
para a F7; Q-b lojas a positivar e potencial por cluster no grão distribuidor × cluster × categoria; Q-c potencial em regime como
coluna rotulada; Q-d aba entre Pontos de venda e RTM; Q-e cards e gráfico seguem o chip de Categoria) pelo Douglas em 10/09/2026.
Regras implementadas: **RN-27** (competência = último mês fechado), **RN-28/RN-29** (réguas), **RN-30** (benchmark P75),
**RN-31** (lojas a positivar), **RN-34/RN-35** (potencial de entrada com fator observado; em regime), **RN-36** (cores 95/70),
**RN-19** (cards sobre as foco), **RN-45** (referências fixas com filtro), **RN-38** (máscara PDV × categoria **medida**) e a aba
de **RN-50**. Sem regra nova.

**Publicado em 11/09/2026 às 07h33** (execução `20260911-073129-a0f1a3`, 86 validações ok, md5 `b3fdb0703fe2dcb1a1fc1419cf655d54`, 10.353.006 bytes), após o ok do Douglas no checklist (d). Prova final antes da publicação: execução `20260911-002646-e8477a`.

## (a) O que foi alterado

### Pipeline

| Arquivo | Mudança |
|---|---|
| `dn/metrics.py` | `mes_em_andamento` veio de `painel.py`; `mes_fechado(meses, mes_ref)` (RN-27). **`penetracao(c, T)`**: benchmark P75 por categoria entre os distribuidores com venda na categoria no mês fechado (RN-30); kg/loja e R$/loja por distribuidor × categoria = média por loja compradora **truncada no P99** da categoria, média do canal com < 30 lojas (marcado); **fator observado** por categoria = kg médio no 1º mês das lojas com a **1ª compra da categoria** na janela de 5 meses (já ativas no canal antes) ÷ kg médio dos compradores na janela; **lojas a positivar** no grão distribuidor × categoria = (P75 − pen_d) × positivados_d ÷ 100 para quem está abaixo (RN-31), e no grão distribuidor × cluster × categoria (Q-b); potencial de entrada = a positivar × kg/loja × fator, em regime = sem fator (RN-34/35); % da referência e cor (RN-36); categorias por loja por nível; níveis (canal, segmentos, supervisores com e sem segmento, clusters com e sem segmento, distribuidores) por **soma dos distribuidores** com a penetração do nível vinda do cubo (RN-45); máscara PDV × categoria por par da base ativa (10 bits) **medida** em gzip+base64 (RN-38). Tabelas novas: `DN_PEN_BENCHMARK` (10), `DN_PEN_DIST_CAT` (710), `DN_PEN_DIST_CLUSTER_CAT` (7.390), `DN_PEN_NIVEL_CAT` (1.400), `DN_PEN_NIVEL` (140), `DN_PEN_META` (1), `DN_PDV_CAT_MASCARA` (129.148) |
| `dn/painel.py` | `J["penetracao"]` (competência, textos, referência, aviso, limiares, foco, janela do fator, medição da máscara, `benchmarks[]`); listas `pen_nivel_cat` (nível × categoria, chaves `nivel, seg_id, sup_id, cluster, dist_nome`), `pen_nivel` (cards por nível, com "maior oportunidade"), `pen_supervisores` e `pen_clusters` (foco em colunas `pen_f1..f4`, `pb_f*`, `cor_f*`, `apos_f*` + totais) |
| `dn/tabelas.py` | tabelas `pen_nivel_cat`, `pen_nivel`, `pen_supervisores`, `pen_clusters` |
| `dn/pipeline.py` · etapa 4 | **19 validações novas**: `penetracao · competencia = ultimo mes fechado`, `benchmark · P75 = recalculo` (percentil independente), `benchmark · fixo por categoria` (1.400 linhas), `a positivar · niveis = Σ distribuidores` (1.400 linhas, inclusive clusters), `a positivar · canal = recalculo` (fórmula refeita do zero), `potencial · = a positivar × kg/loja × fator` (710 linhas), `kg/loja · truncado P99 e minimo de lojas`, `fator · observado > 0 ou nulo sem lojas novas`, `categorias por loja · recalculo na fato`, `mascara PDV x categoria · medicao registrada`, `penetracao · cores e competencia no HTML`, e `tabela pen_* · registros` + `host no HTML` (4 tabelas). 67 → **86**. `import numpy` no pipeline |
| `config/config.yaml` | `painel.abas` ganha `{id: penetracao, rotulo: "Penetração", filtros: [segmento, categoria, distribuidor, supervisor]}` antes de RTM; `painel.rotulos.pen_todas`; `painel.textos.pen_competencia`, `pen_competencia_parcial`, `pen_referencia`, `pen_fator_indisponivel`, `pen_censura`, `pen_media_canal`, `pen_acima_referencia`; todas as chaves de `regras.penetracao` e `regras.potencial` (F0) passam a ser lidas; `painel.pdv_categoria` lida (medir) |
| `template/data-inventory.json` | 503 → **657** campos (`penetracao.*`, `penetracao.benchmarks.*`, `pen_nivel_cat.*`, `pen_nivel.*`, `pen_supervisores.*`, `pen_clusters.*`) |

### Template

| Onde | Mudança |
|---|---|
| Aba **Penetração** (`tpl-aba-penetracao`) | cabeçalho com competência, definição das réguas, referência, lojas a positivar, potencial e o aviso "oportunidade calculada, não previsão"; nota do recorte; **4 cards** (Categorias por loja "2,7 de 10" · Lojas a positivar nas foco · Potencial de entrada nas foco · Maior oportunidade) ou, com um chip de Categoria, os 4 cards daquela categoria (penetração vs referência com cor, a positivar, potencial de entrada com a memória "a positivar × kg/loja × fator", potencial em regime); linha "Todas as 10 categorias"; **gráfico** barras pareadas penetração × referência (★ foco em azul, outras em cinza-azulado, potencial sobre o par, tooltip com a memória); **tabela por categoria** (lojas, penetração ÷ positivados, % cobertura ÷ base ativa, referência, % da referência com cor, a positivar, kg/R$ por loja, fator, potencial de entrada, em regime, nº de distribuidores com média do canal); **por supervisor** e **por cluster** (segmento da barra; penetração em cada foco com cor; a positivar e potencial nas foco e nas 10); **por distribuidor** (linha por distribuidor × categoria; com "Todas" mostra as foco; "(canal)" marca kg/loja da média do canal) |
| JS | `dnPenNivel()` (distribuidor > supervisor(+segmento) > segmento > canal), `dnPenRows/Row` (linhas pré-calculadas, nada somado), `dnPenCards`, `dnPenDraw`, `dnPenAplicar` (chamado por filtros, métrica e ao montar), colunas com cor (`dnPenColPct`), `DN_PEN` do JSON |
| Filtros | Segmento, Categoria, Distribuidor, Supervisor e Métrica agem; Calendário esmaecido ("não se aplica aqui: calendario") |
| Definições | parágrafo "Penetração" com réguas, referência, a positivar (inclusive o distribuidor sem venda na categoria), fator e censura, potencial, cores, máscara |
| CSS | `.pen-v` / `.pen-r` (limiares do config chegam em `DN_PEN`) |

### Docs

`docs/regras_negocio.md` (RN-19, 27, 28, 30, 31, 34, 35, 36, 45 → **vigente**; RN-38 medida; RN-50 aba Penetração; 45 vigentes ·
7 aprovadas · 3 declaradas); `README.md` (changelog, parâmetros); `docs/RETOMADA.md` (§1, §4 abas, §5 pendência 9 → publicar
a F6 e propor a F7, §6 armadilha, §7); este relatório.

## (b) Por quê

A.1–A.3, A.7, A.8, A.14: a penetração já era calculada, mas sem régua de comparação nem tradução em oportunidade. O P75 por
categoria vira a referência fixa; o gap é somado no grão distribuidor × categoria (a unidade em que a ação acontece), nunca como
gap do nível; o potencial usa um fator **observado** no lugar da premissa de 50% do print, com a memória de cálculo à vista e o
aviso de que é oportunidade calculada. Tudo no mês fechado para não inflar gap com mês parcial.

## Números do canal em ago/26 (para conferência)

| Categoria | Penetração | Referência P75 | % da referência | Lojas a positivar | kg/loja | Fator | Potencial de entrada | Em regime |
|---|---|---|---|---|---|---|---|---|
| ★ Amendoim | 55,7% | 71,4% | 78,0% | 12.824 | 9,3 | 34,4% | 23,4 t/mês | 67,9 |
| ★ Gomas | 53,5% | 60,1% | 89,0% | 6.640 | 8,3 | 49,4% | 14,8 | 29,9 |
| ★ Regaliz | 41,8% | 48,4% | 86,4% | 6.356 | 4,2 | 47,5% | 10,5 | 22,0 |
| ★ Gelatina | 38,1% | 43,8% | 87,0% | 6.111 | 3,6 | 54% | 9,9 | — |

Cards do canal: categorias por loja **2,7 de 10** · lojas a positivar nas foco **31.932** · potencial de entrada nas foco
**58,4 t/mês** · maior oportunidade **Amendoim** (+23,4 t/mês). Todas as 10: 61.285 a positivar · 115,0 t/mês de entrada ·
234,8 t/mês em regime. Lojas a positivar das foco batem com o Anexo C.2 (fórmula reproduzida antes da proposta).

## Pontos a confirmar (não mudam as 4 foco)

- **Distribuidor sem venda na categoria** entra em "lojas a positivar" com penetração 0 (letra da RN-31: "d ∈ nível"). Nas foco
  todos os 71 vendem; afeta Compound, Pirulito, Jubes e Granulado. Se preferir excluir quem não vende a categoria (como o benchmark
  faz), é uma linha de código e a validação acompanha.
- **Fator observado acima de 1** é mantido como observado com aviso no log (não ocorreu em ago/26; o maior foi Pirulito 80%).
- A tabela "Por cluster" aplica a referência da categoria **dentro do cluster** (Q-b): um distribuidor pode estar acima do P75 no
  total e abaixo num cluster.

## Correções feitas durante a prova

| Sintoma | Causa | Correção |
|---|---|---|
| `NameError: np` na validação | `pipeline.py` não importava numpy | `import numpy as np` |
| host das tabelas `pen_nivel_cat`/`pen_nivel` "AUSENTE" | elas alimentam cards, gráfico e tabelas sem componente próprio | checagem aceita `id="dados-<tabela>"` para elas |
| HTML 10,1 MB | chaves redundantes (k1, k2, nome, dist_id, supervisor_id, segmento_id) nas 1.400 linhas nível × categoria | casamento por (nivel, seg_id, sup_id, cluster, dist_nome); 9,9 MB |
| helper `_txt` sombreado dentro de `montar` | nome repetido | renomeado `_ptx` |

## Prova

| Checagem | Resultado |
|---|---|
| Passo 1 (`20260911-000621-612e08`) | 10 validações novas ok; benchmark = recálculo; a positivar canal = recálculo (Amendoim 12.824 · Gelatina 6.111 · Gomas 6.640 · Regaliz 6.356); 127 de 710 linhas com média do canal; fator abr–ago/26 Amendoim 34%, Gelatina 54%, Gomas 49%, Regaliz 48%; categorias por loja 2,70 = recálculo; máscara 129.148 pares = 0,19 MB (cabe) |
| Passo 2 (`20260911-000621-612e08` + JSON, aba ainda sem template) | JSON com 1.400 + 140 + 31 + 35 linhas; inventário 657; 0 campos fora do inventário |
| Completa (`20260911-002646-e8477a`, `--regerar-exemplo --sem-publicar`) | exemplo regerado; byte a byte ok; **86 ok**; 8 abas = config; HTML **9,9 MB**; números iguais (124.600 · 71.478 · 57,4% · 1.199,9 t · 71 · RTM 1762/1589/173) |
| Navegador (servidor local, recarga limpa) | aba montada; cards do canal (2,7 de 10 · 31.932 · 58,4 t/mês · Amendoim +23,4); linha "todas as 10"; gráfico com 10 pares (★ primeiro) e potencial sobre cada par; tabela por categoria com 12 colunas e cores (30 verdes, 54 vermelhas na aba); supervisores 14 de 31 (segmento "todos"), clusters 12 de 35, distribuidores 25 de 284 (foco) de 710; supervisor Murilo Cunha: cards 2,4 · 756 · 1,0 t/mês, linha destacada, 8 linhas de distribuidor; Murilo + Novos: "Sem dado" (não tem distribuidor no segmento); Novos: 2,3 · 3.714; distribuidor Distrilobo: 2,9 · 1.672 · 3,5 t/mês, 4 linhas; chip Amendoim: cards da categoria (55,7% · 12.824 · 23,4 t/mês com "12.824 × 9,3 kg/loja × fator 34,4%" · 67,9); R$: "R$ 873.442/mês", "R$ 345/loja", colunas em R$; chips do calendário esmaecidos com a nota; 375 px sem rolagem horizontal; 0 NaN; **console sem erro** |
| Tamanho | 9,1 → **9,9 MB** (+0,8 MB: 1.400 linhas nível × categoria com ~25 campos, 710 de distribuidor; estimado em P6 +0,35) |

## (c) O que ficou pendente

- Ativação "a ativar (janela)" e recorrência mensal (RN-32, RN-33), drill nominal dos PDVs a positivar e a decisão de embutir a
  máscara (0,19 MB, cabe): **F7**. Matriz: F8. Resumos: F9.
- Os dois pontos a confirmar acima (distribuidor sem venda na categoria; fator > 1).

## (d) Checklist para você

Abra `data/dn/painel/Scorecard_DN_2026-08.html` (Ctrl+F5) — é o gerado, ainda não publicado.

- [ ] Aba "Penetração" entre Pontos de venda e RTM; topo com "Competência: ago/26 (último mês fechado)" e a referência P75.
- [ ] Cards: 2,7 de 10 · 31.932 · 58,4 t/mês · Amendoim (55,7% → 71,4%, +23,4 t/mês); linha "Todas as 10 categorias".
- [ ] Gráfico: 10 pares penetração × referência, ★ primeiro, potencial sobre cada par; tooltip com a memória.
- [ ] Tabela por categoria: Amendoim 12.824 a positivar · 9,3 kg/loja · fator 34,4% · 23,4 t/mês · regime 67,9; cores verde/vermelho na coluna "% da referência".
- [ ] Por supervisor e por cluster: penetração nas 4 foco coloridas; totais das foco e das 10.
- [ ] Por distribuidor: com "Todas" só as foco; escolher um chip de Categoria filtra e os cards viram os da categoria.
- [ ] Supervisor, Segmento e Distribuidor na barra mudam cards, gráfico e tabela de categorias (nota "no recorte selecionado"); Valor · R$ troca kg/loja e potenciais para R$.
- [ ] Chips do Ano esmaecidos nesta aba; console (F12) sem erro.
- [ ] Com o ok: `python run_dn.py --mes 2026-08` publica.
