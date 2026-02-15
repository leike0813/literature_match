import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from normalize import extract_arxiv_id, extract_doi, extract_first_url, extract_year, normalize_doi, normalize_url


class TestNormalize(unittest.TestCase):
    def test_normalize_doi(self) -> None:
        self.assertEqual(normalize_doi("https://doi.org/10.48550/arXiv.2406.03459"), "10.48550/arxiv.2406.03459")
        self.assertEqual(normalize_doi("DOI:10.1000/xyz"), "10.1000/xyz")
        self.assertIsNone(normalize_doi("  "))

    def test_normalize_url(self) -> None:
        self.assertEqual(normalize_url("https://www.arxiv.org/abs/2406.03459/"), "arxiv.org/abs/2406.03459")
        self.assertEqual(normalize_url("http://arxiv.org/abs/2406.03459"), "arxiv.org/abs/2406.03459")
        self.assertIsNone(normalize_url(""))

    def test_extract_helpers(self) -> None:
        text = "See https://arxiv.org/abs/2406.03459 and DOI:10.48550/arXiv.2406.03459."
        self.assertEqual(extract_first_url(text), "https://arxiv.org/abs/2406.03459")
        self.assertEqual(extract_doi(text), "10.48550/arXiv.2406.03459")
        self.assertEqual(extract_arxiv_id(text), "2406.03459")

    def test_extract_year_ignores_arxiv_url_and_accessed(self) -> None:
        self.assertIsNone(extract_year("arXiv:2010.04159"))
        self.assertEqual(extract_year("arXiv preprint arXiv:2406.03459 (2024)."), "2024")
        self.assertIsNone(extract_year("accessed October 31, 2025, https://cs231n.stanford.edu/2024/papers/x.pdf"))
        self.assertEqual(extract_year("Some paper, 2020, accessed October 31, 2025, https://example.com/"), "2020")


if __name__ == "__main__":
    unittest.main()
