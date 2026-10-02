# Evolução · Fase F11 — Alavancas: de onde veio a variação da medida (11/09/2026)

Executada após a carteira de PDVs ponderados (publicada 11/09 16h15) e a aprovação da proposta da F11 **como recomendada** pelo Douglas
em 11/09/2026: P1–P8 e Q1–Q8 (Q1 aba nova depois da Evolução · Q2 média do efeito em todas as ordens de troca · Q3 mês anterior e LY,
sem L3M · Q4 Base RTM em linha própria, "subconjunto, não soma" · Q5 mix no canal, segmento, supervisor e distribuidor · Q6 identidade
da categoria · Q7 três frases de resumo com limiar de 10 t / R$ 300 mil · Q8 entrada e saída em linhas próprias). Base: ficha A.16
(10/09). Regra nova: **RN-57** (vigente); RN-50 registra a aba.

**Publicado em 11/09/2026 às 16h53** (execução `20260911-165038-94803d`, 124 validações ok, md5 `39c5a737fab2d122d522b3f8f46c542f`, 11.562.668 bytes — o mesmo da prova `20260911-164432-1ec375`), após o "checklist ok" do Douglas.

## (a) O que foi alterado

| Arquivo | Mudança |
|---|---|
| `docs/regras_negocio.md` | ficha **RN-57 · Decomposição da variação (alavancas)**, escrita antes do código; RN-50 com a aba Alavancas; 57 fichas (53 vigentes · 1 aprovada · 3 declaradas) |
| `config/config.yaml` | `regras.alavancas` (método, comparações, mix, RTM); aba `alavancas` em `painel.abas` (segmento, categoria, distribuidor, supervisor) e no filtro de supervisor; `painel.alavancas.{textos, rotulos}` (inclui o rótulo fixo "decomposição aritmética, não causa" e o motivo do "sem par"); resumos **A1–A3**; fichas de memória `alav_variacao`, `alav_base`, `alav_dn`, `alav_kg`, `alav_mix` (26 → 31) |
| `dn/metrics.py` | `_shapley` e `alavancas()` → **`DN_ALAVANCAS`**: por nível (canal, segmento, supervisor, supervisor × segmento, distribuidor) × categoria × comparação; cinco fatores nos níveis sem categoria (base ativa, DN, categorias por loja, SKUs por categoria, medida por SKU, tirados da fato), três com categoria; linha da Base RTM; entrada/saída sem decomposição; comparação inteira "sem par" quando o mês de comparação não tem base ativa no canal (menos a Base RTM, que tem régua própria) |
| `dn/painel.py` | `alavancas.json`: lista compacta (cabeçalho de colunas + listas de números), sem as linhas "sem par", com rótulos, textos e o motivo do LY |
| `dn/resumos.py` | tipo `alav_canal` e fontes `alav_fatores`, `alav_dist` |
| `dn/pipeline.py` | **6 validações novas**: `alavancas · Σ contribuicoes = variacao`, `produto dos fatores = medida do cubo`, `entradas e saidas fecham o total`, `LY nulo sem base ativa`, `aba e config no HTML` e `resumos · alavancas = curated`. A conferência das parcelas da memória aceita as colunas declaradas da aba. 118 → **124** |
| `template/template.html` | aba **Alavancas**: cascata SVG (mês anterior → base ativa → DN → medida por PDV → mês), com o valor de antes e de depois de cada fator; linha do mix; tabelas "Alavancas lado a lado", "Por supervisor" e "Por distribuidor" (ordenáveis, com CSV, clique filtra); botões de comparação (mês anterior / ano anterior, guardados na URL como `alavc=`); ganchos de filtro e métrica; motor das frases A1–A3; parágrafo nas Definições |
| `template/data-inventory.json` | 738 → **750** campos |
| `README.md`, `docs/RETOMADA.md` | changelog, estado, pendências, armadilha, índice |

## (b) Por quê

Ficha A.16: mostrar de onde veio a variação da medida, por identidades exatas e sem premissa. O método escolhido (Q2) é a média do
efeito de trocar cada fator em todas as ordens de troca: cada contribuição continua sendo "o efeito daquele fator", e a soma fecha a
variação sem resíduo. A decomposição é aritmética: diz quanto de cada fator, não por quê.

## Resultados em ago/26 contra jul/26 (métrica t)

| Recorte | Variação | Base ativa | DN | Medida por PDV |
|---|---|---|---|---|
| **Canal** (1.279,5 → 1.199,9 t) | **−79,7 t** | +38,2 t | −67,5 t | −50,4 t |
| ↳ mix do canal | | | | categorias por loja −35,4 · SKUs por categoria −6,2 · kg por SKU −8,8 |
| Base atual | −90,7 t | +18,3 t | −57,7 t | −51,3 t |
| Novos distribuidores | +11,0 t | +16,4 t | −11,2 t | +5,9 t |
| Base RTM (subconjunto, não soma) | +7,3 t (29,7 → 37,0) | clientes mensuráveis 0,0 t | aderência +2,3 t | kg por cliente que comprou +5,0 t |
| Canal × Amendoim (437,2 → 372,1 t) | −65,1 t | +12,5 t | % de cobertura da categoria −38,2 t | kg por comprador −39,3 t |

Em R$ (canal): −R$ 2,88 mi = base ativa +R$ 1,29 mi · DN −R$ 2,27 mi · R$ por PDV −R$ 1,89 mi.

Por distribuidor: a maior variação negativa é a **Avante**, −23,8 t (base ativa −0,8 · DN −16,2 · kg por PDV −6,7); por supervisor, BA/SE
(vago, Oliveira), −28,4 t. A **Pellah** não vendeu em jul/26: aparece como entrada, +11,3 t, e fecha a soma dos distribuidores com o canal.

Frases da aba: "Variação −79,7 t vs jul/26: base ativa +38,2 t, DN −67,5 t, medida por PDV −50,4 t" (informativa) · "Fator com maior
contribuição negativa: DN, −67,5 t" (atenção) · "Distribuidor com maior perda por DN: AVANTE, −16,2 t" (atenção).

**Contra o ano anterior:** ago/25 não tem base ativa (a janela de 5 meses só fica completa em nov/25). As 1.128 linhas ficam "sem par",
fora do HTML, e a tela diz o motivo e que a comparação aparece a partir do mês de referência nov/26. A exceção é a Base RTM, que tem régua
própria: contra ago/25, de 3,0 t para 37,0 t (aderência +22,4 t, kg por cliente +11,6 t).

## Correções feitas durante a execução

| Sintoma | Causa | Correção |
|---|---|---|
| duas edições (config e cálculo) não rodaram | o terminal não aceitou o texto longo embutido no comando | scripts gravados em arquivo e executados |
| distribuidores sem linha em ago/25 apareciam como "entrada" contra o LY, e chegaram ao HTML | o teste de "entrada" vinha antes do teste de "sem base ativa no mês de comparação" | mês de comparação sem base ativa no canal deixa a comparação inteira "sem par" (menos a Base RTM); a validação `LY nulo sem base ativa` pegou |
| a conferência das frases da aba reprovou valores certos | tolerância de 1e-6 contra um JSON com três casas | tolerância de meia unidade na terceira casa, mais o arredondamento das duas pontas |

## Prova

| Checagem | Resultado |
|---|---|
| Completa final (`20260911-164432-1ec375`, `--regerar-exemplo --sem-publicar`) | byte a byte ok; **124 ok**; HTML **11,0 MB**; números iguais (124.600 · 71.478 · 57,4% · 1.199,9 t · 71 · RTM 1762/1589/173) |
| Decomposição | 1.102 linhas decompostas, em t e R$: contribuições somam a variação e os fatores reproduzem a medida do cubo; 208 com mix; 70 distribuidores decompostos + 1 entrada = −79,7 t do canal |
| Navegador (servidor local) | aba entre Evolução e Clusters; cascata com 5 barras e os valores de antes e depois; mix; 4 alavancas lado a lado, 14 supervisores, 71 distribuidores; R$ troca a cascata e as frases; Amendoim troca a identidade e esconde o mix; Pellah mostra "entrada"; comparação com o ano anterior mostra o motivo e só a Base RTM; `alavc=ly` na URL; ⓘ do cabeçalho abre a memória sem reordenar; frases sem divergência; 0 NaN; **console sem erro** |

## (c) O que ficou pendente

- **Tamanho:** o HTML foi de 10,6 para 11,0 MB (+0,4 MB), acima dos 0,1–0,3 MB que estimei na proposta; o limite é 12 MB. Quando a
  comparação com o ano anterior tiver par (mês de referência nov/26, ou antes com a Mtrix de set/24 a jun/25), as linhas dobram e o HTML
  chega perto de **11,6 MB**. Mitigação possível, para decidir antes disso: compactar os dados da aba como a lista de PDVs (gzip).
- Comparação com o ano anterior: aparece sozinha a partir de nov/26, sem mudar código.
- Da carteira: linha 179 × 41 (Preço Baixo em dois clusters) e os CNPJs das linhas fora seguem com você.

## (d) Checklist para você

Abra `data/dn/painel/Scorecard_DN_2026-08.html` (Ctrl+F5) — é o gerado, ainda não publicado.

- [ ] Aba **Alavancas**, entre Evolução e Clusters: a cascata vai de 1.279,5 t (jul/26) a 1.199,9 t (ago/26), com base ativa +38,2 t, DN −67,5 t e kg por PDV −50,4 t.
- [ ] A linha do mix abaixo: categorias por loja −35,4 t, SKUs por categoria −6,2 t, kg por SKU −8,8 t.
- [ ] "Valor · R$" troca a cascata e as frases para R$.
- [ ] Filtre a categoria Amendoim: a cascata passa a usar a % de cobertura da categoria e o kg por comprador.
- [ ] Filtre um distribuidor (por exemplo Avante): a cascata é a dele. Pellah aparece como "entrada".
- [ ] Botão "vs ago/25": a tela explica por que não há decomposição contra o ano anterior.
- [ ] O ⓘ de um cabeçalho das tabelas abre a memória de cálculo.
- [ ] Definições: o parágrafo "Alavancas".
- [ ] Console (F12) sem erro.
- [ ] Com o ok: `python run_dn.py --mes 2026-08` publica.
