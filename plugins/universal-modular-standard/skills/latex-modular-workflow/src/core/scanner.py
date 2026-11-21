"""Pure LaTeX content scanner with zero filesystem side effects."""

import re
from typing import List

from .contracts import ModuleSummaryDict, ParsedTexModule, ProjectIndexDict

_RE_INPUT = re.compile(r"\\(?:input|include)\{([^}]+)\}")
_RE_SECTION = re.compile(
    r"\\(?:chapter|section|subsection)\*?\{([^}]+)\}|\\begin\{frame\}(?:\[[^\]]*\])?\{([^}]+)\}"
)
_RE_LABEL = re.compile(r"\\label\{([^}]+)\}")
_RE_CITE = re.compile(r"\\cite[a-zA-Z]*\{([^}]+)\}")
_RE_FIG = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}")
_RE_HDR_MOD = re.compile(r"^%\s*@module:\s*(.+)$", re.MULTILINE)
_RE_HDR_SEC = re.compile(r"^%\s*@sections:\s*(.+)$", re.MULTILINE)


def _strip_comments(line: str) -> str:
    """Remove unescaped LaTeX comments from a single line."""
    for idx, ch in enumerate(line):
        if ch == "%" and (idx == 0 or line[idx - 1] != "\\"):
            return line[:idx]
    return line


def _normalize_tex_ref(ref: str) -> str:
    """Normalize an \\input reference so it always ends with .tex."""
    cleaned = ref.strip().replace("\\", "/")
    return cleaned if cleaned.endswith(".tex") else f"{cleaned}.tex"


def _dedupe_preserve(items: List[str]) -> List[str]:
    """Deduplicate strings while preserving first-seen order."""
    seen = set()
    result: List[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def parse_tex_content(rel_path: str, content: str) -> ParsedTexModule:
    """Parse LaTeX text into structured module metadata without I/O."""
    lines = content.splitlines()
    code_only = "\n".join(_strip_comments(line) for line in lines)

    hdr_mod_match = _RE_HDR_MOD.search(content)
    hdr_sec_match = _RE_HDR_SEC.search(content)
    hdr_sections = (
        [s.strip() for s in hdr_sec_match.group(1).split("|") if s.strip()]
        if hdr_sec_match
        else []
    )

    sections: List[str] = []
    for match in _RE_SECTION.finditer(code_only):
        title = (match.group(1) or match.group(2) or "").strip()
        if title:
            sections.append(title)

    citations: List[str] = []
    for raw_cite in _RE_CITE.findall(code_only):
        for key in raw_cite.split(","):
            if key.strip():
                citations.append(key.strip())

    inputs = [_normalize_tex_ref(x) for x in _RE_INPUT.findall(code_only)]
    labels = _dedupe_preserve([x.strip() for x in _RE_LABEL.findall(code_only)])
    figures = _dedupe_preserve([x.strip().replace("\\", "/") for x in _RE_FIG.findall(code_only)])

    return ParsedTexModule(
        rel_path=rel_path.replace("\\", "/"),
        loc=len(lines),
        header_module=hdr_mod_match.group(1).strip() if hdr_mod_match else "",
        header_sections=hdr_sections,
        inputs=_dedupe_preserve(inputs),
        sections=_dedupe_preserve(sections or hdr_sections),
        labels=labels,
        citations=_dedupe_preserve(citations),
        figures=figures,
    )


def build_index_dict(
    entrypoint: ParsedTexModule,
    modules: List[ParsedTexModule],
    warnings: List[str],
) -> ProjectIndexDict:
    """Assemble the serializable INDEX.json dictionary from parsed modules."""
    module_entries: List[ModuleSummaryDict] = [
        {
            "path": mod.rel_path,
            "loc": mod.loc,
            "header_module": mod.header_module,
            "sections": mod.sections,
            "labels": mod.labels,
            "citations": mod.citations,
            "figures": mod.figures,
        }
        for mod in modules
    ]
    total_loc = entrypoint.loc + sum(mod.loc for mod in modules)
    return {
        "schema_version": 1,
        "entrypoint": entrypoint.rel_path,
        "entrypoint_loc": entrypoint.loc,
        "total_modules": len(modules),
        "total_loc": total_loc,
        "input_order": entrypoint.inputs,
        "modules": module_entries,
        "warnings": warnings,
    }
