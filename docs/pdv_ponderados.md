# Carteira de PDVs ponderados na aba Pontos de venda (RN-56) — 11/09/2026

Pedido do Douglas em 10/09 (a aba Pontos de venda abre nos PDVs DESTAQUE da `DE-PARA_Ponderada_Clusters.xlsx`, com botões PRIME e
Todos) e em 11/09 ("seguir construindo com o que está OK"). Proposta `PDVs ponderados` (P1–P9, Q1–Q6) aprovada **como recomendada**
em 11/09/2026: Q1 abre em Destaque · Q2 linha inválida = aviso e segue · Q3 regra por CNPJ (o distribuidor já vendeu ao PDV na série)
· Q4 nome diferente = aviso, inclusive a linha 177 · Q5 par repetido ou PDV em dois clusters = linha fora com aviso · Q6 só Pontos de
venda. Regra nova: **RN-56** (vigente).

**Publicado em 11/09/2026 às 16h15** (execução `20260911-161300-beb5ea`, 118 validações ok, md5 `bb51bfbe4e2c3cdfcb67f24f1c4a98d1`, 11.164.977 bytes — o mesmo da prova `20260911-160600-2c3e1c`), após o "checklist ok" do Douglas. A linha 179 segue pela regra aprovada até a decisão dele.

## (a) O que foi alterado

| Arquivo | Mudança |
|---|---|
| `docs/regras_negocio.md` | ficha **RN-56 · Carteira de PDVs ponderados**, escrita antes do código (P1); vigente ao fim |
| `config/config.yaml` | `fontes.pdv_ponderada` (opcional: arquivo, aba `PONDERADA`, 5 colunas); `regras.carteira` (clusters válidos, exige compra na série, limite do aviso de nome, palavras ignoradas); `painel.pdv_carteira` (ativo, padrão `destaque`, rótulo, botões, textos da nota e das Definições) |
| `dn/manifesto.py` | a planilha entra nas bases observadas: trocá-la dispara a releitura |
| `dn/extract/cadastros.py` | `ler_pdv_ponderada`: lê a planilha como está (linha do Excel, CNPJs com 14 dígitos, razão social, cluster); nada é corrigido na leitura |
| `dn/pipeline.py` | ingestão grava `DIM_PDV_PONDERADA`; **3 validações novas**: `carteira · linhas = validas + invalidas`, `pares no HTML = validos na base ativa`, `botoes e padrao = config`. 115 → **118** |
| `dn/metrics.py` | `carteira()`: aplica a regra da RN-56 a cada linha e grava `DN_PDV_CARTEIRA` (situação, motivo, aviso de nome, meses com compra, última compra, na base ativa) e o relatório `data/dn/quality/carteira_pdv.md`; linha fora da regra vai para o log como aviso e **não aborta** |
| `dn/painel.py` | `carteira.json`: pares válidos da base ativa (chave = distribuidor da lista de PDVs + PDV), contagens por cluster, válidos que saírem da base ativa; o blob de PDVs **não mudou** |
| `template/template.html` | botões **Destaque · Prime · Todos os PDVs** na tabela de Pontos de venda (abre em Destaque; combinam com distribuidor, supervisor, Situação e busca; o CSV sai filtrado); nota da carteira acima da tabela; escolha guardada no navegador e na URL (`cart=`); **os atalhos da Penetração e da Matriz para esta lista abrem em Todos** (senão mostrariam só os 6 Destaque); parágrafo nas Definições |
| `template/data-inventory.json` | 733 → **738** campos |
| `README.md`, `docs/RETOMADA.md` | changelog, estado, pendências, armadilha, índice |

## (b) Por quê

Nome não serve para decidir se uma linha da planilha vale: a razão social aprova erros ("Mateus Supermercados" casa com um posto de
gasolina) e rejeita acertos ("DB Torquato" é loja da rede Supermercados DB). A regra por CNPJ é verificável na base e não depende de
interpretação: o distribuidor está no painel, o PDV existe na Mtrix, e esse distribuidor já vendeu para esse PDV. Linha inválida não
trava o painel, para você corrigir a planilha aos poucos; cada correção entra sozinha na próxima execução.

## Resultado em ago/26

| Cluster | Linhas na planilha | Válidas (na lista) | Fora da regra |
|---|---|---|---|
| DESTAQUE | 9 | **6** | 3 |
| PRIME | 172 | **51** | 121 |
| Total | 181 | **57** | 124 |

As 57 válidas estão todas na base ativa de ago/26. Motivos das 124 fora (uma linha pode ter mais de um): CNPJ do PDV é de distribuidor
32 (linhas 2–33) · esse distribuidor nunca vendeu para esse PDV 91 · PDV em dois clusters 2 (linhas 41 e 179) · distribuidor fora do
de-para 1 (linha 31) · fora do painel 1 (linha 68). Avisos de nome, que entram: linhas 121, 181, 182 (nome de loja da mesma rede) e 177.
Detalhe linha a linha em `data/dn/quality/carteira_pdv.md`.

DESTAQUE na tela: Super Vilton (EBD Aquiraz) · Supermercados DB ×2 (EBD Manaus: DB Torquato e DB Coroado) · Genival Argemiro da Silva
e Pai e Filho (EBD Caruaru) · **Bom Vizinho** (EBD Aquiraz: é a linha 177, "Pinheiro Supermercado" na planilha). Um deles sem compra
em ago/26.

### Uma afirmação minha estava errada

Na proposta escrevi que PDV em dois clusters "hoje não ocorre" (Q5). **Ocorre**: a linha 179 ("Preço Baixo", DESTAQUE, EBD PA) tem o
mesmo CNPJ de PDV da linha 41 ("Grupo Preço Baixo", PRIME, com distribuidor errado). Pela regra aprovada as duas saem, e por isso a
DESTAQUE ficou com **6, não 7**. Duas saídas possíveis:

1. **Corrigir na planilha** (recomendada): decidir se essa loja é DESTAQUE ou PRIME e deixar uma linha só. Não muda regra.
2. Mudar a regra para que o conflito só conte entre linhas que passam no resto (a 41 já está fora pelo distribuidor): a 179 volta
   hoje, mas o conflito reaparece quando a 41 for corrigida.

Nada foi mudado; é decisão sua.

## Correções feitas durante a execução

| Sintoma | Causa | Correção |
|---|---|---|
| cálculo abortou (`CNPJ_DISTRIBUIDOR not in index`) | no cálculo a coluna do distribuidor da fato chama `DIST` | `carteira()` e a validação usam `DIST` |
| aviso e depois erro de escape inválido em dois arquivos | barra invertida consumida ao gravar o código | trechos reescritos sem barra invertida; a compilação passou a tratar aviso como erro |

## Prova

| Checagem | Resultado |
|---|---|
| Ingestão completa (`--regerar-exemplo --sem-publicar`; o código dos leitores e o de-para de distribuidores mudaram) | 181 linhas lidas da planilha (PRIME 172, DESTAQUE 9); bases relidas em 360 s |
| Completa final (`20260911-160600-2c3e1c`) | byte a byte ok; **118 ok**; HTML **10,6 MB** (+0,01 MB); números iguais (124.600 · 71.478 · 57,4% · 1.199,9 t · 71 · RTM 1762/1589/173); avisos: os 4 destinos RTM de sempre + linhas fora da carteira + avisos de nome |
| Navegador (servidor local) | abre em Destaque com 6 PDVs e a nota "Carteira Destaque: 6 PDVs válidos de 9 na planilha · 3 fora da regra"; Prime 51; Todos 129.148; URL `cart=prime`/`cart=todos` e navegador guardam a escolha; Destaque + "Sem compra no mês" = 1; atalho "a ativar Amendoim" da Penetração abre em Todos com os mesmos 47.088 pares da F7; Definições com o parágrafo; 0 NaN; **console sem erro** |

## (c) O que ficou pendente

- **Linha 179 × 41** (Preço Baixo em dois clusters): sua decisão, ver acima.
- **Linha 177**: aparece na lista Destaque como "Bom Vizinho" (é o CNPJ que está na planilha); confirmar o CNPJ da Pinheiro Supermercado.
- **CNPJs das 124 linhas fora**: você vai pedir a quem montou a lista; a planilha de trabalho está em `PDVs_ponderados_o_que_corrigir.xlsx`.
  Cada linha corrigida entra sozinha na próxima execução.

## (d) Checklist para você

Abra `data/dn/painel/Scorecard_DN_2026-08.html` (Ctrl+F5) — é o gerado, ainda não publicado.

- [ ] Aba Pontos de venda: abre com o botão **Destaque** marcado, 6 PDVs e a nota da carteira acima da tabela.
- [ ] **Prime** mostra 51 PDVs; **Todos os PDVs** volta à lista completa.
- [ ] Escolha Prime, feche e reabra o painel: ele volta em Prime.
- [ ] Filtre um distribuidor da carteira (por exemplo EBD - Manaus AM): a lista Destaque mostra só os dele.
- [ ] Na Penetração, clique em "a ativar" de uma categoria: a lista abre em Todos, com a situação por categoria.
- [ ] CSV com Destaque marcado: sai só com os 6.
- [ ] Definições: o parágrafo "Carteira de PDVs ponderados".
- [ ] Console (F12) sem erro.
- [ ] Com o ok: `python run_dn.py --mes 2026-08` publica.
