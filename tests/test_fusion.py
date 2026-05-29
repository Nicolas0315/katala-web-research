import unittest

from katala_web_research.fusion import fuse_and_rank, reciprocal_rank_fusion
from katala_web_research.models import SearchResult


class FusionTests(unittest.TestCase):
    def test_rrf_promotes_cross_engine_consensus(self):
        fused = reciprocal_rank_fusion(
            [
                [
                    SearchResult(title="Outlier", url="https://example.com/outlier", source="a", rank=1),
                    SearchResult(title="Consensus result", url="https://docs.github.com/search", source="a", rank=3),
                ],
                [
                    SearchResult(title="Consensus result", url="https://docs.github.com/search/", source="b", rank=1),
                ],
            ]
        )

        self.assertEqual(fused[0].url, "https://docs.github.com/search/")
        self.assertEqual(fused[0].metadata["source_count"], 2)
        self.assertEqual(fused[0].metadata["engine_ranks"], {"a": 3, "b": 1})
        self.assertEqual(fused[0].metadata["engine_health"], {"a": 1.0, "b": 1.0})

    def test_rrf_downweights_unhealthy_engine(self):
        fused = reciprocal_rank_fusion(
            [
                [
                    SearchResult(
                        title="Slow outlier",
                        url="https://example.com/slow",
                        source="slow",
                        rank=1,
                        metadata={"engine_health_score": 0.2},
                    )
                ],
                [
                    SearchResult(
                        title="Healthy result",
                        url="https://example.com/healthy",
                        source="healthy",
                        rank=2,
                    )
                ],
            ],
            rrf_k=1,
        )

        self.assertEqual(fused[0].url, "https://example.com/healthy")
        self.assertEqual(fused[0].metadata["engine_health"], {"healthy": 1.0})

    def test_fuse_and_rank_keeps_limit(self):
        ranked = fuse_and_rank(
            "agent research",
            [
                [SearchResult(title="Agent research", url="https://example.com/a", source="a", rank=1)],
                [SearchResult(title="Agent research", url="https://example.com/b", source="b", rank=1)],
            ],
            limit=1,
        )

        self.assertEqual(len(ranked), 1)


if __name__ == "__main__":
    unittest.main()
