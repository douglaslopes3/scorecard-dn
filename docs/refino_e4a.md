# Refino do painel · Etapa E4a · mês fechado + parcial no mesmo arquivo, dados comprimidos, publicação do parcial

13/09/2026. Plano aprovado pelo Douglas: seletor Mês já nesta etapa; histórico começando em set/24 (fica para a E4b); Pontos de
venda com mês antigo mostram o fechado com etiqueta (E4b); reduzir e medir antes de decidir limite; E4 dividida em E4a e E4b.
Decisões de origem: D2, D4, D5, D22 de `docs/refino_painel_proposta.md`. **Gerada com `--sem-publicar`; checklist único no fim.**

## (a) O que mudou

| Onde | Mudança |
|---|---|
| Execução padrão | `python run_dn.py` (sem `--mes`) gera o arquivo do mês em andamento (set/26 parcial) **com o último mês fechado (ago/26) dentro**. `--mes 2026-08` continua gerando só ago/26 |
| Publicação | `publicacao.publicar_mes_em_andamento: true`: o parcial passa a ser publicado (D2). Nesta etapa nada foi publicado |
| Pipeline | Nova etapa **2b · mês fechado**: com os mesmos cubos mensais, refaz para o mês fechado só o que depende do mês de referência (base ativa dos PDVs, carteira, máscara PDV × categoria, RTM, PDVs distintos do acumulado, meses de histórico dos distribuidores). Nada disso é gravado na curated |
| Seletor Mês | Primeiro item da lateral: "set/26 parcial" e "ago/26". Abre no parcial (o mês vem só da URL, não fica lembrado no navegador); vale em Visão Geral, Supervisores e distribuidores, Pontos de venda e RTM; some na Penetração (sempre no mês fechado, a linha de filtros ativos mostra ago/26) |
| O que troca com o mês | Cabeçalho (mês, PARCIAL, janela da base ativa); aviso de mês em andamento (só no parcial); cards e linha de acumulado (valores e rótulos do ano); "O que aconteceu no mês"; tabelas de categorias, supervisores, distribuidores e clusters; cards, destinos e clientes do RTM (e o drill no mês escolhido); lista de PDVs e carteira |
| RTM | Num mês anterior ao corte da migração (01/09/2026), a visão "a partir da migração" fica desabilitada e o RTM mostra o histórico completo |
| Dados comprimidos (D22) | As tabelas do mês vão num pacote comprimido por mês e as fixas (Penetração, série do RTM) num pacote único; o navegador abre tudo antes da primeira aba, com o aviso "carregando os dados do painel…" |
| Lista de PDVs combinada (D22) | Uma lista só com 130.560 pares distribuidor × PDV: cadastro uma vez e as colunas de cada mês (nulo quando o par não está na base ativa daquele mês) |
| Validações novas | `comprimidos · pacotes = tabelas de cada mes` · `pdv · lista combinada = listas de cada mes` (254.223 linhas conferidas coluna a coluna) · `mes fechado · cards do canal = fato` · `mes fechado · acumulado de PDVs distintos = fato` · `mes fechado · RTM estados = mensuraveis` · `mes fechado · lista de PDVs = base ativa`; a da lateral passa a exigir o Mês |
| Config | `publicar_mes_em_andamento: true`; filtro `mes` nas abas; rótulos `lateral_mes`, `carregando` |
| Código | `dn/pipeline.py` (`calcular_fechado`, validações), `dn/painel.py` (`combinar_pdv_blobs`), `dn/tabelas.py` (`pacote_mes`, `comprimidos`), `dn/render.py` (`preparar` com meses extras), `template/template.html`, `template/data-inventory.json` (+10 campos) |
| Documentos | `docs/regras_negocio.md`: RN-02, RN-26, RN-52, RN-56, RN-59 com a nota da E4a |

Backup antes da E4a: scratchpad da sessão, pastas `backup_pre_E4a` (código) e `curated_ago26` (curated e JSON de ago/26 para a comparação).

## (b) Por quê

O time precisa acompanhar o mês enquanto ele acontece (D2) sem perder o mês fechado como referência. Um arquivo só, abrindo no
parcial, com a troca na lateral. A compressão e a lista combinada mantêm o arquivo menor que o de hoje mesmo com dois meses.

## (c) Resultado e pendências

| Item | E3 (só ago/26) | E4a (set/26 parcial + ago/26) |
|---|---|---|
| HTML | 11,6 MB | **9,9 MB** |
| Validações | 111 ok | **117 ok** |
| Tempo da execução | ~6,5 min | ~7 a 14 min (a etapa 2b soma ~1,5 a 2 min; o cálculo variou de 4,5 a 12 min entre execuções nesta máquina) |
| ago/26 dentro do arquivo × execução só de ago/26 | — | **idêntico**: 7 tabelas (distribuidores, supervisores, clusters, categorias, categorias × supervisor, destinos e clientes RTM), cards dos 3 segmentos, RTM e os 129.359 pares da lista de PDVs coluna a coluna; 57 pares de carteira |
| set/26 parcial | — | base ativa 120.742 · positivados 15.644 · DN 13,0% · 201,2 t · 67 distribuidores · RTM aderência 2,7% (43) |
| Avisos | 3 | 9: os 3 de sempre repetidos para o mês fechado e o parcial, e "4 distribuidores ainda sem venda em set/26" (PROPEC, NAIELEN Mandaguaçu, AVANTE, MAM Feira de Santana) |

Execução de prova sem `--regerar-exemplo` (`resumo_20260913-185440-67a689.json`): renderizador validado byte a byte, 117 ok, HTML
idêntico ao testado no navegador (md5 `45706e741417bfb4d7ddf975b8a129e0`, 10.341.466 bytes).

Defeitos achados nos testes e corrigidos antes da entrega:
1. PDVs distintos do acumulado do Ano Calendário no ago/26 contavam até set/26 (138.541 em vez de 137.592); agora são recontados até o mês fechado.
2. "Meses de histórico" dos distribuidores no ago/26 saía com um mês a mais; agora é contado até o mês fechado.
3. O período dentro dos cards aparecia em maiúsculas.
4. Com ago/26 escolhido, a linha de acumulado dizia "Ano fiscal 2027 … vs FY26"; os rótulos do ano agora trocam com o mês.

Regra registrada: a divisão Base atual × Novos dos cubos é a do mês de referência; se algum distribuidor mudar de segmento entre
o mês fechado e o parcial, o log avisa (em 13/09/2026: nenhum).

Pendências para a E4b: histórico desde set/24 no seletor; Pontos de venda com mês antigo mostrando o fechado com etiqueta; evolução
por categoria seguindo o Segmento; gráfico das linhas por categoria; medir o tamanho com os 25 meses.

## (d) Checklist para o Douglas (arquivo `data/dn/painel/Scorecard_DN_2026-09.html`)

1. Ao abrir aparece "carregando os dados do painel…" por um instante e o painel abre em **set/26 parcial**, com o aviso de mês em andamento e "PARCIAL" no cabeçalho.
2. Lateral: primeiro item "Mês" com set/26 parcial e ago/26.
3. Trocar para ago/26: cards 124.800 · 53.322 · 71.478 · 57,3% · 1.199,9 t; o aviso some; acumulado "Ano fiscal 2026 (set/25–ago/26): 13.133,5 t · 150.453 PDVs distintos · vs FY25".
4. Voltar para set/26: números do parcial (base ativa 120.742, DN 13,0%).
5. "O que aconteceu no mês", categorias, Supervisores e distribuidores mudam com o mês.
6. Pontos de venda: set/26 e ago/26 mostram listas diferentes (124.864 e 129.359 pares); carteira Destaque/Prime/Todos funciona nos dois.
7. RTM: em set/26 aderência 2,7%; em ago/26 aderência 13,4% (213 · 93 · 1.283), com a visão "a partir da migração" desabilitada.
8. Penetração: o seletor Mês some e a linha de filtros ativos mostra ago/26.
9. Voltar da lateral volta também o mês.
