"""Filesystem boundary adapter for scanning and indexing LaTeX projects."""

import json
from pathlib import Path
from typing import List, Tuple

from config.limits import (
    BUILD_LEAK_EXTENSIONS,
    INDEX_FILE_NAME,
    SOURCE_DIR_NAME,
    VALID_ENTRYPOINTS,
)
from src.core.contracts import ParsedTexModule, ProjectIndexDict
from src.core.scanner import parse_tex_content


def find_entrypoint(doc_dir: Path) -> Path:
    """Locate the canonical LaTeX entrypoint in the document root."""
    for name in VALID_ENTRYPOINTS:
        candidate = doc_dir / name
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        f"No canonical entrypoint ({', '.join(VALID_ENTRYPOINTS)}) found in '{doc_dir}'."
    )


def load_project_modules(doc_dir: Path) -> Tuple[ParsedTexModule, List[ParsedTexModule], List[str]]:
    """Read entrypoint, .sumber/*.tex modules, and detect root build leaks."""
    entry_path = find_entrypoint(doc_dir)
    entry_mod = parse_tex_content(
        entry_path.name,
        entry_path.read_text(encoding="utf-8-sig"),
    )

    sumber_dir = doc_dir / SOURCE_DIR_NAME
    if not sumber_dir.is_dir():
        raise FileNotFoundError(f"Required decomposition directory '{sumber_dir}' not found.")

    modules: List[ParsedTexModule] = []
    for tex_file in sorted(sumber_dir.rglob("*.tex")):
        if ".build" in tex_file.parts or "arsip" in tex_file.parts:
            continue
        rel = tex_file.relative_to(doc_dir).as_posix()
        modules.append(parse_tex_content(rel, tex_file.read_text(encoding="utf-8-sig")))

    root_leaks = sorted(
        item.name
        for item in doc_dir.iterdir()
        if item.is_file() and any(item.name.endswith(ext) for ext in BUILD_LEAK_EXTENSIONS)
    )
    return entry_mod, modules, root_leaks


def write_index_json(doc_dir: Path, index_data: ProjectIndexDict) -> Path:
    """Persist ProjectIndexDict cleanly to .sumber/INDEX.json."""
    out_path = doc_dir / SOURCE_DIR_NAME / INDEX_FILE_NAME
    out_path.write_text(
        json.dumps(index_data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return out_path
