# Reforma · Fase 4 — RTM: aderência ao direcionamento, drill-down (09/09/2026)

Proposta aprovada integralmente pelo Douglas em 09/09/2026 (P1 rótulo "Destino não mensurável" com
três causas; P2 chave por CNPJ quando a base trouxer a coluna; P3 ativação recomeça no corte na visão
de migração; P4 drill em modal; P5 todos os "outros" com o kg de cada; P6 valor em kg).

## (a) O que foi alterado

### Pipeline

| Arquivo | Mudança |
|---|---|
| `dn/extract/cadastros.py` | leitor da base RTM lê a coluna opcional `CNPJ Distribuidor Destino` (`fontes.rtm.colunas_opcionais`); sem ela, avisa no log que o destino é casado por nome |
| `dn/metrics.py` · `rtm_aderencia` | destino resolvido por CNPJ quando existe, senão por nome; **três motivos** de destino não mensurável (`sem_cadastro`, `fora_do_painel`, `sem_sellout`) com aviso listando cada destino; **`DN_RTM_CLIENTE_MES`** (cliente × mês, 22.906 linhas): estado, kg no destino e em outros, **quem atendeu** (nome reduzido + CNPJ; para "outro", todos com o kg de cada), último mês com compra; **ativação em duas réguas** (histórico completo e a partir de `regras.rtm.data_migracao`); série com ativados acumulados nas duas réguas e a marca `desde_migracao`; `DN_RTM_DESTINO` com motivo e ativados nas duas réguas; `DN_RTM_CLIENTE` com nome Mtrix, atendeu, última compra, ativação nas duas réguas. A coluna `sem_cobertura` virou `nao_mensuravel` |
| `dn/painel.py` | bloco `rtm` do JSON: `nao_mensuravel`, `rotulo_nao_mensuravel` e `definicao_nao_mensuravel` (config), `motivos[]`, `corte{}` (data, mês, rótulo, tem_meses, visão padrão resolvida), KPIs de ativação nas duas réguas, série/destinos/clientes com os campos novos (`situacao` com quem atendeu, `ultimo_mes_compra`, `motivo`), `rotulos_json` e **`blob`** cliente × mês (gzip+base64) para os drills |
| `config/config.yaml` | `fontes.rtm.colunas_opcionais`; `painel.rotulos.estados_rtm.nao_mensuravel`; `painel.rotulos.rtm_motivos`; `painel.textos.rtm_nao_mensuravel` (definição exibida) |
| `template/data-inventory.json` | 274 campos: `rtm.nao_mensuravel` (era `sem_cobertura`), `rtm.motivos.*`, `rtm.corte.*`, KPIs `_mig`, `rtm.serie.{i_mes, desde_migracao, ativados_hist, ativados_mig}`, `rtm.destinos.{motivo, motivo_rotulo, ativados_mig}`, `rtm.clientes.{nome_origem, situacao, motivo, atendeu, ultimo_mes_compra, ativado_mig, mes_ativacao_mig}`, `rtm.blob.*`, `rtm.rotulos_json` |
| `dn/pipeline.py` | etapa 4: motivos somam o total não mensurável; **grade cliente × mês = série** em todos os meses e estados; kg no destino da grade = série; grade = clientes × meses; blob descompacta com as contagens certas; modal do drill presente no HTML |
| `dn/render.py` | exemplo reduzido encolhe também o blob RTM |

### Template

| Onde | Mudança |
|---|---|
| Bloco RTM | chips **A partir da migração (set/26)** · **Histórico completo** (o primeiro desabilitado, com nota, enquanto a série não alcança o corte; `auto` do config decide o padrão); os 5 cards com **números clicáveis**; texto do card "Base RTM" com o rótulo novo e tooltip com a definição; parágrafo fixo com a definição e as três causas com a contagem de hoje |
| Evolução | Compraram do destino, Compraram de outro, Não compraram e **Já ativados** (acumulado, na régua da visão) clicáveis por mês; na visão migração só os meses desde o corte aparecem |
| Destinos | Clientes, Compraram do destino, Compraram de outro, Não compraram e Já ativados clicáveis; coluna **Motivo** para destino não mensurável |
| Clientes | **Situação no mês** passa a trazer quem atendeu ("Comprou de outro · NOME (CNPJ) 12 kg"; "Comprou do destino · FILIAL (CNPJ)"); coluna **Última compra** (mês); "(bandeira)" marca a razão social vinda do cadastro antigo; Ativação segue a visão |
| Drill | `<dialog>` de largura total com o **mesmo `DnTabela`** (busca, ordenação, amostra/expandir, CSV). Colunas: código do cliente (antigo) · razão social · CNPJ · distribuidor destino · distribuidor que atendeu · situação · kg no destino · kg em outros · última compra (mês). Título diz estado, mês e destino; subtítulo diz a visão. **Herda** destino selecionado, chip de estado e busca da tabela de clientes e a visão temporal. Fecha por Esc, botão ou clique fora; trocar de aba fecha |
| Estado | `DNE.rtm` persistido no `localStorage` e na URL (`&rtm=migracao`) |

## (b) Por quê

Fase 4 do prompt e §0.6 da auditoria (rótulo ambíguo, três causas num só, junção por texto silenciosa).

## Diagnóstico registrado de "sem cobertura" (agora "destino não mensurável")

Regra anterior: destino casado por texto contra os distribuidores do painel; 453 clientes em 5 destinos
(PELLAH, NOVO RIBEIRÃO PRETO, NOVO SJRP, DIBS, NOVA ENERGIA). Diagnóstico: correta como "não afirmar
não comprou", ambígua no nome, incompleta (três causas) e frágil (nome). Correção aplicada: rótulo e
definição na tela, três causas separadas e exibidas, chave por CNPJ quando a base trouxer a coluna
(`CNPJ Distribuidor Destino`), aviso no log com cada destino que não casou. Hoje os 453 continuam
todos em `sem_cadastro`; o denominador não mudou.

## Prova (execução final e teste no navegador, sem erro de console)

| Checagem | Resultado |
|---|---|
| Validações do pipeline | 37 ok (31 anteriores + 6 RTM); grade cliente × mês = série nos 13 meses × 4 estados; kg no destino grade = série (dif 0,0000); grade 22.906 = 1.762 × 13; blob 157 KB em base64; motivos 453 sem_cadastro + 0 + 0 = 453; HTML 6,2 MB |
| Números do painel | inalterados: jul/26 · 120.817 · 73.185 · 60,6% · 1.279,5 t · 70 · RTM 1.762 / 1.309 / 453 · aderência 15,2% · 199 / 81 / 1.029 · ativados 271 · parados 72 |
| Visão temporal | chip "A partir da migração (set/26)" desabilitado; nota "sem meses desde 01/09/2026 (série até jul/26); a visão liga sozinha quando a Mtrix de set/26 entrar"; histórico completo ligado; URL `#aba=rtm&rtm=historico`; ativação desde 2026-09 = 0 (log) |
| Definição na tela | parágrafo "Destino não mensurável. Cliente cujo distribuidor de destino não existe…" + "453 destino sem cadastro · 0 fora do painel · 0 sem sell-out"; tooltip no card |
| Card "não mensurável" | drill "Destino não mensurável · jul/26": 453 registros; coluna Situação traz a causa ("… · destino sem cadastro no de-para") |
| Card "Compraram de outro" | drill com 81; "Distribuidor que atendeu" = "TOP SERVICE (20023288000127) 61 kg", kg em outros 61, última compra jul/26 |
| Evolução (célula jun/26) | drill "Comprou do destino · jun/26": 153 (= série) |
| Destinos (DISO · de outro) | drill "Comprou de outro · jul/26 · destino DISO": 29 (= tabela); linhas destacadas com Motivo preenchido (PELLAH, NOVO RIBEIRÃO PRETO, NOVO SJRP…) |
| Ativados / parados | drills com 271 e 72 (= cards) |
| Clientes | Situação com quem atendeu ("Comprou de outro · DIN (05139469000120) 1.280 kg"); coluna Última compra (mês); "(bandeira)" quando aplicável |
| Herança de filtros | clientes com Destino = DISO + chip "Não compraram" + busca "super" = 309 na tabela; card "Não compraram" abre o drill "Não comprou · jul/26 · destino DISO" com 309 no total e 88 com a busca herdada "super" |
| Modal | abre por qualquer número (173 links no bloco, 113 nas células de destinos), fecha por botão (clique real), clique fora e Esc (handler explícito além do nativo; no navegador de teste a tecla física Esc é interceptada pelo próprio painel, então o Esc foi verificado por evento de teclado sintético), fecha ao trocar de aba; busca/ordenação/expandir/CSV do componente dentro do modal |

## (c) O que ficou pendente

- A coluna `CNPJ Distribuidor Destino` na base RTM (P2) é opcional: o pipeline já a lê; enquanto não
  existir, o destino é casado por nome com aviso.
- A visão "a partir da migração" só ganha dados quando a Mtrix de set/26 entrar (A4); até lá o chip
  fica desabilitado com a nota.
- Lacunas declaradas (A8): sem dia de compra; razão social = bandeira antiga para quem nunca apareceu
  na Mtrix; valor em kg (R$ fica no Parquet).

## (d) Checklist de validação

- [ ] RTM: chip "A partir da migração (set/26)" desabilitado com a nota "sem meses desde 01/09/2026"; "Histórico completo" ligado.
- [ ] Card "Base RTM": "1.309 mensuráveis · 453 com Destino não mensurável" — passar o mouse mostra a definição; clicar abre o drill com 453 clientes e a causa em "Situação".
- [ ] Parágrafo com a definição e "453 destino sem cadastro… · 0 … · 0 …".
- [ ] Cards: clicar em 199 (compraram do destino), 1.029 (não compraram), 81 (de outro) e 72 (ativados parados) abre o drill com esse nº de clientes; no drill de "de outro", a coluna "Distribuidor que atendeu" mostra nome (CNPJ) e kg.
- [ ] Evolução: clicar num número de jun/26 abre o drill de jun/26 (título com o mês).
- [ ] Destinos: linhas destacadas com a coluna Motivo; clicar em "Compraram de outro" de DISO abre 29 clientes.
- [ ] Clientes: Situação traz quem atendeu; coluna Última compra; selecionar destino DISO e chip "Não compraram" e depois clicar no card "Não compraram" abre 309 (herda os filtros).
- [ ] Drill: busca, ordenação, Expandir e CSV funcionam; Esc fecha.
