# Etapa 1 · Performance do pipeline (15/09/2026)

Objetivo aprovado pelo Douglas em 15/09/2026: reduzir o tempo de execução do `run_dn.py` sem mudar nenhum número, preparando o
terreno para a Etapa 2 (um painel por usuário). A meta de 5 minutos era referência, não obrigação; a orientação foi "otimizar
processamento, sem loucura", e consumir menos RAM e CPU da máquina.

Critério de aceite de cada passo: `python run_dn.py --sem-publicar`, 120 validações ok, `painel_dn.json` **idêntico** ao da linha
de base (comparação campo a campo, só `gerado_em` e `execucao_id` fora) e HTML idêntico fora os carimbos. Todos os passos passaram.

## 1. Medição (antes)

Execução real das 21h46 de 15/09 (log `pipeline_20260915-214634`): 997 s sem ingestão. Medição isolada, função a função, no
mesmo dia: 598 s. Linha de base tirada às 22h59 já com o `Distribuidores_DePara.xlsx` alterado (P0, `resumo_20260915-225911`):
1.052 s, dos quais 36 s de ingestão em cache.

Onde o tempo estava (isolado): 14 cubos nível × mês em `metrics.calcular` (136 s, cada um varrendo os 10 M de linhas com chaves em
texto e refazendo a base ativa em 20 janelas), montagem do JSON dos 25 meses em `painel.montar` (172 s, filtros pandas item a
item), etapa 2b repetindo base ativa, carteira, penetração e RTM (81 s), validação com recálculos na fato (71 s). Handlebars,
json.dumps e gzip somavam 2,3 s: template e serialização nunca foram gargalo. Não há biblioteca JS embutida (o CDN não se aplica).

A execução real era 40% mais lenta que a isolada: a fato ocupava 2,2 GB em memória (20 colunas, 8 de texto) e cada filtro copiava o
bloco, numa máquina de 15,7 GB com 2 a 6 GB livres. O pipeline trabalhava no limite da memória.

## 2. O que mudou (P1 a P6)

| Passo | Mudança | Arquivos |
|---|---|---|
| P0 | Linha de base guardada (JSON, HTML, resumo) antes de qualquer alteração | scratchpad da sessão |
| P1 | A fato é lida com 7 das 11 colunas; as chaves (mês, distribuidor, PDV, segmento, supervisor, categoria, cluster) viram **categoria ordenada** (categorias em ordem lexicográfica: `==`, `<=`, `isin`, `sort` e `groupby` dão o mesmo resultado do texto). Atributos de distribuidor, produto e PDV entram pelo de-para das categorias, não linha a linha. Fato em memória: 2.240 MB → 972 MB | `metrics.carregar`, `_categorizar`, `_mapear_cat`, `load/parquet.carregar(colunas=)` |
| P2 | `metrics.preparar_codigos` monta **uma vez** os pares mês × distribuidor × PDV (× categoria) e a base ativa dos 7 níveis; os 14 cubos derivam daí. Somas de kg, R$ e atendimentos continuam nas linhas da fato, numa passada por cubo, na mesma ordem (mesmo float). `acum_ano` e `acum_pdvs_mensal` usam as mesmas tabelas. Os cubos voltam a texto ao sair (`_descat`). Calibração da frequência (RN-58) guardada em `DN_FREQ_CALIBRACAO` com a execução da ingestão (`curated_execucao`) e reaproveitada enquanto as bases não mudam | `metrics.py` |
| P3 | `_ativacao_recorrencia` parte da tabela de pares (11 → 5 s); etapa 2b recebe os pares cortados no mês fechado (`recortar_codigos`) em vez de recalcular | `metrics.py`, `pipeline.calcular_fechado` |
| P4 | `painel.montar` consulta índices `{chave: {mês: linha}}` construídos uma vez por cubo (`_indice`), em vez de filtrar o DataFrame por entidade, mês e categoria; `_serie` faz o LY por dicionário; `_pdvs` (acumulados) idem. Mês leve: 10,7 → 0,6 s; completo: 19 → 7,6 s | `painel.py` |
| P5 | Validação: os recálculos pesados (PDVs distintos por mês e por ano, frequência por par) rodam sobre as mesmas linhas da fato em códigos inteiros (`c["K"]`); as 120 conferências continuam, com a mesma independência (é a fato, não os cubos) | `pipeline.validar` |
| P6 | JSON e HTML datado gerados em pasta **local** (`projeto.pasta_painel`, padrão `%LOCALAPPDATA%/Dori/DN/painel`); publicação só copia quando o md5 muda (`publicacao.pular_se_identico`); prioridade do processo e threads configuráveis (`recursos.prioridade`, `recursos.threads`) | `config.yaml`, `utils/config.py`, `utils/recursos.py` (novo), `run_dn.py`, `pipeline.executar/publicar` |

## 3. Resultado

Sem ingestão, mesma máquina, mesmas bases (execução `p6`, 23h50 de 15/09):

| Etapa | Antes (P0, 22h59) | Depois | Ganho |
|---|---|---|---|
| 2 · calcular | 320 s | 55 s | 5,8× |
| 2b · mês fechado | 95 s | 19 s | 5,0× |
| 3 · renderizar (histórico de 23 meses: 176 → 16 s) | 451 s | 44 s | 10× |
| 4 · validar | 147 s | 29 s | 5,1× |
| **Total sem ingestão** | **1.016 s** | **147 s** | **6,9×** |

- HTML: 14,88 MB antes e depois (conteúdo idêntico). JSON: 34,9 MB. Nada mudou no arquivo que o usuário abre.
- Memória: fato 2,2 GB → 0,97 GB; as tabelas compartilhadas somam 93 MB; sem cópias de 10 M de linhas por filtro.
- CPU: `recursos.threads: 4` (de 12) e prioridade "abaixo do normal" — o Excel, o navegador e o OneDrive passam na frente.
- Ingestão (só quando uma base muda): inalterada, ~36 s com cache, dos quais 43 s eram o relatório de qualidade na medição de
  15/09 21h18; não foi otimizada (roda uma vez por mês).

## 4. Trade-offs e decisões

- Paralelismo: não usado. Na máquina do Douglas (15,7 GB) processos paralelos copiariam dados e disputariam CPU com ele.
- CDN e serializador: não se aplicam (sem biblioteca JS embutida; `json.dumps` leva 0,2 s).
- Cubos na curated: mesmas colunas, chaves em `string` como antes. `DN_FREQ_CALIBRACAO` ganhou a coluna `curated_execucao`.
- `_grupos` (frequência): com chaves categóricas a numeração dos grupos sai dos códigos, na ordem de 1ª aparição, como o
  `ngroup` de antes. Linha com categoria nula entraria num grupo próprio (antes caía no último grupo por um `-1`); hoje não há
  categoria nula na fato, então nada muda.
- A pasta `data/dn/painel/` no OneDrive ainda tem os HTMLs datados antigos (jul, ago, set/26) e o `painel_dn.json` (70 MB);
  não foram apagados. A partir de agora esses arquivos nascem em `%LOCALAPPDATA%\Dori\DN\painel`.
- Cópia de segurança do código anterior: `scratchpad/backup_dn_pre_etapa1` da sessão de 15/09 (fora do projeto).

## 5. Como conferir

```powershell
python run_dn.py --sem-publicar
```

Deve terminar em ~2,5 min com "120 validações ok", `base ativa 125.955 · positivados 15.644 · DN 12,4% · 201,2 t · 67 distribuidores`
e o HTML em `%LOCALAPPDATA%\Dori\DN\painel\Scorecard_DN_2026-09.html`. Primeira execução depois de uma ingestão: +15 s
(calibração da frequência refeita).

## 6. Checklist

- [x] JSON idêntico à linha de base em todos os passos (P1+P2, P3, P4+P5, P6)
- [x] HTML idêntico fora os carimbos
- [x] 120 validações ok em todas as execuções
- [x] Nenhuma regra de negócio, texto do painel ou parâmetro alterado (config só ganhou `pasta_painel`, `recursos`, `pular_se_identico`)
- [x] Template intocado (a prova byte a byte do renderizador continua passando)
- [ ] Publicar: não feito (regra: publicação só com aprovação escrita). O HTML gerado hoje difere do publicado em 15/09 22h03
      apenas pela reingestão do `Distribuidores_DePara.xlsx` alterado pelo Douglas (nomes reduzidos SBN → SBM etc.)
