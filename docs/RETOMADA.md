# RETOMADA · Scorecard DN — leia isto primeiro

Reescrito em **13/09/2026**, ao fim do refino do painel (E1–E6), atualizado em **14/09/2026** (estabilização após o checklist) em **15/09/2026** (limite do HTML, PELLAH; à noite, Etapa 1 de performance) em **16/09/2026** (Etapa 2 publicada, RN-60 a RN-64, aba Pontos de venda, limpeza da pasta) em **22/09/2026** (CSV sem tags, média por PDV RN-65, distribuidor na Visão Geral; Mtrix de 21/09) e em **02–03/10/2026** (hierarquia e bases comuns, git/GitHub, limpeza — §0).
Serve para qualquer pessoa ou IA retomar o trabalho sem a conversa anterior. O histórico completo (reforma, evolução F0–F11,
frequência) está nos documentos da §7; esta página traz só o que vale hoje.

## 0. Atualização de 02–03/10/2026 (ler antes da §1, que é de 22/09)

- **Pastas:** o projeto mudou para `Documentos/PAINÉIS - SCORECARDS/Painéis - Alavancas/DN` (junto com ROTA e `Dashboard - Gerencial`). Publicação em `../../../Painéis Comerciais/...`.
- **Hierarquia:** a `Hierarquia_Consolidada` saiu. Vale a `Hierarquia_AAAAMMDD.xlsx` mais recente em `PAINÉIS - SCORECARDS/bases compartilhadas/` (comum aos 3 projetos). Rótulo = "código - nome" (RN-15). A `Estrutura de Clientes` da mesma pasta não é usada no DN.
- **81 distribuidores no painel** (eram 71): os 10 sem hierarquia ganharam linha. 9 deles não vendem há 3+ meses → novo segmento **Sem venda** (RN-14). Validação "distribuidores no painel" agora = os com linha no mês, e os demais todos Sem venda.
- **RTM:** supervisor do destino = o da filial do código (RN-44/RN-52), não do grupo pelo nome (a CHUA passou a ter filiais de 2 supervisores).
- **Out/26 ignorado** (`fontes.sellout.arquivos_ignorados`): extração de 02/10 com 7 distribuidores; tirar da lista quando chegar extração maior.
- **Publicado 02/10/2026 11h55**: só o canal, md5 `8c1151a8…`, 14,1 MB, set/26 fechado: base ativa 133.984 · positivados 69.348 · DN 51,8% · 1.211,7 t · 72 distribuidores com venda · volume vs LY +0,7% (Base atual +3,0%).
- **Fechado no mesmo dia (02/10, tarde):** Gerencial migrado (D-83: hierarquia comum, rótulo "código - nome", saneamento Faltando desligado; D-84: pallet e displays fora) e publicado; as pastas de `Painéis Comerciais/Gerencial` foram renomeadas pelo código e os **18 painéis por usuário do DN foram publicados** nelas (89 arquivos de nome antigo em quarentena no `_arquivo` do Gerencial). ROTA migrado (D-49) e com publicação liberada (D-50). O DN volta a rodar normal (`python run_dn.py`, sem `--sem-usuarios`). Regra de limpeza do nome igual nos três: tira o "(código)" final e o "_" inicial quando o número é o código da linha.
- **Bases comuns (02/10, tarde):** `Produtos.xlsx` e `RTM_DePara_Transicao.xlsx` passaram para `PAINÉIS - SCORECARDS/bases compartilhadas/` (uma cópia para DN e Gerencial; o RTM é a versão do DN, com CNPJ). As cópias antigas foram excluídas na limpeza de 03/10/2026. Rodado com `--sem-publicar`: HTML do canal md5 `8c1151a8…` = publicado, 18 painéis por usuário = publicados, FATO_SELLOUT idêntica (Gerencial: D-85).
- **Cadastro único de distribuidores (02/10, noite):** `Distribuidores_DePara.xlsx` também foi para `bases compartilhadas/` (o Gerencial lê dele o nome do destino do RTM pelo código, D-86; a tela do Gerencial segue com a bandeira do BI). Coluna `Supervisor` virou opcional (vazia; supervisor só pela Hierarquia). Regra "1 nome reduzido = 1 bandeira do BI": 1039743 → CHUA SERRA, 1022476/1022475 → ZAFFALON PELOTAS / ZAFFALON RIO PARDO (versão anterior excluída na limpeza de 03/10/2026). Medido: o nome reduzido NÃO aparece no HTML (a tela usa a descrição da filial na Mtrix) — canal md5 `8c1151a8…` e 18 usuários idênticos ao publicado; ganho = nenhum nome reduzido com 2 supervisores (CHUA tinha 2; o RTM busca supervisor por nome). Pendente: DIBS (1006829) e NOVA ENERGIA (1054683) no cadastro, aguardando CNPJ/data/status do Douglas.
- **Bases comuns — quadro final (02/10):** em `PAINÉIS - SCORECARDS/bases compartilhadas/` ficam as 6 bases lidas por mais de um painel, uma cópia só de cada: `Hierarquia_AAAAMMDD.xlsx` (DN, Gerencial, ROTA; vale a de data mais recente), `Estrutura de Clientes_AAAAMMDD.xlsx` (Gerencial, ROTA), `Produtos.xlsx`, `RTM_DePara_Transicao.xlsx` e `Distribuidores_DePara.xlsx` (DN, Gerencial), `Metas_*.xlsx` (Gerencial, ROTA). Atualizar uma delas muda todos os painéis que a leem. No DN, `bases/` tem só a Mtrix, `Clusters_DePara` e `DE-PARA_Ponderada_Clusters`.
- **ROTA (02/10):** nome dos clientes pela Estrutura de Clientes (D-51; `Clientes_Rota.xlsx` aposentado) e meta do sell-in pela `Metas_FY'27` (D-52; o export do BI deixava de fora 12 lojas com outro N4 na Hierarquia, R$ 145 mil em set/26). Publicado (6 painéis). Pendência do BI (P-20 do ROTA, o Douglas ajusta): filtrar o export pela lista de clientes da rota, para entrar o faturado dessas 12 lojas.
- **Git e GitHub (03/10):** o DN passou a ter git (era o único sem). Os 3 projetos estão em repositórios **privados** no GitHub, ramo `main`, autor Douglas Souza: [scorecard-dn](https://github.com/douglaslopes3/scorecard-dn), [painel-rota](https://github.com/douglaslopes3/painel-rota), [dashboard-gerencial](https://github.com/douglaslopes3/dashboard-gerencial). Dados nunca entram (`.gitignore`: `bases/`, `data/`, `.claude/`; no DN também os arquivos de exemplo do `template/`, que têm dados reais — só `template.html` é versionado). Os históricos do Gerencial e do ROTA foram reescritos para tirar planilhas com dados: **códigos de commit antigos citados em docs antigos não existem mais**. Envio: `git push` (login guardado pelo Git Credential Manager; o `gh` não pode ser instalado na máquina).
- **Limpeza (03/10):** regra do Douglas — o que deixa de ser usado é **excluído, não arquivado** (o git guarda o histórico do código). Foram excluídos 117 itens (~860 MB): `_arquivo/` do DN e do Gerencial, `_descartar/` e `Transcrições/` do ROTA, `_versoes/`, caches órfãos, builds e pastas locais com nome antigo, `template_v3.html`. Conferido depois: DN canal md5 `8c1151a8…` = publicado; Gerencial e ROTA com testes e pipeline ok.
- **Desenho do fluxo dos 3 painéis (03/10):** [Fluxo dos Painéis Comerciais](https://claude.ai/artifact/2GtTgvnYJjdDsCGZs3hYZG) — substitui o antigo `docs/fluxo_paineis.png` (só do DN, excluído).
- **Como trabalhar a partir daqui:** mudança → rodar → conferir md5/números → commit "D-xx: ..." → `git push`. Exclusão só com lista aprovada pelo Douglas. Para reescrever histórico git: copiar antes os arquivos afetados (o `filter-branch` apaga do disco o que sai do HEAD) e só podar objetos depois de conferir.
- **Pendências:** (1) DIBS (1006829) e NOVA ENERGIA (1054683) no cadastro de distribuidores — aguardando CNPJ, data de cadastro e status do Douglas; (2) out/26 da Mtrix ignorado até chegar extração maior; (3) tabela de absorção (abaixo).
- **Próximo (aprovado, não iniciado):** tabela de absorção dos PDVs dos distribuidores "Sem venda" (quem passou a atender e quanto falta repor).

## 1. Estado

| Item | Estado |
|---|---|
| Publicado no ar | `Painéis Comerciais/DN/Scorecard_DN.html` de **22/09/2026 12h01** (md5 `856f59ce…`, 15,1 MB, 120 validações, canal + 18 usuários; a versão das 11h43, md5 `1a8b7c52…`, ainda levava `nf_min` no blob): set/26 parcial + ago/26 fechado, 25 meses, janela de 6 meses, 4 abas visíveis, **Mtrix atualizado em 21/09/2026** (Douglas rodou a rotina em 21/09 09h35 e publicou). Diferenças para a versão de 21/09 (só template e config, nenhum número): **CSV das tabelas sem tags HTML** (Positivado "não" saía com `<b style=…>`), coluna **kg / R$ médio por mês com compra** na tabela de PDVs (RN-65) e **saída da coluna "NFs mín. no mês"** (RN-58), **filtro Distribuidor na Visão Geral** (cards, acumulado e gráfico mês a mês do distribuidor; ranking do mês oculto; RN-44 revista). JSON: só carimbos e `abas[0].filtros` diferem do de 21/09. Versão anterior de 16/09 07h16: md5 `e6519850…` |
| Painéis por usuário | **Etapa 2 publicada em 16/09/2026 07h21** (`docs/distribuicao_etapa2.md`): 18 painéis em `Painéis Comerciais/Gerencial/<rótulo>/Scorecard_DN_N<n>_<slug>.html` (Michel = cópia do canal, 3 gerentes, 14 supervisores), md5 conferido nos 18, soma dos níveis = canal, zero vazamento. Toda execução de `python run_dn.py` regera e republica os 18 (só copia quando o md5 muda) |
| Performance | **Etapa 1 concluída em 15/09/2026** (`docs/performance_etapa1.md`): sem ingestão 1.016 s → **147 s** para o canal; canal + 18 usuários ≈ 7 min |
| Gerado | JSON e HTMLs em `%LOCALAPPDATA%\Dori\DN\painel\` (canal) e `...\painel\usuarios\<slug>\`. `data/dn/painel/` no OneDrive foi esvaziada em 16/09/2026 a pedido do Douglas (HTMLs de jul, ago, set/26 e o `painel_dn.json`) |
| Próximo passo | nenhum pendente: as pastas de `Painéis Comerciais/Gerencial` já estão compartilhadas com cada usuário desde o projeto dos Gerenciais (Douglas, 16/09). Rotina mensal: soltar o arquivo Mtrix e rodar `python run_dn.py` |
| Números de ago/26 (mês fechado, janela 6 m) | base ativa **129.595** · sem compra **58.117** · positivados **71.478** · DN **55,2%** · **1.199,9 t** · **71 distribuidores** · frequência **1,25** · RTM 1.762 clientes / **1.589 mensuráveis** / 173 não mensuráveis · aderência **13,4%** (com 5 meses eram 124.800 · 53.322 · 57,3%) |
| Números de set/26 (parcial, janela 6 m) | **Mtrix de 21/09/2026**: base ativa **127.774** · sem compra 90.404 · positivados 37.370 · DN **29,2%** · 560,2 t · R$ 18,7 mi · 70 distribuidores com venda · frequência 1,12 · RTM 1.762/1.589/173 (com o Mtrix de 15/09 eram 125.955 · 110.311 · 12,4% · 201,2 t · 67) |
| Período (conferência) | FY26 150.453 PDVs distintos (+12,3%) e 13.133,5 t · FY25 133.992 · Ano Calendário 2025 136.362 e 12.793,8 t · Acumulado FY26 até mar/26 119.611 e 7.257,8 t |
| Manifesto | última leitura das bases em 15/09/2026 (só `Distribuidores_DePara.xlsx` mudou) |

## 2. Regras de trabalho com o Douglas

1. **Nada é executado, criado, alterado, movido ou apagado sem aprovação escrita.** "Analise, mapeie, levante impactos e me pergunte,
   não deduza, invente, imponha ou crie algo que não exista."
2. Escopo: só este projeto (DN).
3. **Todo número exibido vem das bases**; o que é estimado aparece como estimativa (frequência). Nada inferido.
4. Regras e parâmetros no `config/config.yaml`, nunca no código.
5. Cada etapa: plano → aprovação → execução com `--sem-publicar` → validação → teste no navegador → relatório (a) o que mudou, (b) por
   quê, (c) resultado e pendências, (d) checklist.
6. Medir antes de afirmar; ambiguidade se pergunta antes de agir.
7. Painel gerencial para o head (até o supervisor), usado no computador; poucos textos, sem travessões decorativos.

## 3. Como o sistema funciona

Resumo no `README.md` (comandos, pipeline, abas, parâmetros, rotina). Pontos de retomada:

- `python run_dn.py --sem-publicar` leva ~2,5 min sem ingestão (era ~9 a 17 min até 15/09/2026). **Sem `--sem-publicar` publica o
  parcial** (`publicacao.publicar_mes_em_andamento: true`). JSON e HTML datado saem em `%LOCALAPPDATA%\Dori\DN\painel`.
- Etapa 1 de performance (15/09/2026): `metrics.carregar` devolve a fato com chaves categóricas ordenadas; `metrics.preparar_codigos`
  guarda em `c` os pares mês × distribuidor × PDV (× categoria), a base ativa por nível e os códigos (`c["K"]`, `c["pares"]`,
  `c["pares_cat"]`, `c["base"]`, `c["cats"]`); os cubos saem em texto (`_descat`). `painel._indice` cacheia por cubo.
- Etapa 2 (16/09/2026, `dn/distribuicao.py`, etapa 6 do `executar`): `usuarios(c["dist"])` → `recortar(c, u)` (fato e pares só
  do recorte, `c["recorte"]`, `c["pen_canal"]` do canal) → `metrics.calcular` + `pipeline.fechado` + `pipeline.gerar` → `validar_usuario`
  → `conferir_somas` → `publicar_usuario`. `--usuario 1120` para um só. Q1/Q2/Q5 no config e no relatório.
- O arquivo tem o mês de referência (parcial quando existe) e o último mês fechado completos; os demais meses da janela
  (`painel.janela_arquivo_meses: 25`) são montados dos cubos (`painel.montar(..., leve=True)`) e embutidos como pacotes comprimidos
  por mês (`tabelas.pacote_mes`), abertos no navegador ao escolher o mês.
- Etapa 2b (`pipeline.calcular_fechado`): com mês em andamento, base ativa dos PDVs, carteira, máscara, penetração e RTM são refeitos
  para o mês fechado.
- Período (E5): Mês · Acumulado do ano · Ano, no calendário fiscal (set–ago, FY) ou Ano Calendário. Acumulados de medidas vêm dos
  cubos; PDVs distintos do período de `metrics.acum_pdvs_mensal`; o navegador nunca soma meses.

## 4. Decisões que não se reabrem

Fonte única: **`docs/regras_negocio.md`** (fichas RN, com nota de cada etapa do refino). Decisões do refino: **`docs/refino_painel_proposta.md`**
(D1–D27).

| Tema | Decisão |
|---|---|
| Base ativa / cobertura / DN | kg > 0 em ≥ 1 dos últimos **6** meses (5 até 14/09/2026, A8); PDV em mais de um distribuidor conta em cada um e uma vez no nível |
| Segmentos | Base atual > 6 meses de histórico; Novos até 6 (data de cadastro do de-para; sem ela, 1º mês na Mtrix, "≥") |
| Abas | Visão Geral · Supervisores e distribuidores · Pontos de venda · Definições visíveis; **Penetração e RTM ocultas** (`painel.abas[].oculta`, 14/09/2026, A3), mantidas no projeto |
| Removidos | Alavancas e Matriz (código apagado); Ano a ano, mini-linhas, coluna Penetração da Visão Geral, textos explicativos. Resumos e memória de cálculo: código mantido, desligados (`painel.resumos.ativo`, `painel.memoria.ativo`) |
| Filtros | barra lateral recolhível; o filtro que não vale na aba some; Limpar e Voltar (histórico do navegador) |
| Mês parcial | publicado, etiquetado, com o mês fechado no mesmo arquivo; comparativos mantidos e rotulados (Mtrix é mensal) |
| Penetração | sempre no último mês fechado |
| RTM e Pontos de venda | mostram o mês final do período escolhido |
| Frequência de compra | estimativa (RN-58), rotulada "(estimativa)" |
| Histórico no arquivo | janela móvel de 25 meses (E6); cálculo usa todos os meses |
| Publicação | `Painéis Comerciais/DN/Scorecard_DN.html`; compartilhar a **pasta** com pessoas específicas, Pode exibir; nunca "qualquer pessoa com o link" |
| Carimbo | "atualizado em" = data da última leitura das bases |
| Pontos de venda (16/09/2026) | abre em Todos os PDVs (`painel.pdv_carteira.padrao: todos`, "por enquanto"); filtro Situação só com Todos · Sem compra · Positivados · Clientes RTM (`painel.pdv_situacoes_por_categoria: false`; as opções por categoria confundiam) |
| Painel por usuário (16/09/2026) | recorte na fato; Q1 referência da Penetração = canal; Q2 RTM só destinos do recorte; Q3 vagos também; Q4 N1 = cópia do canal; Q5 carteira só do recorte; `em_erro: continuar` |
| Tabela de PDVs e Visão Geral (22/09/2026) | média do PDV = medida na janela ÷ **meses com compra** (RN-65, não pelos 6 meses fixos; ticket por NF não é calculável); coluna "NFs mín. no mês" **fora da tela e `nf_min` fora do blob** ("não faz sentido pra gente"; `NF_MIN` segue nos cubos; validação "freq · blob de PDVs sem nf_min" no lugar da antiga); Distribuidor age na Visão Geral com o **ranking do mês oculto**; CSV e busca das tabelas usam o texto sem tags (`textoPlano`) |

## 5. Pendências

| # | O quê | Quem |
|---|---|---|
| 1 | ~~Tamanho do HTML~~ **resolvido 15/09/2026**: `validacao.html_max_mb` 15 → 20 (aprovação A/B/C do Douglas). Medido: a janela móvel não estabiliza o arquivo (pacote de set/24 86 KiB × ago/26 300 KiB, out/26 estouraria os 15); 24 meses ganharia só 86 KiB. Backlog estrutural: lista de PDVs em colunas com cidade/bairro/último mês por índice (medido 8,25 → 6,53 MiB) | — |
| 2 | Compartilhar `Painéis Comerciais/DN` com o time depois da publicação | Douglas |
| 3 | Destinos RTM sem cadastro: NOVO RIBEIRÃO PRETO (91), NOVO SJRP (75), DIBS (6), NOVA ENERGIA (1) | Douglas / cadastro |
| 4 | ~~Data de cadastro dos 6 distribuidores censurados~~ **superada**: desde 14/09 o log registra 81 distribuidores com data e 0 censurados; em 15/09 Douglas corrigiu a data da PELLAH (2016 → jun/26) | — |
| 5 | CNPJs das 124 linhas fora da carteira de PDVs ponderados; linha 179 × 41; linha 177 | Douglas |
| 6 | ~~Nome reduzido da SBM ("SBN")~~ **resolvida 15/09/2026**: Douglas corrigiu no de-para (SBN → SBM) e encurtou DISPAN, AVANTE, BOA e FAVINHA. Entra na próxima execução de rotina (ingestão completa); só rótulos, nenhum número | — |
| 7 | Alavancas em outro formato (plano por alavanca, como o print do Douglas): só com proposta nova | Douglas |
| 8 | Filtro de Gerente Regional com números próprios (nível novo no pipeline; estudo em `docs/estabilizacao_2026-09-14.md` §5): backlog, só com proposta nova. Desde 16/09 cada gerente tem o próprio painel (Etapa 2), o que atende o uso principal | Douglas |
| 9 | ~~Etapa 2~~ **concluída 16/09/2026**: publicada 07h21, fichas RN-60 a RN-64 registradas; pastas já compartilhadas desde os Gerenciais | — |

## 6. Armadilhas conhecidas

- **Limpeza de 16/09/2026**: `_s1.js`, `_s2.js`, `template/01-analise-prototipo.md`, `template/business-rules.md` e `docs/historico/` (painel v1 e ferramentas do protótipo) foram apagados a pedido do Douglas; nada vigente os lia. Referências a eles em `docs/reforma_fase0/1.md` e `estabilizacao_2026-09-14.md` são históricas.
- **Editou o template?** `python run_dn.py --regerar-exemplo` uma vez; depois uma execução sem a opção deve dar o mesmo md5.
- **Template sem `<tbody`**: a validação `tabelas · sem linhas estaticas` aborta; tabelas são montadas em JS.
- **Pacotes por mês levam só colunas literais do template** (`tabelas.colunas_usadas`); `acum_*` entram por prefixo. Coluna nova lida
  no navegador tem de aparecer escrita no template.
- **Campo novo no JSON** entra em `template/data-inventory.json` (formato; `bruto` para números crus e booleanos).
- **Tamanho**: limite `validacao.html_max_mb: 20` (MiB; 15 até 15/09/2026). Com a janela de 25 meses e a base ativa de 6 meses fica em ~14,9 MB
  e cresce ~0,2 a 0,3 MB por mês (pacotes mensais mais cheios a cada mês, lista de PDVs acompanhando a base ativa). Reserva medida: gráficos
  lendo das tabelas mensais (~1 MB); lista de PDVs em colunas (~1,7 MB).
- **PDVs distintos do período** (`metrics.acum_pdvs_mensal`): agrupar por códigos inteiros; com colunas de texto a execução passa de 20 min.
- **Mês fechado × referência**: cards, acumulados, RTM e lista de PDVs do mês fechado são validados contra a execução só desse mês;
  mexer em `montar` sem `leve` equivalente quebra `comprimidos · leve == completo`.
- **Heredoc longo no terminal falha**: gravar scripts em arquivo no scratchpad e executar. Fim de linha misto: `pipeline.py`,
  `metrics.py`, `painel.py` e `config.yaml` usam CRLF; `run_dn.py`, `utils/log.py`, README e docs usam LF. Reescrever um arquivo
  por script Python converte sem querer (aconteceu em 15/09; restaurado).
- **Chaves categóricas (Etapa 1)**: `c["fato"]` tem ANO_MES, DIST, COD_PDV, SEG, SUP, CAT e CLUSTER como categoria ORDENADA.
  Comparar, `isin`, ordenar e agrupar funcionam como texto, mas `.map(Series)` devolve categoria (converter com `.astype(object)`
  antes, como em `penetracao`), e uma coluna nova derivada por `groupby` sai categórica: passar por `_descat` antes de sair de
  `metrics`. `c2["fato"]` do mês fechado precisa de `metrics.recortar_codigos(c, c2)`.
- **Calibração da frequência em cache**: `DN_FREQ_CALIBRACAO.parquet` traz `curated_execucao`; muda a ingestão, recalcula. Para
  forçar, apagar o arquivo.
- **Aceite de mudança de código**: guardar `painel_dn.json` e o HTML de antes e comparar campo a campo (script da sessão de 15/09,
  `comparar_json.py`); só carimbos podem diferir.
- **Frequência (RN-58)**: estimativa gravada numa única linha por par distribuidor × PDV (e × categoria); nunca agrupar por SKU.
  Arquivo Mtrix novo sem `# Frequência de compra` aborta.
- **RTM**: destino casado pelo código do distribuidor (`regras.rtm_destino_chave: codigo`); supervisor do destino em `DN_RTM_SUP_MES`;
  clientes do mês vêm da lista cliente × mês (`painel.rtm_clientes_da_lista`, espelhado no navegador).
- **Carteira de PDVs ponderados (RN-56)**: validade pela regra de CNPJ; linha fora não aborta (`data/dn/quality/carteira_pdv.md`).
- **Máscara PDV × categoria**: janela termina no mês fechado; a máscara do blob é do mês de referência.
- **CSS**: classe de alternância fica no `body`; seletor solto `.classe{display:none}` apaga a página (use `:not(body)`).
  `[hidden]` dentro de `.k` precisa de `display:none` explícito.
- **Mesmo mês em dois arquivos Mtrix** e **distribuidor sem de-para** abortam. Mês faltando no meio da série aborta.
- **Mudou um leitor** (`dn/extract/*`, `dn/utils/texto.py`): cache invalida e a ingestão completa roda (~6 min).
- **OneDrive** pode segurar arquivos (EBUSY): gravar em sequência; pausar a sincronização se o Parquet falhar.
- **Teste no navegador da IA**: `file://` não abre; servir uma cópia por `python -m http.server` numa pasta do scratchpad.

## 7. Onde está cada coisa

| Quero… | Vá em |
|---|---|
| comandos, pipeline, abas, parâmetros, rotina | `README.md` |
| regras de negócio (fichas RN) | `docs/regras_negocio.md` |
| decisões do refino e andamento | `docs/refino_painel_proposta.md` |
| o que cada etapa do refino mudou | `docs/refino_e1.md` … `refino_e6.md` |
| checklist final do refino (respondido em 14/09) | `docs/refino_checklist.md` |
| estabilização de 14/09 (A1–A8, estudo do Gerente Regional, checklist de tela) | `docs/estabilizacao_2026-09-14.md` |
| performance (Etapa 1, 15/09: medição, P1–P6, antes × depois, trade-offs) | `docs/performance_etapa1.md` |
| painéis por usuário (Etapa 2, 16/09: modelo, usuários, segurança, validação, `em_erro`) | `docs/distribuicao_etapa2.md` |
| desenho do fluxo dos 3 painéis (bases compartilhadas → comandos → conferência → publicação → agenda) | [Fluxo dos Painéis Comerciais](https://claude.ai/artifact/2GtTgvnYJjdDsCGZs3hYZG) (página no Claude, privada do Douglas; atualizar quando o fluxo mudar) |
| frequência de compra | `docs/frequencia_etapa1_medicao.md`, `etapa2_proposta.md`, `etapa3_implementacao.md` |
| evolução anterior (F0–F11, carteira) | `docs/evolucao_etapa1_auditoria.md`, `docs/evolucao_f0.md` … `f11.md`, `docs/pdv_ponderados.md` |
| reforma e fases originais | `docs/reforma_fase0.md` … `fase5.md`, `docs/rodada_2026-09-10.md`, `docs/fase1..3.md` |
| contrato de campos | `template/data-inventory.json` |
| qualidade da última ingestão | `data/dn/quality/relatorio_qualidade.md` |
| logs e resumos por execução | `data/dn/logs/` |

## 8. Primeiro comando ao retomar

```powershell
cd "C:\Users\dldsouza\OneDrive - Dori Alimentos S.A\Documentos\Painéis - Alavancas\DN"
python run_dn.py --sem-publicar
```

Deve terminar em ~2,5 min com "bases inalteradas", **120 validações ok** e os números da §1, com o HTML em
`%LOCALAPPDATA%\Dori\DN\painel`. Se disser "base(s) alterada(s)", a ingestão roda (~1 a 6 min) e os números podem mudar de forma
legítima: comparar com a §1 e explicar a diferença antes de publicar.
