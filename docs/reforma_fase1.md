# Reforma · Fase 1 — pipeline único (09/09/2026)

Executada após a auditoria (`docs/reforma_fase0.md`) e a aprovação integral do desenho
(D1–D11, Q1–Q12, quarentena, decisões A1–A9) pelo Douglas em 09/09/2026.

## (a) O que foi alterado

### Quarentena e limpeza (Q1–Q12)

| Item | O que | Para onde |
|---|---|---|
| Q1–Q5 | `src/`, `ferramentas/`, `data/curated|staging|quality|raw`, `bases/Sell In`, `bases/Canais`, `Hierarquia_Clientes_Faltando.xlsx` (202 MB, projeto gerencial) | `Painéis - Alavancas/_fora_do_DN_2026-09-09/` |
| Q6 | `Scorecard_DN_v1.html` (protótipo com dados simulados) | `docs/historico/` |
| Q7 | `template/tools/` (build.py, extract_proto.py, proto.json) | `docs/historico/template_tools/` |
| Q8 | `run_fase1.py`, `run_fase2.py` | apagados (substituídos por `run_dn.py`) |
| Q9–Q12 | `Scorecard_DN_2026-06.html`, `painel_dn.raw.json`, `dn/README.md`, `__pycache__`, `data/dn/staging` | apagados (cache recriado na 1ª execução) |

### Código (D1–D11)

| Item | Arquivo | Mudança |
|---|---|---|
| D1 | `run_dn.py` (novo), `dn/pipeline.py` (novo) | orquestrador com 6 etapas; flags `--mes`, `--sem-publicar`, `--forcar`, `--regerar-exemplo` |
| D2 | `dn/pipeline.py`, `dn/metrics.py` | `RTM_DePara_Transicao` e `Clusters_DePara` entram na curated como `DIM_RTM` e `DIM_CLUSTER`; `metrics.carregar` e `rtm_aderencia` leem só da curated (fim da leitura direta do Excel na etapa de cálculo) |
| D3 | `dn/manifesto.py` (novo) | `data/dn/curated/manifesto.json`: impressão digital (caminho, tamanho, mtime, hash) de cada base + versão dos leitores + totais dos gabaritos; decide a ingestão e é conferido na validação |
| D4 | `dn/extract/cache.py` | `VERSAO_CACHE` manual substituída por `VERSAO_LEITORES` = hash do código de `dn/extract/*.py` e `dn/utils/texto.py` |
| D5 | `config/config.yaml` | novas chaves: `calendario.meses_abrev`, `regras.rtm.{data_migracao, visao_padrao}`, `validacao.html_max_mb`, `painel.rotulos.{canal, segmentos, estados_rtm}`, `painel.tabela.{amostra_linhas, debounce_ms}`, `publicacao.{pasta, arquivo}` |
| D6 | `dn/painel.py`, `dn/metrics.py`, `dn/transform/calendario.py` | rótulos saem do código e vêm do config; `pdv_top_por_distribuidor` sem fallback; JSON ganha `periodo.{janela_meses, segmento_novos_meses, n_meses_serie}` e `meta_execucao.{gerado_em, execucao_id}` |
| D7 | `template/template.html` | 4 trechos: "últimos 5 meses", "(Base atual > 6 meses · Novos < 6 meses)", "(Base atual acima de 6 meses, Novos até 6)" e "13 meses" passam a ler os campos acima. **Nenhuma outra alteração de layout.** Observação: o segundo trecho dizia "Novos < 6"; o código classifica "até 6" (histórico = 6 é Novo); o texto agora reflete a regra |
| D8 | `template/example-data*.json`, `template/Scorecard_DN_base.html` | regerados a partir do painel real de jul/26 (retrato reduzido: 8 distribuidores, 40 PDVs, 40 clientes RTM, blob de 200 pares; todos os blocos, inclusive RTM, exercitados) |
| D9 | `dn/render.py`, `template/data-inventory.json` | `_FMT_EXTRA` removido; inventário passa de 227 para 242 campos (5 novos + 10 que já existiam no JSON sem contrato); campo fora do inventário vira aviso no log |
| D10 | `dn/utils/log.py`, leitores | contagem de linhas lidas/rejeitadas por arquivo; etapas com início/fim/duração; `data/dn/logs/resumo_<execução>.json` com etapas, contagens, avisos, erros, validações, números e o que foi publicado |
| D11 | `README.md`, este documento, `docs/reforma_fase0.md` | documentação; `dn/README.md` (cópia) removido |

Também: `dn/load/parquet.py` e `dn/qualidade.py` só tiveram mensagens/títulos ajustados
(`run_pipeline.py` → `run_dn.py`).

## (b) Por quê

Cada item corresponde a um achado da auditoria (`docs/reforma_fase0.md`, §0.4 e §0.7):
camada curated furada (P1 → D2), painel gerado sem saber que a base mudou (P2 → D3),
bump manual do cache (P11 → D4), rótulos e parâmetros fixos (H1–H8 → D5–D7), prova do
renderizador sobre um exemplo incompleto (H10 → D8), contrato incompleto (H8 → D9),
requisitos de log e falha explícita da Fase 1 (D10), material de outro projeto na pasta (A1).

## Prova de que nada mudou nos números

Execução `20260909-195850-4777a4` (`--sem-publicar --forcar --regerar-exemplo`, 400 s, cache frio):

| Checagem | Resultado |
|---|---|
| 13 validações da etapa 4 | todas ok (placeholders 0; 6,1 MB; positivados 73.185 = recálculo independente; base ativa 120.817; volume 1.279,5 t; 70 distribuidores; RTM 199+81+1029 = 1.309; 1.309+453 = 1.762 = DIM_RTM; fato 15.034.602,7 kg = soma dos totais da Mtrix, dif 0,00; 5.851.509 linhas; manifesto sem base mais nova; blob 124.395 pares) |
| JSON antes × depois | 62.849 folhas do JSON anterior: 0 faltando, 0 com valor diferente; 5 campos novos |
| HTML antes × depois | idêntico byte a byte (6.405.363 chars) após neutralizar as 3 frases do D7 |
| RTM e Hierarquia alteradas hoje após o painel | relidas nesta execução; nenhum número mudou |

Execução seguinte sem `--forcar` (`20260909-200627-3a8adf`, 132 s): ingestão pulada ("bases
inalteradas"), 0 avisos, HTML idêntico ao da primeira (md5 d3b01719…). Terceira execução (`python run_dn.py`): publicou em
`Painéis Comerciais/DN/Scorecard_DN.html` com md5 conferido.

## (c) O que ficou pendente

- Nada da Fase 1. Pendências de negócio continuam as do README (datas de cadastro, os 5
  destinos RTM sem cadastro, PROPEC, V.M., DISO/UNIVALE, CLAUMAR).
- A pasta de quarentena `_fora_do_DN_2026-09-09/` (202 MB) foi apagada em 09/09/2026, a pedido do Douglas.
- Avisos informativos permanecem: 15 distribuidores sem data de cadastro no de-para; PDVs
  distintos 1 a 10 abaixo do total da Mtrix em 9 meses (a Mtrix conta com a chave crua dela).

## (d) Checklist de validação

- [ ] `python run_dn.py` termina com `ok`, mostra o resumo e diz onde publicou.
- [ ] `Painéis Comerciais/DN/Scorecard_DN.html` abre com Ctrl+F5 e mostra jul/26 · 120.817 · 73.185 · 60,6% · 1.279,5 t · 70 distribuidores · RTM 1.762 / 1.309 / 453.
- [ ] Nas "Notas da visão" aparece "últimos 5 meses" e "Base atual acima de 6 meses, Novos até 6"; no título do gráfico, "13 meses".
- [ ] Rodar de novo sem mudar nada: etapa 1 "pulada: bases inalteradas", ~2 min, arquivo publicado idêntico.
- [ ] Salvar um de-para sem mudar conteúdo (Ctrl+S no Excel): a execução seguinte detecta "1 base(s) alterada(s)", reingere (~6 min) e os números não mudam.
- [ ] Trocar de propósito `fontes.rtm.arquivo` no config para um nome inexistente: aborta na etapa 0 com a mensagem do caminho; nada gravado, nada publicado. Desfazer.
- [ ] `data/dn/logs/resumo_<execução>.json` existe e lista etapas, linhas por arquivo, validações e o arquivo publicado.
- [ ] A pasta `DN/` contém só `bases/`, `config/`, `data/`, `dn/`, `docs/`, `template/`, `run_dn.py`, `README.md`.
