# Refino do painel · Etapa E6 · Definições, janela do arquivo e documentação

13/09/2026. Plano aprovado pelo Douglas ("Sim, seguir com as recomendações"): Definições em tabelas Indicador · Fórmula com
observação curta só onde precisa; tamanho pela opção (c), janela móvel de 25 meses; README e RETOMADA reescritos; checklist único.
**Gerada com `--sem-publicar`.**

## (a) O que mudou

| Onde | Mudança |
|---|---|
| Aba Definições | 7 temas (Base e cobertura, Volume e valor, Frequência, Período e comparativos, Penetração, RTM, Regras de contagem), 37 linhas Indicador · Fórmula · Observação; os parágrafos antigos saíram. Textos no config (`painel.definicoes`), com os parâmetros preenchidos do config (5 meses, 6 meses, P75, 25 meses) |
| Janela do arquivo | `painel.janela_arquivo_meses: 25`: seletor de mês, séries dos gráficos, pacotes por mês e série do RTM levam só os últimos 25 meses. O cálculo segue com todos os meses (base ativa, LY, acumulados). Hoje a série tem exatamente 25 meses, então nada muda no conteúdo; a partir de out/26 o mês mais antigo sai a cada mês novo |
| Pipeline | histórico montado só dentro da janela; validações `periodo · serie inteira embutida` e `tabela rtm_serie · registros` contam a janela |
| Inventário | `definicoes.tema`, `definicoes.itens.indicador`, `formula` (texto) e `obs` (bruto: vazia fica em branco) |
| Documentos | `README.md` e `docs/RETOMADA.md` reescritos para o estado atual; `docs/refino_checklist.md` (checklist único por aba); `docs/refino_painel_proposta.md` com o andamento; RN-59 com a nota da janela |

Backup antes da E6: scratchpad da sessão, pasta `backup_pre_E6`.

## (b) Por quê

As Definições eram parágrafos longos; o pedido do refino é menos texto e só o medido. A janela móvel mantém o arquivo abaixo do
limite de 15 MB sem perder o cálculo de longo prazo (cada mês novo somaria ~0,3 MB).

## (c) Resultado e pendências

| Item | E5 | E6 |
|---|---|---|
| HTML | 14,5 MB | **14,5 MB** |
| Validações | 119 ok | **119 ok** |
| Tempo | ~9 min | ~10 min |
| Números | — | iguais aos da E5 (set/26 parcial: base ativa 120.742 · DN 13,0% · 201,2 t · 67 distribuidores; RTM 1.762/1.589/173) |

Prova do template: a execução sem `--regerar-exemplo` gerou o mesmo HTML (15.242.655 bytes, md5 `5e817e98fad0fc77f169799ad7feb167`),
com o renderizador validado byte a byte (`resumo_20260913-214406-3171c3.json`).

Conferido no navegador, sem erro no console: aba Definições com os 7 temas e 37 linhas, parâmetros preenchidos, sem marcadores
`{...}` sobrando; seletor de mês com 25 meses (set/26 parcial a set/24).

Defeito achado e corrigido antes da entrega: observação vazia aparecia como "—" (o formato texto troca vazio por travessão); o campo
passou a formato bruto e a célula fica em branco.

Pendências: nenhuma de código. Checklist único do Douglas e publicação.

## (d) Checklist

Consolidado com o das etapas anteriores em **`docs/refino_checklist.md`** (itens 31 e 32 são desta etapa).
