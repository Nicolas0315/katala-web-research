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

    def test_future_year_gets_no_bonus(self):
        self.assertEqual(_freshness_bonus(f"{date.today().year + 1}-01-01"), 0.0)

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

    def test_substring_does_not_count_as_token_overlap(self):
        query = "on"
        substring_only = SearchResult(
            title="Optimization and personalization", url="https://example.com/x", snippet="comparison"
        )
        real_token = SearchResult(title="On the record", url="https://example.com/y", snippet="on")

        self.assertGreater(
            source_quality_score(query, real_token),
            source_quality_score(query, substring_only),
        )


if __name__ == "__main__":
    unittest.main()
