# -*- coding: utf-8 -*-
"""Identidade visual Dori | Ferrara aplicada ao HTML do painel (oficial desde 07/10/2026).

É a mesma transformação da prévia de 06/10/2026 (gerar_previa_paleta.py + dori-ovr.css da skill
paineis-html-dori), agora dentro do pipeline: roda no fim de `pipeline.gerar`, então o painel do canal e os
painéis por usuário saem iguais e todas as validações olham o HTML final.

O que faz, nesta ordem:
  1. paleta: cada cor do DN vira a cor oficial de mesmo papel (azul -> roxo, neutros, textos, semânticas);
     linhas gigantes (dados embutidos) não são tocadas;
  2. EVO_CORES (séries por categoria) na ordem de séries da marca; Chart.js com cor e fonte padrão da marca;
  3. o "✕" dos botões Fechar vira ícone SVG;
  4. o marcador de vazio "—" vira "-" em todo o arquivo, inclusive dentro dos pacotes comprimidos
     (gzip+base64), porque o JS compara com o marcador;
  5. CSS da marca (template/dori/dori.css) com Poppins embutida, círculos e logo no cabeçalho e rodapé com selo.
Tudo é embutido no HTML: o painel continua abrindo por file:// sem rede.
"""
from __future__ import annotations

import base64
import gzip
import re

from .utils.config import CFG, PASTA_TEMPLATE

PASTA = PASTA_TEMPLATE / "dori"

# Paleta DN -> paleta oficial Dori (mesmo papel de cada cor)
MAPA = {
    # azul principal e família -> roxo
    "1E4FA1": "3D2B70", "16376E": "1E1141", "274C8C": "3D2B70", "4B72B4": "9E95B8", "7895C7": "9E95B8",
    "BBCAE3": "C5BFD6", "C7D3E8": "C5BFD6", "D2DCEC": "C5BFD6", "CFDDF4": "C5BFD6",
    "E8EDF7": "ECE9F3", "EEF3FC": "ECE9F3", "EEF4FF": "ECE9F3", "EEF3FB": "ECE9F3", "F4F7FC": "F3F1F8", "F7F9FD": "F3F1F8",
    # fundos e bordas neutros (levemente roxos)
    "F4F5F8": "F6F5F9", "F5F6FA": "F6F5F9", "F4F6FA": "F6F5F9", "FAFBFC": "F6F5F9", "FAFBFD": "F6F5F9", "F7F8FB": "F6F5F9",
    "E4E6ED": "E3E1EA", "D9DCE6": "E3E1EA", "E7EAF2": "E3E1EA", "ECEEF3": "EEEDF2", "EEF0F5": "EEEDF2", "F0F1F5": "EEEDF2", "F1F2F6": "EEEDF2",
    # textos
    "1A1D2B": "4A4A4A", "2A2E42": "4A4A4A", "33384A": "4A4A4A", "4A4E62": "626262", "5A5F75": "626262", "6D7288": "626262", "4A4530": "626262",
    "7A7F94": "767676", "8C90A3": "767676", "8A8FA3": "767676", "9498AA": "767676",
    "A2A6B8": "B9B6C4", "A3A7B8": "B9B6C4", "B0B4C4": "B9B6C4", "B9BDCB": "B9B6C4", "C3C7D4": "B9B6C4",
    # semânticas
    "00713A": "005C20", "1E8A4C": "005C20", "00612F": "005C20", "EAF7EF": "E6F4EC",
    "D2222D": "E30613", "C22B2B": "E30613", "FDEDED": "FDE8E9",
    "E8710A": "F59C00", "B5720C": "F59C00", "D99000": "F59C00", "F5A200": "F59C00",
    "A56A00": "9A5C00", "C07A00": "9A5C00", "7A4A00": "9A5C00",
    "FEF6E7": "FEF3E0", "FFF4E5": "FEF3E0", "F5DFAF": "F8D9A0", "F0B96B": "F8D9A0",
    # tons claros e médios restantes do DN
    "E2E8F4": "ECE9F3", "EEF2FA": "ECE9F3", "E2E9F7": "ECE9F3", "E4EDFC": "ECE9F3", "B9C6E4": "C5BFD6", "7A8BB0": "9E95B8",
    "FBFCFD": "F6F5F9", "FBFCFB": "F6F5F9", "FBFBFD": "F6F5F9", "F3F6FB": "F6F5F9", "F2F5FA": "F6F5F9", "F1F3F8": "F6F5F9", "F2F3F9": "F6F5F9",
    "E3E8F2": "E3E1EA", "DDE3EE": "E3E1EA", "9AA3B5": "B9B6C4", "5A5F73": "626262", "5A6078": "626262", "4A5670": "626262",
    "1B7F4C": "005C20", "4FA575": "009640", "F2FAF5": "E6F4EC", "F2F7F3": "E6F4EC", "B9E3CB": "B5DEC6",
    "FEF4F4": "FDE8E9", "FDECEC": "FDE8E9", "FFF7F7": "FDE8E9", "FEF6F6": "FDE8E9", "E7B4B4": "F4C2C4", "5A2B2B": "8E0000",
    "FEFAF0": "FEF3E0", "FFF6E8": "FEF3E0", "FFF6E5": "FEF3E0", "F0D9AE": "F8D9A0", "7A2E8C": "3D2B70",
}
# séries por categoria do gráfico de evolução -> ordem de séries da marca (sem vermelho)
SERIES = "['#3D2B70','#009FE3','#F59C00','#009640','#1E1141','#005E8E','#9A5C00','#005C20','#9E95B8','#B9B6C4']"
RGBA = {"30,79,161": "61,43,112", "20,30,60": "30,17,65", "20,40,80": "30,17,65", "0,0,0": "30,17,65"}
# hex curtos (3 dígitos): vermelhos de texto do DN. Não confundir com entidade HTML (&#233; = é)
MAPA3 = {"A00": "8E0000", "C00": "E30613"}
# "#" também aparece URL-codificado ("%23") dentro de ícone SVG embutido em data URI
_PADRAO = re.compile(r"(#|%23)(" + "|".join(MAPA) + r")\b", re.I)
_PADRAO3 = re.compile(r"(?<!&)#(" + "|".join(MAPA3) + r")\b(?![0-9A-Fa-f;])", re.I)

# Chart.js embutido: cor e fonte PADRÃO da biblioteca (#666, grade preta translúcida, Helvetica no canvas) -> marca
CHART_DORI = ('<script>if(window.Chart&&Chart.defaults){Chart.defaults.color="#767676";'
              'Chart.defaults.borderColor="rgba(30,17,65,0.1)";Chart.defaults.backgroundColor="rgba(61,43,112,0.1)";'
              'Chart.defaults.font.family="\'Poppins\',\'Segoe UI\',Arial,sans-serif";}</script>\n')
ICO_X = ('<svg class="dori-ico" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" '
         'stroke-width="2.6" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>')
CIRC = ('<svg class="dori-circ" viewBox="0 0 78 66" aria-hidden="true"><circle cx="4" cy="6" r="38" fill="#3D2B70"/>'
        '<circle cx="35" cy="16" r="20" fill="#E30613"/><circle cx="60" cy="50" r="11" fill="#F59C00"/></svg>')


def _recolorir(linha: str) -> str:
    if len(linha) > 20000:      # linhas gigantes são dados embutidos: não mexer
        return linha
    linha = _PADRAO.sub(lambda m: m.group(1) + MAPA[m.group(2).upper()], linha)
    linha = _PADRAO3.sub(lambda m: "#" + MAPA3[m.group(1).upper()], linha)
    for a, b in RGBA.items():
        linha = linha.replace(f"rgba({a},", f"rgba({b},")
    return linha


def _troca_blob(m: re.Match) -> str:
    txt = gzip.decompress(base64.b64decode(m.group(1))).decode("utf-8")
    if "—" not in txt:
        return m.group(0)
    txt = txt.replace("—", "-")
    return '"' + base64.b64encode(gzip.compress(txt.encode("utf-8"), mtime=0)).decode() + '"'


def _data_uri(nome: str, mime: str) -> str:
    return f"data:{mime};base64,{base64.b64encode((PASTA / nome).read_bytes()).decode()}"


def _css() -> str:
    css = re.sub(r"/\*.*?\*/", "", (PASTA / "dori.css").read_text(encoding="utf-8"), flags=re.S)
    return re.sub(r"url\((fonts/[^)]+\.woff2)\)", lambda m: f"url({_data_uri(m.group(1), 'font/woff2')})", css)


def selo() -> str:
    return str((CFG.get("identidade") or {}).get("selo") or "")


def aplicar(html: str) -> str:
    html = "\n".join(_recolorir(l) for l in html.split("\n"))
    html = re.sub(r"var EVO_CORES=\[[^\]]*\]", "var EVO_CORES=" + SERIES, html)
    i_lib = html.find('this.color="#666"')
    if i_lib >= 0:
        fim_lib = html.find("</script>", i_lib) + len("</script>")
        html = html[:fim_lib] + "\n" + CHART_DORI + html[fim_lib:]
    html = html.replace("Fechar ✕</button>", "Fechar " + ICO_X + "</button>")
    # "—" é o marcador de vazio (formatadores devolvem '—' e o JS compara x==='—'): troca global e consistente
    html = html.replace("join(' — ')", "join(' · ')").replace("—", "-")
    html = re.sub(r'"(H4sI[A-Za-z0-9+/=]{40,})"', _troca_blob, html)
    fim_head = html.find("</head>")
    html = html[:fim_head] + "<style>\n" + _css() + "\n</style>\n" + html[fim_head:]
    html, n = re.subn(r'<div class="top">', '<div class="top">' + CIRC, html, count=1)
    assert n == 1, "identidade: cabeçalho <div class=\"top\"> não encontrado"
    logo = f'<img class="dori-logo" src="{_data_uri("logo_dori_ferrara.png", "image/png")}" alt="dori | Ferrara">'
    html, n = re.subn(r'(<div class="top">.*?<div class="sp"></div>)', lambda m: m.group(1) + logo, html, count=1, flags=re.S)
    assert n == 1, "identidade: <div class=\"sp\"> do cabeçalho não encontrado"
    sel = selo().replace("\\", "\\\\").replace("'", "\\'")
    rodape = ("<script>(function(){var w=document.querySelector('.wrap');if(!w)return;var f=document.createElement('footer');"
              "f.className='dori-rodape';\nf.innerHTML='<div><b>Loved by generations. Crafted by you.</b><span class=\"l2\">"
              "Amado por gerações. Criado por você.</span></div><div class=\"esp\"></div>"
              + (f"<span class=\"selo\">{sel}</span>" if sel else "") + "';w.appendChild(f);})();</script>\n")
    i = html.rfind("</body>")
    return html[:i] + rodape + html[i:]
