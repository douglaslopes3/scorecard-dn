# Scorecard DN · Distribuição Numérica

Painel de Distribuição Numérica do Canal Distribuição, a partir do sell-through da Mtrix. **Um comando** lê as bases, calcula,
valida e publica **um HTML offline único**.

Estado em **14/09/2026** (estabilização após o checklist do refino): arquivo com **set/26 parcial** e os **25 meses** de set/24 a
set/26; ago/26 é o último mês fechado (**janela da base ativa de 6 meses** desde 14/09: base ativa 129.595 · DN 55,2% · 1.199,9 t ·
71 distribuidores). 6 abas no projeto, **4 visíveis** (Penetração e RTM ocultas), filtros numa barra lateral, período Mês · Acumulado
do ano · Ano (com o ano em curso). **Publicado em 14/09/2026 22h03** (`docs/estabilizacao_2026-09-14.md`).

> **Retomando o trabalho?** Comece por `docs/RETOMADA.md`: estado, regras de trabalho, decisões, pendências e armadilhas.

## Como rodar

```powershell
cd "C:\Users\dldsouza\OneDrive - Dori Alimentos S.A\Documentos\Painéis - Alavancas\DN"
python run_dn.py                    # tudo: verificar -> ingerir (se preciso) -> calcular -> renderizar -> validar -> publicar
python run_dn.py --sem-publicar     # gera e valida, sem copiar para a pasta de publicação
python run_dn.py --mes 2026-08      # arquivo com um mês de referência fixo (sem o parcial)
python run_dn.py --forcar           # relê todas as bases mesmo sem mudança
python run_dn.py --regerar-exemplo  # uma vez, depois de editar template/template.html
python run_dn.py --usuario 1120     # Etapa 2: só o painel do usuário cujo rótulo contém o texto (mais o canal)
python run_dn.py --sem-usuarios     # Etapa 2: sem os painéis por usuário nesta execução
```

- Sem mudança nas bases a ingestão é pulada; a execução leva **~2,5 min** desde a Etapa 1 de performance (15/09/2026: cálculo ~55 s,
  mês fechado ~20 s, renderização ~45 s, validação ~30 s; era ~17 min). Depois de uma ingestão a primeira execução soma ~15 s
  (calibração da frequência refeita). Com um mês novo da Mtrix ou um de-para alterado, a ingestão soma ~1 a 6 min.
- O JSON e o HTML datado de cada execução nascem em `%LOCALAPPDATA%\Dori\DN\painel` (`projeto.pasta_painel`), fora do OneDrive;
  só o HTML publicado vai para a pasta sincronizada.
- **Com o arquivo do mês corrente em `bases/`, `python run_dn.py` publica o parcial** (com o último mês fechado dentro).
- Qualquer falha termina com `PIPELINE ABORTADO`, exit code 1, e **nada é publicado**.

## Pipeline

```
bases/ (raw)  Sell Out - MTRIX/*.xlsx · Clusters_DePara · DE-PARA_Ponderada_Clusters
../../bases compartilhadas/Hierarquia_AAAAMMDD.xlsx (a mais recente; comum ao Gerencial e ao ROTA)
../../bases compartilhadas/Produtos.xlsx · RTM_DePara_Transicao.xlsx · Distribuidores_DePara.xlsx (cadastro único; comuns ao Gerencial, desde 02/10/2026)
0 verificar    config, bases, manifesto (precisa ingerir?)
1 ingerir      raw -> staging (cache) -> curated (FATO_SELLOUT, DIM_*, manifesto) + data/dn/quality/
2 calcular     curated -> cubos DN_*_MES e DN_*_CAT_MES (todos os meses), DN_RTM_*, DN_PDV_BASE_ATIVA, DN_PEN_* (mês de referência)
2b mês fechado com o mês de referência em andamento: base ativa dos PDVs, carteira, máscara e RTM refeitos para o mês fechado
3 renderizar   painel_dn.json + Scorecard_DN_<mês>.html (pasta local): mês de referência, mês fechado e o histórico (montado dos cubos)
4 validar      120 conferências (cards = fato, cubos, pacotes comprimidos, lista de PDVs combinada, acumulados, RTM, frequência…)
5 publicar     cópia atômica para Painéis Comerciais/DN/Scorecard_DN.html (md5 conferido; nada copiado se o md5 não mudou) — só se tudo validou
6 distribuir   Etapa 2: um painel por usuário da hierarquia (1 head, 3 gerentes, 14 supervisores), fato recortada antes de tudo,
               validação essencial + vazamento + soma dos níveis, publicado em Painéis Comerciais/Gerencial/<rótulo>/ (~6 min)
```

Desenho do fluxo dos 3 painéis (bases compartilhadas, comandos, publicação, agenda): [Fluxo dos Painéis Comerciais](https://claude.ai/artifact/2GtTgvnYJjdDsCGZs3hYZG).

Código em `dn/`: `pipeline.py`, `metrics.py` (métricas e acumulados), `painel.py` (JSON do painel), `tabelas.py` (tabelas e pacotes
comprimidos), `render.py` (Handlebars mínimo e prova do template), `manifesto.py`, `extract/`, `transform/`, `load/`, `utils/`.
Desde 15/09/2026 (`docs/performance_etapa1.md`) a fato viaja com chaves categóricas, os cubos derivam de uma tabela de pares
calculada uma vez (`metrics.preparar_codigos`) e `painel.montar` consulta índices por cubo; mesmos números, 7× mais rápido.

## O painel

| Aba | Conteúdo |
|---|---|
| **Visão Geral** | cards do período, "O que aconteceu no mês / no período" (maiores quedas e altas), gráfico mês a mês, evolução por categoria (linhas com chips, foco ★ e Outras), tabela de categorias. Com supervisor **ou distribuidor** (22/09/2026, RN-44) os cards e o gráfico mês a mês são do recorte; com distribuidor o ranking fica oculto |
| **Supervisores e distribuidores** | uma tabela com Ver por Supervisor · Distribuidor · Cluster; clicar na linha abre o gráfico mês a mês |
| **Pontos de venda** | lista nominal da base ativa (mês parcial e mês fechado; o seletor de mês mostra só esses dois), carteira Destaque · Prime · Todos; coluna **kg / R$ médio por mês com compra** (RN-65, 22/09/2026); o CSV das tabelas sai sem tags HTML |
| **Penetração** | **oculta da navegação** desde 14/09/2026 (`painel.abas[].oculta`); mantida no projeto: sempre no último mês fechado: penetração, referência P75, lojas a positivar, potencial, ativação e recorrência |
| **RTM** | **oculta da navegação** desde 14/09/2026 (`painel.abas[].oculta`); mantida no projeto: aderência ao direcionamento, destinos e clientes do mês |
| **Definições** | uma linha de fórmula por indicador, por tema (textos em `painel.definicoes`) |

- **Barra lateral** (recolhível): Período (Mês · Acumulado do ano · Ano) · Mês ou Ano · Ano fiscal / Ano Calendário · Segmento ·
  Supervisor · Distribuidor · Categoria · Métrica (t / R$) · Limpar filtros · Voltar. O filtro que não vale na aba some.
- **Linha de filtros ativos** abaixo das abas, presa ao rolar.
- **Voltar**: cada troca de aba é um passo (aba, filtros, período, rolagem), também pelo botão do navegador.
- **Dados embutidos**: tabelas comprimidas por mês (abertas ao escolher o mês), lista de PDVs combinada dos dois meses, lista cliente ×
  mês do RTM. Histórico: janela móvel de `painel.janela_arquivo_meses` (25).

## Parâmetros principais (`config/config.yaml`)

| Chave | Hoje | O que controla |
|---|---|---|
| `regras.janela_base_ativa_meses` | **6** (era 5 até 14/09/2026) | janela da base ativa, base elegível, ativação, recorrência e máscara; `regras.potencial.janela_fator_meses` acompanha |
| `regras.segmento_novos_meses` | 6 | Base atual × Novos |
| `regras.mes_em_andamento` | auto | mês de referência parcial quando é o mês da última leitura das bases |
| `publicacao.publicar_mes_em_andamento` | **true** | o parcial é publicado (com o mês fechado dentro) |
| `painel.janela_arquivo_meses` | 25 | meses no arquivo (seletor, gráficos, pacotes) |
| `painel.abas` | 6 abas, 2 com `oculta: true` | ordem, rótulo, filtros e visibilidade de cada aba (oculta = fora da navegação, conteúdo mantido) |
| `painel.mes_ranking.n` | 5 | itens das listas de quedas e altas |
| `painel.definicoes` | 7 temas | textos da aba Definições |
| `painel.resumos.ativo` / `painel.memoria.ativo` | false | resumos automáticos e memória de cálculo (código mantido, desligados) |
| `regras.penetracao.*` · `regras.potencial.*` | P75 · foco · 95/70 · fator observado | Penetração |
| `regras.rtm.*` | corte 01/09/2026 | RTM |
| `validacao.html_max_mb` | 20 | limite do HTML (15 até 15/09/2026) |
| `publicacao.pasta` / `arquivo` | Painéis Comerciais/DN · Scorecard_DN.html | destino |
| `publicacao.pular_se_identico` | true | não copia quando o publicado já tem o mesmo md5 (Etapa 1, 15/09/2026) |
| `projeto.pasta_painel` | `%LOCALAPPDATA%/Dori/DN/painel` | pasta local do JSON e do HTML datado (null = `data/dn/painel`, no OneDrive) |
| `recursos.prioridade` / `threads` | abaixo_do_normal · 4 | prioridade do processo no Windows e threads do pyarrow/numpy (0 = padrão) |
| `distribuicao.*` | ativo · destino `../../Painéis Comerciais/Gerencial` · níveis N1/N2/N3 · `em_erro: continuar` | Etapa 2 (16/09/2026): painéis por usuário; ver `docs/distribuicao_etapa2.md` |

Regras de negócio: **`docs/regras_negocio.md`** (fichas `RN-nn`, com a nota de cada etapa do refino).

## Template

`template/template.html` é editado à mão. O pipeline aborta se o renderizador não reproduzir `template/Scorecard_DN_base.html` byte a
byte; depois de editar o template, `python run_dn.py --regerar-exemplo` uma vez. Campo novo no JSON entra em
`template/data-inventory.json`. Coluna nova que o navegador lê precisa aparecer como literal no template (os pacotes levam só as
colunas usadas; as `acum_*` entram por prefixo).

## Publicação e rotina

- A pasta `Painéis Comerciais/DN` contém só `Scorecard_DN.html`. Compartilhar a **pasta** com pessoas específicas, *Pode exibir*;
  nunca "qualquer pessoa com o link" (o HTML embute CNPJ, razão social e endereço).
- Abrir no Chrome ou Edge (Ctrl+F5). "atualizado em" = data da última leitura das bases.

| Quando | Passos |
|---|---|
| Durante o mês | soltar o `ScoreCard_Mtrix_MM.AAAA.xlsx` parcial em `bases/Sell Out - MTRIX/` (substituindo o anterior do mesmo mês) e rodar `python run_dn.py` |
| Mês fechou | soltar a versão fechada do mês e rodar: o mês vira fechado sozinho; o parcial do mês seguinte entra quando o arquivo chegar |
| De-para alterado | `python run_dn.py` (o manifesto detecta e reingere) |
| Template alterado | `python run_dn.py --regerar-exemplo` |
| Validação falhou | nada é publicado; corrigir e rodar de novo |

## Changelog

- **16/09/2026 07h16 · publicação** — canal (`Painéis Comerciais/DN`, md5 `e6519850…`) e os 18 painéis por usuário
  (`Painéis Comerciais/Gerencial/<rótulo>/`), com o de-para de nomes reduzidos do Douglas. Aba Pontos de venda: abre em Todos os PDVs
  (`painel.pdv_carteira.padrao`) e o filtro Situação fica só com Todos · Sem compra · Positivados · Clientes RTM
  (`painel.pdv_situacoes_por_categoria: false`); template com `sit_cat`, exemplo regerado.
- **16/09/2026 · Etapa 2, um painel por usuário** — modelo dos Gerenciais: usuários descobertos da hierarquia
  (`DIM_DISTRIBUIDOR`), fato recortada por usuário antes de qualquer cubo, mesmo código do canal, pasta = rótulo, arquivo
  `Scorecard_DN_N3_<slug>.html`, publicação atômica só quando o md5 muda, falha isolada por usuário. 18 painéis em 6 min (64 MB);
  soma dos gerentes e dos supervisores = canal com diferença zero; zero vazamento em 18 de 18; painel do canal inalterado.
  Decisões Q1–Q5 e pendências: `docs/distribuicao_etapa2.md`.
- **15/09/2026 · Etapa 1 de performance (P1–P6), gerada sem publicar** — pedido do Douglas: pipeline mais rápido e mais leve para a
  máquina, preparando os painéis por usuário (Etapa 2). Fato com 7 colunas e chaves categóricas (2,2 GB → 1 GB), pares e base ativa
  calculados uma vez para os 14 cubos, calibração da frequência guardada por ingestão, `montar` por índices, validação em códigos
  inteiros, JSON/HTML em pasta local, publicação só quando o md5 muda, prioridade e threads configuráveis. **Sem ingestão: 1.016 s →
  147 s; JSON e HTML idênticos aos de antes; 120 validações.** Relatório: `docs/performance_etapa1.md`.
- **14/09/2026 · estabilização após o checklist (A1, A2, A3, A5, A7, A8, A9), publicada às 22h03** — checklist do refino respondido
  pelo Douglas; correções: gráfico "Evolução por categoria" voltou (regressão da E3), cards Volume do mês / kg por PDV e cards do
  RTM no padrão (CSS); Penetração e RTM ocultas da navegação (config, reversível); ano em curso no modo Ano (D26 revista); seletor
  de mês da aba Pontos de venda só com os meses com lista; tabela do bloco por categoria acompanhando o período (A9); **janela da base ativa de 5 para 6 meses** (regra nova, todos os
  números mudam). 120 validações; HTML 14,9 MB. Gerente Regional: estudo feito, backlog. Relatório: `docs/estabilizacao_2026-09-14.md`.
- **13/09/2026 · refino do painel (E1–E6), gerado sem publicar** — pedido do Douglas: painel mais objetivo, só o medido.
  E1 limpeza (saem Alavancas, Matriz, Ano a ano, mini-linhas, textos; resumos e memória desligados); E2 barra lateral, filtros ativos,
  Limpar e Voltar; E3 6 abas, "O que aconteceu no mês", gráfico em janela; E4a mês fechado + parcial no mesmo arquivo, dados
  comprimidos, publicação do parcial; E4b histórico de 25 meses; E5 período Mês · Acumulado do ano · Ano; E6 Definições em tabelas,
  janela móvel de 25 meses. 119 validações; HTML 14,5 MB. Decisões e relatórios: `docs/refino_painel_proposta.md`, `docs/refino_e1.md`
  … `docs/refino_e6.md`.
- **13/09/2026** — frequência de compra (RN-58), seletor Período (RN-59), RTM por supervisor do destino e destino pelo código;
  publicado 13h55. `docs/frequencia_etapa*.md`.
- **11/09/2026** — F6 a F11 (Penetração, ativação e recorrência, Matriz, resumos, memória de cálculo, Alavancas) e carteira de PDVs
  ponderados. `docs/evolucao_f6.md` … `evolucao_f11.md`, `docs/pdv_ponderados.md`.
- **10/09/2026** — F0 a F5 (dicionário de regras, Volume × Valor, LY explícito, aba Evolução, filtro por Supervisor, calendário).
  `docs/evolucao_f0.md` … `evolucao_f5.md`, `docs/rodada_2026-09-10.md`.
- **09/09/2026** — reforma, Fases 1 a 5 (pipeline único, abas, componente de tabela, RTM, publicação). `docs/reforma_fase1.md` … `fase5.md`.
- **08/09/2026** — fases originais. `docs/fase1.md` … `fase3.md`.

## Pendências de negócio

1. Data de cadastro dos 6 distribuidores ainda censurados.
2. Destinos RTM sem cadastro: NOVO RIBEIRÃO PRETO (91), NOVO SJRP (75), DIBS (6), NOVA ENERGIA (1).
3. CNPJs das 124 linhas fora da carteira de PDVs ponderados; linha 179 × 41 e linha 177.
4. Compartilhar `Painéis Comerciais/DN` com o time depois da publicação.
5. Tamanho: com a janela de 25 meses o HTML fica em ~14,9 MB e cresce ~0,2 a 0,3 MB por mês (limite 20 MB desde 15/09/2026). Backlog: lista de PDVs em colunas (−1,7 MB).
6. Filtro de Gerente Regional com números próprios (nível novo no pipeline): estudo em `docs/estabilizacao_2026-09-14.md`, backlog.
