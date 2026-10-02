# Evolução · Fase F1 — seletor Volume × Valor (10/09/2026, noite)

Executada após a F0 (`docs/evolucao_f0.md`) e a aprovação item a item da proposta da F1 (P1–P9, Q-a um card por medida,
Q-b três R$ por par, Q-c nota só em Definições) pelo Douglas em 10/09/2026. Regras implementadas: **RN-06** (Valor do
sell-through), **RN-07** (R$ / PDV), **RN-09** (Unidades fora), **RN-43** (seletor de métrica), **RN-55** (Valor no RTM).

**Publicado em 10/09/2026 às 21h24** (execução `20260910-212250-272f75`, 44 validações ok, md5 `6568ee5d5e695e57420b0ab909882639`, 8.177.039 bytes), após o ok do Douglas no checklist (d).

## (a) O que foi alterado

### P4 · Resíduos do protótipo removidos (`template/template.html`, 1.787 → 1.515 linhas antes do P3)

| Removido | O que era |
|---|---|
| `var RKG=34.26, UMODE, PCL, HERO, HISTDATA, HVK, UFJ, PENJ, EX3, PLANJ` e `applyUnit()`, `YMODE`, `sety()`, `setu()` | preço médio único e conversor kg → R$ do protótipo (RK1); toggles de unidade e ano da visão antiga |
| `cls3`, `svgBullet`, `row`, `kgcell`, `pctxt`, `renderHero` | cartões de meta/projeção sobre objetos vazios; as chamadas em `fcat`, `fdist` e `fclear` foram retiradas |
| bloco "aba Histórico" (`HST`, `hstate` … `hexp`, 2 listeners) | aba do protótipo, sem marcação correspondente |
| `pdexp`, `acexp` | exportadores CSV mortos (`ponderada_top20.csv`, `plano_de_acao_*.csv`) |
| `Object.keys(HERO)…`, `try{acap()}`, `try{pdap()}`, `Object.keys(HVK)…` | inicializações do protótipo |

Método: análise de alcance (raízes = atributos `on*=` da marcação + script das Fases 2–4), remoção só do que estava na lista
aprovada e do que dependia dela, `grep` de cada nome removido = 0, `node --check` nos dois scripts, `--regerar-exemplo` e prova
byte a byte do renderizador; 40 validações ok e números iguais antes de seguir. **Ficaram** no arquivo outras funções mortas do
protótipo (`pd*`, `ac*`, `sw2`, `dnlev`…) que o comentário de 08/09 pede para manter "para reaproveitamento"; não fazem parte
da lista aprovada e não convertem unidade. Removê-las é um item à parte, se você quiser.

### P2 · Pipeline

| Arquivo | Mudança |
|---|---|
| `dn/metrics.py` · base ativa de PDVs | `rs_mes`, `rs_ultimo_mes`, `rs_janela` por par, somando `RECEITA` nas mesmas linhas do kg (kg > 0) |
| `dn/painel.py` | blob de PDVs com 3 colunas novas (15–17, R$ inteiros); blob do RTM com `rs_certo`, `rs_outro` (cols 8–9, no fim, para não mover índices); `receita_mi` nos cards; `meta_execucao.pares_kg_sem_rs` e `linhas_kg_sem_rs`; bloco `metrica` (padrão, rótulos dos chips, nome e definição do Valor, do config) |
| `dn/render.py` | formato `R$ #,# mi` |
| `dn/pipeline.py` · etapa 4 | **4 validações novas**: `card canal · valor (R$)` = recálculo na fato; `blob de PDVs · R$ do mes` = curated = fato (kg > 0); `RTM · R$ no destino (grade = serie)`; `metrica · pares t/R$ no HTML`. 40 → **44** |
| `config/config.yaml` | `painel.rotulos.metrica_t` / `metrica_rs` (P6); as chaves `regras.metrica.*` da F0 passam a ser lidas |
| `template/data-inventory.json` | 280 → **292** campos: `*.receita_mi` (5 níveis), `meta_execucao.pares_kg_sem_rs`, `linhas_kg_sem_rs`, `metrica.{padrao, rotulo_t, rotulo_rs, valor_nome, valor_definicao}`; descrições dos blobs |

### P3 · Template

| Onde | Mudança |
|---|---|
| CSS | `.m-rs:not(body){display:none} body.m-rs .m-rs{display:inline} body.m-rs .m-kg{display:none}` (mesmo padrão do chip do RTM, com `:not(body)`) |
| Barra | linha **Métrica** com os chips "Volume · t" e "Valor · R$" (rótulos do config) e a nota "contagens de PDVs não mudam com a métrica" |
| Cards | um card por medida (Q-a): "Volume do mês" ↔ "Valor do mês" (`R$ 40,3 mi`), "kg / PDV comprador" ↔ "R$ / PDV comprador", com os três Δ de cada medida; pares `.m-kg`/`.m-rs` |
| Tabelas | `DN_COLS_KPI` virou função da métrica (Volume/kg·PDV/Δ Volume ↔ Valor/R$·PDV/Δ Valor); colunas de clusters, supervisores, distribuidores, categorias, PDVs (cols 12/13/7 ↔ 16/17/15), RTM (série, destinos, clientes) e drill viraram funções; `DnTabela` ganhou `colsDe()`, `remetrica()` (refaz o `<thead>`, limpa o cache da busca, re-renderiza) e os listeners do cabeçalho passaram para a `<table>` |
| Séries e gráfico | `rs:"{{receita_rs}}"` nas 4 definições de série; `dnDraw` usa a medida do seletor na linha "Volume · t" ↔ "Valor · R$" e nos drills só de medida; barras de PDVs inalteradas |
| RTM | `dnRtmDrill` lê `rs_certo`/`rs_outro` do blob; subtítulo do drill cita a métrica ativa |
| Estado | `DNE.met` (padrão `regras.metrica.padrao`), `localStorage`, URL `&met=rs`; `dnMet()` / `dnAplicarMetrica()`; aplicado na carga antes de abrir a aba |
| CSV | sufixo `_t` / `_rs` no nome (tabelas e séries) |
| Definições | parágrafo com a definição de RN-06 e a nota de pares com volume e sem R$ (Q-c) |

### P9 · Docs

`docs/regras_negocio.md` (RN-06, RN-07, RN-09, RN-43, RN-55 → **vigente**; 28 vigentes · 24 aprovadas · 3 declaradas);
`README.md` (changelog, parâmetros, regra RN-06/RN-43); `docs/RETOMADA.md` (§1, §5 pendência 9 → publicar a F1 e propor a
F2, §6 armadilha do seletor, §7); este relatório.

## (b) Por quê

Regra A.4/A.5 (D1, D2, D3, D30): o Valor já estava calculado em todos os cubos desde 09/09 e nunca foi exibido; o seletor
anterior tinha sido removido (Q1) e o template ainda carregava um conversor por preço médio (`RKG=34.26`) que produziria R$
fictício se religado (RK1). A F1 liga a exibição sob a regra escrita, com o R$ vindo **só** de `receita_rs`, e tira o caminho
perigoso do arquivo.

## Prova (execuções `20260910-210347-982cf8` P4, `20260910-210920-54f51d` P2, `20260910-211510-10642a` P3, todas `--sem-publicar`)

| Checagem | Resultado |
|---|---|
| Após P4 (só remoção) | renderizador byte a byte ok; 40 validações ok; números iguais; HTML 6,88 MB |
| Após P2 | 43 ok; `card canal · valor` R$ 40.329.521,59 = recálculo; blob R$ 40.329.518 ≈ curated 40.329.521,59 = fato (72.279 pares com R$); RTM R$ grade = série (dif 0,0000); HTML 7,77 MB |
| Após P3 (final) | exemplo regerado; byte a byte ok; **44 validações ok**; **18 marcações `m-kg` = 18 `m-rs`**; 0 campos fora do inventário; HTML **7,8 MB** (limite 12); 1 aviso informativo (os 4 destinos RTM sem cadastro) |
| Números em t | **idênticos**: 124.600 · 71.478 · 57,4% · 1.199,9 t · 71 · RTM 1762/1589/173 |
| Navegador (servidor local, Chromium do painel) | abre em t igual ao painel atual (cards, tabela de categorias, série); chip "Valor · R$" → card "R$ 40,3 mi", "R$ 564,22 / PDV", Δ do valor (−6,7% · −2,0% · +11,1%), colunas "Valor (R$)" / "R$ / PDV" / "Δ Valor" em distribuidores, "Valor · R$" em categorias (Amendoim 13.723.354) e na série; PDVs: colunas "R$ último mês / R$ na janela / R$ no mês", resumo "56.869 sem compra no mês (R$ 42.439.505 vendidos a eles na janela)"; RTM: "R$ no destino / R$ vazados" na Evolução, "R$ em outros" nos Clientes, drill "Comprou de outro · ago/26" com 93 clientes e colunas em R$; CSV `scorecard-dn_distribuidores_2026-08_rs.csv`; URL `#aba=…&met=rs`; `localStorage` guarda `met`; voltar a t restaura tudo; Definições com o parágrafo do sell-through (29 pares · 1.326 linhas); 375 px sem rolagem horizontal (375 = 375); **console sem erro** |
| Contagens em R$ | base ativa, cobertura, DN, penetração, aderência: iguais nos dois modos |

O md5 do HTML mudou (esperado: chips, colunas, blob). A prova de "nada mudou" é a linha "Números em t".

## (c) O que ficou pendente

- **"Distribuidor que atendeu"** no RTM (texto "TOP SERVICE (CNPJ) 4 kg") continua em kg mesmo em R$: é um rótulo montado no
  pipeline (`_rot_atendeu`) com o kg de cada "outro". Para alternar seria preciso um segundo rótulo em R$ por linha (+ bytes no
  blob). Deixo como está e registro; se quiser, entra na F2.
- **Funções mortas remanescentes do protótipo** (`pd*`, `ac*`, `sw2`, `dnlev`, `stcf`…): fora da lista aprovada; remoção como
  item à parte, com o mesmo método (alcance + `node --check` + byte a byte).
- A nota de Definições diz 1.326 linhas com kg > 0 e R$ = 0 (série do painel até ago/26, 71 distribuidores); as 1.402 da
  auditoria contavam a fato inteira (15 arquivos, 72 distribuidores). O inventário guarda o valor como exemplo, não como regra.
- Próxima fase: **F2** (LY explícito no gráfico: `volume_ly`, `receita_ly`, coluna + linha, Δ% do JSON), por proposta escrita.

## (d) Checklist para você

Abra `data/dn/painel/Scorecard_DN_2026-08.html` (Ctrl+F5) — é o gerado, ainda não publicado.

- [ ] Abre em "Volume · t" e está igual ao painel publicado: cards, gráfico, tabela de categorias, mesmos números.
- [ ] Clicar em "Valor · R$": o card vira "Valor do mês · R$ 40,3 mi" e "R$ / PDV comprador · 564,22"; base ativa, sem compra, cobertura e % DN **não** mudam.
- [ ] Distribuidores: colunas "Valor (R$)", "R$ / PDV" e "Δ Valor"; ordenar por "Valor (R$)"; CSV baixa `scorecard-dn_distribuidores_2026-08_rs.csv` com valores inteiros.
- [ ] Pontos de venda: "R$ último mês", "R$ na janela", "R$ no mês"; o rodapé fala em "R$ … vendidos a eles na janela".
- [ ] RTM: Evolução com "R$ no destino / R$ vazados"; clicar num número abre o drill com "R$ no destino / R$ em outros".
- [ ] Voltar em "Volume · t": tudo volta a kg e t.
- [ ] Copiar a URL com `met=rs`, abrir em outra aba: abre em R$. Recarregar sem hash: mantém o último escolhido.
- [ ] Definições: parágrafo "Valor do sell-through (R$)" com a nota dos 29 pares.
- [ ] Console do navegador (F12) sem erro ao trocar de métrica e de aba.
- [ ] Com o ok: `python run_dn.py --mes 2026-08` publica; conferir no publicado o chip e a tarja "ago/26".
