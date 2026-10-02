# Reforma · Fase 3 — tabelas: amostra, busca, expansão e exportação (09/09/2026)

Proposta aprovada integralmente pelo Douglas em 09/09/2026 (P1–P6: expansão em passos de 200 com
teto 2.000; só CSV nas tabelas dos gráficos; selects "Ordenar por" e "linhas" dos PDVs substituídos;
CSV como exibido; clusters e supervisores como uma tabela cada; amostra 25).

## (a) O que foi alterado

| Arquivo | Mudança |
|---|---|
| `template/template.html` | **`DnTabela`** (≈ 200 linhas de JS): um componente para as 8 tabelas — barra com busca (debounce do config), filtros próprios da tabela, "mostrando X de Y registros", Expandir/Recolher, CSV; cabeçalho com ordenação por clique/Enter (`aria-sort`, ▲▼), 2 linhas quando há grupos (Δ Cobertura, Δ % de cobertura, Δ Volume); "Mostrar mais N" até o teto; linhas clicáveis (drills) e classes de linha (`sem`). **`DN_TAB_SPECS`**: as colunas de cada tabela (mesmos rótulos e ordem de antes), filtro externo (Segmento/Categoria/Distribuidor da barra global), filtros próprios (Situação nos PDVs; Estado e Destino nos clientes RTM) e resumo (PDVs sem compra e t na janela). As tabelas em HTML (`<thead>`/`<tbody>` com `{{#each}}`) saíram; no lugar, `<div class="dntab" data-tabela="…">` + `<script type="application/json" id="dados-…">{{{tabelas_json.…}}}</script>`. Clusters e supervisores: uma tabela cada, com a coluna `segmento_id` filtrada pela barra; os 3 blocos por segmento (`.mmlw`) saíram dessa aba. PDVs: os selects "Ordenar por" e "linhas", o campo de busca e o rodapé próprios saíram (o componente faz); o blob e `dnPdvCarregar` ficaram. RTM: a barra de chips/select/busca dos clientes virou filtros do componente. `dnDraw` (96 tabelas de série dos gráficos) ganhou só o botão CSV. `rtmf`, `dnPdvRender`, `dnPdvInfo` removidos |
| `dn/tabelas.py` (novo) | serializa os registros de cada tabela a partir do JSON **formatado** (mesmo contrato do inventário) e os parâmetros do componente |
| `dn/render.py` | `preparar(JF)` acrescenta `tabelas_json.*` e `tabela_cfg_json`; exemplo reduzido sem a lista `pdvs` |
| `dn/painel.py` | a lista `pdvs` (20 maiores por distribuidor, 1.400 linhas) e `pdv_top_por_distribuidor` saíram: a tabela nasce do blob completo |
| `config/config.yaml` | `painel.tabela.expandir_passo: 200`, `expandir_maximo: 2000`; `pdv_top_por_distribuidor` removido |
| `template/data-inventory.json` | 239 campos: `tabelas_json.*` (7), `tabela_cfg_json`, `rtm.clientes.{cidade, uf}`; os 17 `pdv.*` e `meta_execucao.pdv_top_por_distribuidor` saíram |
| `dn/pipeline.py` | etapa 4: para cada tabela, nº de registros no JSON embutido = linhas da tabela DN_* do mês (7 checagens); nenhum `<tbody>` na marcação do template; host de cada tabela presente no HTML (7) |

## (b) Por quê

Requisitos da Fase 3 do prompt e achados P8 (JS próprio por tabela, 35 funções mortas) e P6 da
auditoria. Decisão A3: a base completa continua embutida; o botão CSV exporta só o que está
filtrado e ordenado em tela.

## Prova (execução final e teste no navegador, sem nenhum erro de console)

| Checagem | Resultado |
|---|---|
| Validações do pipeline | 31 ok (16 anteriores + 15 de tabelas); registros embutidos: clusters 35, supervisores 31, categorias 10, distribuidores 70, rtm_serie 13, rtm_destinos 27, rtm_clientes 1.762 = curated; HTML 5,6 MB (era 6,1: as 1.400 linhas estáticas de PDV e as 1.762 de clientes RTM saíram do HTML; os dados vão em JSON compacto) |
| Amostra | Distribuidores abre com "mostrando 25 de 70 registros"; Categorias (10) abre completa com Expandir desabilitado |
| Expandir / Recolher | Distribuidores: 70 linhas, botão vira "Recolher"; PDVs: 200 linhas, "Mostrar mais 200" → 400 |
| Ordenação | clique em "% de cobertura": 100,0% · 100,0% · 100,0% (desc, `aria-sort=descending`); 2º clique: 0,6% · 25,1% · 35,5% (asc). PDVs abrem por kg na janela desc (24.528 · 18.690 · 13.261) |
| Busca | Distribuidores "ebd": 11 de 70 (todas as filiais EBD); PDVs "padaria" com Situação = sem compra: 2.866 de 124.395; PDVs "mercado": 16.814, resposta em ~350 ms + debounce |
| Filtros próprios | PDVs Situação = "Sem compra no mês": 50.634 (igual ao número do card); RTM clientes Estado = "Não compraram": 1.029; + Destino = DISO: 309 (bate com a tabela de destinos); select de destinos com 27 opções + "Todos" |
| Filtros globais | Segmento = Novos: Clusters 11 de 35, Supervisores 3 de 31, Distribuidores 3 de 70; Categoria = GOMAS: Categorias 1 de 10; Distribuidor = AVANTE: PDVs 4.069 |
| Drills | clique na linha de supervisor abre `ds-novos-…`; clique em distribuidor abre `dd-…` |
| CSV | distribuidores com busca "ebd": 11 linhas + cabeçalho, `;`, aspas, valores como exibidos ("≥ 13", "47,9%"), BOM EF BB BF; nome `scorecard-dn_distribuidores_2026-07_busca-ebd.csv`; cabeçalho sem `<br>` |
| Números do painel | inalterados: jul/26 · 120.817 · 73.185 · 60,6% · 1.279,5 t · 70 · RTM 1.762/1.309/453 |

## Ajuste de 09/09/2026 (noite) · seta no lugar do botão "Expandir"

O botão "Expandir" da barra ficava esmaecido nas tabelas que cabem na amostra (Categorias 10,
Clusters 12, Supervisores 14, RTM Evolução 13) e o comportamento não se explicava sozinho. A pedido
do Douglas, o botão saiu; entrou um **rodapé na própria tabela** que só aparece quando há mais
registros do que a amostra: "▼ mostrar os outros 45 registros" (tudo de uma vez quando o restante
cabe num passo) ou "▼ mostrar mais 200 (restam 124.370)" nas tabelas grandes, e "▲ recolher para 25"
quando expandida. Tabela que cabe na amostra não mostra nada. Vale também dentro do drill do RTM.
Testado: Distribuidores 25 → 70 → 25; Categorias sem rodapé; PDVs 25 → 225 → 425 → 25; drill
199 → 25 → 199. Publicado no mesmo dia.

## (c) O que ficou pendente

- Nada da Fase 3. Virtualização não foi necessária (teto de 2.000 linhas em tela).
- O download do CSV depende do navegador permitir `a.download` (Chrome/Edge sim; abrir o HTML de
  dentro do Teams/SharePoint em visualizador embutido pode bloquear downloads).

## (d) Checklist de validação

- [ ] Distribuidores: abre com 25 linhas e "mostrando 25 de 70"; Expandir mostra 70; clicar em "% de cobertura" ordena (▼/▲); digitar "ebd" na busca deixa 11; CSV baixa `scorecard-dn_distribuidores_2026-07_busca-ebd.csv` e abre certo no Excel (acentos, `;`).
- [ ] Pontos de venda: abre com os 25 maiores por kg na janela; Situação "Sem compra no mês" mostra 50.634 (o mesmo do card); buscar um PDV por nome/CNPJ/cidade/bairro; Expandir e "Mostrar mais 200"; CSV do filtro.
- [ ] RTM › Clientes: chips de Estado e select de Destino filtram; busca por nome/CNPJ/cidade; CSV.
- [ ] Clusters e supervisores: com Segmento "Novos" mostram 11 e 3 linhas; clicar num supervisor abre a série mensal.
- [ ] Gráfico de 13 meses: botão CSV abaixo da tabela da série.
- [ ] Nenhum número mudou em relação à versão anterior (cards, séries, tabelas).
