# Refino do painel · Etapa E3 · fusão das abas, "O que aconteceu no mês" e gráfico em janela

13/09/2026. Plano aprovado pelo Douglas: comparação só vs mês anterior, 5 quedas e 5 altas, bloco abaixo dos cards, gráfico do
canal seguindo o Segmento (4a), série dos clusters embutida (5b), Penetração fundida com Ver por. Checklist único no fim do refino.
Decisões de origem: D7, D14, D15, D19, D20, D27 de `docs/refino_painel_proposta.md`. **Gerada com `--sem-publicar`.**

Junto com a E3 foi corrigido (aprovado em 13/09) o defeito do card da frequência: os números de apoio ocultos (NFs estimadas,
NFs mínimas, frequência mínima) apareciam porque `.k span{display:block}` vencia o atributo `hidden`; uma linha de CSS resolve.

## (a) O que mudou

| Onde | Mudança |
|---|---|
| Abas | De 8 para **6**: Visão Geral · Supervisores e distribuidores · Pontos de venda · Penetração · RTM · Definições. Links salvos para Evolução ou Clusters abrem a Visão Geral |
| Visão Geral | Ordem: aviso de parcial · cards e acumulado · **O que aconteceu no mês** · Cobertura mês a mês · Evolução por categoria · Por categoria |
| O que aconteceu no mês | Maiores quedas e maiores altas vs mês anterior (5 de cada), por Supervisor ou Distribuidor, na régua PDVs positivados ou Volume/Valor (segue a métrica). Respeita segmento, supervisor e categoria da lateral; com supervisor escolhido, lista os distribuidores dele. Clicar no nome abre Supervisores e distribuidores filtrado; "sem compra" (distribuidor) abre Pontos de venda nesse distribuidor com a situação Sem compra no mês. Os saltos entram no Voltar |
| Cobertura mês a mês | Sem o seletor de categoria próprio: segue a Categoria da lateral e agora também o Segmento (séries do canal em Base atual e Novos, e segmento × categoria). Com supervisor: série do supervisor (sem recorte de categoria, com nota curta quando há categoria) |
| Supervisores e distribuidores | Um bloco com **Ver por: Supervisor · Distribuidor · Cluster**. Clicar no nome do supervisor filtra os distribuidores dele. Na visão Supervisor o filtro Distribuidor some; na visão Cluster somem Supervisor e Distribuidor (a tabela não tem esses recortes) |
| Gráfico em janela | Clicar na linha de categorias (Visão Geral), supervisores, distribuidores ou clusters abre o gráfico mês a mês numa janela (PDVs, medida, frequência, LY; Esc ou Fechar). Os gráficos que abriam abaixo das tabelas saíram. Linhas por categoria dentro de supervisor, distribuidor e cluster não abrem gráfico (sem série embutida; entram na E4), e a tabela de categorias com supervisor escolhido também não |
| Penetração | As tabelas por supervisor, por cluster e por distribuidor viraram um bloco com **Ver por** |
| Estado e Voltar | O Ver por das duas abas fica no estado (`vp`, `pvp`) e no passo do Voltar |
| Pipeline | `dn/painel.py`: diferenças absolutas vs mês anterior (`cobertura_dif_mes_anterior`, `volume_dif_mes_anterior`, `receita_dif_mes_anterior`) em supervisores, distribuidores e suas linhas por categoria; séries do canal por segmento e segmento × categoria; id e série dos clusters; rótulos `mes_ranking` |
| Validações novas | `mes · diferencas vs mes anterior = cubos` (778 linhas recalculadas nos cubos) e `series · segmento, segmento × categoria e cluster no HTML` (2 + 20 + 35) |
| Config | `painel.abas` (6), `painel.mes_ranking.n: 5`, rótulos `mr_*`, `ver_por`, `vp_cluster`; `filtros.supervisor.abas` |
| Inventário | +19 campos |
| Documentos | `docs/regras_negocio.md`: RN-21, RN-44, RN-46, RN-50 com a nota da E3 |

Backup antes da E3: scratchpad da sessão, pasta `backup_pre_E3`.

## (b) Por quê

Visão Geral e Evolução contavam a mesma história em duas abas; Clusters e supervisores e Distribuidores repetiam as mesmas colunas.
O head precisa ver o que aconteceu no mês logo abaixo dos números e chegar em um clique a quem puxou a queda ou a alta, e dali à
lista de PDVs sem compra. O gráfico abaixo da tabela não era visto; a janela resolve.

## (c) Resultado e pendências

| Item | E2 | E3 |
|---|---|---|
| Números de ago/26 | 124.800 · 71.478 · 57,3% · 1.199,9 t · 71 · RTM 1.762/1.589/173 | iguais |
| Validações | 109 ok | **111 ok** |
| HTML | 11,2 MB | 11,6 MB (séries novas de segmento, segmento × categoria e clusters) |
| Avisos | 3 | os mesmos 3 |

Conferido no navegador, sem erro no console: 6 abas; ranking por supervisor (maior queda 1320 BA/SE −831 PDVs; maior alta 1110 SPI
+293), por distribuidor e em t; o gráfico mês a mês troca para Novos e para Novos × Amendoim; clique no supervisor do ranking abre a
aba na visão Distribuidor com os 9 distribuidores dele, e Voltar retorna; "sem compra" abre Pontos de venda com 1.038 PDVs sem compra
da MAM Feira de Santana; janelas de gráfico de distribuidor, supervisor, cluster e categoria abrem e fecham com Esc; linhas por
categoria não clicam; Ver por da Penetração alterna; o título do gráfico mostra o período escolhido.

Segunda execução sem `--regerar-exemplo` (`resumo_20260913-175125-cd988e.json`): renderizador validado byte a byte, 111 ok,
mesmos números, HTML idêntico ao testado (md5 `189969584561e26ee82168549a7279fd`).

Dois defeitos achados no próprio teste e corrigidos antes desta entrega: a aba aberta pelo ranking mostrava a tabela de supervisores
em vez da de distribuidores (a aba já tinha sido montada escondida); o título "Cobertura mês a mês" mostrava "24 meses" em vez do
período escolhido.

Diferença em relação ao plano: o plano dizia que o filtro Distribuidor aparece na visão Supervisor; ele some ali, porque a tabela de
supervisores não recorta por distribuidor (regra D11).

Pendências para a E4: evolução por categoria em linhas seguindo o Segmento; gráfico das linhas por categoria de supervisor,
distribuidor e cluster.

## (d) Checklist para o Douglas (junto com os da E1 e E2)

1. As abas são 6: Visão Geral, Supervisores e distribuidores, Pontos de venda, Penetração, RTM, Definições.
2. Visão Geral: abaixo dos cards, "O que aconteceu no mês · vs jul/26" com 5 maiores quedas e 5 maiores altas.
3. Trocar Supervisor/Distribuidor e PDVs positivados/Volume no bloco; trocar t/R$ na lateral: as listas mudam.
4. Escolher Segmento e Categoria na lateral: o bloco e o gráfico "Cobertura mês a mês" mudam juntos.
5. Clicar num supervisor da lista: abre Supervisores e distribuidores com os distribuidores dele; Voltar retorna à Visão Geral.
6. Com Distribuidor na lista, clicar em "sem compra": abre Pontos de venda com os PDVs sem compra daquele distribuidor.
7. Supervisores e distribuidores: Ver por Supervisor, Distribuidor e Cluster; clicar no nome do supervisor filtra os distribuidores.
8. Clicar numa linha (supervisor, distribuidor, cluster, categoria na Visão Geral): o gráfico abre em janela; Esc fecha.
9. Penetração: o bloco Ver por alterna entre supervisor, cluster e distribuidor com os mesmos números de antes.
10. Card "Frequência de compra (estimativa)": só 1,25 e os comparativos, sem os três números soltos.
