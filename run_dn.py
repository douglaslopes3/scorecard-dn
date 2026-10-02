# -*- coding: utf-8 -*-
"""Scorecard DN · ponto único de execução.

    python run_dn.py                    tudo: verificar -> ingerir (se preciso) -> calcular -> renderizar -> validar -> publicar
    python run_dn.py --mes 2026-06      mês de referência específico
    python run_dn.py --sem-publicar     gera e valida, não copia para a pasta de publicação
    python run_dn.py --forcar           ignora cache e manifesto: relê todas as bases
    python run_dn.py --regerar-exemplo  regrava o exemplo do template (só depois de editar template/template.html)

Saídas: data/dn/curated/ (Parquet + manifesto.json), data/dn/painel/ (JSON + HTML datado),
data/dn/quality/, data/dn/logs/ (log + resumo da execução) e o HTML publicado
(config: publicacao.pasta/arquivo). Exit code 1 e "PIPELINE ABORTADO" em qualquer falha.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
for _f in (sys.stdout, sys.stderr):
    try:
        _f.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass


def main() -> int:
    ap = argparse.ArgumentParser(description="Scorecard DN · pipeline único")
    ap.add_argument("--mes", metavar="AAAA-MM", help="mês de referência (padrão: painel.mes_referencia ou o último da série)")
    ap.add_argument("--sem-publicar", action="store_true", help="não copia o HTML para a pasta de publicação")
    ap.add_argument("--forcar", action="store_true", help="relê todas as bases mesmo sem mudança")
    ap.add_argument("--regerar-exemplo", action="store_true", help="regrava template/example-data*.json e Scorecard_DN_base.html")
    ap.add_argument("--usuario", metavar="CODIGO|TEXTO", help="Etapa 2: gera só o painel do usuário cujo rótulo contém o texto (ex.: 1120)")
    ap.add_argument("--sem-usuarios", action="store_true", help="Etapa 2: não gera os painéis por usuário nesta execução")
    a = ap.parse_args()
    if a.mes and not (len(a.mes) == 7 and a.mes[4] == "-" and a.mes[:4].isdigit() and a.mes[5:].isdigit()):
        ap.error("--mes precisa estar no formato AAAA-MM")
    from dn.utils import recursos   # P6: threads e prioridade ANTES de carregar numpy/pandas (so config e yaml ate aqui)
    recursos.aplicar_ambiente()
    from dn import pipeline
    return pipeline.executar(mes=a.mes, sem_publicar=a.sem_publicar, forcar=a.forcar,
                             regerar_exemplo=a.regerar_exemplo, usuario=a.usuario, sem_usuarios=a.sem_usuarios)


if __name__ == "__main__":
    sys.exit(main())
