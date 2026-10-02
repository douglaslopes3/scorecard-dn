# Reforma · Fase 2 — navegação por abas (09/09/2026)

Proposta aprovada integralmente pelo Douglas em 09/09/2026: seis abas, filtros de segmento e
categoria na barra global, filtros e aba persistidos, aba padrão "Visão geral".

## (a) O que foi alterado

| Arquivo | Mudança |
|---|---|
| `template/template.html` | O conteúdo foi **reagrupado em 6 `<template id="tpl-aba-…">`**, um por aba, sem alterar o HTML interno dos blocos (cards, tabelas, gráficos, drills, notas). Nova barra `<nav role="tablist">` sticky com os botões vindos de `{{#each abas}}`. A barra de filtros virou global (`#dnfiltros`): os chips de **Segmento** subiram do bloco de KPIs e os de **Categoria** já estavam lá; o select de Distribuidor não mudou de lugar. A barra "Alavanca · Distribuição Numérica" (um botão só, resquício do protótipo) saiu. Duas frases de nota que diziam "o filtro acima" passaram a dizer "da barra no topo". CSS novo só para `.dntabs`, `.dnpanel`, `.fchip.na` e impressão. JS novo: controlador de abas (`dnAbaAbrir`, `dnAbaMontar`, `dnAplicarFiltros`, `dnFiltrosAplicabilidade`, `dnEstadoLer/Gravar`); `dnCat`, `dnSeg`, `fdist` passaram a escrever no estado global e reaplicar; as chamadas de carga (`dnDraw`, `dnColor`, `rtmf`, `dnPdvCarregar`) saíram do fim do script e são feitas por aba, ao montar |
| `config/config.yaml` | `painel.abas` (id, rótulo, ordem, filtros aplicáveis) e `painel.aba_padrao` |
| `dn/painel.py` | bloco `abas` no JSON (id, rótulo, filtros, padrão) a partir do config |
| `dn/render.py` | entidade `abas → aba` no formatador |
| `template/data-inventory.json` | `aba.{id, rotulo, filtros, padrao}` (246 campos) |
| `dn/pipeline.py` | etapa 4 ganhou 4 checagens: ids das abas no template = config (e na mesma ordem); toda seção `<h3>` dentro de um `<template>`; nenhuma aba vazia; nº de botões `role="tab"` no HTML = nº de abas |
| `template/example-data*.json`, `Scorecard_DN_base.html` | regerados (`--regerar-exemplo`) com o template novo |

Como o lazy funciona: o navegador não constrói DOM nem calcula layout para o que está dentro de
`<template>`. Ao abrir uma aba pela primeira vez o conteúdo é clonado para o painel, os
`<script>` inline das séries são recriados (clones de template não executam), os gráficos são
desenhados e os filtros aplicados. A lista completa de PDVs (4,9 MB em gzip+base64) só é
descompactada ao abrir "Pontos de venda". Trocar de aba depois disso é instantâneo.

Estado: `localStorage` (`scorecard_dn.estado.v1`) + URL (`#aba=…&seg=…&cat=…&dist=…`). A URL
vence o `localStorage`; valor que não existe mais no painel volta ao padrão.

## (b) Por quê

Auditoria §0.5: scroll único com 9 seções, 89% do DOM em duas tabelas, nenhuma persistência,
nenhum teclado/ARIA (P6, P7, P14). Requisitos da Fase 2 do prompt.

## Prova (execução `20260909-202110-920d3c` e teste no navegador)

| Checagem | Resultado |
|---|---|
| Validações do pipeline (etapa 4) | 16 ok: as 12 da Fase 1 + 4 de abas; HTML 6,1 MB; 0 avisos; números inalterados (jul/26 · 120.817 · 73.185 · 60,6% · 1.279,5 t · 70 · RTM 1.762/1.309/453) |
| Carga inicial | só "Visão geral" montada (132 `<tr>` em vez de 3.376); 5 `<template>` inertes; blob de PDVs não descompactado (`PDV.rows = null`) |
| Tempo de carga (navegador embutido, arquivo local via servidor) | DOMContentLoaded 191 ms · load 197 ms · 3.163 nós e 1.620 `<td>` no DOM (antes: 36.777 `<td>` construídos na carga) |
| Pontos de venda | ao abrir: 124.395 pares carregados, 50 linhas, texto "124.395 PDVs · 50.634 sem compra no mês" |
| RTM | ao abrir: 5 cards, 1.762 linhas, sub-abas Evolução/Destinos/Clientes intactas; nota "filtros da barra não se aplicam a esta aba" |
| Filtro Segmento = Novos | Distribuidores mostra só DIPAM GAÚCHA, UNIVALE, DISO (3); Clusters e supervisores mostra só o bloco `novos`; URL `#aba=distribuidores&seg=novos` |
| Filtro Categoria = GOMAS | painel `dnc2-__canal__-GOMAS` visível, linha GOMAS na tabela por categoria, select sincronizado; URL `#aba=visao&cat=GOMAS` |
| Filtro Distribuidor = AVANTE | tabela de distribuidores com 1 linha; PDVs: "4.069 PDVs de AVANTE · 2.623 sem compra" |
| Teclado | clique em "Visão geral", → → leva a "Distribuidores" com foco no botão; End leva a "Definições" |
| Persistência | recarga sem hash: reabre "Definições" com categoria GOMAS (do localStorage); `#aba=rtm` na URL: abre RTM |
| Console do navegador | nenhum erro em todo o teste |
| Responsivo | viewport 375 px: barra de abas com rolagem horizontal (616 px em 339 px), página sem rolagem horizontal (375 = 375); cards de KPI passam a 2 colunas abaixo de 700 px (regra nova, o estilo inline de 6 colunas os esmagava) |

## (c) O que ficou pendente

- Nada da Fase 2. As tabelas grandes (PDVs 1.400 linhas renderizadas, RTM Clientes 1.762)
  continuam estáticas dentro das suas abas: viram o componente da Fase 3 (amostra/expandir,
  busca com debounce, ordenação, CSV).
- Impressão: `beforeprint` monta todas as abas e as exibe; não testado em impressora real.

## (d) Checklist de validação

- [ ] Abrir `Painéis Comerciais/DN/Scorecard_DN.html` (Ctrl+F5): abre em "Visão geral" com os cards e o gráfico; nada de scroll longo.
- [ ] Clicar em cada uma das 6 abas: Clusters e supervisores · Distribuidores · Pontos de venda (a lista completa carrega em ~1 s e o rodapé diz "124.395 pares") · RTM (Evolução/Destinos/Clientes) · Definições.
- [ ] Segmento "Novos distribuidores": Distribuidores mostra 3 linhas; a nota à direita das abas diz que categoria não se aplica.
- [ ] Categoria "Gomas" em Visão geral: gráfico e tabela mudam; em "Pontos de venda" os chips de categoria ficam esmaecidos.
- [ ] Trocar de aba, fechar o navegador, abrir de novo: volta na mesma aba com os mesmos filtros.
- [ ] Colar a URL com `#aba=rtm` em outra janela: abre direto em RTM.
- [ ] Teclado: Tab até a barra de abas, setas ←/→, Home/End trocam a aba.
- [ ] Reduzir a janela: as abas rolam na horizontal; nada some.
