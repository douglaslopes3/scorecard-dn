# Evolução · Fase F2 — Last Year explícito no gráfico de evolução (10/09/2026, noite)

Executada após a F1 (`docs/evolucao_f1.md`, publicada 21h24) e a aprovação item a item da proposta da F2 (P1–P8; Q-a chave
padrão PDVs, Q-b eixo em "R$ mi", Q-c Δ% vs LY só na tabela e no tooltip na chave PDVs, Q-d "quem atendeu" em R$ fica
registrado) pelo Douglas em 10/09/2026. Regras implementadas: **RN-47** (coluna + linha LY + Δ% sob o mês, chave PDVs/medida,
campos `volume_ly` e `receita_ly`), **RN-22** (mês sem LY = ausência) e a parte de **RN-21/RN-25** que manda os Δ% do gráfico
virem do JSON (fecha o RK13 da auditoria).

**Publicado em 10/09/2026 às 21h49** (execução `20260910-214652-3bcbf1`, 46 validações ok, md5 `8e842b9eafb1a73e8234a1c2a5eb9158`, 8.318.807 bytes), após o ok do Douglas no checklist (d).

## (a) O que foi alterado

### P2 · Pipeline

| Arquivo | Mudança |
|---|---|
| `dn/painel.py` · série de cada nível | por ponto: `volume_ly` e `receita_ly` (junção em `ANO_MES_LY` dentro do mesmo grupo, como o `cobertura_ly`), e os 12 comparativos que a curated já tinha por mês (`cobertura_var_*`, `pct_cobertura_var_*`, `volume_var_*`, `receita_var_*`, cada um vs mês anterior, L3M e LY). Números crus da série **arredondados** (t com 3 casas, R$ inteiro, % e p.p. com 2 casas; antes iam com 14 casas). Bloco `graficos` no JSON (chave padrão, rótulo do chip de PDVs, texto "sem LY" com o primeiro mês da série) |
| `dn/pipeline.py` · etapa 4 | **2 validações novas**: `serie · LY = mes correspondente` (canal + 5 distribuidores: LY de cada ponto = valor do mês `ANO_MES_LY` na curated, ou nulo quando não há par) e `serie · Δ do JSON = curated = recalculo` (12 comparativos × 12 meses do canal iguais à curated, com recálculo independente de dois deles a partir dos valores crus). 44 → **46** |
| `config/config.yaml` | `painel.graficos.chave_padrao: pdv`; `painel.rotulos.graf_pdv`; `painel.textos.sem_ly` |
| `template/data-inventory.json` | 292 → **351** campos: 14 por entidade de série (`dn.serie`, `categoria.serie`, `segmento.supervisor.serie`, `distribuidor.serie`) + 3 de `graficos.*` |

### P3 · Template

| Onde | Mudança |
|---|---|
| Séries embutidas (4 definições) | `vly`, `rly` e os 12 Δ com chaves curtas; `DN_GRAF` (config do gráfico) no `<script>` inicial |
| `dnDraw` | reescrito em **duas chaves**. **PDVs**: barras empilhadas base atual/novos, linha da base ativa, linha tracejada do mesmo mês LY **com marcadores** (só entre meses consecutivos com par), % DN sob o mês; **Medida**: coluna do mês na medida do seletor (t ou R$), linha LY com marcadores, **Δ% vs LY sob o mês** (verde/vermelho, "—" sem par). Tooltip nativo por mês (`<title>`): atual, LY e Δ. Legenda "sem LY na série (Mtrix a partir de jul/25)" quando algum mês exibido não tem par. Chips da chave renderizados **dentro** do gráfico (valem também nos drills de supervisor e distribuidor); o chip PDVs fica desabilitado em série que só tem medida |
| Tabela da série | chave PDVs: base ativa, positivados (e por segmento), % cobertura, **positivados · mesmo mês LY**, Δ% PDVs (3), Δ % de cobertura (mês anterior e LY), medida do seletor. Chave medida: medida, **medida · mesmo mês LY**, Δ% (3), PDVs positivados. **Todos os Δ vêm do JSON**; `dnVar` e `dnMean` removidos |
| Estado | `DNE.graf` (`pdv` \| `med`, padrão do config), `localStorage`, URL `&graf=med`; `dnGraf()` redesenha os gráficos montados |
| CSV da série | nome com a chave (`serie_<key>_pdv` / `_med`) e a métrica (F1) |
| Definições | frase sobre "Mesmo mês LY" (junção, nunca deslocamento; sem par = em branco, não zero) e as duas chaves do gráfico |
| CSS | `.dnchave` (barra de chips do gráfico) |

Correção durante o teste de navegador: a linha LY não era traçada quando o primeiro mês com par vinha depois de meses sem par
(os marcadores apareciam; o traço entre jul/26 e ago/26 não). A montagem dos segmentos passou a começar um novo `M` a cada
retomada; nova prova completa depois da correção.

### P6 · Docs

`docs/regras_negocio.md` (RN-22 e RN-47 → **vigente**; RN-21 e RN-25 anotadas: Δ do gráfico já vêm do JSON; 30 vigentes ·
22 aprovadas · 3 declaradas); `README.md` (changelog, parâmetros); `docs/RETOMADA.md` (§1, §5 pendência 9 → publicar a F2 e
propor a F3, §6 armadilha do gráfico, §7); este relatório.

## (b) Por quê

A.11 (D6, D7): comparar cada mês com o mesmo mês do ano anterior de forma explícita, em PDVs e na medida do seletor, sem nunca
preencher com zero o que não existe (RN-22). E A.10 (D31)/RK13: o gráfico recalculava Δ em JS, duplicando as fórmulas do
Python; agora o pipeline entrega tudo e valida.

## Prova

| Checagem | Resultado |
|---|---|
| Após P2 (execução `20260910-213235-dd6a3d`, sem template) | 46 validações ok; `serie · LY = mes correspondente` (canal + 5 distribuidores); `serie · Δ do JSON = curated = recalculo` (12 × 12); HTML 7,77 MB (o arredondamento já encolheu) |
| Após P3 (`20260910-213551-40a673`) | exemplo regerado; byte a byte ok; 46 ok; HTML 7,93 MB; números iguais |
| Após a correção da linha LY | execução final registrada abaixo, em (e) |
| Números | **inalterados**: 124.600 · 71.478 · 57,4% · 1.199,9 t · 71 · RTM 1762/1589/173 |
| Navegador (servidor local) | abre em PDVs com o gráfico de hoje mais a legenda "sem LY na série (Mtrix a partir de jul/25)" e 2 marcadores LY (jul/26, ago/26); tooltip "jul/26: 73.185 · mesmo mês LY 62.278 · Δ +17,5%"; tabela com "PDVs positivados · mesmo mês LY" (62.278 · 60.796) e Δ% vs LY (+17,5% · +17,6%), iguais aos de antes; chave "Volume · t": 12 colunas, linha LY só em jul/26 e ago/26, Δ% sob os meses "+9,9%" e "+5,4%" e "—" nos outros 10; em R$: eixo "0,0 mi … 49,7 mi", Δ% "+16,9%" e "+11,1%", tooltip "ago/26: R$ 40,3 mi · mesmo mês LY R$ 36,3 mi · Δ +11,1%"; drill de distribuidor com os mesmos chips e 2 marcadores; URL `graf=med`; `localStorage` guarda `graf`; Definições com a frase; 375 px sem rolagem; **console sem erro** |
| Tamanho | 7,8 → **7,9 MB** (+0,13 MB líquido, com o arredondamento) |

## (c) O que ficou pendente

- **Q-d (registrado)**: "quem atendeu" no drill do RTM segue em kg em modo R$.
- LY só existe para jul/26 e ago/26 até a Mtrix de set/24 a jun/25 entrar (D5, pendência de dado).
- Próxima fase: **F3** (aba Evolução: reorganização + evolução por categoria Top N + tabela com participação e sparkline).

## (d) Checklist para você

Abra `data/dn/painel/Scorecard_DN_2026-08.html` (Ctrl+F5) — é o gerado, ainda não publicado.

- [ ] Visão geral abre em "PDVs positivados": gráfico igual ao de hoje, com dois marcadores na linha tracejada (jul/26 e ago/26) e a nota "sem LY na série (Mtrix a partir de jul/25)".
- [ ] Passar o mouse numa coluna: tooltip com o mês, o valor, o mesmo mês LY e o Δ.
- [ ] Tabela da série: linha "PDVs positivados · mesmo mês LY" com 62.278 e 60.796; "Δ% PDVs vs LY" +17,5% e +17,6%; os demais meses "—".
- [ ] Clicar em "Volume · t": colunas de volume, linha LY só em jul/26 e ago/26, "+9,9%" e "+5,4%" sob esses meses e "—" nos outros.
- [ ] Trocar o seletor para "Valor · R$": eixo em "R$ mi", "+16,9%" e "+11,1%".
- [ ] Distribuidores: clicar numa linha → o gráfico do drill tem os mesmos chips e a mesma lógica.
- [ ] URL com `graf=med` abre na chave medida; recarregar mantém.
- [ ] Definições: frase "Mesmo mês LY = valor do mesmo mês do ano anterior, obtido por junção…".
- [ ] Console (F12) sem erro ao trocar chave, métrica e aba.
- [ ] Com o ok: `python run_dn.py --mes 2026-08` publica.

## (e) Execução final

Execução `20260910-214031-fff6f5` (`--mes 2026-08 --regerar-exemplo --sem-publicar`, 213 s): exemplo regerado, renderizador byte a byte ok, **46 validações ok**, HTML 7,93 MB, números iguais. Navegador após a correção (cache limpo): linha LY traçada nas duas chaves (`M 904.5 133.4 L 985.5 135.4` em PDVs; `M 904.5 63.1 L 985.5 66.3` em medida), 2 marcadores, console sem erro.
