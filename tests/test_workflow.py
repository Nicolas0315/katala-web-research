import unittest
from unittest.mock import patch

from katala_web_research.models import PageSnapshot, SearchResult
from katala_web_research.workflow import enrich_search_results, search_with_plan


class SearchWithPlanTests(unittest.TestCase):
    def test_blank_query_with_expansion_falls_back_to_direct_search(self):
        with patch("katala_web_research.workflow.search", return_value=[]) as search:
            results, plan = search_with_plan("   ", provider="ddg", limit=5, expand_queries=True)

        self.assertEqual(results, [])
        self.assertEqual(plan, [])
        search.assert_called_once_with("   ", provider="ddg", limit=5)

    def test_candidate_multiplier_fetches_more_than_final_limit(self):
        candidates = [
            SearchResult(title=f"Agent research {idx}", url=f"https://example.com/{idx}", source="ddg", rank=idx)
            for idx in range(1, 7)
        ]
        with patch("katala_web_research.workflow.search", return_value=candidates) as search:
            results, plan = search_with_plan(
                "agent research",
                provider="ddg",
                limit=3,
                candidate_multiplier=2,
            )

        self.assertEqual(plan, [])
        search.assert_called_once_with("agent research", provider="ddg", limit=6)
        self.assertLessEqual(len(results), 3)

    def test_year_is_threaded_into_freshness_subquery(self):
        with patch("katala_web_research.workflow.search", return_value=[]):
            _results, plan = search_with_plan(
                "kubernetes scheduler",
                provider="ddg",
                limit=5,
                expand_queries=True,
                max_subqueries=5,
                year=2026,
            )

        intents = [step.intent for step in plan]
        self.assertIn("freshness", intents)

    def test_enrich_search_results_reads_top_candidates_and_reranks(self):
        results = [
            SearchResult(title="Thin", url="https://example.com/a", snippet="thin", source="ddg", rank=1),
            SearchResult(title="Plain", url="https://example.com/b", snippet="plain", source="ddg", rank=2),
        ]
        page = PageSnapshot(
            url="https://example.com/a",
            title="Deep source",
            content="agentic retrieval evaluation benchmark primary source",
            source="direct",
            fetched_at="2026-06-15T00:00:00+00:00",
            status_code=200,
        )

        with patch("katala_web_research.workflow.read_url", return_value=page) as read_url:
            enriched = enrich_search_results("agentic retrieval benchmark", results, read_top=1, reader="direct")

        read_url.assert_called_once_with("https://example.com/a", reader="direct")
        self.assertEqual(enriched[0].url, "https://example.com/a")
        self.assertIn("agentic retrieval evaluation", enriched[0].snippet)
        self.assertEqual(enriched[0].metadata["read_status"], "ok")

    def test_enrich_search_results_keeps_failures_observable(self):
        results = [SearchResult(title="Thin", url="https://example.com/a", snippet="thin", source="ddg", rank=1)]

        with patch("katala_web_research.workflow.read_url", side_effect=RuntimeError("nope")):
            enriched = enrich_search_results("agentic retrieval benchmark", results, read_top=1)

        self.assertEqual(enriched[0].metadata["read_status"], "error")
        self.assertEqual(enriched[0].metadata["read_error_kind"], "RuntimeError")


if __name__ == "__main__":
    unittest.main()
