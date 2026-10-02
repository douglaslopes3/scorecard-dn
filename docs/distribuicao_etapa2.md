# Etapa 2 · Um painel por usuário (16/09/2026)

Aprovada pelo Douglas em 16/09/2026 com as recomendações Q1 a Q5. Objetivo: cada usuário do canal Distribuição recebe, na pasta
dele em `Painéis Comerciais/Gerencial`, um Scorecard DN só com os dados que ele pode ver, seguindo o modelo já implementado nos
painéis Gerenciais (`Dashboard - Gerencial/run_dashboard.py`). Gerado e validado sem publicar; a publicação depende do ok do Douglas.

## 1. Modelo (o que veio dos Gerenciais)

| Gerenciais | DN |
|---|---|
| usuários descobertos do cubo (`dims.perfil`), sem lista para manter | usuários descobertos de `DIM_DISTRIBUIDOR` (HEAD, GERENTE, SUPERVISOR) entre os distribuidores do painel |
| `por_nivel.niveis: {N1: 0, N2: 1, N3: 2}` | `distribuicao.niveis: {N1: HEAD, N2: GERENTE, N3: SUPERVISOR}` |
| recorte físico das linhas do cubo antes do HTML | recorte físico da FATO antes de qualquer cubo, JSON ou HTML |
| pasta = rótulo `código - papel - NOME` com `/` → `-` | igual (`distribuicao.pasta_usuario`); as 18 pastas já existiam |
| arquivo `Dashboard_Gerencial_N3_<slug>.html`, nome estável | `Scorecard_DN_N3_<slug>.html` (`distribuicao.prefixo`) |
| `publicacao.destino` relativo à raiz do projeto | `distribuicao.destino: ../../Painéis Comerciais/Gerencial`; `publicacao.pasta` também virou relativo |
| Full em subpasta própria; N1 = head | `Painéis Comerciais/DN/Scorecard_DN.html` continua o painel do canal; N1 recebe cópia byte a byte (Q4) |
| erro aborta tudo; publica dentro do laço | erro isola o usuário; publicação só no fim, atômica, só quando o md5 muda |

## 2. Usuários (execução de 16/09/2026 06h55, `--sem-publicar`)

| Nível | Usuário | Dist. | Linhas da fato | PDVs base ativa | HTML | Tempo |
|---|---|---|---|---|---|---|
| N1 | 10 - DISTRIBUICAO - MICHEL MEIRA | 71 | 10.009.461 | 130.560 | 14,9 MB | cópia do canal |
| N2 | 11000 - Ger Reg_SUDESTE - [VAGO] | 21 | 1.798.981 | 35.931 | 5,2 MB | 34 s |
| N2 | 12000 - Ger Reg_ CO/SUL - FRANCISCO REZENDE | 22 | 4.890.647 | 44.227 | 6,3 MB | 47 s |
| N2 | 13000 - Ger Reg_NO/NE - BERNARDO VERAS | 28 | 3.319.833 | 50.402 | 6,1 MB | 40 s |
| N3 | 1110 - Superv_SPI - MURILO CUNHA | 2 | 15.564 | 1.402 | 0,6 MB | 8 s |
| N3 | 1120 - Superv_SPC - CAIO LUPERNI | 4 | 230.638 | 7.816 | 2,1 MB | 18 s |
| N3 | 1130 - Superv_RJ/ES - FABIO MONTEIRO | 5 | 416.726 | 7.933 | 2,2 MB | 14 s |
| N3 | 1140 - Superv_MG - BONIFACIO ARAUJO | 7 | 1.064.455 | 13.861 | 2,8 MB | 19 s |
| N3 | 1150 - Superv_SPC+Litoral - DEODATO CARMO | 3 | 71.598 | 4.919 | 1,2 MB | 11 s |
| N3 | 1210 - Superv_PR - [VAGO] | 4 | 1.011.984 | 9.397 | 2,4 MB | 17 s |
| N3 | 1220 - Superv_SC - ALEXANDRO VALERIO | 6 | 898.409 | 6.433 | 2,3 MB | 16 s |
| N3 | 1230 - Superv_RS - ROGERIO PIETSCHAKI | 5 | 639.238 | 10.017 | 2,4 MB | 16 s |
| N3 | 1240 - Superv_DF/GO/TO - [VAGO - FRANCISCO 1] | 2 | 1.080.211 | 9.193 | 2,3 MB | 17 s |
| N3 | 1250 - Superv_AC/MS/MT/RO - [VAGO - FRANCISCO 2] | 5 | 1.260.805 | 9.187 | 2,4 MB | 18 s |
| N3 | 1310 - Superv_AL/PB/PE/RN - ARLINDO NASCIMENTO | 8 | 594.381 | 10.889 | 2,5 MB | 18 s |
| N3 | 1320 - Superv_BA/SE - [VAGO - OLIVEIRA] | 9 | 963.308 | 12.782 | 2,7 MB | 18 s |
| N3 | 1330 - Superv_CE/MA/PI - FELIPE BARBOSA | 5 | 828.668 | 14.528 | 2,6 MB | 18 s |
| N3 | 1340 - Superv_NO - HERILSON HOLANDA | 6 | 933.476 | 12.203 | 2,4 MB | 18 s |

Execução completa: canal 133 s + 18 usuários 346 s = **8 min**, sequencial, prioridade abaixo do normal, 4 threads. 64 MB de HTML
no total (contra 100 MB dos 73 Gerenciais).

## 3. Como funciona (`dn/distribuicao.py`)

1. `usuarios(dist)`: um registro por rótulo distinto de cada nível, com os CNPJs dos distribuidores dele.
2. `recortar(c, u)`: `c` do usuário = fato e distribuidores só do recorte; `metrics.preparar_codigos` refaz pares e base ativa no
   subconjunto (segundos). A referência da Penetração vem do canal (`c["pen_canal"]`, Q1). O nome do "canal" no painel vira o
   rótulo do usuário (`distribuicao.rotulo_canal`).
3. `metrics.calcular` → `pipeline.fechado` → `pipeline.gerar`: exatamente o código do canal, sem gravar nada. O log fica em
   silêncio (só avisos e erros) para não repetir 18 vezes as linhas do canal.
4. `validar_usuario`: 12 conferências essenciais (placeholders, tamanho, cards = fato do recorte, distribuidores e supervisores só
   do recorte, blob de PDVs = base ativa do recorte, RTM sem não mensuráveis e só destinos do recorte, **vazamento**).
5. Gravação em `%LOCALAPPDATA%\Dori\DN\painel\usuarios\<slug>\`; `conferir_somas`; publicação só dos que passaram.
6. `--usuario 1120` gera um só (e não confere somas); `--sem-usuarios` desliga a etapa nesta execução; `--sem-publicar` vale para todos.

Regras aplicadas no recorte (flag `c["recorte"]`):
- RTM: só clientes cujo destino, pela chave do código, é um distribuidor do recorte (Q2). "Só de outro" passa a significar "de
  outro distribuidor do próprio recorte" — comprar de um distribuidor de outro supervisor não é visível para o supervisor.
- Carteira de PDVs ponderados: linhas de outros distribuidores são inválidas por definição, sem aviso nem relatório (Q5).
- Penetração: benchmark P75, cortes P99, kg/R$ por loja do canal e fator observado = canal inteiro (Q1); o que é do distribuidor
  (kg/loja, lojas, penetração) é recalculado no recorte.
- Calendário: um recorte sem venda até certo mês recebe o bloco do calendário da DIM_CALENDARIO (Murilo Cunha começa em abr/26,
  Deodato Carmo em set/25).

## 4. Segurança

O filtro é na fato, antes de qualquer cubo, JSON ou HTML. O que o pipeline não viu não existe no arquivo: dropdown de supervisor
(1 opção para o supervisor, os dele para o gerente), mapa JS distribuidor → supervisor, tabelas, pacotes mensais, blob de PDVs, RTM.

Busca no código-fonte de cada HTML (validação 2): rótulo, slug, id, nome e `código - ` de todos os outros usuários que não estão
acima nem abaixo do recorte na hierarquia, CNPJ e nome Mtrix de todos os distribuidores fora da carteira. 18 de 18 arquivos com
**zero ocorrências** (152 a 210 termos por arquivo). Nome reduzido de distribuidor fora da carteira é só aviso, porque colide com
nomes de cidade e de PDV: "SANTO ANTONIO" (distribuidor de SC) aparece em dois painéis dentro de "V.M. (Filial) - SANTO ANTONIO DE
JESUS BA", distribuidor do próprio recorte.

## 5. Validação (16/09/2026 06h55)

1. **Soma dos níveis = canal**: os 14 supervisores e os 3 gerentes somam o canal em kg, R$ e NFs, mês a mês (25 meses) e por
   categoria, com diferença 0,000. PDVs distintos: máximo dos usuários ≤ canal ≤ soma dos usuários em todos os meses (o mesmo PDV
   atendido por dois supervisores conta uma vez no canal), e cada painel confere seus PDVs por recálculo na fato do recorte.
2. **Vazamento**: zero ocorrências em 18 de 18 (acima).
3. **Painel do canal = pipeline anterior**: JSON idêntico à linha de base de 15/09 e HTML idêntico fora os carimbos; 120 validações.
   O N1 do Michel é cópia byte a byte.
4. Abertos no navegador: Caio Luperni (título, cards, tabela com um supervisor, 7.816 PDVs) e Sudeste (5 supervisores, 21
   distribuidores). Sem erro no console.

## 6. Erro em um usuário (`distribuicao.em_erro`)

| Valor | Comportamento | Quando faz sentido |
|---|---|---|
| `continuar` (padrão) | gera todos, publica os que passaram, o que falhou fica com o arquivo anterior na pasta e o pipeline sai com exit 1 | o problema é de um usuário e os outros 17 não devem esperar |
| `abortar_publicacao` | gera todos, mas não publica nenhum se algum falhou | todos precisam ver o mesmo mês ao mesmo tempo |
| `parar` | interrompe no primeiro erro, nada publicado | diagnóstico: um erro por vez |

Em qualquer modo o painel do canal (`Painéis Comerciais/DN`) já foi validado e publicado antes da etapa 6; a soma dos níveis não é
conferida quando algum usuário do nível falhou. Um `abortar()` dentro do cálculo de um usuário vira erro do usuário, não do pipeline.

## 7. Publicação (16/09/2026) e pendências

Aprovado pelo Douglas em 16/09/2026: `python run_dn.py` publicou o canal às 07h16 (md5 `e6519850…`) e os 18 painéis às 07h21, md5
conferido nos 18 destinos; soma dos níveis e vazamento ok. Antes da publicação, dois ajustes pedidos pelo Douglas na aba Pontos de
venda: abre em **Todos os PDVs** (`painel.pdv_carteira.padrao: todos`, "por enquanto") e o filtro Situação fica só com **Todos da
base ativa · Sem compra no mês · Positivados no mês · Clientes RTM** (`painel.pdv_situacoes_por_categoria: false`; template com
`PDV_ROT.sit_cat`, `--regerar-exemplo` rodado; o drill da Penetração oculta continua funcionando).

1. Compartilhar cada pasta com o respectivo usuário (Pode exibir) é ato do Douglas, como nos Gerenciais.
2. ~~Registrar Q1/Q2/Q5 e Pontos de venda como fichas RN~~ feito: RN-60 a RN-64.
3. A pasta `usuarios/` local guarda 64 MB por execução (sobrescritos a cada rodada).
4. Cada `python run_dn.py` regera e republica os 18 (só copia quando o md5 muda): canal + usuários ≈ 7 min.

## 8. Checklist

- [x] 18 usuários descobertos da hierarquia; 18 pastas existentes conferidas
- [x] 18 painéis gerados, 0 com erro, 12 conferências essenciais ok em cada um
- [x] soma N2 e N3 = canal (kg, R$, NFs, por categoria) com diferença zero
- [x] vazamento: zero ocorrências em 18 de 18
- [x] painel do canal inalterado (JSON idêntico à linha de base)
- [x] falha isolada por usuário, três políticas configuráveis, log e resumo por usuário
- [x] caminhos relativos à raiz do projeto (sem `dldsouza` no config)
- [x] publicação (ok do Douglas, 16/09/2026 07h16 e 07h21)
- [x] `docs/regras_negocio.md`: RN-60 a RN-64 (painel por usuário, Q1, Q2, Q5, aba Pontos de venda), 16/09/2026
