"""Isolated unit tests for modular LaTeX scanner, validator, and fs adapter."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

_SKILL_ROOT = Path(__file__).resolve().parent.parent
if str(_SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(_SKILL_ROOT))

from src.adapters.fs_adapter import load_project_modules, write_index_json  # noqa: E402
from src.core.scanner import build_index_dict, parse_tex_content  # noqa: E402
from src.core.validator import validate_project  # noqa: E402


class TestTexIndex(unittest.TestCase):
    """Verify pure parsing, invariant validation, and INDEX.json persistence."""

    def test_parse_semantic_headers_and_macros(self) -> None:
        sample = (
            "% @module: 01_pendahuluan\n"
            "% @sections: 1.1 Latar Belakang\n"
            "\\section{Pendahuluan}\\label{sec:pendahuluan}\n"
            "Lihat \\cite{rudin1976,bartle2011} dan \\includegraphics[width=0.8\\linewidth]{fig01.png}.\n"
        )
        parsed = parse_tex_content(".sumber/bagian/01_pendahuluan.tex", sample)
        self.assertEqual(parsed.loc, 4)
        self.assertEqual(parsed.header_module, "01_pendahuluan")
        self.assertEqual(parsed.sections, ["Pendahuluan"])
        self.assertEqual(parsed.labels, ["sec:pendahuluan"])
        self.assertEqual(parsed.citations, ["rudin1976", "bartle2011"])
        self.assertEqual(parsed.figures, ["fig01.png"])

    def test_validator_catches_loc_limit_and_orphans(self) -> None:
        entry = parse_tex_content("makalah.tex", "\\input{.sumber/bagian/01_isi.tex}\n")
        long_body = "\n".join(["Baris teks."] * 151)
        mod_long = parse_tex_content(".sumber/bagian/01_isi.tex", long_body)
        mod_orphan = parse_tex_content(".sumber/bagian/02_yatim.tex", "% @module: 02_yatim\n\\label{badlabel}\n")
        report = validate_project(entry, [mod_long, mod_orphan], ["makalah.aux"])
        self.assertFalse(report.passed)
        self.assertEqual(report.stats["error_count"], 1)
        self.assertGreaterEqual(report.stats["warning_count"], 3)

    def test_fs_adapter_roundtrip_index_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bagian = root / ".sumber" / "bagian"
            bagian.mkdir(parents=True)
            (root / "ppt.tex").write_text(
                "\\input{.sumber/bagian/01_cover.tex}\n", encoding="utf-8"
            )
            (bagian / "01_cover.tex").write_text(
                "% @module: 01_cover\n\\begin{frame}{Judul}\\end{frame}\n", encoding="utf-8"
            )
            entry, mods, leaks = load_project_modules(root)
            report = validate_project(entry, mods, leaks)
            self.assertTrue(report.passed)
            idx_path = write_index_json(root, build_index_dict(entry, mods, report.warnings))
            loaded = json.loads(idx_path.read_text(encoding="utf-8"))
            self.assertEqual(loaded["entrypoint"], "ppt.tex")
            self.assertEqual(loaded["total_modules"], 1)


if __name__ == "__main__":
    unittest.main()
