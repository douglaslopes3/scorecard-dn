# -*- coding: utf-8 -*-
"""F9 (RN-48) · Resumos executivos dinâmicos — avaliador em Python.

Cada frase é uma regra declarada em `painel.resumos.regras[]` (config). O navegador avalia as mesmas regras sobre as
tabelas embutidas e os filtros ativos (motor `dnRs*` no template); aqui elas são avaliadas uma vez, no recorte do canal
(sem filtros, métrica t), para (1) gravar o esperado no JSON — o navegador confere a si mesmo contra ele — e (2) a
validação da etapa 4 comparar cada aba com um recálculo independente na curated.

Nenhum texto ou limiar vive aqui: tipo, texto, limiar e link vêm do config. Só existem as OPERAÇÕES (um tipo = uma
função), que selecionam, ordenam e comparam números já calculados pelo pipeline.
"""
from __future__ import annotations

import json
import re

import numpy as np
import pandas as pd

from .utils.config import CFG
from .utils.log import abortar, log


def config() -> tuple[list[dict], bool, list[str]]:
    R = CFG["painel"].get("resumos") or {}
    return list(R.get("regras") or []), bool(R.get("ativo", False)), [str(x) for x in (R.get("termos_vetados") or [])]


# ----------------------------------------------------------------- utilidades
def _num(x):
    if x is None:
        return None
    if isinstance(x, str):
        return x
    try:
        if pd.isna(x):
            return None
    except (TypeError, ValueError):
        pass
    return float(x)


def _fnum(x: float, d: int) -> str:
    return f"{abs(x):,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt(campo: str, v, met: str = "t") -> str:
    """Formata pelo SUFIXO do nome do campo — a mesma convenção do motor JS (dnRsFmt)."""
    if v is None:
        return "—"
    if isinstance(v, str):
        return v
    s = campo.rsplit("_", 1)[-1]
    if s == "pct":
        return _fnum(v, 1) + "%"
    if s == "pp":
        return ("+" if v >= 0 else "−") + _fnum(v, 1) + " p.p."
    if s == "t":
        return ("−" if v < 0 else "") + _fnum(v, 1) + " t"
    if s == "rs":
        return ("−" if v < 0 else "") + "R$ " + _fnum(v, 0)
    if s == "m":
        return fmt("x_t" if met == "t" else "x_rs", v)
    if s == "dn":
        return ("+" if v >= 0 else "−") + _fnum(v, 0)
    if s == "dm":
        return ("+" if v >= 0 else "−") + (_fnum(v, 1) + " t" if met == "t" else "R$ " + _fnum(v, 0))
    if s == "n":
        return _fnum(v, 0)
    return _fnum(v, 2)


def frase(texto: str, vals: dict, met: str = "t") -> str:
    return re.sub(r"\{([a-z0-9_]+)\}", lambda m: fmt(m.group(1), vals.get(m.group(1)), met), texto)


def _limiar(reg: dict, vals: dict, met: str) -> bool | None:
    L = reg.get("limiar")
    if not L:
        return None
    v = vals.get(L["campo"])
    if v is None or isinstance(v, str):
        return False
    ref = L.get("valor")
    if ref is None:
        ref = L.get("valor_t") if met == "t" else L.get("valor_rs")
    op = str(L.get("op", ">="))
    return {">=": v >= ref, "<=": v <= ref, ">": v > ref, "<": v < ref}[op]


def _pt(serie: list[dict], mes: str) -> dict | None:
    for p in serie:
        if p.get("mes") == mes:
            return p
    return None


def _campo_met(campo, met: str):
    if isinstance(campo, dict):
        return campo["t"] if met == "t" else campo["rs"]
    return campo


# ----------------------------------------------------------------- operações
def _dn_mes(ctx, reg, met):
    k = ctx["kpi"]
    d1 = _num(k.get("pct_cobertura_var_mes_anterior")); dly = _num(k.get("pct_cobertura_var_ly"))
    return {"dn_pct": _num(k.get("pct_cobertura")), "d1_pp": d1, "dly_pp": dly if dly is not None else ctx["sem_ly"],
            "mes": ctx["mes"], "mes_ant": ctx["mes_ant"], "mes_ly": ctx["mes_ly"], "d1_abs": None if d1 is None else abs(d1)}


def _delta_serie_extremo(ctx, reg, met):
    fonte, campo = reg["fonte"], reg["campo"]
    items = {"distribuidores": ctx["dists"], "supervisores": ctx["sups"], "categorias": ctx["cats"]}[fonte]
    key = "cobertura_pdv" if campo == "pos" else ("volume_t" if met == "t" else "receita_rs")
    suf = "dn" if campo == "pos" else "dm"
    best = []
    for it in items:
        a, b = _pt(it.get("serie") or [], ctx["mes"]), _pt(it.get("serie") or [], ctx["mes_ant"])
        if a is None or b is None or _num(a.get(key)) is None or _num(b.get(key)) is None:
            continue
        best.append((float(a[key]) - float(b[key]), it.get("nome"), it.get("id")))
    if not best:
        return None
    best.sort(key=lambda x: x[0])
    mn, mx = best[0], best[-1]
    vals = {"mes": ctx["mes"], "mes_ant": ctx["mes_ant"], f"min_d_{suf}": mn[0], "min_nome": mn[1], "min_id": mn[2],
            f"max_d_{suf}": mx[0], "max_nome": mx[1], "max_id": mx[2], "ext_abs": max(abs(mn[0]), abs(mx[0])), "n_n": len(best)}
    if reg.get("incluir_kpi"):
        vals["cob_n"] = _num(ctx["kpi"].get("cobertura_pdv")); vals["cob_var_pct"] = _num(ctx["kpi"].get("cobertura_var_mes_anterior"))
    if reg.get("incluir_total"):
        a, b = _pt(ctx["serie_total"], ctx["mes"]), _pt(ctx["serie_total"], ctx["mes_ant"])
        vals["tot_d_dm"] = None if a is None or b is None else float(a[key]) - float(b[key])
    return vals


def _extremo(ctx, reg, met):
    rows = ctx["fontes"][reg["fonte"]]()
    campo = _campo_met(reg["campo"], met)
    filtro = reg.get("filtro") or {}
    cand = []
    for r in rows:
        if any(r.get(k) != v for k, v in filtro.items()):
            continue
        v = _num(r.get(campo))
        if v is None or isinstance(v, str):
            continue
        cand.append((v, r))
    piso = reg.get("piso") or {}
    if piso:   # F10 (Q6, Q7): piso de base — so entra quem tem base >= min (no proprio campo ou na serie, no mes de comparacao)
        def _base(r):
            if piso.get("campo"):
                return _num(r.get(piso["campo"]))
            p = _pt(r.get("serie") or [], ctx["mes"] if piso.get("mes") == "mes" else ctx["mes_ant"])
            return None if p is None else _num(p.get({"pos": "cobertura_pdv"}.get(piso["serie"], piso["serie"])))
        cand = [(v, r) for v, r in cand if (lambda b_: b_ is not None and not isinstance(b_, str) and b_ >= float(piso["min"]))(_base(r))]
    if not cand:
        return None
    cand.sort(key=lambda x: x[0])
    saida = reg.get("saida", "valor_n")
    nome_de = reg.get("nome", "nome")

    def _nome(r):
        if nome_de == "pen_sup":
            return f"{ctx['sup_nome'].get(r.get('sup_id'), r.get('sup_id'))} em {r.get('categoria')}"
        if nome_de == "pen_par":
            return f"{r.get('dist_nome') or ctx['sup_nome'].get(r.get('sup_id'), r.get('sup_id'))} × {r.get('categoria')}"
        return r.get(nome_de)

    def _extras(r, out, pref=""):
        for k, src in (reg.get("extras") or {}).items():
            out[pref + k] = _num(r.get(_campo_met(src, met)))
        for k in ("id", "cat_id", "sup_id", "dist_nome"):
            if k in r:
                out[pref + k] = r[k]

    vals = {"mes": ctx["mes"], "mes_ant": ctx["mes_ant"], "n_n": len(cand)}
    if reg.get("ambos"):
        mn, mx = cand[0], cand[-1]
        vals.update({"min_nome": _nome(mn[1]), f"min_{saida}": mn[0], "max_nome": _nome(mx[1]), f"max_{saida}": mx[0],
                     "ext_abs": max(abs(mn[0]), abs(mx[0]))})
        _extras(mn[1], vals, "min_"); _extras(mx[1], vals, "max_")
    else:
        r = cand[0] if reg.get("direcao", "max") == "min" else cand[-1]
        vals.update({"nome": _nome(r[1]), saida: r[0], "categoria": r[1].get("categoria")})
        _extras(r[1], vals)
        cmp_ = reg.get("comparar")
        if cmp_:
            ref = _num(ctx["kpi"].get(cmp_["kpi"]))
            vals[cmp_["saida"]] = ref
            vals[cmp_["dif"]] = None if ref is None else r[0] - ref
    return vals


def _pdv_sem_compra(ctx, reg, met):
    pb = ctx["pb"]
    if pb is None or not len(pb):
        return None
    sem = pb[pb["positivado_mes"] == 0]
    return {"mes": ctx["mes"], "n_sem_n": int(len(sem)), "n_base_n": int(len(pb)), "pct_pct": len(sem) / len(pb) * 100,
            "kg_t": float(sem["kg_janela"].fillna(0).sum()) / 1000, "rs_rs": float(sem["rs_janela"].fillna(0).sum())}


def _pdv_maior_sem_compra(ctx, reg, met):
    pb = ctx["pb"]
    if pb is None or not len(pb):
        return None
    sem = pb[pb["positivado_mes"] == 0]
    if not len(sem):
        return None
    r = sem.sort_values("kg_janela", ascending=False).iloc[0]
    return {"mes": ctx["mes"], "cnpj": str(r["COD_PDV"]), "nome": str(r.get("NOME_PDV") or ""), "dist": str(r.get("nome_dist") or ""),
            "kg_t": float(r["kg_janela"] or 0) / 1000, "rs_rs": float(r.get("rs_janela") or 0)}


def _pdv_concentracao(ctx, reg, met):
    pb = ctx["pb"]
    if pb is None or not len(pb):
        return None
    N = int(reg.get("n", 1000)); col = "kg_mes" if met == "t" else "rs_mes"
    v = pb[col].fillna(0).astype(float).sort_values(ascending=False).values
    tot = float(v.sum())
    if tot <= 0:
        return None
    k10 = max(1, int(len(v) * 0.10))
    return {"mes": ctx["mes"], "pct10_pct": float(v[:k10].sum()) / tot * 100, "pctN_pct": float(v[:N].sum()) / tot * 100,
            "N_n": N, "n_pares_n": int(len(v)), "n10_n": k10}


def _novos(ctx, reg, met):
    novos = [d for d in ctx["dists"] if d.get("segmento_id") == "novos"]
    kn = ctx["kpi_seg"].get("novos") or {}; kt = ctx["kpi_seg"].get("todos") or {}
    if not novos or not kn:
        return {"n_novos_n": 0, "pdvs_n": 0, "pct_pct": 0.0, "vol_m": 0.0, "mes": ctx["mes"]}
    pdvs = _num(kn.get("cobertura_pdv")) or 0; tot = _num(kt.get("cobertura_pdv")) or 0
    return {"mes": ctx["mes"], "n_novos_n": len(novos), "pdvs_n": pdvs, "pct_pct": (pdvs / tot * 100) if tot else None,
            "vol_m": _num(kn.get("volume_t")) if met == "t" else _num(kn.get("receita_rs"))}


def _abaixo_p75(ctx, reg, met):
    rows = ctx["fontes"]["pen_dist"]()
    foco = ctx["foco"]
    por = {}
    for r in rows:
        if r.get("cat_id") not in foco:
            continue
        pb_ = _num(r.get("pct_bench"))
        por.setdefault(r.get("dist_nome"), {})[r.get("cat_id")] = (pb_ is not None and pb_ < 100)
    if not por:
        return None
    n_um = sum(1 for d in por.values() if any(d.values()))
    n_q = sum(1 for d in por.values() if len(d) == len(foco) and all(d.values()))
    return {"n_dist_n": len(por), "n_um_n": n_um, "n_quatro_n": n_q, "n_foco_n": len(foco), "pct_quatro_pct": n_q / len(por) * 100, "mes": ctx["mes"]}


def _sem_venda_mes(ctx, reg, met):
    if not ctx["em_andamento"]:
        return "pular"
    lst = ctx["sem_venda"]
    return {"n_n": len(lst), "mes": ctx["mes"], "lista": ", ".join(lst[:6]) + (" …" if len(lst) > 6 else "")}


def _rtm_ultimos(ctx):
    s = ctx["rtm_serie"]
    return (s[-1] if s else None), (s[-2] if len(s) > 1 else None)


def _rtm_aderencia(ctx, reg, met):
    a, b = _rtm_ultimos(ctx)
    if a is None:
        return None
    pa = _num(a.get("pct_aderencia")); pb_ = None if b is None else _num(b.get("pct_aderencia"))
    return {"pct_pct": pa, "d1_pp": None if pa is None or pb_ is None else pa - pb_, "mes": a.get("mes"), "mes_ant": b.get("mes") if b else "—",
            "d1_abs": None if pa is None or pb_ is None else abs(pa - pb_)}


def _rtm_vazamento(ctx, reg, met):
    a, _ = _rtm_ultimos(ctx)
    if a is None:
        return None
    so = int(a.get("so_outro") or 0); rastr = int(a.get("certo") or 0) + so + int(a.get("sem_compra") or 0)
    return {"n_n": so, "rastr_n": rastr, "pct_pct": so / rastr * 100 if rastr else None, "kg_t": float(a.get("kg_outro") or 0) / 1000,
            "rs_rs": float(a.get("receita_outro_rs") or 0), "mes": a.get("mes")}


def _rtm_parados(ctx, reg, met):
    a, _ = _rtm_ultimos(ctx)
    if a is None:
        return None
    ativ = int(a.get("ativados_hist") or 0); par = ativ - int(a.get("certo") or 0)
    return {"parados_n": par, "ativados_n": ativ, "pct_pct": par / ativ * 100 if ativ else None, "mes": a.get("mes")}


TIPOS = {"dn_mes": _dn_mes, "delta_serie_extremo": _delta_serie_extremo, "extremo": _extremo, "pdv_sem_compra": _pdv_sem_compra,
         "pdv_maior_sem_compra": _pdv_maior_sem_compra, "pdv_concentracao": _pdv_concentracao, "novos": _novos, "abaixo_p75": _abaixo_p75,
         "sem_venda_mes": _sem_venda_mes, "rtm_aderencia": _rtm_aderencia, "rtm_vazamento": _rtm_vazamento, "rtm_parados": _rtm_parados}


# ----------------------------------------------------------------- avaliação no recorte do canal
def contexto(J: dict, pb_full: pd.DataFrame, foco_ids: list[str], sem_venda: list[str]) -> dict:
    P = J["periodo"]; seg0 = J["segmentos"][0]
    pnc = J["pen_nivel_cat"]
    sup_nome = {s["id"]: s["nome"] for s in J.get("supervisores_lista", [])}
    ctx = {"mes": P["mes_atual"], "mes_ant": P["mes_anterior"], "mes_ly": P["mesmo_mes_ano_anterior"],
           "sem_ly": str((CFG["painel"].get("textos") or {}).get("resumo_sem_ly", "sem LY na série")),
           "kpi": seg0["kpi"], "kpi_seg": {s["id"]: s["kpi"] for s in J["segmentos"]},
           "dists": J["distribuidores"], "sups": seg0["supervisores"], "cats": J["categorias"], "clusters": seg0["clusters"],
           "serie_total": J["dn"]["serie"], "sup_nome": sup_nome, "foco": list(foco_ids),
           "rtm_serie": (J.get("rtm") or {}).get("serie") or [], "pb": pb_full,
           "em_andamento": bool(P.get("mes_em_andamento")), "sem_venda": list(sem_venda)}
    ctx["fontes"] = {
        "categorias": lambda: ctx["cats"], "clusters": lambda: ctx["clusters"], "supervisores": lambda: ctx["sups"],
        "distribuidores": lambda: ctx["dists"],
        "pen_canal": lambda: [x for x in pnc if x["nivel"] == "canal"],
        "pen_sup_foco": lambda: [x for x in pnc if x["nivel"] == "supervisor_canal" and x.get("foco")],
        "pen_dist": lambda: [x for x in pnc if x["nivel"] == "distribuidor"],
        "rtm_destinos": lambda: [d for d in ((J.get("rtm") or {}).get("destinos") or []) if d.get("coberto")],
    }
    ctx["J"] = J
    return ctx


def avaliar(J: dict, pb_full: pd.DataFrame, foco_ids: list[str], sem_venda: list[str], met: str = "t") -> list[dict]:
    regs, ativo, vet = config()
    out = []
    if not ativo:
        return out
    ctx = contexto(J, pb_full, foco_ids, sem_venda)
    for reg in regs:
        t = str(reg.get("tipo"))
        if t not in TIPOS:
            abortar(f"painel.resumos.regras[{reg.get('id')}]: tipo '{t}' desconhecido (tipos: {sorted(TIPOS)})")
        vals = TIPOS[t](ctx, reg, met)
        if vals == "pular":
            continue
        item = {"id": str(reg["id"]), "aba": str(reg["aba"]), "rn": str(reg.get("rn", "")), "indicador": str(reg.get("indicador", reg["id"])),
                "informativa": not reg.get("limiar")}
        if vals is None:
            item.update({"sem_dado": True, "valores": {}, "atencao": False, "frase": None})
        else:
            item.update({"sem_dado": False, "valores": {k: (v if isinstance(v, str) or v is None else float(v)) for k, v in vals.items()},
                         "atencao": bool(_limiar(reg, vals, met)), "frase": frase(str(reg["texto"]), vals, met)})
        out.append(item)
    return out


def lint_textos() -> list[str]:
    """Termos vetados (config) nos textos das regras: adjetivo, meta, previsão, culpa… (RN-48)."""
    regs, _, vet = config()
    achados = []
    for reg in regs:
        txt = " ".join(str(reg.get(k, "")) for k in ("texto", "indicador")).lower()
        for w in vet:
            if re.search(r"\b" + re.escape(w.lower()) + r"\b", txt):
                achados.append(f"{reg.get('id')}: '{w}'")
    return achados


def regras_json() -> str:
    regs, ativo, _ = config()
    return json.dumps({"ativo": ativo, "regras": regs}, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
