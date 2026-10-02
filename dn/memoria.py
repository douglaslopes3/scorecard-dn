# -*- coding: utf-8 -*-
"""F10 (RN-49) · Memória de cálculo por número.

Cada número de card, cada coluna ligada das tabelas e as colunas de oportunidade linha a linha abrem uma FICHA declarada no
config (`painel.memoria.fichas[]`): indicador, RN, período, fórmula, parcelas, conta (t e R$; soma nos níveis acima do
distribuidor), conferência aritmética, fonte e nota. O navegador (motor `dnMem*`) monta a ficha com os números do recorte
ativo; aqui as mesmas fichas são (1) avaliadas no recorte do canal — o esperado que o navegador usa para se conferir —,
(2) conferidas contra os dados crus do painel na etapa 4 e (3) empacotadas no JSON embutido, com o extrato das RN citadas
lido de docs/regras_negocio.md.

Nenhum texto, fórmula ou rótulo vive aqui: tudo vem do config. Só existem as OPERAÇÕES das conferências (`confere`):
div100 a÷b×100=r · sub a−b=r · div a×k÷b=r · mul a×b×k=r · mul3 a×b×c×k=r · gap max(0,b−p)×n÷100=r.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from . import resumos
from .extract import cadastros
from .utils.config import CFG
from .utils.log import abortar

RAIZ = Path(__file__).resolve().parents[1]
DICIONARIO = RAIZ / "docs" / "regras_negocio.md"
OPS = ("div100", "sub", "div", "mul", "mul3", "gap")
CTX_CAMPOS = ("janela", "mes", "mes_fechado", "janela_fator", "periodo")


# ----------------------------------------------------------------- config
def config() -> dict:
    return CFG["painel"].get("memoria") or {}


def fichas() -> list[dict]:
    return list(config().get("fichas") or [])


def rns_de(f: dict) -> list[str]:
    r = f.get("rn") or []
    return [str(x) for x in (r if isinstance(r, list) else [r])]


def parcelas(f: dict) -> list[str]:
    return [str(p) for p in (f.get("parcelas") or [])]


def checks(f: dict, met: str = "t") -> list[dict]:
    c = f.get("confere_rs") if (met == "rs" and f.get("confere_rs") is not None) else f.get("confere")
    if not c or c == "nenhuma":
        return []
    return [x for x in (c if isinstance(c, list) else [c]) if isinstance(x, dict)]


def ligacoes(fs: list[dict]) -> dict:
    """{'col': {'tabela.coluna': ficha}, 'alvo': {'card:x' | 'pen:x' | 'rtm:x': ficha}}; coluna ligada a duas fichas aborta."""
    col, alvo = {}, {}
    for f in fs:
        for l in f.get("liga") or []:
            tipo, _, chave = str(l).partition(":")
            if tipo == "col":
                if chave in col:
                    abortar(f"painel.memoria: a coluna '{chave}' está ligada a duas fichas ({col[chave]} e {f['id']})")
                col[chave] = f["id"]
            elif tipo in ("card", "pen", "rtm"):
                alvo[str(l)] = f["id"]
            else:
                abortar(f"painel.memoria.fichas[{f['id']}].liga: tipo '{tipo}' desconhecido (card, pen, rtm, col)")
    return {"col": col, "alvo": alvo}


# ----------------------------------------------------------------- conferência aritmética (dados crus)
def _num(v):
    v = resumos._num(v)
    return None if isinstance(v, str) else v


def calcula(ch: dict, row: dict):
    """(recalculado, resultado) da conferência `ch` sobre a linha; (None, None) se falta parcela ou o denominador é zero."""
    op = ch.get("op")
    if op not in OPS:
        abortar(f"painel.memoria: operação de conferência '{op}' desconhecida ({', '.join(OPS)})")
    g = lambda k: None if ch.get(k) is None else _num(row.get(ch[k]))
    k = float(ch.get("k", 1)); r = g("r")
    a, b, c = g("a"), g("b"), g("c")
    try:
        if op == "div100":
            calc = None if a is None or not b else a / b * 100
        elif op == "sub":
            calc = None if a is None or b is None else a - b
        elif op == "div":
            calc = None if a is None or not b else a * k / b
        elif op == "mul":
            calc = None if a is None or b is None else a * b * k
        elif op == "mul3":
            calc = None if None in (a, b, c) else a * b * c * k
        else:   # gap
            bb, p, n = g("b"), g("p"), g("n")
            calc = None if None in (bb, p, n) else max(0.0, bb - p) * n / 100
    except ZeroDivisionError:
        calc = None
    return (None, None) if calc is None or r is None else (calc, r)


def agregada(f: dict, row: dict) -> bool:
    """Linha de nível acima do distribuidor numa ficha que tem conta de soma: a conferência de grão não se aplica."""
    return bool(f.get("conta_soma")) and bool(row.get("nivel")) and row.get("nivel") != "distribuidor"


def confere_linha(f: dict, row: dict, met: str = "t", tol_rel: float = 1e-6, tol_abs: float = 1e-6) -> list[str]:
    if agregada(f, row):
        return []
    difs = []
    for ch in checks(f, met):
        calc, r = calcula(ch, row)
        if calc is None:
            continue
        if abs(calc - r) > max(tol_abs, abs(r) * tol_rel):
            difs.append(f"{f['id']} {ch['op']} → {ch.get('r')}: recalculado {calc:.6g} x {r:.6g}")
    return difs


# ----------------------------------------------------------------- extrato das RN (docs/regras_negocio.md)
def _limpa(s: str) -> str:
    return re.sub(r"\s+", " ", s.replace("\\|", "|").replace("**", "").replace("`", "")).strip()


def dicionario() -> dict:
    if not DICIONARIO.exists():
        abortar(f"painel.memoria.extrato_rn: dicionário de regras não encontrado em {DICIONARIO}")
    blocos = re.split(r"\n### (RN-\d+) · ", DICIONARIO.read_text(encoding="utf-8"))
    out = {}
    for i in range(1, len(blocos), 2):
        rid, corpo = blocos[i], blocos[i + 1]

        def campo(n):
            m = re.search(r"^\| " + re.escape(n) + r" \| (.*?) \|\s*$", corpo, re.M)
            return _limpa(m.group(1)) if m else ""
        out[rid] = {"id": rid, "titulo": _limpa(corpo.split("\n", 1)[0]), "objetivo": campo("Objetivo"), "definicao": campo("Definição"),
                    "formula": campo("Fórmula"), "campos": campo("Campos usados"), "status": campo("Status")}
    return out


def rns_citadas() -> list[str]:
    ids = []
    for f in fichas():
        for x in rns_de(f):
            if x not in ids:
                ids.append(x)
    return sorted(ids, key=lambda s: int(s.split("-")[1]))


# ----------------------------------------------------------------- fontes
def fontes() -> dict:
    rot = config().get("fontes_rotulos") or {}
    out = {}
    for k, v in (CFG.get("fontes") or {}).items():
        if k == "hierarquia":                   # 02/10/2026: o arquivo vigente (data mais recente no nome)
            arq = cadastros.arquivo_hierarquia().name
        else:
            arq = v.get("arquivo") or (str(v.get("pasta", "")).rstrip("/") + "/" + ", ".join(v.get("padroes_aceitos") or []))
        out[k] = {"rotulo": str(rot.get(k, k)), "arquivo": str(arq)}
    return out


# ----------------------------------------------------------------- linhas do recorte do canal
def rtm_linha(J: dict, cru: bool = False) -> dict:
    R = J.get("rtm") or {}; k = R.get("kpi") or {}
    base = {"certo": k.get("certo"), "rastreaveis": R.get("rastreaveis"), "pct_aderencia": k.get("pct_aderencia"), "so_outro": k.get("so_outro"),
            "sem_compra": k.get("sem_compra"), "ativados": k.get("ativados"), "ativados_parados": k.get("ativados_parados"),
            "ativados_mig": k.get("ativados_mig"), "ativados_parados_mig": k.get("ativados_parados_mig")}
    if cru:
        return base
    return {c: resumos.fmt(c + ("_pct" if c.startswith("pct") else "_n"), _num(v)) for c, v in base.items()}


def _cru(v):
    v = _num(v)
    return None if v is None else float(v)


def esperado(J: dict) -> dict:
    """Valores crus das parcelas no recorte do canal, por ficha e alvo: '<id>|canal' (cards da Visão geral, segmento todos),
    '<id>|canal|<cat_id>' (cards da Penetração no canal) e '<id>|rtm'. O navegador compara a tela com isto sem filtros."""
    kpi = next(s for s in J["segmentos"] if s["id"] == "todos")["kpi"]
    canal = [x for x in J.get("pen_nivel_cat") or [] if x.get("nivel") == "canal"]
    rtm = rtm_linha(J, cru=True)
    E = {}
    for f in fichas():
        alvos = {str(l).split(":")[0] for l in f.get("liga") or []}
        ps = parcelas(f)
        if "card" in alvos:
            E[f"{f['id']}|canal"] = {"valores": {p: _cru(kpi.get(p)) for p in ps if p in kpi}, "difs": confere_linha(f, kpi)}
        if "pen" in alvos:
            for r in canal:
                E[f"{f['id']}|canal|{r['cat_id']}"] = {"valores": {p: _cru(r.get(p)) for p in ps if p in r}, "difs": confere_linha(f, r)}
        if "rtm" in alvos:
            E[f"{f['id']}|rtm"] = {"valores": {p: _cru(rtm.get(p)) for p in ps if p in rtm}, "difs": confere_linha(f, rtm)}
    return E


# ----------------------------------------------------------------- textos
def lint_textos() -> list[str]:
    """Termos vetados dos resumos (RN-48) nos textos das fichas; o rótulo obrigatório do potencial (RN-35) é permitido."""
    vet = [str(x) for x in ((CFG["painel"].get("resumos") or {}).get("termos_vetados") or [])]
    aviso = str(((CFG.get("regras") or {}).get("potencial") or {}).get("aviso", "")).lower()
    achados = []
    M = config()
    textos = [("textos", json.dumps(M.get("textos") or {}, ensure_ascii=False))]
    for f in fichas():
        textos.append((f["id"], " ".join(str(f.get(k, "")) for k in ("titulo", "indicador", "formula", "conta", "conta_rs", "conta_soma", "conta_soma_rs", "nota"))))
    for nome, txt in textos:
        t = txt.lower().replace(aviso, " ") if aviso else txt.lower()
        for w in vet:
            if re.search(r"\b" + re.escape(w.lower()) + r"\b", t):
                achados.append(f"{nome}: '{w}'")
    return achados


# ----------------------------------------------------------------- bloco do painel
def bloco(J: dict) -> dict:
    M = config(); fs = fichas()
    if not M.get("ativo"):
        return {"ativo": False, "marca": "", "n_fichas": 0, "n_rn": 0, "json": "{}", "rns": [], "texto_definicoes": ""}
    marca = str(M.get("marca", "ⓘ"))
    dic = dicionario(); cit = rns_citadas()
    faltam = [x for x in cit if x not in dic]
    if faltam:
        abortar(f"painel.memoria: RN citada(s) nas fichas e ausente(s) do dicionário: {', '.join(faltam)}")
    rns = [dic[x] for x in cit] if M.get("extrato_rn", True) else []
    P = J["periodo"]; PEN = J.get("penetracao") or {}; CAL = J.get("calendario") or {}
    ctx = {"mes": P.get("mes_atual"), "mes_fechado": PEN.get("competencia"), "janela": P.get("janela_base_ativa"),
           "janela_fator": PEN.get("janela_fator"), "periodo_fiscal": (CAL.get("fiscal") or {}).get("rotulo_longo"),
           "periodo_civil": (CAL.get("civil") or {}).get("rotulo_longo")}
    textos = dict(M.get("textos") or {})
    textos["coluna"] = str(textos.get("coluna", "")).replace("{marca}", marca)
    carga = {"ativo": True, "marca": marca, "copiar": bool(M.get("copiar", True)), "tol": M.get("tolerancia") or {"abs": 0.06, "rel": 0.5},
             "por_linha": list((M.get("tabelas") or {}).get("por_linha") or []), "por_coluna": bool((M.get("tabelas") or {}).get("por_coluna", True)),
             "textos": textos, "ctx": ctx, "fichas": fs, "lig": ligacoes(fs), "rn": {r["id"]: r for r in rns}, "fontes": fontes(),
             "esperado": esperado(J), "rtm": rtm_linha(J)}
    return {"ativo": True, "marca": marca, "n_fichas": len(fs), "n_rn": len(rns),
            "json": json.dumps(carga, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/"),
            "rns": [{k: r[k] for k in ("id", "titulo", "objetivo", "definicao", "formula")} for r in rns],
            "texto_definicoes": str(textos.get("definicoes", "")).replace("{marca}", marca)}
