# Evolução · Fase F8 — Matriz de Oportunidades (11/09/2026, manhã)

Executada após a F7 (`docs/evolucao_f7.md`, publicada 11/09 08h31) e a aprovação da proposta da F8 (P1–P10; Q-a dois grãos,
distribuidor × categoria ao abrir e supervisor × categoria como alternativa; Q-b só as 4 foco ligadas ao abrir; Q-c drill "Positivados
no mês sem {categoria}"; Q-d eixo X linear; Q-e aba própria entre Penetração e RTM) pelo Douglas em 11/09/2026. Regra
implementada: **RN-42** (Matriz de Oportunidades); aba de **RN-50** (regra agora completa). Sem regra nova.

**Publicado em 11/09/2026 às 09h35** (execução `20260911-093218-7a71bc`, 97 validações ok, md5 `3b40185c085e139310a1ae6985325a45`, 10.991.511 bytes), após o ok do Douglas no checklist (d). Prova final antes da publicação: execução `20260911-092523-b0ce29`.

Princípio da fase: **nenhuma tabela nova** — a matriz lê a tabela nível × categoria da Penetração (710 pares distribuidor ×
categoria e as linhas de supervisor), que já tinha penetração, referência, lojas a positivar, kg/loja, fator, potencial, a ativar e
sem compra no mês. Entraram só dois campos por linha (`gap_pp`, `positivados_nivel`) e a aba: +0,1 MB.

## (a) O que foi alterado

### Pipeline

| Arquivo | Mudança |
|---|---|
| `dn/painel.py` | `pen_nivel_cat` ganha `gap_pp` (referência − penetração, p.p.; negativo = acima da referência) e `positivados_nivel`; `J["matriz"]` (unidade, eixos e bolha **lidos e conferidos** do `regras.matriz` — valor diferente do implementado, ou `quadrantes`/`score` ligados, **aborta**; grão padrão, rótulos dos chips, situação do drill, nota, contagem de pares, lista de categorias) |
| `dn/pipeline.py` · etapa 4 | **3 validações novas**: `matriz · gap = referencia − penetracao` (1.050 linhas), `matriz · positivados do distribuidor = cubo` (710 pares = `DN_DISTRIBUIDOR_MES`), `matriz · config lido e aba no HTML` (eixos e bolha do config = da aba; sem quadrantes; sem score; `DN_MX`, tabela e situação nova no HTML). 94 → **97** |
| `config/config.yaml` | `painel.abas` ganha `{id: matriz, rotulo: "Matriz de oportunidades", filtros: [segmento, categoria, distribuidor, supervisor]}` antes de RTM; `painel.rotulos.pdv_sit_pos_sem`, `matriz_grao_dist`, `matriz_grao_sup`; `painel.textos.matriz_nota`; `regras.matriz.*` (F0) passa a ser lido |
| `template/data-inventory.json` | 688 → **704** campos (`pen_nivel_cat.gap_pp`, `positivados_nivel`, `matriz.*`) |

### Template

| Onde | Mudança |
|---|---|
| Aba **Matriz de oportunidades** (`tpl-aba-matriz`) | cabeçalho com competência, nota da matriz, referência e o aviso "oportunidade calculada, não previsão"; nota do recorte ("284 par(es) na nuvem · N sem referência ou sem fator"); chips de **grão** (Distribuidor × categoria · Supervisor × categoria) e de **categoria** (★ foco ligadas ao abrir; botões "todas" / "só as foco"); **nuvem** SVG: X = lojas a positivar (linear), Y = referência − penetração em p.p. com a linha do zero rotulada "abaixo da linha: acima da referência", bolha com área proporcional ao potencial de entrada na métrica do seletor, cor por categoria (paleta da Evolução), foco mais opacas; tooltip com a memória ("penetração 25,5% → referência 48,4% (+22,8 p.p.) · lojas a positivar 658 · 10,5 kg/loja × fator 47,5% = Potencial de entrada 1,4 t/mês · Potencial em regime 2,9 t/mês"); clique fixa o distribuidor (ou o supervisor) na barra; **tabela** `matriz` ordenável com busca e CSV: distribuidor/supervisor, supervisor (ou segmento), categoria, PDVs positivados, compram a categoria, penetração, referência, gap p.p. com cor 95/70, lojas a positivar (botão do drill), kg ou R$ por loja (marca "canal"), fator, potencial de entrada e em regime, a ativar e sem compra no mês (botões); ordem inicial: potencial de entrada |
| Drill | situação nova em Pontos de venda **"Positivados no mês sem {categoria}"** = positivado no mês (coluna 8) e sem o bit do mês da categoria; 44 opções no select; mesmo mecanismo da F7 (`dnPenDrill('posmes')`) |
| Estado | `mxg=` (grão) e `mxc=` (categorias) em `localStorage` e URL |
| JS | `dnMxRows/Grao/Sel/Cats/Cor/Nome/Chips/Draw/Aplicar/Toggle/Set/GraoSet`; hooks em filtros, métrica e ao montar; se a Matriz abre antes da Penetração, monta a Penetração escondida (os dados vivem lá) |
| Definições | parágrafo "Matriz de oportunidades" |

### Docs

`docs/regras_negocio.md` (RN-42 → **vigente**; RN-50 completa; 50 vigentes · 2 aprovadas · 3 declaradas); `README.md`
(changelog, parâmetros); `docs/RETOMADA.md` (§1, §4 abas, §5 pendência 9 → publicar a F8 e propor a F9, §6 armadilha, §7); este
relatório.

## (b) Por quê

A.12 (D10–D13): "onde atuar primeiro" precisa de uma leitura de dois eixos por par distribuidor × categoria, sem esconder a régua
num score e sem quadrantes arbitrários. Como a Penetração já produzia todos os números no grão certo, a Matriz é só uma disposição
deles: qualquer número da nuvem é o mesmo da tabela e do drill.

## Correções feitas durante a prova

| Sintoma | Causa | Correção |
|---|---|---|
| lista de categorias dos chips chegaria com `=` escapado | mesmo caso das faixas da F5 | separador `:` antes de aplicar |
| tabela no grão supervisor mostrava "Supervisor \| Supervisor" | 2ª coluna fixa | 2ª coluna vira "Segmento" no grão supervisor |

## Prova

| Checagem | Resultado |
|---|---|
| Completa 1 (`20260911-092117-fb06c1`) | 97 ok; abas template = config (9); gap = referência − penetração em 1.050 linhas; 710 pares = cubo; config lido; HTML 10,5 MB |
| Completa final (`20260911-092523-b0ce29`, `--regerar-exemplo --sem-publicar`) | exemplo regerado; byte a byte ok; **97 ok**; HTML **10,5 MB**; números iguais (124.600 · 71.478 · 57,4% · 1.199,9 t · 71 · RTM 1762/1589/173) |
| Navegador (servidor local) | aba montada (Penetração montada escondida junto); chips de grão e 10 categorias (★ 4 ligadas); nuvem com **284** pontos (foco), 710 com "todas", 355 com Bala ligada, **70** no grão supervisor (14 × 5); linha do zero "acima da referência"; tooltip com a memória; clique na maior bolha fixa Distrilobo (4 pontos); tabela com 15 colunas, 25 de 284 registros, botões de drill; drill "Positivados no mês sem Amendoim" abre Pontos de venda com **1.343** registros, todos positivados no mês e sem o bit de Amendoim; 44 situações no select; R$: colunas e tooltip em R$ ("R$ 59.140/mês"); URL com `mxg=` e `mxc=`; chips do calendário esmaecidos; 0 NaN; **console sem erro** |
| Tamanho | 10,4 → **10,5 MB** (+0,1 MB; limite 12; sobram ~1,5 MB para F9 e F10) |

## (c) O que ficou pendente

- 2ª entrega da matriz (quadrantes por mediana de X e Y do recorte, com nomes validados em exemplos reais): só com proposta
  aprovada; hoje ligar o config aborta. Score único: não criar (D13).
- Destaques e resumos sobre a matriz: F9. Rastreabilidade por número: F10.
- Próxima fase: **F9** (resumos executivos dinâmicos, RN-48).

## (d) Checklist para você

Abra `data/dn/painel/Scorecard_DN_2026-08.html` (Ctrl+F5) — é o gerado, ainda não publicado.

- [ ] Aba "Matriz de oportunidades" entre Penetração e RTM; competência ago/26 e a referência P75 no topo.
- [ ] Nuvem com as 4 foco ligadas (284 pontos); "todas" mostra 710; chips ligam e desligam categorias; grão "Supervisor × categoria" muda a nuvem e a tabela.
- [ ] Passar o mouse numa bolha mostra a memória de cálculo; clicar fixa o distribuidor na barra (a Penetração passa a ser dele).
- [ ] Tabela: ordenada por potencial de entrada; gap com cor; clicar em "lojas a positivar" abre Pontos de venda com "Positivados no mês sem X".
- [ ] "Valor · R$" troca kg/loja e potenciais para R$ na tabela e no tooltip.
- [ ] Chips do Ano esmaecidos; console (F12) sem erro.
- [ ] Com o ok: `python run_dn.py --mes 2026-08` publica.
