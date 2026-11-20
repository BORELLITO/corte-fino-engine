"""python -m producer.cli episodes/E02.json --out build/E02 [--footage pexels|local:DIR] [--no-asr]"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from orchestrator.runflow import run_flow

from .build import build_package
from .captions import FasterWhisperAligner
from .common import ProducerError
from .footage import LocalCatalogFootage, PexelsFootage, PixabayFootage
from .rejections import load_rejections
from .voice import KokoroVoice


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Produce a Verbo no Chão preview package and validate it")
    ap.add_argument("spec", type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--report-dir", type=Path, default=Path("run-reports"))
    ap.add_argument("--footage", default="pexels", help="pexels | pixabay | local:<dir with catalog.json>")
    ap.add_argument("--no-asr", action="store_true", help="skip ASR alignment (captions will NOT be marked synchronized)")
    args = ap.parse_args(argv)
    try:
        spec = json.loads(args.spec.read_text(encoding="utf-8"))
        if spec.get("approved_sources_only") and not args.footage.startswith("local:"):
            raise ProducerError("producer:spec:approved_sources_only_requires_local_catalog")
        rejected = load_rejections(Path(__file__).resolve().parent.parent / "contracts")
        footage = (LocalCatalogFootage(Path(args.footage[6:])) if args.footage.startswith("local:")
                   else PixabayFootage() if args.footage == "pixabay" else PexelsFootage())
        aligner = None if args.no_asr else FasterWhisperAligner()
        build_package(spec, args.out, KokoroVoice(**spec.get("voice", {})), footage, aligner, rejected)
    except (ProducerError, OSError, json.JSONDecodeError) as exc:
        print(f"BLOCKED\n- {exc}")
        return 1
    result = run_flow({"episode": spec["episode_id"]}, args.out, args.report_dir, render=True)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0 if result.status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
