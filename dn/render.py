# -*- coding: utf-8 -*-
"""Renderização do painel: formatação pt-BR pelo inventário e um Handlebars
mínimo em Python (each / if @first / else / ../ / caminhos com ponto / {{{ }}}),
validado byte a byte contra `template/Scorecard_DN_base.html` (ver `validar_renderer`).

Contrato: `template/data-inventory.json` diz o `formato` de cada campo; os
valores chegam ao template já formatados (regras em docs/regras_negocio.md; o business-rules.md do protótipo está em _obsoleto/template).
Campo fora do inventário passa sem formatar e é listado em `fora_do_inventario()`
para o orquestrador avisar (D9 da reforma: o inventário é o único contrato).
"""
from __future__ import annotations

import base64
import gzip
import json
import re
from pathlib import Path

from .utils.config import PASTA_TEMPLATE

TEMPLATE_DIR = PASTA_TEMPLATE

# ----------------------------------------------------------------- formatação
LIST_ENTITY = {"categorias": "categoria", "segmentos": "segmento", "clusters": "segmento.cluster",
               "supervisores": "segmento.supervisor", "distribuidores": "distribuidor", "pdvs": "pdv",
               "abas": "aba"}

_FORA: set[str] = set()


def inventario() -> dict[str, dict]:
    inv = json.loads((TEMPLATE_DIR / "data-inventory.json").read_text(encoding="utf-8"))
    return {e["path"]: e for e in inv}


def fora_do_inventario() -> list[str]:
    return sorted(_FORA)


def fmt_num(v: float, dec: int) -> str:
    return f"{abs(v):,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt(v, formato: str):
    if v is None or v == "" or (isinstance(v, float) and v != v):
        return "—"
    f = formato
    if f == "sim/não":
        return "sim" if v else "não"
    if isinstance(v, str):
        return v
    if f.startswith("R$ #,# mi"):          # F1 (A.5): cards de valor, em R$ milhoes com 1 decimal
        return ("−" if v < 0 else "") + "R$ " + fmt_num(v, 1) + " mi"
    if f.startswith("+0,0 p.p."):
        return ("+" if v >= 0 else "−") + fmt_num(v, 1) + " p.p."
    if f.startswith("+0,0%"):
        return ("+" if v >= 0 else "−") + fmt_num(v, 1) + "%"
    if f.startswith("0,0%"):
        return fmt_num(v, 1) + "%"
    if f.startswith("#.##0,00"):
        return ("−" if v < 0 else "") + fmt_num(v, 2)
    if f.startswith("#.##0,0"):
        return ("−" if v < 0 else "") + fmt_num(v, 1)
    if f.startswith("#.##0") or f == "0":
        return ("−" if v < 0 else "") + fmt_num(v, 0)
    return str(v)


def formatar(obj, prefix: str, inv: dict[str, dict]):
    """Aplica `formato` do inventário a cada folha; séries "(bruto)" seguem
    numéricas; campo fora do inventário fica como está e é registrado."""
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            path = k if prefix == "" else prefix + "." + k
            if isinstance(v, list):
                ent = LIST_ENTITY.get(k, path)
                out[k] = [formatar(it, ent, inv) for it in v]
            elif isinstance(v, dict):
                out[k] = formatar(v, path, inv)
            else:
                meta = inv.get(path)
                if meta is None:
                    # metricas e comparativos tem o mesmo formato em todos os niveis:
                    # o campo homonimo do distribuidor (ou do pdv) vale como contrato
                    meta = inv.get("distribuidor." + k) or inv.get("pdv." + k)
                if meta is None:
                    _FORA.add(path)
                    out[k] = v
                elif "bruto" in meta["formato"]:
                    out[k] = _raw(v)
                else:
                    out[k] = fmt(v, meta["formato"])
        return out
    return obj


def _raw(v):
    if v is None or (isinstance(v, float) and v != v):
        return None
    if isinstance(v, float) and v.is_integer():
        return int(v)
    return v


# ------------------------------------------------------------ mini-handlebars
_TOK = re.compile(r"\{\{\{\s*([^}]*?)\s*\}\}\}|\{\{(#each|/each|#if|/if|else)?\s*([^}]*?)\s*\}\}")


class _Node:
    def __init__(self, kind, arg=None):
        self.kind, self.arg, self.body, self.alt = kind, arg, [], []


def _parse(tpl: str) -> list:
    root = _Node("root")
    stack = [root]
    cur_list = lambda: (stack[-1].alt if getattr(stack[-1], "_in_else", False) else stack[-1].body)
    pos = 0
    for m in _TOK.finditer(tpl):
        if m.start() > pos:
            cur_list().append(("text", tpl[pos:m.start()]))
        if m.group(1) is not None:                    # {{{x}}}: sem escape HTML
            cur_list().append(("raw", m.group(1)))
            pos = m.end()
            continue
        kind, arg = m.group(2), m.group(3)
        if kind == "#each":
            n = _Node("each", arg); cur_list().append(("node", n)); stack.append(n)
        elif kind == "#if":
            n = _Node("if", arg); cur_list().append(("node", n)); stack.append(n)
        elif kind == "else":
            stack[-1]._in_else = True
        elif kind in ("/each", "/if"):
            stack.pop()
        else:
            cur_list().append(("var", arg))
        pos = m.end()
    if pos < len(tpl):
        cur_list().append(("text", tpl[pos:]))
    return root.body


def _escape(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
             .replace("'", "&#x27;").replace("`", "&#x60;").replace("=", "&#x3D;"))


def _to_text(v) -> str:
    if v is None or v is False:
        return ""
    if v is True:
        return "true"
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def _lookup(path: str, stack: list, first: list):
    depth = 0
    while path.startswith("../"):
        path = path[3:]; depth += 1
    ctx = stack[-1 - depth]
    if path == "@first":
        return first[-1 - depth]
    if path in ("this", "."):
        return ctx
    cur = ctx
    for part in path.split("."):
        cur = cur.get(part) if isinstance(cur, dict) else None
        if cur is None:
            return None
    return cur


def _render(nodes, stack, first, out: list) -> None:
    for kind, val in nodes:
        if kind == "text":
            out.append(val)
        elif kind == "var":
            out.append(_escape(_to_text(_lookup(val, stack, first))))
        elif kind == "raw":
            out.append(_to_text(_lookup(val, stack, first)))
        else:
            n = val
            if n.kind == "each":
                items = _lookup(n.arg, stack, first) or []
                for i, it in enumerate(items):
                    _render(n.body, stack + [it], first + [i == 0], out)
            elif n.kind == "if":
                cond = _lookup(n.arg, stack, first)
                _render(n.body if cond else n.alt, stack, first, out)


def render(tpl: str, data: dict) -> str:
    out: list[str] = []
    _render(_parse(tpl), [data], [False], out)
    return "".join(out)


def preparar(JF: dict, extras: list[dict] | None = None) -> dict:
    """Acrescenta ao JSON formatado o que o template emite cru ({{{ }}}): os dados
    de cada tabela e os parametros do componente (Fase 3). Refino E4a: `extras` = JSON formatado de outros meses do arquivo
    (o mes fechado, quando o de referencia esta em andamento); as tabelas do mes e as fixas vao comprimidas."""
    from . import tabelas
    JF["tabelas_json"] = tabelas.gerar(JF)
    JF["tabela_cfg_json"] = tabelas.cfg_json()
    JF["dados_comprimidos_json"] = tabelas.comprimidos(JF, extras)
    return JF


def template() -> str:
    return (TEMPLATE_DIR / "template.html").read_text(encoding="utf-8")


def validar_renderer() -> bool:
    """Prova de paridade: template + example-data.json == Scorecard_DN_base.html."""
    data = json.loads((TEMPLATE_DIR / "example-data.json").read_text(encoding="utf-8"))
    esperado = (TEMPLATE_DIR / "Scorecard_DN_base.html").read_text(encoding="utf-8")
    return render(template(), data) == esperado


# ------------------------------------------------------- exemplo do template
def _blob_reduzido(blob: dict, n: int) -> dict:
    """Recompacta o blob de PDVs com só as primeiras `n` linhas."""
    raw = gzip.decompress(base64.b64decode(blob["b64"]))
    d = json.loads(raw.decode("utf-8"))
    chave = "rows" if "rows" in d else "linhas"
    d[chave] = d[chave][:n]
    novo = json.dumps(d, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    b64 = base64.b64encode(gzip.compress(novo, compresslevel=9)).decode("ascii")
    out = dict(blob); out.update({"n": len(d[chave]), "bytes_json": len(novo), "bytes_b64": len(b64), "b64": b64})
    return out


def exemplo_reduzido(J: dict, n_dist: int = 8, n_rtm: int = 40, n_blob: int = 200) -> dict:
    """Retrato do JSON real com as listas grandes encurtadas. Serve de prova do
    renderizador (byte a byte) sem carregar 6 MB de dados no repositório.
    Cada bloco do template continua exercitado (todas as listas ficam não vazias)."""
    E = json.loads(json.dumps(J))
    E["distribuidores"] = E["distribuidores"][:n_dist]
    if E.get("rtm"):
        E["rtm"]["clientes"] = E["rtm"]["clientes"][:n_rtm]
        if E["rtm"].get("blob", {}).get("b64"):
            E["rtm"]["blob"] = _blob_reduzido(E["rtm"]["blob"], n_blob)
    if E.get("pdv_blob", {}).get("b64"):
        E["pdv_blob"] = _blob_reduzido(E["pdv_blob"], n_blob)
    if E.get("pdv_blob_comb", {}).get("b64"):   # Refino E4a
        E["pdv_blob_comb"] = _blob_reduzido(E["pdv_blob_comb"], n_blob)
    E["meta_execucao"]["gerado_em"] = "exemplo"
    E["meta_execucao"]["execucao_id"] = "exemplo"
    return E


def regerar_exemplo(J: dict) -> Path:
    """Regrava example-data.raw.json, example-data.json e Scorecard_DN_base.html
    a partir do JSON real (D8). Depois disto `validar_renderer()` é verdadeiro
    por construção; a prova vale a partir da PRÓXIMA execução."""
    E = exemplo_reduzido(J)
    (TEMPLATE_DIR / "example-data.raw.json").write_text(json.dumps(E, ensure_ascii=False, indent=1), encoding="utf-8")
    EF = preparar(formatar(E, "", inventario()))
    (TEMPLATE_DIR / "example-data.json").write_text(json.dumps(EF, ensure_ascii=False, indent=1), encoding="utf-8")
    alvo = TEMPLATE_DIR / "Scorecard_DN_base.html"
    alvo.write_text(render(template(), EF), encoding="utf-8")
    return alvo
