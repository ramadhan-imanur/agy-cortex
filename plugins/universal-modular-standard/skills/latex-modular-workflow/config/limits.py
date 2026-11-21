"""Externalized limits and conventions for modular LaTeX indexing."""

from typing import FrozenSet, Tuple

MAX_ENTRY_LOC: int = 80
MAX_MODULE_LOC: int = 150

VALID_ENTRYPOINTS: Tuple[str, ...] = ("makalah.tex", "laporan.tex", "ppt.tex")

VALID_LABEL_PREFIXES: FrozenSet[str] = frozenset({
    "sec:",
    "subsec:",
    "def:",
    "thm:",
    "lem:",
    "prop:",
    "cor:",
    "eq:",
    "fig:",
    "tab:",
    "alg:",
    "app:",
})

BUILD_LEAK_EXTENSIONS: FrozenSet[str] = frozenset({
    ".aux",
    ".bbl",
    ".blg",
    ".fdb_latexmk",
    ".fls",
    ".lof",
    ".log",
    ".lot",
    ".nav",
    ".out",
    ".snm",
    ".synctex.gz",
    ".toc",
})

SOURCE_DIR_NAME: str = ".sumber"
INDEX_FILE_NAME: str = "INDEX.json"
BUILD_DIR_REL: str = ".sumber/.build"
