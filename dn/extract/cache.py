# -*- coding: utf-8 -*-
"""Cache de leitura de Excel em Parquet.

Ler 500 MB de Excel custa minutos; ler o Parquet equivalente custa segundos. A
chave do cache é (caminho relativo, tamanho, data de modificação, hash rápido do
conteúdo, VERSÃO DOS LEITORES).

------------------------------------------------------------------------------
Versão dos leitores — automática (Fase 1 da reforma, 09/09/2026, item D4)
------------------------------------------------------------------------------
Até a v9 a versão era um inteiro subido à mão (`VERSAO_CACHE`). O risco, que
aconteceu de verdade no projeto anterior: um leitor passa a gravar um campo novo,
ninguém sobe a versão, o cache antigo é servido sem o campo e a checagem que
depende dele roda de mão vazia — dado errado com todas as checagens verdes.

Agora a versão é o hash do CÓDIGO dos leitores (`dn/extract/*.py` e
`dn/utils/texto.py`). Mudou uma linha em qualquer leitor, o cache inteiro é
invalidado sozinho. Custo: uma releitura completa (~4 min) a cada mudança de
leitor; benefício: não existe mais o "esqueci de subir a versão".

Histórico das versões manuais (v1 a v9) está em `docs/fase1.md` e
`docs/rodada_2026-09-09.md`.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

from ..utils.config import PASTA_STAGING, RAIZ
from ..utils.log import log

_KB64 = 65536
_PASTA_EXTRACT = Path(__file__).resolve().parent
_ARQUIVOS_LEITORES = sorted(_PASTA_EXTRACT.glob("*.py")) + [RAIZ / "dn" / "utils" / "texto.py"]


def versao_leitores() -> str:
    """Hash curto do código-fonte dos leitores. É a 'versão do cache'."""
    h = hashlib.md5()
    for arq in _ARQUIVOS_LEITORES:
        h.update(arq.name.encode())
        h.update(arq.read_bytes())
    return h.hexdigest()[:10]


VERSAO_LEITORES = versao_leitores()


def hash_rapido(arq: Path, tamanho: int | None = None) -> str:
    """Hash dos primeiros e últimos 64 KB — barato (2 leituras) e suficiente
    para pegar conteúdo trocado com tamanho+mtime preservados."""
    tamanho = arq.stat().st_size if tamanho is None else tamanho
    h = hashlib.md5()
    with open(arq, "rb") as f:
        h.update(f.read(_KB64))
        if tamanho > _KB64:
            f.seek(max(tamanho - _KB64, 0))
            h.update(f.read(_KB64))
    return h.hexdigest()[:8]


def relativo(arq: Path) -> str:
    try:
        return arq.resolve().relative_to(RAIZ).as_posix()
    except ValueError:                       # fora da raiz do projeto
        return arq.resolve().as_posix()


def impressao(arq: Path) -> dict:
    """Impressão digital de um arquivo de base: o que o manifesto guarda."""
    st = arq.stat()
    return {"caminho": relativo(arq), "tamanho": st.st_size, "mtime": int(st.st_mtime),
            "hash": hash_rapido(arq, st.st_size)}


def _chave(arq: Path) -> str:
    i = impressao(arq)
    crua = f"v{VERSAO_LEITORES}|{i['caminho']}|{i['tamanho']}|{i['mtime']}|{i['hash']}"
    return hashlib.md5(crua.encode()).hexdigest()[:10]


def ler(arq: Path, leitor) -> tuple[pd.DataFrame, dict]:
    """`leitor(caminho) -> (df, extra)`. `extra` é um dict pequeno (gabaritos,
    contagens) guardado num JSON ao lado do Parquet."""
    arq = Path(arq)
    PASTA_STAGING.mkdir(parents=True, exist_ok=True)
    ch = _chave(arq)
    alvo = PASTA_STAGING / f"{arq.stem}.{ch}.parquet"
    lado = PASTA_STAGING / f"{arq.stem}.{ch}.json"

    if alvo.exists() and lado.exists():
        df = pd.read_parquet(alvo)
        with open(lado, encoding="utf-8") as f:
            extra = json.load(f)
        log(f"{arq.name:<40} {len(df):>10,} linhas  (cache)")
        return df, extra

    df, extra = leitor(arq)
    df.to_parquet(alvo, index=False)
    with open(lado, "w", encoding="utf-8") as f:
        json.dump(extra, f, ensure_ascii=False)
    # Versões antigas do MESMO arquivo saem sozinhas.
    for velho in PASTA_STAGING.glob(f"{arq.stem}.*"):
        if velho not in (alvo, lado):
            try:
                velho.unlink()
            except OSError:
                pass
    log(f"{arq.name:<40} {len(df):>10,} linhas  (lido)")
    return df, extra
