import unittest

from katala_web_research.evaluation import build_eval_report, run_eval


class EvaluationTests(unittest.TestCase):
    def test_default_eval_passes(self):
        summary = run_eval(min_score=80)

        self.assertTrue(summary.passed)
        self.assertGreaterEqual(summary.score, 80)
        self.assertEqual(len(summary.cases), 3)

    def test_eval_report_includes_case_scores(self):
        summary = run_eval(min_score=80)
        report = build_eval_report(summary)

        self.assertIn("Research Quality Benchmark", report)
        self.assertIn("agentic_retrieval_prefers_official_and_primary", report)


if __name__ == "__main__":
    unittest.main()
