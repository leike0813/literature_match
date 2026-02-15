import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from bbt_library import build_library_index, load_betterbibtexjson_from_file


class TestBetterBibTeXParse(unittest.TestCase):
    def test_build_library_index_from_fixture(self) -> None:
        data = load_betterbibtexjson_from_file("examples/example_entry.library.betterbibtexjson")
        lib = build_library_index(data)

        self.assertGreaterEqual(lib.total_items, 1)
        self.assertGreaterEqual(lib.indexed_items, 1)

        record = lib.records.get("chen_lwdetr-transformer_2024")
        self.assertIsNotNone(record)
        assert record is not None
        self.assertEqual(record["citekey"], "chen_lwdetr-transformer_2024")
        self.assertTrue(record["itemKey"])
        self.assertTrue(record["title"])
        self.assertTrue(record["pdf_attachments"])
        self.assertIsInstance(record["zotero_tags"], list)


if __name__ == "__main__":
    unittest.main()

