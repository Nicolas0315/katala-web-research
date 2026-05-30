import unittest
from datetime import date

from katala_web_research.models import SearchResult
from katala_web_research.source_quality import _freshness_bonus, source_quality_score


class FreshnessBonusTests(unittest.TestCase):
    def test_current_year_gets_full_bonus(self):
        self.assertEqual(_freshness_bonus(f"{date.today().year}-01-01"), 0.3)

    def test_last_year_gets_partial_bonus(self):
        self.assertEqual(_freshness_bonus(f"{date.today().year - 1}-06-01"), 0.15)

    def test_two_year_old_gets_no_bonus(self):
        self.assertEqual(_freshness_bonus(f"{date.today().year - 2}-06-01"), 0.0)

    def test_non_iso_and_missing_dates_are_ignored(self):
        self.assertEqual(_freshness_bonus("recently"), 0.0)
        self.assertEqual(_freshness_bonus("20"), 0.0)
        self.assertEqual(_freshness_bonus(None), 0.0)


class OverlapNormalizationTests(unittest.TestCase):
    def test_keyword_stuffed_low_quality_does_not_overtake_primary(self):
        query = "agentic retrieval source quality evaluation pipeline fusion"
        primary = SearchResult(
            title="Agentic retrieval pipeline",
            url="https://learn.microsoft.com/azure/agentic-retrieval",
            snippet="overview",
        )
        keyword_stuffed = SearchResult(
            title="Generic notes",
            url="https://example.com/blog",
            snippet="agentic retrieval source quality evaluation pipeline fusion explained",
        )

        self.assertGreater(
            source_quality_score(query, primary),
            source_quality_score(query, keyword_stuffed),
        )


if __name__ == "__main__":
    unittest.main()
