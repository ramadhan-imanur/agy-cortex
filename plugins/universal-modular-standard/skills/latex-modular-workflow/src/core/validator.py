"""Pure validation logic for modular LaTeX and anti-monolithic invariants."""

from typing import FrozenSet, List, Set

from config.limits import MAX_ENTRY_LOC, MAX_MODULE_LOC, VALID_LABEL_PREFIXES
from .contracts import ParsedTexModule, ValidationReport


def _collect_all_inputs(
    entrypoint: ParsedTexModule,
    modules: List[ParsedTexModule],
) -> Set[str]:
    """Gather all transitive \\input targets referenced by the project."""
    referenced: Set[str] = set(entrypoint.inputs)
    for mod in modules:
        referenced.update(mod.inputs)
    return referenced


def validate_project(
    entrypoint: ParsedTexModule,
    modules: List[ParsedTexModule],
    root_leaks: List[str],
    valid_prefixes: FrozenSet[str] = VALID_LABEL_PREFIXES,
    max_entry_loc: int = MAX_ENTRY_LOC,
    max_module_loc: int = MAX_MODULE_LOC,
) -> ValidationReport:
    """Validate LOC caps, semantic headers, label prefixes, and clean root."""
    errors: List[str] = []
    warnings: List[str] = []

    if entrypoint.loc > max_entry_loc:
        errors.append(
            f"Entrypoint '{entrypoint.rel_path}' exceeds {max_entry_loc} LOC ({entrypoint.loc} LOC)."
        )
    if not entrypoint.inputs:
        errors.append(
            f"Entrypoint '{entrypoint.rel_path}' has no \\input/{{...}} modules; monolithic TeX is forbidden."
        )

    referenced = _collect_all_inputs(entrypoint, modules)

    for mod in modules:
        if mod.loc > max_module_loc:
            errors.append(
                f"Module '{mod.rel_path}' exceeds {max_module_loc} LOC ({mod.loc} LOC)."
            )
        if not mod.header_module:
            warnings.append(f"Module '{mod.rel_path}' is missing '% @module:' semantic header.")
        if mod.rel_path not in referenced:
            warnings.append(f"Orphan module '{mod.rel_path}' is not referenced via \\input.")
        for lbl in mod.labels:
            if not any(lbl.startswith(prefix) for prefix in valid_prefixes):
                warnings.append(
                    f"Label '{lbl}' in '{mod.rel_path}' lacks a standard prefix (e.g., sec:, eq:, thm:)."
                )

    for leak in root_leaks:
        warnings.append(f"Build artifact '{leak}' found in root; isolate outputs in .sumber/.build/.")

    stats = {
        "entrypoint_loc": entrypoint.loc,
        "module_count": len(modules),
        "error_count": len(errors),
        "warning_count": len(warnings),
    }
    return ValidationReport(
        passed=len(errors) == 0,
        warnings=warnings,
        errors=errors,
        stats=stats,
    )
