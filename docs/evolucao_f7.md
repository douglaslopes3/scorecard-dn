# Evolução · Fase F7 — ativação e recorrência por categoria, máscara PDV × categoria embutida, drill nominal (11/09/2026, manhã)

Executada após a F6 (`docs/evolucao_f6.md`, publicada 11/09 07h33) e a aprovação da proposta da F7 (P1–P10; Q-a distribuidor sem
venda na categoria segue com penetração zero; Q-b fator observado acima de 100% mantido com aviso; Q-c máscara de 20 bits, janela e
mês; Q-d drill abre Pontos de venda com a Situação pré-selecionada; Q-e coluna de recorrência LY visível com "—") pelo Douglas em
11/09/2026. Regras implementadas: **RN-32** (ativação da categoria), **RN-33** (recorrência mensal), **RN-38** (máscara embutida,
drill nominal), **RN-41** (base elegível = base ativa); decisões registradas em **RN-31** e **RN-34**. Sem regra nova.

**Publicado em 11/09/2026 às 08h31** (execução `20260911-082929-68662a`, 94 validações ok, md5 `c19d9c740458536e2d0500c8ffd68462`, 10.926.389 bytes), após o ok do Douglas no checklist (d). Prova final antes da publicação: execução `20260911-080302-7fc61b`.

## (a) O que foi alterado

### Pipeline

| Arquivo | Mudança |
|---|---|
| `dn/metrics.py` | `_ativacao_recorrencia(f, meses, mp, cal)`: na janela de 5 meses que termina no mês fechado, por nível × categoria (canal, segmentos, supervisores com e sem segmento, clusters com e sem segmento, distribuidores): **base elegível** (PDVs com kg > 0 em ≥ 1 mês da janela = base ativa do nível; no distribuidor, pares), **compradores da categoria na janela**, **a ativar** = base − compradores, % da base; **compradores no mês**, **recorrência mensal** = mês ÷ janela, **sem compra no mês**, distribuição de frequência `freq_1..freq_5` e `meses_medios`; `recorrencia_ly` quando a janela LY inteira está na série (hoje não). Junta tudo em `DN_PEN_NIVEL_CAT` (21 → 36 colunas); `DN_PEN_NIVEL` ganha `base_elegivel`, `a_ativar_foco/total`, `sem_compra_foco/total`. **Máscara** passa a **20 bits** por par (0–9 comprou a categoria na janela, 10–19 comprou no mês de referência) mais a flag `novo` (PRIMEIRO_MES dentro da janela, A.6) em `DN_PDV_CAT_MASCARA`; `DN_PEN_META` ganha `mascara_bits`, `janela_ativacao`, `janela_ativacao_ly` |
| `dn/painel.py` | `pen_nivel_cat` ganha os 12 campos de ativação/recorrência (frequência compactada em `freq = "n1|n2|n3|n4|n5"`) e **perde as linhas de cluster** (só o pivot `pen_clusters` as usa: 1.400 → 1.050 linhas); `pen_nivel` ganha os totais; `penetracao.*` ganha janela, rótulos e textos da F7 e `mascara_embutida`; `blob_pdvs` recebe a máscara e grava as colunas 18 (`mascara`) e 19 (`novo`), com `cats`, `cats_nomes` e `bits` na carga; se `embutir_mascara: sim` e a máscara passar do limite, o pipeline **aborta** (RN-38) |
| `dn/pipeline.py` · etapa 4 | **8 validações novas**: `ativacao · a ativar = base elegivel − compradores` (1.400 linhas; base elegível = base ativa do cubo no canal e segmentos; compradores no mês = lojas), `ativacao · canal = recalculo na fato` (PDVs distintos), `ativacao · distribuidor = pares da mascara` (20 pares distribuidor × categoria = bits), `recorrencia · = compradores no mes ÷ janela`, `recorrencia · distribuicao de frequencia soma os compradores`, `recorrencia · LY nulo sem par`, `mascara · embutida = curated` (5.000 pares, bits e "novo"), `pdv · situacoes por categoria no HTML`. 86 → **94** |
| `config/config.yaml` | `painel.pdv_categoria.embutir_mascara: sim`; `painel.rotulos.pen_ativar`, `pen_sem_compra`, `pdv_novo`, `pdv_sit_ativar`, `pdv_sit_sem_mes`, `pdv_sit_mes`; `painel.textos.pen_janela`, `pen_ativacao_nota`, `pen_recorrencia_nota` |
| `template/data-inventory.json` | 657 → **688** campos |

### Template

| Onde | Mudança |
|---|---|
| Penetração | linha abaixo dos cards: "A ativar (janela) nas foco: 211.598 positivações de categoria (base elegível 124.600) · sem compra no mês nas foco: 151.628 · todas as 10 …" (com chip de Categoria: os números da categoria); bloco **"A ativar (janela) · abr/26 a ago/26"** (tabela por categoria: base elegível, compram na janela, % da base, a ativar com botão, % da base, lojas a positivar para contraste); bloco **"Recorrência mensal · ago/26"** (compram na janela, no mês, recorrência, sem compra no mês com botão, recorrência LY, média de meses, 1 a 5 de 5 meses); a tabela "Por distribuidor" ganha a ativar (pares), recorrência e sem compra no mês, com botões |
| Drill (`dnPenDrill`) | fixa o recorte da linha (distribuidor, supervisor + segmento, ou segmento) e abre **Pontos de venda** com a Situação "A ativar em X" ou "Compram X na janela, sem compra no mês"; se a tabela de PDVs ainda não montou, a situação fica pendente e entra pelo novo gancho `extrasIniciais` do componente |
| Pontos de venda | `dnPdvSituacoes()` gera 30 situações por categoria a partir de `cats` do blob (34 opções no select); `dnPdvBit()` lê os bits; coluna **"Novo na janela"**; resumo do rodapé: "47.088 PDVs · A ativar em Amendoim · …"; `PDV_ROT` com os rótulos do config |
| Definições | máscara embutida (20 bits) e parágrafo "Ativação e recorrência" (base elegível, ausência de cadastro/bloqueio/carteira/vendedor) |

### Docs

`docs/regras_negocio.md` (RN-32, RN-33, RN-38, RN-41 → **vigente**; RN-31 e RN-34 com as decisões Q-a/Q-b; 49 vigentes · 3
aprovadas · 3 declaradas); `README.md` (changelog, parâmetros); `docs/RETOMADA.md` (§1, §5 pendência 9 → publicar a F7 e propor a
F8, §6 armadilha da máscara, §7); este relatório.

## (b) Por quê

A.6 (D24, D28) e §18 da Etapa 1: a Penetração media o gap do mês contra a referência, mas não dizia **quem** nunca comprou a
categoria (ativação) nem **quem** comprou e parou (recorrência). Os dois objetivos ficam em blocos separados, com denominadores e
nomes próprios, e a máscara de 20 bits é o que leva cada número até a lista nominal de PDVs, com busca e CSV, sem cálculo no
template (os bits são lidos, não calculados).

## Números do canal em ago/26 (janela abr/26 a ago/26)

| Categoria | Base elegível | Compram na janela | A ativar | Compram no mês | Recorrência | Sem compra no mês | Meses (média) | 1 de 5 |
|---|---|---|---|---|---|---|---|---|
| ★ Amendoim | 124.600 | 80.455 (64,6%) | 44.145 (35,4%) | 39.832 | 49,5% | 40.623 | 2,46 | 28.066 |
| ★ Gomas | 124.600 | 84.079 (67,5%) | 40.521 (32,5%) | 38.242 | 45,5% | 45.837 | 2,18 | 35.171 |
| ★ Regaliz | 124.600 | 64.258 (51,6%) | 60.342 (48,4%) | 29.877 | 46,5% | 34.381 | 2,20 | 26.842 |
| ★ Gelatina | 124.600 | 58.010 (46,6%) | 66.590 (53,4%) | 27.223 | 46,9% | 30.787 | 2,08 | (ver painel) |

Leitura: metade de quem compra a categoria não compra no mês; um terço a metade comprou em um único mês dos cinco. A recorrência
é uma oportunidade do mesmo tamanho da ativação. Em pares (drill nominal), a ativar em Amendoim = 47.088 (o mesmo PDV atendido
por dois distribuidores conta duas vezes; no canal conta uma).

## Correções feitas durante a prova

| Sintoma | Causa | Correção |
|---|---|---|
| `ArrowExtensionArray` sem `.sum()` na validação da máscara | máscara booleana em dtype Arrow | `.to_numpy(dtype=bool)` |
| HTML 10,7 MB após o passo 2 | 17 campos novos em 1.400 linhas + máscara | linhas de cluster fora da tabela embutida (só no pivot) e frequência compactada em um campo → 10,4 MB |

## Prova

| Checagem | Resultado |
|---|---|
| Passo 1 (`20260911-075302-2a4d17`) | 6 validações novas ok; base elegível 124.600 = recálculo; 20 pares distribuidor × categoria = bits da máscara; recorrência e frequência conferidas em 1.400 linhas; LY nulo (sem janela LY) |
| Passo 2 (`20260911-075756-c69c5f`) | máscara embutida = curated (5.000 pares, 20 bits, 0,29 MB ≤ 1 MB); 0 campos fora do inventário |
| Completa (`20260911-080302-7fc61b`, `--regerar-exemplo --sem-publicar`) | exemplo regerado; byte a byte ok; **94 ok**; HTML **10,4 MB**; números iguais (124.600 · 71.478 · 57,4% · 1.199,9 t · 71 · RTM 1762/1589/173) |
| Navegador (servidor local, recarga limpa) | linha de ativação/recorrência dos cards; bloco "A ativar (janela)" com 10 linhas e 10 botões (Amendoim 124.600 · 80.455 · 64,6% · 44.145 · 35,4% · 12.824); bloco "Recorrência mensal" com 12 colunas (Amendoim 80.455 · 39.832 · 49,5% · 40.623 · — · 2,46 · 28.066/17.826/13.694/11.168/9.701); tabela por distribuidor com as 3 colunas novas e 50 botões; **drill** "a ativar em Amendoim" no canal abre Pontos de venda com a Situação selecionada, 47.088 registros, resumo "47.088 PDVs · A ativar em Amendoim · 25.615 sem compra no mês", nenhum dos exibidos com o bit da janela; drill "sem compra no mês" do Distrilobo × Regaliz: distribuidor fixado, 612 registros = tabela, todos com bit da janela e sem bit do mês; select com 34 situações; coluna "Novo na janela"; 0 NaN; **console sem erro** |
| Tamanho | 9,9 → **10,4 MB** (+0,5 MB: máscara 0,29 + campos novos; limite 12) |

## (c) O que ficou pendente

- Recorrência LY e janela LY: dependem da Mtrix set/24–jun/25 (D5); a coluna já existe.
- Frequência por PDV × categoria (por par) não vai ao blob: só a distribuição agregada. Sazonalidade: sem regra (série curta).
- **Orçamento de tamanho**: 10,4 de 12 MB. A F8 (Matriz) deve reaproveitar `pen_nivel_cat` e o blob, sem tabela nova grande.
- Próxima fase: **F8** (Matriz de Oportunidades, RN-42).

## (d) Checklist para você

Abra `data/dn/painel/Scorecard_DN_2026-08.html` (Ctrl+F5) — é o gerado, ainda não publicado.

- [ ] Penetração: abaixo dos cards, "A ativar (janela) nas foco: 211.598 … sem compra no mês nas foco: 151.628 …".
- [ ] Bloco "A ativar (janela) · abr/26 a ago/26": Amendoim 80.455 compram na janela · 44.145 a ativar (35,4%); clicar em 44.145 abre Pontos de venda com "A ativar em Amendoim" e 47.088 registros (pares).
- [ ] Bloco "Recorrência mensal": Amendoim 49,5% · 40.623 sem compra no mês · 2,46 meses · distribuição 1 a 5; clicar em 40.623 abre a lista.
- [ ] Por distribuidor: colunas a ativar, recorrência e sem compra no mês; clicar fixa o distribuidor e abre a lista dele.
- [ ] Pontos de venda: select Situação com as opções por categoria; coluna "Novo na janela"; resumo do rodapé com a situação; CSV.
- [ ] Um chip de Categoria na barra muda a linha dos cards para a categoria.
- [ ] Console (F12) sem erro.
- [ ] Com o ok: `python run_dn.py --mes 2026-08` publica.
