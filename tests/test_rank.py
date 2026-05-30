import unittest

from katala_web_research.models import SearchResult
from katala_web_research.rank import rank_results


class RankTests(unittest.TestCase):
    def test_ranks_by_query_overlap_and_dedupes(self):
        results = [
            SearchResult(title="Unrelated", url="https://example.com/a", source="ddg", rank=1),
            SearchResult(title="Agent web research", url="https://example.com/b", source="ddg", rank=2),
            SearchResult(title="Duplicate", url="https://example.com/b/", source="ddg", rank=3),
        ]

        ranked = rank_results("agent research", results)

        self.assertEqual(ranked[0].url, "https://example.com/b")
        self.assertEqual(len(ranked), 2)
        self.assertGreater(ranked[0].score, ranked[1].score)

    def test_ranking_rewards_primary_sources_and_freshness(self):
        results = [
            SearchResult(title="Agentic retrieval overview", url="https://example.com/post", rank=1),
            SearchResult(
                title="Agentic retrieval paper",
                url="https://arxiv.org/abs/2603.13853",
                snippet="agentic retrieval evaluation",
                published_at="2026-03-14",
                rank=2,
            ),
        ]

        ranked = rank_results("agentic retrieval evaluation", results)

        self.assertEqual(ranked[0].url, "https://arxiv.org/abs/2603.13853")

    def test_diversity_drops_host_dominated_overflow(self):
        results = [
            SearchResult(title=f"Agent research {i}", url=f"https://example.com/p{i}", rank=i)
            for i in range(1, 7)
        ]
        results.append(
            SearchResult(title="Agent research docs", url="https://docs.github.com/agent", rank=7)
        )

        ranked = rank_results("agent research", results)
        example_hosts = [r.url for r in ranked if "example.com" in r.url]

        self.assertLess(len(ranked), 7)
        self.assertLessEqual(len(example_hosts), 3)
        self.assertIn("https://docs.github.com/agent", {r.url for r in ranked})


if __name__ == "__main__":
    unittest.main()
