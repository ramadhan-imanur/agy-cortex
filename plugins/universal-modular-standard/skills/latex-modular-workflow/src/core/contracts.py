"""Explicit data contracts for modular LaTeX scanning and validation."""

from dataclasses import dataclass, field
from typing import Dict, List, TypedDict


class ModuleSummaryDict(TypedDict):
    """Serialized summary of a single .tex module for INDEX.json."""

    path: str
    loc: int
    header_module: str
    sections: List[str]
    labels: List[str]
    citations: List[str]
    figures: List[str]


class ProjectIndexDict(TypedDict):
    """Top-level schema written to .sumber/INDEX.json."""

    schema_version: int
    entrypoint: str
    entrypoint_loc: int
    total_modules: int
    total_loc: int
    input_order: List[str]
    modules: List[ModuleSummaryDict]
    warnings: List[str]


@dataclass(frozen=True)
class ParsedTexModule:
    """Pure in-memory representation of a scanned .tex file."""

    rel_path: str
    loc: int
    header_module: str
    header_sections: List[str] = field(default_factory=list)
    inputs: List[str] = field(default_factory=list)
    sections: List[str] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)
    citations: List[str] = field(default_factory=list)
    figures: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ValidationReport:
    """Pure validation outcome for modular LaTeX compliance."""

    passed: bool
    warnings: List[str]
    errors: List[str]
    stats: Dict[str, int]
