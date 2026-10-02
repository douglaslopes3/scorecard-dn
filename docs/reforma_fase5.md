# Reforma · Fase 5 — pasta de publicação e compartilhamento (09/09/2026)

Proposta aprovada integralmente pelo Douglas em 09/09/2026 (P1 pasta e nome; P2 sem LEIA-ME na
pasta; P3 compartilhamento pela pasta do OneDrive com pessoas específicas; P4 só avisar sobre
arquivos estranhos; P5 carimbo de atualização; P6 só o Douglas roda).

## (a) O que foi alterado

| Arquivo | Mudança |
|---|---|
| `dn/pipeline.py` · etapa 5 | lista e **avisa** sobre qualquer item na pasta de publicação além do `Scorecard_DN.html` (não remove); grava md5, tamanho e a data dos dados no `resumo_<execução>.json` |
| `dn/manifesto.py` | `gravado_em` no manifesto a cada ingestão; `dados_atualizados_em()` devolve a data da última leitura das bases (dd/mm/aaaa) — para manifestos anteriores a este campo, cai no id da execução |
| `dn/painel.py` | `meta_execucao.dados_atualizados_em` |
| `template/template.html` | carimbo "atualizado em dd/mm/aaaa" na tarja do cabeçalho (visível em todas as abas) e no rodapé da aba Definições ("dados até jul/26 · painel atualizado em … (data da última leitura das bases)") |
| `template/data-inventory.json` | `meta_execucao.dados_atualizados_em` |
| `README.md` | seção "Publicação e compartilhamento" (estrutura da pasta, o que entra/fica de fora, como compartilhar, como abrir) e rotina completa |

A publicação em si (cópia atômica, md5 conferido, só após todas as validações) existe desde a Fase 1.

## Estrutura final

```
Painéis - Alavancas/DN/            desenvolvimento: bases, config, pipeline, template, data/dn, docs
Painéis Comerciais/DN/             publicação: Scorecard_DN.html (e nada mais)
Painéis - Alavancas/_fora_do_DN_2026-09-09/   quarentena do material do projeto gerencial (você apaga)
```

## Compartilhamento (padrão adotado)

1. No OneDrive, pasta `Painéis Comerciais/DN` → **Compartilhar** → pessoas específicas do time →
   **Pode exibir** → enviar o link da pasta (ou do arquivo). Não usar "qualquer pessoa com o link":
   o HTML embute CNPJ, razão social e endereço de PDVs e clientes.
2. O link não muda quando o pipeline sobrescreve o arquivo; quem tem o link vê sempre a última versão.
3. Como abrir: Chrome ou Edge, **Ctrl+F5**. Se abrir no visualizador do SharePoint/Teams e a busca de
   PDVs ou o CSV não funcionar, usar "Abrir no navegador" ou baixar e abrir localmente.
4. Quando um novo membro entra no time: adicionar na permissão da pasta. Quando sai: remover.

## Rotina (também no README)

| Quando | Passos |
|---|---|
| Mensal, quando a Mtrix do mês fechado chegar | 1. soltar `ScoreCard_Mtrix_MM.AAAA.xlsx` em `bases/Sell Out - MTRIX/`; 2. atualizar de-paras se houver distribuidor, cluster ou cliente RTM novo (o pipeline aborta e diz qual CNPJ falta no de-para); 3. `python run_dn.py`; 4. conferir o fim do log (mês, números, avisos, "publicado em"); 5. abrir o publicado com Ctrl+F5 e conferir mês e "atualizado em" na tarja |
| De-para alterado sem Mtrix nova | `python run_dn.py` (o manifesto detecta e reingere) |
| Template alterado | `python run_dn.py --regerar-exemplo` uma vez |
| Validação falhou | nada é publicado; a versão anterior continua no ar; corrigir e rodar de novo |

## Prova (execução `20260909-212043-86535b`)

| Checagem | Resultado |
|---|---|
| Publicação | `Painéis Comerciais/DN/Scorecard_DN.html`, 6.451.424 bytes, md5 `35b0f724…` igual ao gerado; a pasta contém só esse arquivo (nenhum aviso de item estranho) |
| Carimbo | "atualizado em 09/09/2026" na tarja do cabeçalho e no rodapé (data da última ingestão, do manifesto) |
| Resumo da execução | `publicado`, `publicado_md5`, `publicado_bytes`, `dados_atualizados_em` gravados em `resumo_<execução>.json` |
| Validações | 37 ok; números inalterados (jul/26 · 120.817 · 73.185 · 60,6% · 1.279,5 t · 70 · RTM 1.762/1.309/453); 1 aviso informativo (destinos não mensuráveis) |

## (c) O que ficou pendente

- O compartilhamento no OneDrive/SharePoint é uma ação sua (permissões por pessoa); o pipeline não
  a faz nem a verifica.
- Quarentena `_fora_do_DN_2026-09-09/` (202 MB) apagada em 09/09/2026, a pedido do Douglas.

## (d) Checklist de validação

- [ ] `Painéis Comerciais/DN/` contém só `Scorecard_DN.html`.
- [ ] Tarja do cabeçalho mostra "atualizado em 09/09/2026"; rodapé da aba Definições idem.
- [ ] Colocar um arquivo qualquer na pasta de publicação e rodar `python run_dn.py`: o log avisa o nome e não o apaga.
- [ ] Compartilhar a pasta com uma pessoa do time (Pode exibir) e pedir que abra o link com Ctrl+F5.
- [ ] `resumo_<execução>.json` traz `publicado_md5`, `publicado_bytes` e `dados_atualizados_em`.
