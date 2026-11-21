"""Thin CLI orchestrator for generating .sumber/INDEX.json and validating rules."""

import argparse
import sys
from pathlib import Path

_SKILL_ROOT = Path(__file__).resolve().parent
if str(_SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(_SKILL_ROOT))

from src.adapters.fs_adapter import load_project_modules, write_index_json  # noqa: E402
from src.core.scanner import build_index_dict  # noqa: E402
from src.core.validator import validate_project  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Index and validate modular LaTeX projects.")
    parser.add_argument("doc_dir", help="Document root containing makalah.tex/laporan.tex/ppt.tex.")
    parser.add_argument("--check", action="store_true", help="Exit non-zero on rule errors.")
    return parser.parse_args()


def main() -> int:
    """Run modular LaTeX scan, validation, and INDEX.json generation."""
    args = _parse_args()
    doc_dir = Path(args.doc_dir).resolve()
    entry, modules, leaks = load_project_modules(doc_dir)
    report = validate_project(entry, modules, leaks)
    index_data = build_index_dict(entry, modules, report.warnings)
    out_path = write_index_json(doc_dir, index_data)

    print(f"Indexed {report.stats['module_count']} modules -> {out_path}")
    for warn in report.warnings:
        print(f"[WARN] {warn}")
    for err in report.errors:
        print(f"[ERROR] {err}", file=sys.stderr)

    return 1 if (args.check and not report.passed) else 0


if __name__ == "__main__":
    raise SystemExit(main())
