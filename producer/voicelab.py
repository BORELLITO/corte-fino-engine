"""Voice lab: same sentences through several voices/speeds, to be judged by ear. No publication."""
from __future__ import annotations

import sys
from pathlib import Path

from .voice import KokoroVoice

TEXT = ("Tem dias em que a oração parece bater no teto e voltar. "
        "O profeta Habacuque também perguntou: até quando, Senhor? "
        "E mesmo assim, ele continuou de pé, esperando resposta.")

KOKORO = [("pf_dora", 1.0), ("pf_dora", 0.9), ("pm_alex", 0.95), ("pm_santa", 0.95)]


def main(out: Path) -> int:
    out.mkdir(parents=True, exist_ok=True)
    for voice, speed in KOKORO:
        KokoroVoice(voice=voice, speed=speed).synthesize(TEXT, out / f"kokoro_{voice}_v{int(speed * 100)}.wav")
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1])))
