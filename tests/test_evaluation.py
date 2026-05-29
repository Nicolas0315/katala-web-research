import unittest

from katala_web_research.evaluation import build_eval_report, run_eval


class EvaluationTests(unittest.TestCase):
    def test_default_eval_passes(self):
        summary = run_eval(min_score=80)

        self.assertTrue(summary.passed)
        self.assertGreaterEqual(summary.score, 80)
        self.assertGreaterEqual(len(summary.cases), 10)
        self.assertIn("platform_api_docs", summary.category_scores)
        self.assertIn("bias_aware_news", summary.category_scores)
        self.assertIn("feed_monitoring", summary.category_scores)
        self.assertTrue(all(score >= 80 for score in summary.category_scores.values()))

    def test_eval_report_includes_case_scores(self):
        summary = run_eval(min_score=80)
        report = build_eval_report(summary)

        self.assertIn("Research Quality Benchmark", report)
        self.assertIn("Category Scores", report)
        self.assertIn("agentic_retrieval_prefers_official_and_primary", report)
        self.assertIn("category: platform_api_docs", report)


if __name__ == "__main__":
    unittest.main()
