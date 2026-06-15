import unittest

from katala_web_research.query_builder import build_search_query, categorize_url


class SearchQueryBuilderTests(unittest.TestCase):
    def test_builds_github_pdf_and_domain_filters(self):
        built = build_search_query(
            "agent search",
            categories=["github", "pdf"],
            include_domains=["https://docs.example.com/path", "example.org"],
            exclude_domains=["blog.example.com"],
        )

        self.assertIn("site:github.com", built.query)
        self.assertIn("filetype:pdf", built.query)
        self.assertIn("(site:docs.example.com OR site:example.org)", built.query)
        self.assertIn("-site:blog.example.com", built.query)
        self.assertTrue(built.pdf_requested)
        self.assertEqual(built.category_domains["github.com"], "github")

    def test_research_category_uses_primary_research_domains(self):
        built = build_search_query("agent search", categories=["research"])

        self.assertIn("site:arxiv.org", built.query)
        self.assertIn("site:pubmed.ncbi.nlm.nih.gov", built.query)
        self.assertEqual(built.category_domains["arxiv.org"], "research")

    def test_categorizes_urls_from_query_metadata(self):
        built = build_search_query("agent search", categories=["research", "pdf"])

        self.assertEqual(
            categorize_url(
                "https://arxiv.org/abs/1234",
                category_domains=built.category_domains,
                pdf_requested=built.pdf_requested,
            ),
            "research",
        )
        self.assertEqual(
            categorize_url(
                "https://example.com/paper.pdf",
                category_domains=built.category_domains,
                pdf_requested=built.pdf_requested,
            ),
            "pdf",
        )


if __name__ == "__main__":
    unittest.main()
