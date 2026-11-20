"""Gera amostras de voz (mesma frase, vozes/velocidades diferentes) para escolha de ouvido.

Sem footage, sem publicação, sem segredos. Saída: samples/*.wav
"""
from __future__ import annotations

import sys
from pathlib import Path

from .voice import KokoroVoice

TEXT = (
    "Você já perguntou: até quando, Senhor? E parece que nada muda. "
    "Mas respira. Deus ouve o seu clamor, e Ele ainda está no controle."
)
VARIANTS = [("pm_alex", 0.88), ("pm_santa", 0.88), ("pf_dora", 0.88), ("pm_santa", 0.8)]


def main(out: str = "samples") -> int:
    d = Path(out)
    d.mkdir(parents=True, exist_ok=True)
    for voice, speed in VARIANTS:
        KokoroVoice(voice=voice, speed=speed).synthesize(TEXT, d / f"{voice}_v{int(speed*100)}.wav")
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
