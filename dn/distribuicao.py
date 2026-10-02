# -*- coding: utf-8 -*-
"""Etapa 2 · um painel por usuario da hierarquia (aprovada pelo Douglas em 16/09/2026), no modelo dos Gerenciais
(`Dashboard - Gerencial/run_dashboard.py`: recorte fisico por nivel, pasta = rotulo `codigo - NOME` (02/10/2026), arquivo com
nome estavel `prefixo + nivel + _ + slug`).

Como funciona
  1. os usuarios sao descobertos dos distribuidores do painel (DIM_DISTRIBUIDOR: HEAD, GERENTE, SUPERVISOR) a cada execucao;
     nao existe lista de usuarios para manter;
  2. para cada usuario a FATO e recortada pelos distribuidores dele ANTES de qualquer cubo, JSON ou HTML — o que nao esta no
     recorte nao existe para o arquivo (seguranca no dado, nao na interface). O calculo, a montagem e o render sao os mesmos
     do canal (`metrics.calcular`, `pipeline.fechado`, `pipeline.gerar`);
  3. cada painel e validado (essencial + vazamento) e gravado na pasta local; so no fim os que passaram sao publicados,
     cada copia atomica e so quando o md5 muda;
  4. o Head (N1) recebe uma copia identica do painel do canal (Q4);
  5. falha em um usuario nao interrompe os demais (`distribuicao.em_erro`).

Regras aprovadas: Q1 referencia da Penetracao e a do canal (`c["pen_canal"]`); Q2 RTM do usuario so com clientes cujo destino
e um distribuidor dele; Q3 postos vagos tambem recebem painel; Q5 carteira so com pares do usuario, relatorio so no canal.
"""
from __future__ import annotations

import gzip
import base64
import hashlib
import json
import os
import re
import shutil
import time
import unicodedata
from pathlib import Path

import pandas as pd

from . import metrics, painel
from .utils import log as L
from .utils.config import CFG, PASTA_PAINEL, caminho
from .utils.log import log

_D = CFG.get("distribuicao") or {}
NIVEIS: dict[str, str] = dict(_D.get("niveis") or {"N1": "HEAD", "N2": "GERENTE", "N3": "SUPERVISOR"})
PREFIXO = str(_D.get("prefixo") or "Scorecard_DN_")
EM_ERRO = str(_D.get("em_erro") or "continuar").strip().lower()
if EM_ERRO not in ("continuar", "abortar_publicacao", "parar"):
    raise SystemExit(f"distribuicao.em_erro '{EM_ERRO}' invalido (continuar | abortar_publicacao | parar)")


# ------------------------------------------------------------------ nomes (iguais aos dos Gerenciais)
def slug(s: str) -> str:
    t = unicodedata.normalize("NFD", str(s))
    t = "".join(ch for ch in t if unicodedata.category(ch) != "Mn").lower()
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return t[:60]


def pasta_usuario(rotulo: str) -> str:
    """Pasta = rotulo completo, com os caracteres invalidos de pasta trocados por '-' (ex.: 'Superv_RS/SC' -> 'Superv_RS-SC')."""
    return re.sub(r'[<>:"/\\|?*]', "-", str(rotulo)).strip(" .")[:100]


def _partes(rotulo: str) -> tuple[str, str]:
    """('1120', 'CAIO LUPERNI') de '1120 - Superv_SPC - CAIO LUPERNI'."""
    p = [x.strip() for x in str(rotulo).split(" - ")]
    return (p[0] if p else ""), (p[-1] if len(p) > 1 else "")


# ------------------------------------------------------------------ usuarios
def usuarios(dist: pd.DataFrame) -> list[dict]:
    """Um registro por rotulo presente em cada nivel entre os distribuidores do painel."""
    ignorar = {str(x) for x in (_D.get("ignorar_rotulos") or [])}
    out = []
    for nivel, col in NIVEIS.items():
        if col not in dist.columns:
            raise SystemExit(f"distribuicao.niveis: coluna '{col}' nao existe em DIM_DISTRIBUIDOR ({list(dist.columns)})")
        for rot in sorted(dist[col].dropna().astype(str).unique()):
            if rot in ignorar or rot.upper().startswith("SEM "):
                continue
            dd = dist[dist[col].astype(str) == rot]
            cod, nome = _partes(rot)
            out.append({"nivel": nivel, "coluna": col, "rotulo": rot, "codigo": cod, "nome": nome, "slug": slug(rot),
                        "pasta": pasta_usuario(rot), "arquivo": f"{PREFIXO}{nivel}_{slug(rot)}.html",
                        "dists": sorted(dd["CNPJ_DISTRIBUIDOR"].astype(str)), "n_dist": int(len(dd))})
    return out


def _filtrar(lista: list[dict], filtro: str | None) -> list[dict]:
    if not filtro:
        return lista
    f = str(filtro).strip().lower()
    return [u for u in lista if f in u["rotulo"].lower() or f == u["codigo"].lower() or f == u["slug"]]


# ------------------------------------------------------------------ recorte
def recortar(c: dict, u: dict) -> dict:
    """`c` do usuario: fato e distribuidores so do recorte; codigos, pares e base ativa refeitos para o recorte (rapido: e um
    subconjunto). A referencia da Penetracao (`pen_canal`) e a do canal (Q1)."""
    dists = set(u["dists"])
    cu = {k: c[k] for k in ("pdv", "prod", "cal", "meses", "mes_ref", "freq_calib", "janela")}
    cu["dist"] = c["dist"][c["dist"]["CNPJ_DISTRIBUIDOR"].astype(str).isin(dists)].copy()
    f = c["fato"]
    cu["fato"] = f[f["DIST"].isin(dists).to_numpy()]
    cu["pen_canal"] = c["pen_canal"]
    cu["recorte"] = {"nivel": u["nivel"], "rotulo": u["rotulo"]}
    cu["recorte_nome"] = str(_D.get("rotulo_canal") or "{rotulo}").format(rotulo=u["rotulo"], nome=u["nome"], codigo=u["codigo"])
    metrics.preparar_codigos(cu)
    return cu


# ------------------------------------------------------------------ validacao por usuario
def _tokens_vazamento(u: dict, todos: list[dict], dist_all: pd.DataFrame) -> tuple[list[tuple[str, str]], list[str]]:
    """O que NAO pode aparecer no HTML do usuario: rotulos, nomes e slugs dos outros usuarios (fora os que estao acima dele na
    hierarquia dos proprios distribuidores? nao: nenhum outro rotulo aparece no painel), CNPJ e nome Mtrix dos distribuidores
    fora da carteira. Devolve (obrigatorios, so_aviso)."""
    meus = set(u["dists"])
    duros: list[tuple[str, str]] = []
    for o in todos:
        if o["rotulo"] == u["rotulo"]:
            continue
        if set(o["dists"]) >= meus or set(o["dists"]) <= meus:
            continue   # quem esta ACIMA (gerente/head do recorte) ou ABAIXO (supervisores do gerente) pertence ao recorte: nao e vazamento
        duros.append((f"rotulo {o['rotulo']}", o["rotulo"]))
        duros.append((f"slug {o['slug']}", o["slug"]))
        duros.append((f"id {metrics.slug(o['rotulo'])}", metrics.slug(o["rotulo"])))
        if o["nome"] and not o["nome"].startswith("[") and len(o["nome"]) >= 8:
            duros.append((f"nome {o['nome']}", o["nome"]))
        if o["codigo"]:
            duros.append((f"codigo {o['codigo']}", f"{o['codigo']} - "))
    fora = dist_all[~dist_all["CNPJ_DISTRIBUIDOR"].astype(str).isin(meus)]
    for r in fora.itertuples():
        duros.append((f"CNPJ {r.CNPJ_DISTRIBUIDOR}", str(r.CNPJ_DISTRIBUIDOR)))
        nm = str(r.DISTRIBUIDOR_MTRIX)
        if len(nm) >= 8:
            duros.append((f"distribuidor {nm}", nm))
    avisos = [str(x) for x in fora["NOME_REDUZIDO"].dropna().astype(str) if len(str(x)) >= 6]
    return duros, avisos


def validar_usuario(cu: dict, Tu: dict, Ju: dict, html: str, u: dict, todos: list[dict], dist_all: pd.DataFrame) -> tuple[dict, list[str]]:
    checks: dict[str, str] = {}
    erros: list[str] = []

    def ok(nome, cond, det):
        checks[nome] = ("ok" if cond else "FALHOU") + " · " + det
        if not cond:
            erros.append(f"{nome}: {det}")

    f, meses, mes_ref, jan = cu["fato"], cu["meses"], cu["mes_ref"], cu["janela"]
    ok("placeholders", html.count("{{") == 0, f"{html.count('{{')} '{{{{' no HTML")
    mb = len(html.encode("utf-8")) / 1024 / 1024
    ok("tamanho do HTML", mb <= float(CFG["validacao"]["html_max_mb"]), f"{mb:.1f} MB")
    k = Ju["segmentos"][0]["kpi"]
    pos = int(f[(f["PESO_KG"] > 0) & (f["ANO_MES"] == mes_ref)]["COD_PDV"].nunique())
    i = meses.index(mes_ref); janela = meses[max(0, i - jan + 1):i + 1]
    base = int(f[(f["PESO_KG"] > 0) & f["ANO_MES"].isin(janela)]["COD_PDV"].nunique()) if len(janela) == jan else None
    kg = float(f[f["ANO_MES"] == mes_ref]["PESO_KG"].sum()); rs = float(f[f["ANO_MES"] == mes_ref]["RECEITA"].sum())
    ok("card · positivados = fato do recorte", int(k["cobertura_pdv"] or 0) == pos, f"{k['cobertura_pdv']} = {pos:,}")
    ok("card · base ativa = fato do recorte", (k["base_ativa"] is None and base is None) or int(k["base_ativa"] or 0) == int(base or 0), f"{k['base_ativa']} = {base}")
    ok("card · volume = fato do recorte", abs(float(k["volume_t"] or 0) * 1000 - kg) < 0.5, f"{float(k['volume_t'] or 0):,.1f} t = {kg / 1000:,.1f} t")
    ok("card · valor = fato do recorte", abs(float(k["receita_rs"] or 0) - rs) <= float(CFG["validacao"]["tolerancia_receita_reais"]), f"R$ {float(k['receita_rs'] or 0):,.0f} = R$ {rs:,.0f}")
    cn = {d["cnpj"] for d in Ju["distribuidores"]}
    ok("distribuidores · so os do recorte", cn <= set(u["dists"]) and len(cn) <= u["n_dist"], f"{len(cn)} de {u['n_dist']} (todos na carteira)" if cn <= set(u["dists"]) else f"fora da carteira: {sorted(cn - set(u['dists']))[:3]}")
    ok("supervisores · so os do recorte", {s["id"] for s in Ju["supervisores_lista"]} == set(cu["dist"]["SUP_ID"].astype(str)), f"{len(Ju['supervisores_lista'])} no select")
    blob = json.loads(gzip.decompress(base64.b64decode(Ju["pdv_blob"]["b64"])).decode("utf-8"))
    ok("blob de PDVs = base ativa do recorte", len(blob["rows"]) == len(Tu["DN_PDV_BASE_ATIVA"]) == int(Ju["pdv_blob"]["n"]), f"{len(blob['rows']):,} pares")
    r = Ju["rtm"]; soma = int(r["kpi"]["certo"]) + int(r["kpi"]["so_outro"]) + int(r["kpi"]["sem_compra"])
    ok("RTM · estados = rastreaveis e sem nao mensuraveis", soma == int(r["rastreaveis"]) and int(r["nao_mensuravel"]) == 0, f"{soma} = {r['rastreaveis']} · nao mensuraveis {r['nao_mensuravel']}")
    dest_ok = set(Tu["DN_RTM_CLIENTE"]["DESTINO"].astype(str)) <= set(cu["dist"]["NOME_REDUZIDO"].astype(str))
    ok("RTM · destinos so do recorte", dest_ok, f"{int(r['base_total'])} clientes")
    # vazamento: nada de outro usuario nem de distribuidor fora da carteira no codigo-fonte
    duros, avisos = _tokens_vazamento(u, todos, dist_all)
    achados = [nome for nome, tok in duros if tok and tok in html]
    ok("vazamento · outros usuarios e distribuidores fora da carteira", not achados,
       f"{len(duros)} termos procurados, 0 ocorrencias" if not achados else f"ENCONTRADO: {achados[:6]}")
    ach_av = [x for x in avisos if re.search(r"(?<![A-Z0-9])" + re.escape(x) + r"(?![A-Z0-9])", html)]
    if ach_av:
        log(f"{u['rotulo']}: nome reduzido de distribuidor fora da carteira aparece como palavra no HTML (pode ser nome de PDV, so aviso): {ach_av[:5]}", "aviso")
    return checks, erros


# ------------------------------------------------------------------ geracao
def _md5(p: Path) -> str:
    h = hashlib.md5()
    with open(p, "rb") as fh:
        for bloco in iter(lambda: fh.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def gerar_usuario(c: dict, T: dict, u: dict, todos: list[dict], html_canal: str, pasta_local: Path) -> dict:
    from . import pipeline as P
    t0 = time.perf_counter()
    res = {"nivel": u["nivel"], "rotulo": u["rotulo"], "pasta": u["pasta"], "arquivo": u["arquivo"], "distribuidores": u["n_dist"]}
    if u["nivel"] == "N1":
        # Q4: o Head recebe o painel do canal, identico ao publicado em Painéis Comerciais/DN
        html = html_canal
        res.update({"linhas_fato": int(len(c["fato"])), "pdvs_base_ativa": int(len(T["DN_PDV_BASE_ATIVA"])), "checks": {"copia do canal": "ok"}, "erros": []})
    else:
        L.silencio(True)
        try:
            cu = recortar(c, u)
            Tu = metrics.calcular(cu)
            c2u, T2u = (P.fechado(cu, Tu) if metrics.mes_em_andamento(cu["mes_ref"]) else (None, None))
            Ju, JFu, html = P.gerar(cu, Tu, c2u, T2u)
        finally:
            L.silencio(False)
            painel._IX.clear()
        checks, erros = validar_usuario(cu, Tu, Ju, html, u, todos, c["dist"])
        res.update({"linhas_fato": int(len(cu["fato"])), "pdvs_base_ativa": int(len(Tu["DN_PDV_BASE_ATIVA"])), "checks": checks, "erros": erros,
                    "canal_mes": Tu["DN_CANAL_MES"][["ANO_MES", "positivados", "volume_kg", "receita_rs", "atendimentos"]],
                    "canal_cat_mes": Tu["DN_CANAL_CAT_MES"][["ANO_MES", "CAT", "volume_kg", "receita_rs"]]})
        if bool(_D.get("gravar_json")):
            (pasta_local / u["slug"]).mkdir(parents=True, exist_ok=True)
            (pasta_local / u["slug"] / "painel_dn.json").write_text(json.dumps(JFu, ensure_ascii=False, indent=1), encoding="utf-8")
    alvo = pasta_local / u["slug"] / u["arquivo"]
    alvo.parent.mkdir(parents=True, exist_ok=True)
    alvo.write_text(html, encoding="utf-8")
    res.update({"html": str(alvo), "bytes": alvo.stat().st_size, "md5": _md5(alvo), "segundos": round(time.perf_counter() - t0, 1)})
    return res


def conferir_somas(resultados: list[dict], T: dict) -> tuple[dict, list[str]]:
    """Validacao 1 da Etapa 2: kg, R$ e NFs dos usuarios de um nivel somam o canal, mes a mes e por categoria. PDVs distintos nao
    somam (o mesmo PDV atendido por dois supervisores conta uma vez no canal): conferidos por recalculo na fato de cada usuario."""
    checks: dict[str, str] = {}; erros: list[str] = []
    tol_kg = float(CFG["validacao"]["tolerancia_peso_kg"]); tol_rs = float(CFG["validacao"]["tolerancia_receita_reais"])
    canal = T["DN_CANAL_MES"].set_index("ANO_MES"); ccat = T["DN_CANAL_CAT_MES"].set_index(["ANO_MES", "CAT"])
    for nivel in ("N2", "N3"):
        rs_ = [r for r in resultados if r["nivel"] == nivel and "canal_mes" in r and not r["erros"]]
        if not rs_:
            continue
        faltam = [r["rotulo"] for r in resultados if r["nivel"] == nivel and r["erros"]]
        if faltam:
            checks[f"soma {nivel} = canal"] = f"nao conferida · {len(faltam)} usuario(s) do nivel com erro: {faltam[:3]}"
            log(f"soma {nivel} = canal: nao conferida ({len(faltam)} usuario(s) do nivel com erro)", "aviso")
            continue
        soma = pd.concat([r["canal_mes"] for r in rs_]).groupby("ANO_MES")[["volume_kg", "receita_rs", "atendimentos"]].sum()
        j = soma.join(canal[["volume_kg", "receita_rs", "atendimentos", "positivados"]], rsuffix="_canal", how="outer").fillna(0)
        dkg = float((j["volume_kg"] - j["volume_kg_canal"]).abs().max()); drs = float((j["receita_rs"] - j["receita_rs_canal"]).abs().max())
        dat = float((j["atendimentos"] - j["atendimentos_canal"]).abs().max())
        pmax = pd.concat([r["canal_mes"] for r in rs_]).groupby("ANO_MES")["positivados"].agg(["max", "sum"]).join(canal["positivados"])
        pdv_ok = bool(((pmax["max"] <= pmax["positivados"]) & (pmax["positivados"] <= pmax["sum"])).all())
        sc = pd.concat([r["canal_cat_mes"] for r in rs_]).groupby(["ANO_MES", "CAT"])[["volume_kg", "receita_rs"]].sum()
        jc = sc.join(ccat[["volume_kg", "receita_rs"]], rsuffix="_canal", how="outer").fillna(0)
        dkgc = float((jc["volume_kg"] - jc["volume_kg_canal"]).abs().max())
        cond = dkg <= tol_kg and drs <= tol_rs and dat <= 0.01 and dkgc <= tol_kg and pdv_ok
        nome = f"soma {nivel} = canal"
        checks[nome] = ("ok" if cond else "FALHOU") + f" · {len(rs_)} usuarios x {len(soma)} meses: kg dif {dkg:.3f} · R$ dif {drs:.2f} · NFs dif {dat:.4f} · kg por categoria dif {dkgc:.3f} · PDVs: max <= canal <= soma {'ok' if pdv_ok else 'FALHOU'}"
        if not cond:
            erros.append(checks[nome])
        log(f"{nome:<34} {checks[nome][5:]}", "ok" if cond else "erro")
    return checks, erros


# ------------------------------------------------------------------ publicacao
def publicar_usuario(res: dict, destino_base: Path) -> dict:
    pasta = destino_base / res["pasta"]
    if not pasta.exists():
        if bool(_D.get("criar_pasta", True)):
            pasta.mkdir(parents=True, exist_ok=True)
            log(f"{res['rotulo']}: pasta criada em {pasta}", "aviso")
        else:
            res["publicacao"] = "erro: pasta inexistente"; res["erros"].append(f"pasta inexistente: {pasta}")
            return res
    origem = Path(res["html"]); destino = pasta / res["arquivo"]
    if destino.exists() and bool((CFG.get("publicacao") or {}).get("pular_se_identico", True)) and destino.stat().st_size == origem.stat().st_size \
            and _md5(destino) == res["md5"]:
        res["publicacao"] = "sem mudanca"; res["destino"] = str(destino)
        return res
    tmp = pasta / (res["arquivo"] + ".tmp")
    shutil.copyfile(origem, tmp)
    os.replace(tmp, destino)
    if _md5(destino) != res["md5"]:
        res["publicacao"] = "erro: md5 divergente apos a copia"; res["erros"].append(f"md5 divergente em {destino}")
        return res
    res["publicacao"] = "publicado"; res["destino"] = str(destino)
    return res


# ------------------------------------------------------------------ orquestracao
def executar(c: dict, T: dict, html_canal: str, sem_publicar: bool, filtro: str | None = None) -> dict:
    L.etapa_inicio("6 · distribuir (um painel por usuario)")
    todos = usuarios(c["dist"])
    lista = _filtrar(todos, filtro)
    if not lista:
        log(f"nenhum usuario casa com '{filtro}' (rotulos: {[u['rotulo'] for u in todos][:5]}...)", "erro")
        L.etapa_fim("erro", motivo="filtro sem usuario")
        return {"usuarios": [], "erros": [f"filtro sem usuario: {filtro}"]}
    pasta_local = PASTA_PAINEL / "usuarios"
    destino_base = caminho(_D.get("destino") or "../../../Painéis Comerciais/Gerencial")
    log(f"{len(lista)} de {len(todos)} usuario(s) ({', '.join(f'{k}: {sum(1 for u in todos if u['nivel'] == k)}' for k in NIVEIS)}) · "
        f"local {pasta_local} · destino {destino_base} · em_erro {EM_ERRO}")
    resultados: list[dict] = []
    for u in lista:
        try:
            res = gerar_usuario(c, T, u, todos, html_canal, pasta_local)
        except (Exception, SystemExit) as e:   # abortar() dentro do calculo do usuario vira erro do usuario, nao do pipeline
            res = {"nivel": u["nivel"], "rotulo": u["rotulo"], "pasta": u["pasta"], "arquivo": u["arquivo"], "distribuidores": u["n_dist"],
                   "erros": [f"{type(e).__name__}: {e}"], "checks": {}, "segundos": None}
            L.silencio(False); painel._IX.clear()
        situacao = "ok" if not res["erros"] else "ERRO"
        log(f"{u['nivel']} {u['rotulo']:<50} {situacao:<4} {res.get('distribuidores', 0):>3} dist · {res.get('linhas_fato', 0):>10,} linhas · "
            f"{res.get('pdvs_base_ativa', 0):>8,} PDVs · {(res.get('bytes') or 0) / 1024 / 1024:5.1f} MB · {res.get('segundos') or 0:5.1f} s"
            + ("" if not res["erros"] else f" · {res['erros'][0][:120]}"), "ok" if not res["erros"] else "erro")
        resultados.append(res)
        if res["erros"] and EM_ERRO == "parar":
            log("distribuicao.em_erro = parar: interrompendo (nada publicado)", "erro")
            break
    checks_soma, erros_soma = ({}, []) if filtro else conferir_somas(resultados, T)
    com_erro = [r for r in resultados if r["erros"]]
    if sem_publicar:
        log(f"publicacao por usuario pulada (--sem-publicar ou mes em andamento sem publicacao)", "ok")
        for r in resultados:
            r["publicacao"] = "nao publicado"
    elif com_erro and EM_ERRO != "continuar" or erros_soma:
        log(f"{len(com_erro)} usuario(s) com erro e em_erro = {EM_ERRO}" + (" · soma dos niveis falhou" if erros_soma else "") + ": nenhum painel por usuario publicado", "erro")
        for r in resultados:
            r["publicacao"] = "nao publicado"
    else:
        for r in resultados:
            if r["erros"]:
                r["publicacao"] = "nao publicado (erro)"
                log(f"{r['rotulo']}: NAO publicado; o arquivo anterior (se existir) continua na pasta", "aviso")
                continue
            try:
                publicar_usuario(r, destino_base)
            except OSError as e:
                r["publicacao"] = f"erro: {e}"; r["erros"].append(f"publicacao: {e}")
    n_pub = sum(1 for r in resultados if r.get("publicacao") == "publicado")
    n_igual = sum(1 for r in resultados if r.get("publicacao") == "sem mudanca")
    resumo = {"usuarios": [{k: v for k, v in r.items() if k not in ("canal_mes", "canal_cat_mes")} for r in resultados],
              "somas": checks_soma, "erros": [f"{r['rotulo']}: {e}" for r in com_erro for e in r["erros"]] + erros_soma,
              "publicados": n_pub, "sem_mudanca": n_igual, "com_erro": len(com_erro)}
    log(f"usuarios: {len(resultados)} gerados · {len(com_erro)} com erro · {n_pub} publicados · {n_igual} sem mudanca", "ok" if not com_erro else "erro")
    L.etapa_fim("ok" if not com_erro and not erros_soma else "erro", usuarios=len(resultados), com_erro=len(com_erro), publicados=n_pub)
    return resumo
