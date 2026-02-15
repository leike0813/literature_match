import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from refs_extracted import load_refs_extracted


class TestRefsExtractedTolerantParse(unittest.TestCase):
    def test_accepts_refs_under_alias_key_and_string_entries(self) -> None:
        payload = {"references": ["Ref A", "Ref B"], "meta": {"doc_path": "x.md"}}
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "refs_extracted.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(payload, f)
            parsed = load_refs_extracted(path)
            self.assertEqual(len(parsed.refs), 2)
            self.assertEqual(parsed.refs[0]["raw_text"], "Ref A")

    def test_accepts_line_range_variants(self) -> None:
        payload = {
            "refs": [
                {"ref_id": "1", "raw_text": "X", "line_range": ["12", "13"]},
                {"ref_id": "2", "raw_text": "Y", "lines": {"start": 5, "end": 5}},
                {"ref_id": "3", "raw_text": "Z", "line": 7},
            ]
        }
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "refs_extracted.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(payload, f)
            parsed = load_refs_extracted(path)
            self.assertEqual([r["line_start"] for r in parsed.refs], [12, 5, 7])
            self.assertEqual([r["line_end"] for r in parsed.refs], [13, 5, 7])


if __name__ == "__main__":
    unittest.main()

