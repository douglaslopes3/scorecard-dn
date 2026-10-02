# Fase 3 · template com dados reais: busca de PDVs, campos novos, contrato atualizado

Executada em 08/09/2026. A partir daqui **`template/template.html` é a fonte da verdade** do painel (editado diretamente); `template/tools/build.py`, que gerava o template a partir do protótipo, fica como histórico e não deve mais ser rodado (ver `template/tools/README.md`). O exemplo `template/Scorecard_DN_base.html` e `template/example-data.json` passam a ser regenerados por `dn.render` a partir de `template/example-data.raw.json`.

## O que mudou no painel

| Bloco | Mudança | Dados |
|---|---|---|
| Cabeçalho | tag mostra mês de referência e a janela da base ativa | `periodo.janela_base_ativa` |
| Cards KPI (por segmento) | 6 cards: entra **"Sem compra no mês"** (base ativa − positivados = oportunidade) | `segmento.kpi.sem_compra_mes` |
| Chips de segmento | mostram o nº de distribuidores | `segmento.n_distribuidores` |
| Distribuidores | ordenados da menor para a maior DN; "≥" nos meses de histórico quando o histórico é censurado pelo início da série; drill mostra nome reduzido e supervisor | `distribuidor.{historico_censurado,nome_reduzido,supervisor}` |
| **Pontos de venda** | tabela passa a ser a **base ativa** (não só positivados), com busca por nome/CNPJ/cidade/bairro, filtro (todos / sem compra / positivados / RTM), ordenação (kg na janela, kg no mês, kg do último mês, último mês mais antigo) e limite de linhas. Colunas: positivado no mês e no anterior, meses na janela, último mês com compra, kg do último mês, kg na janela, kg no mês, RTM. Linhas sem compra no mês ficam destacadas. Antes da busca, os 20 maiores por kg na janela de cada distribuidor (renderizados no HTML) | `pdvs[]` (top N) + `pdv_blob` (lista completa) |
| Notas da visão | texto com as definições reais (positivado, janela de 5 meses, contagem por nível, LGPD, CNPJ de filial, N3, exclusões) | — |

## Como a lista completa de PDVs viaja

`dn.painel.blob_pdvs` grava toda a base ativa (jun/26: **118.371 pares distribuidor × PDV**) como JSON posicional compacto, gzip nível 9, base64, no campo `pdv_blob.b64`. O template o emite com `{{{pdv_blob.b64}}}` (sem escape HTML) e o navegador descompacta com `DecompressionStream('gzip')` (Chrome/Edge 80+, Firefox 113+, Safari 16.4+). Sem suporte, a tabela mantém os maiores por distribuidor e avisa. Tamanhos medidos: JSON 13,7 MB → base64 4,7 MB → HTML final 5,3 MB (o painel gerencial do outro projeto usa o mesmo padrão com ~7 MB).

## Contrato e validação

- `template/data-inventory.json` passou de 129 para 162 campos (`sem_compra_mes` em todos os níveis, `periodo.janela_base_ativa`, `segmento.n_distribuidores`, atributos novos de distribuidor, comparativos completos de categoria, `pdv.{cidade,ultimo_mes_compra,kg_ultimo_mes,kg_janela,origem_rtm,tipo_chave}`, `pdv_blob.*`, `meta_execucao.*`). Exemplos vêm de jun/26.
- Renderizador Python (`dn/render.py`) ganhou `{{{ }}}`. Continua provado byte a byte contra o exemplo do template a cada execução do `run_fase2.py`.
- Validação independente feita nesta fase: o Handlebars real (Node, `handlebars@4.7.8`) renderizou `template.html` com `painel_dn.json` e produziu **exatamente** o mesmo HTML do renderizador Python (5,5 MB), e o blob embutido descompactou em Node com os 118.371 registros.

## Gancho do de-para de clusters (C5)

`config/config.yaml → fontes.clusters` aponta para `bases/Bases para tabelas dimensões/Clusters_DePara.xlsx` (colunas `SEGMENTO MTRIX`, `CLUSTER PAINEL`). Enquanto o arquivo não existir, o `run_fase2.py` avisa e usa os 34 segmentos da Mtrix. Quando existir, o mapeamento é aplicado na carga; segmento sem linha no de-para mantém o próprio nome, com aviso. O esqueleto para preencher está em `data/dn/quality/segmentos_mtrix.csv`.

## Leitura dos dois números de "sem compra"

O card do canal mostra **49.308** (115.017 PDVs da base ativa − 65.709 positivados, PDV contado uma vez). A tabela de PDVs mostra **51.059** pares distribuidor × PDV sem compra (118.371 − 67.312), porque ali o PDV atendido por dois distribuidores aparece em cada um. Os dois estão certos pela regra da rodada 5; o card de cada distribuidor bate com a tabela filtrada por ele.

## Pendências que restam

Atualizado em 09/09/2026 — ver `docs/rodada_2026-09-09.md`, que incorporou jul/26 à série
(painel agora em jul/26, 70 distribuidores) e corrigiu o caminho da pasta de sell-out no config.

1. ~~Reextração de jul/26~~ — feita em 09/09/2026; `arquivos_ignorados` está vazio.
2. ~~De-para de clusters (C5)~~ — resolvido em 09/09/2026: `Clusters_DePara.xlsx` criado com a nomenclatura do projeto `Dashboards - Heads - Canais`, 34 segmentos da Mtrix em 12 clusters. Ver `docs/rodada_2026-09-09.md` §8.
3. ~~Data de início dos distribuidores (C3)~~ — resolvida em 09/09/2026 com a coluna `Data de Cadastro` no de-para: 64 dos 70 com data, 6 ainda censurados (PROPEC, AVANTE, EBD PA ×2, EBD AM, A.S DA S E SILVA). Medição em `docs/c3_medicao_2026-09-09.md`, implementação em `docs/rodada_2026-09-09.md` §7.
4. ~~Checagem visual~~ — feita em 09/09/2026 e achou um erro real na tabela da série (total somando os segmentos, 58 PDVs em dobro), corrigido no template; ver `docs/rodada_2026-09-09.md` §9. Nota original: checagem visual no seu navegador: o navegador embutido desta sessão não abriu arquivos locais; a prévia (hoje `data/dn/painel/Scorecard_DN_2026-07.html`) foi validada por script (zero placeholders, Handlebars real idêntico, blob descompactável).
