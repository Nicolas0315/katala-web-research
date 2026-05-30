import unittest
from unittest.mock import patch

from katala_web_research.workflow import search_with_plan


class SearchWithPlanTests(unittest.TestCase):
    def test_blank_query_with_expansion_falls_back_to_direct_search(self):
        with patch("katala_web_research.workflow.search", return_value=[]) as search:
            results, plan = search_with_plan("   ", provider="ddg", limit=5, expand_queries=True)

        self.assertEqual(results, [])
        self.assertEqual(plan, [])
        search.assert_called_once_with("   ", provider="ddg", limit=5)

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


if __name__ == "__main__":
    unittest.main()
