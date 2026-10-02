# Evolução · Fase F9 — resumos executivos dinâmicos (11/09/2026, manhã)

Executada após a F8 (`docs/evolucao_f8.md`, publicada 11/09 09h35) e a aprovação da proposta da F9 (P1–P10; Q-a bloco no topo de
cada aba; Q-b a frase aparece sempre e o limiar só marca "atenção"; Q-c maior PDV sem compra com nome, distribuidor e CNPJ; Q-d os
24 limiares aprovados como propostos) pelo Douglas em 11/09/2026. Regra implementada: **RN-48** (modelo e frases da A.14, D17);
**RN-49** fica parcialmente vigente (memória no tooltip de cada frase). Sem regra nova.

**Publicado em 11/09/2026 às 10h49** (execução `20260911-104728-6f337a`, 107 validações ok, md5 `7f5c67a8366e84b322b73c3f6251699f`, 11.061.531 bytes), após o ok do Douglas no checklist (d). Prova final antes da publicação: execução `20260911-100258-aebf63`.

## (a) O que foi alterado

### Config e pipeline

| Arquivo | Mudança |
|---|---|
| `config/config.yaml` | `painel.resumos.ativo: true`; `termos_vetados` (15 palavras: meta, previsão, garantido, culpa, deveria, precisa, ruim, ótimo…); **24 regras** em `painel.resumos.regras[]`, cada uma com id, aba, RN, indicador, tipo (operação), parâmetros, texto com `{campo}` (formato pelo sufixo: `_pct`, `_pp`, `_t`, `_rs`, `_m` métrica, `_n`, `_dn`/`_dm` com sinal), **limiar** (campo, operador, valor; ausente = informativa) e link de próximo nível; `painel.textos.resumo_titulo/sem_dado/sem_ly/atencao/nota` |
| `dn/resumos.py` (novo) | avaliador em Python: um **tipo = uma operação** (`dn_mes`, `delta_serie_extremo`, `extremo`, `pdv_sem_compra`, `pdv_maior_sem_compra`, `pdv_concentracao`, `novos`, `abaixo_p75`, `sem_venda_mes`, `rtm_aderencia`, `rtm_vazamento`, `rtm_parados`), aplicada às tabelas do JSON no recorte do canal (métrica t) → esperado; `lint_textos` (termos vetados abortam a execução); formatação por sufixo igual à do navegador |
| `dn/painel.py` | `rtm.destinos[].pct_sem_compra` (R4) e `pen_nivel_cat[].pct_sem_compra_mes` (N3); `kpi_json` (KPIs crus por segmento para o motor do navegador); `resumos.{regras_json, esperado_json, textos, sem_venda}`; lista de distribuidores sem venda quando o mês está em andamento (D4) |
| `dn/pipeline.py` · etapa 4 | **10 validações novas**: `resumos · {visao, evolucao, clusters, distribuidores, pdv, rtm, penetracao, matriz} = curated` (a regra avaliada em Python no JSON = recálculo independente na curated: V2 em `DN_DISTRIBUIDOR_MES`, E1 em `DN_CANAL_CAT_MES`, C1 em `DN_CLUSTER_CANAL_MES`, D1, P2 no blob, R4 em `DN_RTM_DESTINO`, N1/N3 em `DN_PEN_NIVEL_CAT`, M1 em `DN_PEN_DIST_CAT`), `resumos · regras do config no HTML` (24 ids e o esperado embutidos), `resumos · textos sem termos vetados`. 97 → **107** |
| `template/data-inventory.json` | 704 → **717** campos |

### Template

| Onde | Mudança |
|---|---|
| Bloco **"Resumo do recorte"** | no topo de Visão geral, Evolução, Clusters e supervisores, Distribuidores, Pontos de venda, Penetração, Matriz e RTM (Definições não tem); uma linha por frase: marca **atenção** quando o limiar é atingido, a frase (o que · onde · quanto · contra o quê) e o botão **ver** (aplica o filtro do próximo nível e abre a aba); tooltip com a **memória** (regra, RN, indicador, período, filtros ativos, fonte, limiar, valores, data dos dados); "sem dado suficiente para {indicador} no recorte" quando falta dado; frases sobre o blob de PDVs esperam a descompactação ("carregando") |
| Motor `dnRs*` | espelho de `dn/resumos.py`: mesmos tipos, mesma formatação por sufixo; lê as tabelas embutidas do recorte ativo (KPIs por segmento ou do supervisor, séries `DN_SERIES`/`EVO_SUP`, tabelas por aba, `dnPenRows`, `dnMxRows`, blob de PDVs); monta escondida a aba que guarda o dado quando preciso; **auto-conferência**: sem filtros e na métrica t, compara os valores de cada frase com o esperado do pipeline e marca divergência com tracejado (tolerância 0,06 ou 0,5%, por causa dos números formatados) |
| Dados | `DN_KPI` (KPIs crus por segmento), `dados-resumos-regras` e `dados-resumos-esperado` (JSON) no cabeçalho; `DN_RS_TXT` com os textos do config |
| Ganchos | filtros, métrica, montagem de aba e carga do blob de PDVs redesenham os resumos |
| Definições | parágrafo "Resumos" |

### Docs

`docs/regras_negocio.md` (RN-48 → **vigente** com os 24 limiares registrados; RN-49 parcial; 51 vigentes · 1 aprovada · 3
declaradas); `README.md` (changelog, parâmetros); `docs/RETOMADA.md` (§1, §5 pendência 9 → publicar a F9 e propor a F10, §6
armadilha dos resumos, §7); este relatório.

## (b) Por quê

A.14 (D17, D27): não havia resumo; o modelo aprovado exige que cada frase seja uma regra declarada, com limiar objetivo, sem
adjetivo, causa ou prescrição, avaliada sobre o recorte que o leitor está vendo e auditável. Avaliar no navegador é o que
permite a frase acompanhar os filtros; avaliar também no pipeline, no recorte do canal, é o que mantém a rastreabilidade
(validação contra a curated e auto-conferência na tela).

## As 24 frases em ago/26, recorte do canal (métrica t)

| Aba | Frase (como aparece) | Atenção |
|---|---|---|
| Visão geral | DN 57,4% em ago/26: −3,2 p.p. vs jul/26; vs ago/25: sem LY na série | sim |
| Visão geral | Cobertura 71.478 PDVs (−2,3% vs jul/26): maior queda MAM Feira de Santana (−500), maior alta Francal Imperatriz (+699) | sim |
| Visão geral | Categoria com maior queda de % cobertura: Amendoim, −3,2 p.p. vs jul/26 | sim |
| Visão geral | 56.869 pares da base ativa sem compra em ago/26 (44,0%), que compraram 1.231,5 t / R$ 42.439.505 na janela | sim |
| Evolução | Medida −79,7 t vs jul/26: maior retração Amendoim (−65,1 t), maior contribuição Bala (+5,5 t) | sim |
| Clusters | Cluster com maior queda de DN: AS 20+ (−9,2 p.p.); maior alta AS 10-19 (+1,0 p.p.) | sim |
| Clusters | Supervisor com maior queda de PDVs: BA/SE (vago, Oliveira) (−831); maior alta SPI Murilo Cunha (+759) | sim |
| Clusters | Menor DN entre supervisores: NO Herilson Holanda, 44,8%, −12,6 p.p. vs o recorte (57,4%) | sim |
| Distribuidores | Maior queda de cobertura: MAM Feira de Santana (−82,5%); maior alta Propec (+7.550,0%) | sim |
| Distribuidores | 3 distribuidores novos: 4.905 PDVs (6,9% da cobertura) e 50,6 t | informativa |
| Distribuidores | 66 de 71 distribuidores abaixo da referência P75 em pelo menos uma categoria foco; 28 nas 4 | sim |
| Distribuidores | (D4 não aparece: ago/26 é mês fechado) | — |
| Pontos de venda | Maior PDV sem compra em ago/26: Distribuidora Freitas Lopes · EBD (Pará) · 02846807000175, 12,7 t / R$ 329.875 na janela | informativa |
| Pontos de venda | Os 10% maiores pares (12.914) concentram 75,9% do volume de ago/26; os 1.000 maiores, 32,2% | sim |
| RTM | Aderência 13,4% em ago/26, +0,9 p.p. vs jul/26 | não |
| RTM | 93 clientes compraram de outro distribuidor em ago/26 (5,9% dos mensuráveis): 2,3 t / R$ 64.643 | sim |
| RTM | 100 ativados parados de 313 já ativados (31,9%) | não |
| RTM | Destino com maior gap: VJS, 1 de 1 clientes sem compra (100,0%) | sim |
| Penetração | Categoria com mais lojas a positivar: Amendoim, 12.824 (potencial de entrada 23,4 t/mês) | informativa |
| Penetração | Nível mais distante da referência nas foco: SPC+Litoral Deodato Carmo em Amendoim, 37,0% da referência | sim |
| Penetração | Maior oportunidade de recorrência: Gomas, 45.837 compradores na janela sem compra no mês (54,5%) | sim |
| Matriz | Maior potencial de entrada do recorte: Distrilobo × Regaliz, 1,4 t/mês | informativa |
| Matriz | Principal gap de recorrência: Central Goiânia × Gomas, 3.086 compradores na janela sem compra no mês | informativa |
| Matriz | Principal oportunidade de mix: EBD Aquiraz × Gomas, 715 lojas a positivar (714,5 arredondado na tela) | informativa |

Duas leituras que a regra revela e que valem registro: a "maior alta" de cobertura por distribuidor (D1) é a Propec, com base
minúscula (+7.550%); e o "destino com maior gap" do RTM (R4) é a VJS, com 1 cliente. As regras estão certas pelo que foi
aprovado; se quiser piso de base (por exemplo, ≥ 30 PDVs ou ≥ 10 clientes), é um parâmetro a acrescentar na regra, com sua
aprovação.

## Correções feitas durante a prova

| Sintoma | Causa | Correção |
|---|---|---|
| N3 apontava Compound (68% sem compra, 2.471 compradores) | ranking pelo % | ranking pelo número absoluto, limiar no % (Gomas 45.837, 54,5%) |
| frase da Matriz no grão supervisor mostrava "— × Amendoim" | tabela formatada traz "—" no distribuidor vazio | o motor trata "—" como vazio e usa o nome do supervisor |
| aviso de escape (`\/`) em `painel.py` | string mal escapada pelo script | corrigido |
| frases da Matriz não acompanhavam a troca de grão/chips | ganchos ausentes | `dnRsAplicar` nos chips da Matriz |

## Prova

| Checagem | Resultado |
|---|---|
| Completa 1 (`20260911-095310-0e70ff`) | 107 ok; 8 abas = curated; 24 regras, 23 avaliadas no canal (15 em atenção, 0 sem dado); 15 termos vetados conferidos |
| Completa final (`20260911-100258-aebf63`, `--regerar-exemplo --sem-publicar`) | exemplo regerado; byte a byte ok; **107 ok**; HTML **10,5 MB**; números iguais (124.600 · 71.478 · 57,4% · 1.199,9 t · 71 · RTM 1762/1589/173) |
| Navegador (servidor local) | bloco em 8 abas com as frases da tabela acima; **0 divergências** na auto-conferência do recorte do canal (todas as 23 frases batem com o esperado do pipeline); com supervisor Murilo Cunha as frases da Visão geral e da Penetração passam ao recorte dele; grão supervisor na Matriz muda as três frases; tooltip com a memória; "ver" da V2 abre Distribuidores com o MAM fixado; frases do blob aparecem após a descompactação; 0 NaN; **console sem erro** |
| Tamanho | 10,5 → **10,5 MB** (+0,03 MB) |

## (c) O que ficou pendente

- Piso de base para D1 e R4 (ver leitura acima): parâmetro novo só com sua aprovação.
- Rastreabilidade por **número** (cards, oportunidades) a um clique: F10 (RN-49). As frases já têm a memória.
- D4 só será vista com mês em andamento (set/26).
- Próxima fase: **F10**.

## (d) Checklist para você

Abra `data/dn/painel/Scorecard_DN_2026-08.html` (Ctrl+F5) — é o gerado, ainda não publicado.

- [ ] Bloco "Resumo do recorte" no topo de cada aba (menos Definições), com as frases da tabela acima e a marca "atenção".
- [ ] Nenhuma frase tracejada (auto-conferência contra o pipeline) sem filtros.
- [ ] Escolher um supervisor ou distribuidor muda as frases; "Valor · R$" troca a Evolução e a Matriz para R$.
- [ ] Passar o mouse numa frase mostra a memória (regra, RN, período, filtros, fonte, limiar, valores, data); "ver" leva ao próximo nível.
- [ ] Pontos de venda: as duas frases aparecem depois que a lista carrega.
- [ ] Console (F12) sem erro.
- [ ] Com o ok: `python run_dn.py --mes 2026-08` publica.
