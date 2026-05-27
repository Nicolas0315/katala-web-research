import unittest
from unittest.mock import patch

from katala_web_research.models import SearchResult
from katala_web_research.planner import build_search_plan, format_search_plan
from katala_web_research.workflow import search_with_plan


class PlannerTests(unittest.TestCase):
    def test_build_search_plan_adds_research_intents(self):
        plan = build_search_plan("agentic retrieval", max_subqueries=3, year=2026)

        self.assertEqual([step.intent for step in plan], ["baseline", "official", "primary"])
        self.assertIn("official docs", plan[1].query)
        self.assertIn("arxiv", plan[2].query)

    def test_format_search_plan_is_compact(self):
        plan = build_search_plan("source quality", max_subqueries=1)

        self.assertEqual(format_search_plan(plan), ["baseline: source quality"])

    def test_search_with_plan_dedupes_and_limits(self):
        def fake_search(query, *, provider, limit):
            return [
                SearchResult(title=query, url="https://docs.github.com/example", source=provider, rank=1),
                SearchResult(title="duplicate", url="https://docs.github.com/example/", source=provider, rank=2),
                SearchResult(title="paper", url=f"https://arxiv.org/abs/{len(query)}", source=provider, rank=3),
            ][:limit]

        with patch("katala_web_research.workflow.search", side_effect=fake_search):
            results, plan = search_with_plan(
                "agentic retrieval",
                provider="ddg",
                limit=3,
                expand_queries=True,
                max_subqueries=2,
            )

        self.assertEqual(len(plan), 2)
        self.assertLessEqual(len(results), 3)
        self.assertEqual(len({result.url.rstrip('/') for result in results}), len(results))


if __name__ == "__main__":
    unittest.main()
