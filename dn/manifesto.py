# -*- coding: utf-8 -*-
"""Manifesto das bases: o que a camada curada foi construída a partir de.

`data/dn/curated/manifesto.json` guarda a impressão digital (caminho, tamanho,
mtime, hash rápido) de CADA arquivo de base lido na última ingestão, mais a
versão do código dos leitores. É contra ele que o orquestrador decide se a
ingestão precisa rodar e que a validação final prova que nenhuma base é mais
nova do que o curated (item D3 da reforma, 09/09/2026).

Sem isso o painel podia ser gerado sobre um curated velho sem ninguém saber —
aconteceu em 09/09/2026, quando RTM e Hierarquia mudaram depois da execução.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .extract import cache, cadastros
from .utils.config import CFG, PASTA_CURATED, caminho
from .utils.log import log

ARQUIVO = PASTA_CURATED / "manifesto.json"


def bases_declaradas() -> list[Path]:
    """Todos os arquivos de base que o config declara (existentes)."""
    F = CFG["fontes"]
    out: list[Path] = []
    pasta = caminho(F["sellout"]["pasta"])
    ignorados = set((F["sellout"].get("arquivos_ignorados") or {}).keys())
    if pasta.exists():
        for padrao in F["sellout"]["padroes_aceitos"]:
            out += [a for a in pasta.glob(padrao) if not a.name.startswith("~$") and a.name not in ignorados]
    for chave in ("produtos", "distribuidores", "hierarquia", "rtm", "clusters", "pdv_ponderada"):   # RN-56: planilha ponderada (opcional)
        cfg = F.get(chave)
        if cfg and cfg.get("arquivo"):
            a = caminho(cfg["arquivo"])
            if a.exists():
                out.append(a)
    out.append(cadastros.arquivo_hierarquia())   # 02/10/2026: hierarquia por pasta + data no nome, nao por `arquivo`
    return sorted(set(out))


def atual() -> dict:
    return {"versao_leitores": cache.VERSAO_LEITORES,
            "bases": {cache.relativo(a): cache.impressao(a) for a in bases_declaradas()}}


def gravado() -> dict | None:
    if not ARQUIVO.exists():
        return None
    try:
        return json.loads(ARQUIVO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def comparar(novo: dict | None = None, velho: dict | None = None) -> dict:
    """Diferenças entre o estado atual das bases e o manifesto gravado."""
    novo = novo or atual()
    velho = gravado() if velho is None else velho
    if velho is None:
        return {"motivo": "sem manifesto (curated nunca gerado ou apagado)", "precisa_ingerir": True,
                "novos": sorted(novo["bases"]), "alterados": [], "removidos": [], "leitores_mudaram": False}
    nb, vb = novo["bases"], velho.get("bases", {})
    novos = sorted(set(nb) - set(vb))
    removidos = sorted(set(vb) - set(nb))
    alterados = sorted(k for k in set(nb) & set(vb)
                       if (nb[k]["tamanho"], nb[k]["mtime"], nb[k]["hash"]) !=
                          (vb[k]["tamanho"], vb[k]["mtime"], vb[k]["hash"]))
    leitores = novo["versao_leitores"] != velho.get("versao_leitores")
    precisa = bool(novos or removidos or alterados or leitores)
    motivo = ("bases inalteradas" if not precisa else
              "; ".join(m for m in (f"{len(novos)} base(s) nova(s)" if novos else "",
                                    f"{len(alterados)} base(s) alterada(s)" if alterados else "",
                                    f"{len(removidos)} base(s) removida(s)" if removidos else "",
                                    "codigo dos leitores mudou" if leitores else "") if m))
    return {"motivo": motivo, "precisa_ingerir": precisa, "novos": novos, "alterados": alterados,
            "removidos": removidos, "leitores_mudaram": leitores}


def dados_atualizados_em() -> str:
    """Data da ultima ingestao (dd/mm/aaaa), do manifesto — deterministica entre execucoes
    sem mudanca de base. Cai no id da execucao quando o manifesto e anterior a este campo."""
    m = gravado() or {}
    g = m.get("gravado_em")
    if g:
        return f"{g[8:10]}/{g[5:7]}/{g[0:4]}"
    e = str(m.get("execucao", ""))
    return f"{e[6:8]}/{e[4:6]}/{e[0:4]}" if len(e) >= 8 else "—"


def gravar(execucao_id: str, extras: dict | None = None) -> None:
    m = atual()
    m["execucao"] = execucao_id
    m["gravado_em"] = datetime.now().strftime("%Y-%m-%d %H:%M")     # carimbo "dados atualizados em" do painel (Fase 5)
    m.update(extras or {})
    PASTA_CURATED.mkdir(parents=True, exist_ok=True)
    ARQUIVO.write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"manifesto: {len(m['bases'])} base(s) registradas -> {ARQUIVO.name}", "ok")
