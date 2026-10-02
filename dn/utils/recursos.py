# -*- coding: utf-8 -*-
"""Etapa 1 · performance (P6, 15/09/2026): convivencia do pipeline com a maquina.

`config.yaml -> recursos`:
  prioridade   normal | abaixo_do_normal | baixa   prioridade do processo no Windows (SetPriorityClass)
  threads      N (0 = padrao)                       threads do pyarrow e das bibliotecas numericas (OMP/MKL/OpenBLAS)

`aplicar_ambiente()` precisa rodar ANTES de importar numpy/pandas/pyarrow (as variaveis de ambiente so valem na carga);
`aplicar_pyarrow()` roda depois do import. Nada aqui muda resultado: so quanta CPU o processo disputa e com que prioridade.
"""
from __future__ import annotations

import os
import sys

from .config import CFG

_PRIORIDADE = {"normal": 0x00000020, "abaixo_do_normal": 0x00004000, "baixa": 0x00000040}   # NORMAL, BELOW_NORMAL, IDLE


def _cfg() -> dict:
    return CFG.get("recursos") or {}


def aplicar_ambiente() -> str:
    r = _cfg()
    partes = []
    n = int(r.get("threads") or 0)
    if n > 0:
        for var in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_MAX_THREADS", "POLARS_MAX_THREADS"):
            os.environ.setdefault(var, str(n))
        partes.append(f"threads {n}")
    pri = str(r.get("prioridade") or "normal").strip().lower()
    if pri not in _PRIORIDADE:
        raise SystemExit(f"recursos.prioridade '{pri}' invalida (normal | abaixo_do_normal | baixa)")
    if pri != "normal" and sys.platform == "win32":
        try:
            import ctypes
            k32 = ctypes.windll.kernel32
            k32.GetCurrentProcess.restype = ctypes.c_void_p            # HANDLE (64 bits): sem isto o pseudo-handle -1 e truncado
            k32.SetPriorityClass.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
            if k32.SetPriorityClass(k32.GetCurrentProcess(), _PRIORIDADE[pri]):
                partes.append(f"prioridade {pri}")
        except Exception:   # sem ctypes/kernel32: segue em prioridade normal
            pass
    return " · ".join(partes) if partes else "padrao"


def aplicar_pyarrow() -> None:
    n = int(_cfg().get("threads") or 0)
    if n > 0:
        try:
            import pyarrow as pa
            pa.set_cpu_count(n)
            pa.set_io_thread_count(max(2, n))
        except Exception:
            pass
