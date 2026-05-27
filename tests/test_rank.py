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


if __name__ == "__main__":
    unittest.main()
