# Evolução · Fase F0 — dicionário de regras e config (10/09/2026, noite)

Executada após a Etapa 1 (`docs/evolucao_etapa1_auditoria.md`, 35 decisões fechadas) e a aprovação integral da proposta da
F0 (itens P1–P7) pelo Douglas em 10/09/2026.

## (a) O que foi alterado

| Arquivo | Mudança |
|---|---|
| `docs/regras_negocio.md` (**novo**) | Dicionário de regras de negócio, fonte única: **55 fichas** (`RN-01`…`RN-55`) em 6 blocos (medidas e populações; dimensões e hierarquia; tempo e comparativos; penetração, benchmark e potencial; matriz, filtros, resumos e apresentação; RTM). Cada ficha com objetivo, definição, fórmula, base, campos, granularidade, filtros, exceções, nulos, zeros, duplicidades, parametrização, responsável, status, aprovação e observações. 23 vigentes · 29 aprovadas (não implementadas, com a fase em que entram) · 3 declaradas (drop, faturamento Dori, cadastro de elegíveis). Regra de manutenção no cabeçalho (ficha antes de código; ids nunca renumerados; revogação registrada) |
| `config/config.yaml` | **45 chaves novas, todas inertes** (o pipeline não lê nenhuma até a fase que a implementa): `calendario.{perspectiva_padrao, rotulo_fiscal_longo, rotulo_fiscal_curto}`; `regras.metrica.*` (8); `regras.penetracao.*` (10, inclui `benchmark.*` e `categorias_foco`); `regras.potencial.*` (7); `regras.matriz.*` (6); `regras.hierarquia.*` (2); `painel.graficos.*` (3); `painel.filtros.supervisor.*` (2); `painel.resumos.*` (2, vazio); `painel.pdv_categoria.*` (2). Cada chave comenta o `RN-nn` e a decisão de origem. **Nenhuma chave existente mudou de valor**; `painel.abas` não foi tocado. Cópia do config anterior no scratchpad da sessão (`config.yaml.antes_F0`) |
| `README.md` | tabela de parâmetros ganhou o bloco "F0 · chaves inertes"; "Regras que não são óbvias" aponta para o dicionário e traz o id RN em cada frase; changelog |
| `docs/RETOMADA.md` | §4 aponta para o dicionário como fonte única; §7 ganhou as linhas do dicionário e deste relatório; §1 marca a F0 concluída; pendência 9 passa a ser a **F1** |
| `docs/evolucao_etapa1_auditoria.md` | cada ficha A.1–A.16 do Anexo A ganhou a linha "Regra(s) no dicionário: RN-nn"; o Anexo A passa a ser histórico das decisões |

**Não alterados**: `dn/` (nenhum código), `template/` (template, inventário, exemplo), `bases/`, `data/dn/curated`, publicação.

## (b) Por quê

Regra de ouro do pedido (§1 e §23): toda regra registrada, rastreável e aprovada **antes** de implementar; regras parametrizadas
em vez de hardcoded. A Etapa 1 fechou as decisões; a F0 as transforma em fichas com id e em chaves de config, para que as fases
F1–F10 só liguem o que já está escrito. As chaves entram inertes agora para que cada fase seguinte não tenha de reabrir o config
e para que o dicionário e o config já falem a mesma língua (id RN nos dois).

## Prova (execução `20260910-204805-cbc937`, `--mes 2026-08 --sem-publicar`, 96 s)

| Checagem | Resultado |
|---|---|
| Config | carrega sem erro (`dn.utils.config`); 0 chaves existentes alteradas; 45 novas (conferido por comparação chave a chave antes × depois) |
| Etapa 0 | "bases inalteradas"; ingestão pulada |
| Validações | **40 ok**, 0 falhas; 1 aviso informativo (os 4 destinos RTM sem cadastro, já conhecido) |
| Números ago/26 | 124.600 · 71.478 · 57,4% · 1.199,9 t · 71 · RTM 1762/1589/173 — iguais |
| **HTML** | `data/dn/painel/Scorecard_DN_2026-08.html` com md5 **`466624fc52c5e6d100e50b5d2e650b25`** = md5 do publicado em `Painéis Comerciais/DN/Scorecard_DN.html`. **Idêntico byte a byte**: a F0 não mudou nada na tela |
| Publicação | pulada (`--sem-publicar`); o publicado não foi tocado |
| Dicionário | 55 fichas (`grep -c "^### RN-"` = 55); README 17 referências RN, doc da Etapa 1 17, RETOMADA 1 |

## (c) O que ficou pendente

- Nada da F0.
- As 29 regras "aprovadas" viram "vigentes" à medida que as fases F1–F10 as implementarem; o dicionário é revisado ao fim de cada fase.
- Pendências de dado inalteradas: Mtrix set/24–jun/25 (D5, pedir à Mtrix), coluna `CNPJ Distribuidor Destino` na RTM, datas de
  cadastro de 6 distribuidores, 4 destinos RTM sem cadastro, planilha dos PDVs ponderados (correção em 11/09).
- Próxima fase: **F1** (seletor Volume × Valor; R$ no blob de PDVs e no RTM; remoção de `RKG`, `applyUnit`, `UMODE/YMODE`,
  `setu`, `sety`, `PCL`), a ser proposta por escrito e aprovada item a item.

## (d) Checklist para você

- [ ] Abrir `docs/regras_negocio.md` e conferir 5 fichas ao acaso contra as fichas A.x do Anexo A (ex.: RN-06 × A.4, RN-30 × A.1, RN-34 × A.7, RN-19 × A.8, RN-44 × A.13).
- [ ] Abrir `config/config.yaml`: os blocos novos estão marcados "F0" e cada chave tem o comentário `RN-nn`; nenhuma chave antiga mudou.
- [ ] Rodar `python run_dn.py --mes 2026-08 --sem-publicar` e conferir: "bases inalteradas", 40 ok, e o md5 do HTML gerado igual ao do publicado (`certutil -hashfile ... MD5` no Windows).
- [ ] Abrir o painel publicado (Ctrl+F5): nada mudou (ago/26, mesmos números).
- [ ] `README.md`, seção "Regras que não são óbvias": cada frase começa com o id RN e o parágrafo aponta para o dicionário.
