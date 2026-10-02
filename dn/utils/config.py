# -*- coding: utf-8 -*-
"""Configuração e caminhos do projeto DN.

Todo caminho é resolvido a partir da raiz do projeto (a pasta DN/), nunca de
`os.getcwd()`. Caminho absoluto no config passa direto (é o caso da pasta de
publicação, que fica fora do projeto).
"""
from __future__ import annotations

import os
from pathlib import Path

import yaml

# dn/utils/config.py -> dn/utils -> dn -> raiz (DN/)
RAIZ = Path(__file__).resolve().parents[2]
PASTA_CONFIG = RAIZ / "config"


def _ler_yaml(nome: str) -> dict:
    alvo = PASTA_CONFIG / nome
    if not alvo.exists():
        raise SystemExit(
            f"config nao encontrado: {alvo}\n"
            f"  raiz do projeto : {RAIZ}\n"
            f"  a pasta existe? : {'sim' if PASTA_CONFIG.exists() else 'NAO'}"
        )
    with open(alvo, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


CFG = _ler_yaml("config.yaml")


def caminho(relativo: str | Path) -> Path:
    """Resolve um caminho relativo ao projeto. Absoluto passa direto."""
    p = Path(str(relativo))
    return p if p.is_absolute() else RAIZ / p


PASTA_DADOS = caminho(CFG["projeto"]["pasta_dados"])
PASTA_STAGING = PASTA_DADOS / "staging"
PASTA_CURATED = PASTA_DADOS / "curated"
PASTA_QUALITY = PASTA_DADOS / "quality"
# P6 (Etapa 1 · performance): JSON e HTML gerados em pasta local (projeto.pasta_painel, com variaveis de ambiente
# expandidas); sem a chave, data/dn/painel como antes
_pp = CFG["projeto"].get("pasta_painel")
PASTA_PAINEL = caminho(os.path.expandvars(str(_pp))) if _pp else PASTA_DADOS / "painel"
PASTA_LOGS = caminho(CFG["projeto"]["pasta_logs"])
PASTA_TEMPLATE = RAIZ / "template"


def preparar_pastas() -> None:
    for p in (PASTA_STAGING, PASTA_CURATED, PASTA_QUALITY, PASTA_PAINEL, PASTA_LOGS):
        p.mkdir(parents=True, exist_ok=True)
