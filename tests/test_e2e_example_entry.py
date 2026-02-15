import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from apply_llm_decisions import apply_llm_decisions
from match_pipeline import MatchParams, build_initial_match_result


class TestE2EExampleEntry(unittest.TestCase):
    def test_pipeline_and_apply_decisions(self) -> None:
        refs_extracted = {
            "meta": {"doc_path": "examples/example_entry.md", "warnings": []},
            "refs": [
                {
                    "ref_id": "1",
                    "line_start": 286,
                    "line_end": 286,
                    "raw_text": "Chen, Qihang, et al. https://arxiv.org/abs/2406.03459 (2024)",
                    "parsed": {"url": "https://arxiv.org/abs/2406.03459", "arxiv": "2406.03459", "year": "2024"},
                },
                {
                    "ref_id": "2",
                    "line_start": 292,
                    "line_end": 292,
                    "raw_text": "Li, Feng, et al. https://arxiv.org/abs/2203.01305 (2022)",
                    "parsed": {"url": "https://arxiv.org/abs/2203.01305", "arxiv": "2203.01305", "year": "2022"},
                },
                {
                    "ref_id": "3",
                    "line_start": -1,
                    "line_end": -1,
                    "raw_text": "DAB-DETR: Dynamic Anchor Boxes are Better Queries for DETR (2022)",
                    "parsed": {"title_guess": "DAB-DETR: Dynamic Anchor Boxes are Better Queries for DETR", "year": "2022"},
                },
            ],
        }

        with tempfile.TemporaryDirectory() as td:
            refs_path = os.path.join(td, "refs_extracted.json")
            with open(refs_path, "w", encoding="utf-8") as f:
                json.dump(refs_extracted, f, ensure_ascii=False, indent=2)

            params = MatchParams(tfidf_auto_match_threshold=1.1, tfidf_auto_match_gap=1.0)
            initial = build_initial_match_result(
                refs_extracted_path=refs_path,
                library_cache_path="examples/example_entry.library.betterbibtexjson",
                params=params,
            )

            self.assertEqual(initial["stats"]["total"], 3)
            self.assertEqual(initial["stats"]["matched"], 2)
            self.assertEqual(initial["stats"]["needs_llm"], 1)

            needs_llm_ref = next(r for r in initial["refs"] if r["match"]["status"] == "needs_llm")
            self.assertTrue(needs_llm_ref["candidates"])
            top_citekey = needs_llm_ref["candidates"][0]["citekey"]

            decisions = {"meta": {"doc_path": "examples/example_entry.md"}, "decisions": [{"ref_id": "3", "citekey": top_citekey, "reason": "title match", "confidence": 0.7}]}
            applied = apply_llm_decisions(initial, decisions).updated
            self.assertEqual(applied["stats"]["matched"], 3)
            ref3 = next(r for r in applied["refs"] if r["ref_id"] == "3")
            self.assertEqual(ref3["match"]["status"], "matched")
            self.assertEqual(ref3["match"]["citekey"], top_citekey)


if __name__ == "__main__":
    unittest.main()
