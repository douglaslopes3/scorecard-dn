# -*- coding: utf-8 -*-
"""Dados das tabelas do painel como JSON embutido (Fase 3 da reforma, 09/09/2026).

O template não renderiza mais linhas de tabela em HTML: cada tabela recebe um
`<script type="application/json">` com os seus registros, já **formatados pelo
inventário** (o mesmo contrato de sempre), e o componente `DnTabela` (JS no
template) monta cabeçalho, corpo, busca, ordenação, amostra/expansão e CSV.

Aqui só se serializa o que o JSON do painel já tem; nenhum número é calculado.
Os PDVs continuam no blob gzip+base64 (`pdv_blob`).
"""
from __future__ import annotations

import json

from .utils.config import CFG

# campos de lista (série mensal, linhas por categoria) que não entram na linha da tabela
_SEM_SERIE = ("serie", "serie_js", "categorias")   # RN-59: a serie compacta vai no bloco do grafico, nunca na linha da tabela
# F5 (RN-25): dos acumulados, a linha da tabela leva só o que a coluna "Acum. no ano" usa (t e R$ civil/fiscal) e os
# PDVs distintos; LY, Δ, n meses e R$ mi ficam fora (+0,7 MB se entrassem). A tabela de supervisores mantém R$ mi e
# Δ porque a linha de acumulado da Visão geral filtrada por supervisor lê dali.
_SEM_TABELA = tuple(f"acum_{p}_{s}" for p in ("civil", "fiscal") for s in ("ly_t", "ly_rs", "n"))
_SO_SUPERVISOR = tuple(f"acum_{p}_{s}" for p in ("civil", "fiscal") for s in ("mi",))   # Refino E5: Δ e frequencia acumulada em todas as tabelas   # RN-58: freq acumulada so na linha da Visao geral


def _fora(manter_sup: bool = False) -> set:
    return set(_SEM_SERIE) | set(_SEM_TABELA) | (set() if manter_sup else set(_SO_SUPERVISOR))
_CAT_TODAS = str(CFG["painel"]["rotulos"].get("categoria_todas", "Todas as categorias"))


def _linhas(items: list[dict], extra: dict | None = None) -> list[dict]:
    out = []
    fora = _fora()
    for it in items:
        r = {k: v for k, v in it.items() if k not in fora}
        if extra:
            r.update(extra)
        out.append(r)
    return out


def _distribuidores(items: list[dict]) -> list[dict]:
    """Uma linha por distribuidor (total do mês) e uma por distribuidor × categoria
    (10/09/2026). O filtro de categoria da barra global escolhe qual aparece: com
    "Todas as categorias" a tabela fica idêntica à de antes."""
    out = []
    fora = _fora()
    for d in items:
        base = {k: v for k, v in d.items() if k not in fora}
        out.append(dict(base, cat_id="__all__", categoria=_CAT_TODAS))
        for c in d.get("categorias") or []:
            linha = dict(base)
            linha.update({k: v for k, v in c.items() if k not in ("id", "nome") and k not in fora})
            linha["cat_id"] = c.get("id")
            linha["categoria"] = c.get("nome")
            out.append(linha)
    return out


def _por_categoria(items: list[dict], manter_sup: bool = False) -> list[dict]:
    """F4 (Q-c): clusters e supervisores como Distribuidores — uma linha total (cat_id "__all__") e uma por categoria."""
    out = []
    fora = _fora(manter_sup)
    for d in items:
        base = {k: v for k, v in d.items() if k not in fora}
        out.append(dict(base, cat_id="__all__", categoria=_CAT_TODAS))
        for c in d.get("categorias") or []:
            linha = dict(base)
            linha.update({k: v for k, v in c.items() if k not in ("id", "nome") and k not in fora})
            linha["cat_id"] = c.get("id"); linha["categoria"] = c.get("nome")
            out.append(linha)
    return out


def _json(obj) -> str:
    """JSON compacto, seguro dentro de <script> (nenhum '</' solto)."""
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def tabelas(JF: dict) -> dict[str, list[dict]]:
    """Registros de cada tabela, a partir do JSON formatado do painel."""
    segs = JF.get("segmentos") or []
    T = {
        "clusters": [dict(r, segmento_id=s["id"], segmento=s["nome"]) for s in segs for r in _por_categoria(s.get("clusters") or [])],
        "supervisores": [dict(r, segmento_id=s["id"], segmento=s["nome"]) for s in segs for r in _por_categoria(s.get("supervisores") or [], True)],
        "categorias": _linhas(JF.get("categorias") or []),
        "categorias_sup": _linhas(JF.get("categorias_sup") or []),   # F4: Visao geral filtrada por supervisor
        # F6 (RN-27..RN-36): aba Penetracao — nivel x categoria (cards, grafico, tabela de categorias, distribuidores),
        # por nivel (cards), supervisores e clusters com as foco em colunas
        "pen_nivel_cat": _linhas(JF.get("pen_nivel_cat") or []),
        "pen_nivel": _linhas(JF.get("pen_nivel") or []),
        "pen_supervisores": _linhas(JF.get("pen_supervisores") or []),
        "pen_clusters": _linhas(JF.get("pen_clusters") or []),
        "distribuidores": _distribuidores(JF.get("distribuidores") or []),
        # D18 revista (RN-44): linhas do canal (sup_id "__all__") e de cada supervisor do destino; o filtro da barra escolhe
        "rtm_serie": _linhas(((JF.get("rtm") or {}).get("serie") or []) + ((JF.get("rtm") or {}).get("serie_sup") or [])),
        "rtm_destinos": _linhas((JF.get("rtm") or {}).get("destinos") or []),
        "rtm_clientes": _linhas((JF.get("rtm") or {}).get("clientes") or []),
    }
    return T


# Refino E4a (D22): tabelas que mudam com o mes vao num pacote comprimido por mes; as que nao mudam (Penetracao no mes
# fechado, serie do RTM) num pacote comprimido unico. Formato em listas (cabecalho + valores) para comprimir melhor.
MES_TABELAS = ("distribuidores", "supervisores", "clusters", "categorias", "categorias_sup", "rtm_destinos")   # E4b: clientes RTM saem da lista
_USADAS: set | None = None


def colunas_usadas() -> set:
    """Refino E4b: nomes de coluna que o template le (aparecem como literal no template); as colunas de acumulado entram por prefixo
    (o JS monta 'acum_' + perspectiva + medida). Coluna que nao aparece em lugar nenhum do template nao vai para o pacote."""
    global _USADAS
    if _USADAS is None:
        import re
        from .utils.config import PASTA_TEMPLATE
        tpl = (PASTA_TEMPLATE / "template.html").read_text(encoding="utf-8")
        _USADAS = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", tpl))
    return _USADAS


def _podar(t: dict) -> dict:
    use = colunas_usadas()
    keep = [i for i, c in enumerate(t["c"]) if c in use or c.startswith("acum_")]
    return {"c": [t["c"][i] for i in keep], "r": [[r[i] for i in keep] for r in t["r"]]}
EST_TABELAS = ("pen_nivel_cat", "pen_nivel", "pen_supervisores", "pen_clusters", "rtm_serie")


def _cols(rows: list[dict]) -> dict:
    keys = list(dict.fromkeys(k for r in rows for k in r))
    return {"c": keys, "r": [[r.get(k) for k in keys] for r in rows]}


def _gz(obj) -> str:
    import base64
    import gzip
    raw = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return base64.b64encode(gzip.compress(raw, compresslevel=9)).decode("ascii")


def pacote_mes(JF: dict) -> dict:
    """O que muda com o mes escolhido: periodo (rotulos), cards por segmento, tabelas do mes, cards do RTM, corte do RTM e carteira."""
    T = tabelas(JF)
    P = JF["periodo"]; rt = JF.get("rtm") or {}
    rk = {"base_total": rt.get("base_total"), "rastreaveis": rt.get("rastreaveis")}
    rk.update(rt.get("kpi") or {})
    tab = {k: _podar(_cols(T[k])) for k in MES_TABELAS}
    tab["rtm_sup"] = _cols(json.loads(str(rt.get("por_supervisor_json") or "[]").replace("<\\/", "</")))
    cart = JF.get("carteira") or {}
    return {"id": str(JF["meta_execucao"]["mes_referencia"]), "rotulo": str(P["mes_atual"]), "parcial": bool(P.get("mes_em_andamento")),
            "periodo": {k: P.get(k) for k in ("mes_atual", "mes_anterior", "mesmo_mes_ano_anterior", "janela_l3m", "janela_base_ativa", "aviso_mes_em_andamento")},
            "kpi": {s["id"]: s["kpi"] for s in JF["segmentos"]},
            "calendario": {pp: {k: (JF.get("calendario") or {}).get(pp, {}).get(k) for k in ("ano", "rotulo_curto", "rotulo_anterior_curto", "rotulo_longo", "periodo", "n_meses", "completo")}
                           for pp in ("fiscal", "civil")},   # Refino E4a: rotulos do ano do mes
            "tabelas": tab, "rtm": {"rk": rk, "corte": rt.get("corte") or {}},
            "carteira": json.loads(str(cart.get("json") or "{}").replace("<\\/", "</")) if cart.get("ativo") else {}}


def comprimidos(JF: dict, extras: list[dict] | None = None) -> str:
    """{est: pacote das tabelas fixas, meses: [{id, rotulo, parcial, b64}]}; o primeiro mes e o de referencia (parcial, quando ha)."""
    T = tabelas(JF)
    meses = [JF] + list(extras or [])
    carga = {"est": _gz({k: _cols(T[k]) for k in EST_TABELAS}),
             "meses": [{"id": str(x["meta_execucao"]["mes_referencia"]), "rotulo": str(x["periodo"]["mes_atual"]),
                        "parcial": bool(x["periodo"].get("mes_em_andamento")), "b64": _gz(pacote_mes(x))} for x in meses]}
    return _json(carga)


def gerar(JF: dict) -> dict[str, str]:
    """{id da tabela: JSON pronto para `{{{tabelas_json.<id>}}}`}."""
    return {k: _json(v) for k, v in tabelas(JF).items()}


def cfg_json() -> str:
    """Parâmetros do componente (config painel.tabela) para `{{{tabela_cfg_json}}}`."""
    t = CFG["painel"]["tabela"]
    return _json({"amostra_linhas": int(t["amostra_linhas"]), "debounce_ms": int(t["debounce_ms"]),
                  "expandir_passo": int(t["expandir_passo"]), "expandir_maximo": int(t["expandir_maximo"])})
