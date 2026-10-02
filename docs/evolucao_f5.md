# Evolução · Fase F5 — calendário civil × fiscal, acumulados no pipeline, comparativo anual (10/09/2026, noite)

Executada após a F4 (`docs/evolucao_f4.md`, publicada 23h04) e a aprovação da proposta da F5 (P1–P10; Q-a PDVs distintos que
compraram no período, só no mês de referência; Q-b linha compacta abaixo dos cards; Q-c coluna "Acum. no ano" em categorias,
clusters, supervisores e distribuidores; Q-d a série exibida segue os últimos 12 meses) pelo Douglas em 10/09/2026. Regras
implementadas: **RN-23** (rótulos do ano fiscal e civil), **RN-24** (toggle civil × fiscal, padrão fiscal), **RN-25**
(acumulados calculados no pipeline, comparativo anual bloqueado sem par, mês faltando aborta). Sem regra nova.

**Publicado em 10/09/2026 às 23h44** (execução `20260910-234230-188a2a`, 67 validações ok, md5 `796a1504051d92268ec402e88eab8b21`, 9.540.708 bytes), após o ok do Douglas no checklist (d). Prova final antes da publicação: execução `20260910-233329-fef6a2`.

Dado que condiciona a leitura: a série tem 14 meses (jul/25 a ago/26). **FY26 (set/25–ago/26) está completo**; FY25 só tem
jul e ago/25; o ano civil 2026 tem jan a ago (8 de 12) e 2025 tem jul a dez (6 de 12). Nenhum acumulado tem par no ano
anterior até a Mtrix set/24–jun/25 (pendência D5) entrar; quando entrar, os pares aparecem sem mudança de código.

## (a) O que foi alterado

### Pipeline

| Arquivo | Mudança |
|---|---|
| `dn/metrics.py` | `acumulados(s, G, cal, meses)`: em **todos** os cubos `DN_*_MES` e `DN_*_CAT_MES`, por nível × mês, `ytd_{civil,fiscal}_volume_kg`, `_receita_rs`, `_n_meses` (soma do 1º mês do ano até o mês, **só se todos os meses do período estão na série**; senão nulo, nunca zero), `_volume_ly`, `_receita_ly` (o mesmo acumulado no ano anterior, por **junção** no mesmo mês do período, só se também completo) e `_volume_var_ly`, `_receita_var_ly`. `acum_ano(f, cal, meses)` → tabela **`DN_ACUM_ANO`** (431 linhas): por perspectiva × ano presente na série × nível (canal, segmento, supervisor com e sem segmento, distribuidor, categoria), **PDVs distintos que compraram no período** (Q-a), kg, R$, n meses, `completo` (começa no 1º mês do ano) e `fechado` (termina no 12º) |
| `dn/painel.py` | `_metricas` ganha `acum_{civil,fiscal}_{t, rs, mi, n, ly_t, ly_rs, var_t, var_rs}` para toda entidade (cards, categorias, clusters, supervisores, distribuidores); `_serie` ganha os mesmos por ponto; `acum_*_pdvs` no kpi do canal/segmentos, nos supervisores e nos distribuidores; bloco `calendario` (perspectiva padrão, rótulos dos chips, texto "sem par", e por perspectiva: ano, rótulo curto, rótulo do ano anterior, rótulo longo com o período coberto, período, n meses, `completo`, `faixas` no formato `mes:ano` para todos os meses da série); lista `ano_a_ano` (97 linhas: canal, 14 supervisores, 10 categorias × perspectiva × ano) com situação do ano, PDVs distintos, t, R$, LY e Δ do mesmo período por junção, `tem_par` |
| `dn/tabelas.py` | tabela `ano_a_ano`; das tabelas embutidas saem os acumulados que nenhuma coluna usa (LY, Δ, n meses, R$ mi — supervisores mantêm R$ mi e Δ porque a linha de acumulado da Visão geral filtrada por supervisor lê dali): sem isso o HTML subia 0,7 MB |
| `dn/pipeline.py` · etapa 4 | **9 validações novas**: `serie · sem buraco de mes` (aborta se faltar mês entre o 1º e o último), `acumulados · soma da serie` (146 acumulados recalculados: canal, 2 segmentos, 5 distribuidores, civil e fiscal), `acumulados · periodo incompleto = nulo` (canal: civil 8 com acumulado, jan/26 a ago/26, 6 nulos; fiscal 12, set/25 a ago/26, 2 nulos), `acumulados · LY por juncao` (hoje 0 pares; passa a conferir valores quando a D5 chegar), `acumulados · ano a ano = cubos + fato` (kg e R$ = soma dos meses; PDVs distintos = recálculo independente na fato, entre o máximo mensal e a soma), `calendario · faixas = DIM_CALENDARIO`, `calendario · chips no HTML`, `tabela ano_a_ano · registros`, `tabela ano_a_ano · host no HTML`. 58 → **67** |
| `config/config.yaml` | `calendario.rotulo_civil_longo: "Ano {ano} ({inicio}–{fim})"`, `rotulo_civil_curto: "{ano}"`; `painel.rotulos.cal_fiscal`, `cal_civil`, `acum_ano`, `acum_col`; `painel.textos.sem_par_anual`, `ano_completo`, `ano_em_curso`, `ano_incompleto`; `calendario` nos `filtros` das abas visao, evolucao, clusters e distribuidores; `calendario.perspectiva_padrao`, `rotulo_fiscal_longo/curto` (F0) passam a ser lidos |
| `template/data-inventory.json` | 386 → **503** campos (acumulados por entidade e por ponto das 4 séries, `calendario.*`, `ano_a_ano.*`) |

### Template

| Onde | Mudança |
|---|---|
| Barra | linha **Ano** com chips "Ano fiscal · Ano civil" (`data-cal`), nota com o rótulo longo e o alcance do toggle; `DN_CAL`, `DNE.cal`, `cal=` na URL e no `localStorage`; aplicabilidade por aba (esmaecido em Pontos de venda, RTM e Definições) |
| Gráficos (`dnDraw`, `dnEvoDraw`, supervisores) | `dnFaixasSvg`: faixa de ano sob o eixo (fiscal: "FY26"; civil: "2025" | "2026" com divisória tracejada na virada); a série e os pontos não mudam |
| Visão geral | linha "Acumulado no ano · {rótulo longo}: t ou R$ mi · PDVs distintos no período · vs {ano anterior}: Δ ou nota 'sem par na série (Mtrix a partir de jul/25)'", por segmento, com `data-k` (segue o filtro de Supervisor da F4 e a métrica da F1) |
| Evolução | tabela da série ganha "Acum. no ano · FY26 · t" e "Δ% acum. vs FY25" (nas duas chaves do gráfico); bloco novo **"Ano a ano"**: uma linha por ano na perspectiva ativa (Ano, Recorte, Meses na série, Situação "12 de 12" / "8 de 12 · em curso" / "2 de 12 · incompleto (série começa em jul/25)", PDVs distintos, Volume ou Valor, Δ vs ano anterior bloqueado com a nota); com supervisor ou categoria na barra mostra o recorte |
| Tabelas | coluna **"Acum. no ano"** (sub-rótulo FY26 · t ou 2026 · R$) em categorias, clusters, supervisores e distribuidores, logo após Volume/Valor; CSV ganha `fy26`/`2026` no nome |
| Definições | parágrafo "Calendário e acumulados" |

### Docs

`docs/regras_negocio.md` (RN-23 rótulos, RN-24, RN-25 → **vigente**; 37 vigentes · 15 aprovadas · 3 declaradas); `README.md`
(changelog, parâmetros, rotina: o que acontece quando a Mtrix set/24–jun/25 chegar); `docs/RETOMADA.md` (§1, §4 filtros, §5
pendência 9 → publicar a F5 e propor a F6, §6 armadilha do calendário, §7); este relatório.

## (b) Por quê

A.10 (D4, D29, D31): a empresa lê o ano de setembro a agosto e o painel só falava em meses; o acumulado precisava existir sem
que o JS somasse meses (regra de ouro: nada calculado no template) e sem mascarar período incompleto como zero. PDVs não se
somam, então o acumulado de PDVs é a cobertura do período (Q-a). O comparativo anual fica bloqueado com nota até haver par,
e passa a funcionar sozinho quando a D5 for atendida, porque o par é descoberto por junção.

## Correções feitas durante a prova

| Sintoma | Causa | Correção |
|---|---|---|
| faixas de ano não apareciam | o mapa `mes=ano` chegava com `=` escapado (`&#x3D;`) pelo renderizador em `{{ }}` | separador `:` (pipeline, validação, JS, inventário) |
| HTML 9,4 MB após o passo 2 | todos os campos de acumulado entravam nas ~1.600 linhas das tabelas embutidas | tabelas levam só `acum_*_t/rs` e `acum_*_pdvs` (supervisores também R$ mi e Δ) → 9,1 MB |
| `dnCal` definido duas vezes (getter e setter) | nome repetido no script | getter renomeado para `dnCalAtivo()` antes de aplicar |

## Prova

| Checagem | Resultado |
|---|---|
| Passo 1 (`20260910-231626-2ec0a0`) | 5 validações novas ok; `DN_ACUM_ANO` 431 linhas; canal FY26 = 13.115,8 t · R$ 444,9 mi · 150.249 PDVs distintos; civil 2026 (jan–ago) = 8.841,6 t · R$ 304,0 mi · 137.389 |
| Passo 2 (`20260910-232240-741636`) | 97 linhas de ano a ano; inventário 503; 0 campos fora do inventário |
| Completa (`20260910-233329-fef6a2`, `--regerar-exemplo --sem-publicar`) | exemplo regerado; byte a byte ok; **67 ok**; 30 pares m-kg/m-rs; HTML **9,1 MB** (9.540.848 bytes); números iguais (124.600 · 71.478 · 57,4% · 1.199,9 t · 71 · RTM 1762/1589/173) |
| Navegador (servidor local, recarga limpa) | chips "Ano fiscal*" / "Ano civil"; linha de acumulado "Ano fiscal 2026 (set/25–ago/26): 13.115,8 t · 150.249 PDVs distintos no período · vs FY25: — (sem par na série …)"; em civil "Ano 2026 (jan/26–ago/26): 8.841,6 t · 137.389 …", em R$ "R$ 304,0 mi"; faixas "FY26" (fiscal) e "2025 | 2026" com divisória (civil) nos dois gráficos da Evolução; tabela da série com "Acum. no ano · FY26 · t | 11.915,9 13.115,8" e "Δ% acum. vs FY25 | — —"; "Ano a ano" fiscal: FY25 "2 de 12 · incompleto" 84.382 PDVs 2.302,8 t, FY26 "12 de 12" 150.249 13.115,8 t, Δ com a nota; civil: 2025 "6 de 12 · incompleto", 2026 "8 de 12 · em curso"; com supervisor Murilo Cunha a linha vira "22,4 t · 1.196 PDVs distintos" e o ano a ano mostra o supervisor; com Amendoim, a categoria (FY26 100.876 PDVs · 4.842,5 t); coluna "Acum. no ano FY26 · t" em categorias (Amendoim 4.842,5), clusters (AS 01-04 4.026,1) e distribuidores; URL `cal=civil`; RTM com chips esmaecidos; 375 px sem rolagem horizontal; 0 NaN; **console sem erro** |
| Tamanho | 8,7 → **9,1 MB** (+0,4 MB: séries com acumulados, tabelas, ano a ano; estimado em P6 +0,2) |

## (c) O que ficou pendente

- Par do comparativo anual e LY dos acumulados: dependem da Mtrix set/24–jun/25 (D5, pedido à Mtrix); nenhuma mudança de
  código quando chegar.
- Trimestre e semestre fiscal na tela, acumulado por categoria × distribuidor: fora desta fase (P10).
- Próxima fase: **F6** (aba Penetração).

## (d) Checklist para você

Abra `data/dn/painel/Scorecard_DN_2026-08.html` (Ctrl+F5) — é o gerado, ainda não publicado.

- [ ] Barra: linha "Ano" com "Ano fiscal" ligado e a nota "Ano fiscal 2026 (set/25–ago/26) · muda só …".
- [ ] Visão geral: abaixo dos cards, "Acumulado no ano · Ano fiscal 2026 (set/25–ago/26): 13.115,8 t · 150.249 PDVs distintos no período · vs FY25: — (sem par …)"; em "Valor · R$" vira R$ 444,9 mi; em "Ano civil" vira "Ano 2026 (jan/26–ago/26): 8.841,6 t · 137.389 …".
- [ ] Evolução: faixa "FY26" sob os dois gráficos; em "Ano civil", "2025 | 2026" com a divisória em dez/jan; a tabela da série tem as linhas "Acum. no ano" e "Δ% acum."; a tabela "Ano a ano" mostra FY25 (incompleto) e FY26 (12 de 12), Δ com a nota.
- [ ] Com um supervisor ou uma categoria na barra, a linha de acumulado e o "Ano a ano" mudam para o recorte.
- [ ] Tabelas de categorias, clusters, supervisores e distribuidores: coluna "Acum. no ano" com "FY26 · t" (ou "2026 · R$").
- [ ] Copiar a URL com `cal=civil` e abrir em outra aba: mesma perspectiva.
- [ ] Pontos de venda, RTM e Definições: chips do Ano esmaecidos.
- [ ] Console (F12) sem erro; 375 px sem rolagem horizontal.
- [ ] Com o ok: `python run_dn.py --mes 2026-08` publica.
