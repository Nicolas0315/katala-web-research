import pathlib
import unittest

from katala_web_research.providers import _DuckDuckGoHTMLParser
from katala_web_research.text import SimpleHTMLTextExtractor, normalize_url

_FIXTURES = pathlib.Path(__file__).parent / "fixtures"


class ParserTests(unittest.TestCase):
    def test_normalize_duckduckgo_redirect(self):
        url = "https://duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fa"
        self.assertEqual(normalize_url(url), "https://example.com/a")

    def test_extracts_basic_html_text(self):
        parser = SimpleHTMLTextExtractor()
        parser.feed("<html><head><title>T</title><script>x</script></head><body><h1>A</h1><p>B</p></body></html>")
        self.assertEqual(parser.title, "T")
        self.assertIn("A", parser.content)
        self.assertIn("B", parser.content)
        self.assertNotIn("x", parser.content)

    def test_parses_duckduckgo_html_results(self):
        html = """
        <a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fone">One</a>
        <a class="result__snippet">First snippet</a>
        <a class="result__a" href="https://example.com/two">Two</a>
        <div class="result__snippet">Second snippet</div>
        """
        parser = _DuckDuckGoHTMLParser()
        parser.feed(html)
        parser.close()
        self.assertEqual(len(parser.results), 2)
        self.assertEqual(parser.results[0].url, "https://example.com/one")
        self.assertEqual(parser.results[0].title, "One")

    def test_parses_duckduckgo_html_fixture(self):
        # Fixture-based regression: if DDG changes its CSS class names, the
        # parser returns 0 results instead of silently swallowing the change.
        html = (_FIXTURES / "sample.duckduckgo.html").read_text(encoding="utf-8")
        parser = _DuckDuckGoHTMLParser()
        parser.feed(html)
        parser.close()

        self.assertEqual(len(parser.results), 3)

        # First result — URL rewritten from DDG redirect
        self.assertEqual(parser.results[0].url, "https://docs.python.org/3/library/urllib.html")
        self.assertEqual(parser.results[0].title, "urllib.request — Python 3 docs")
        self.assertIn("Standard library HTTP client", parser.results[0].snippet)

        # Second result — plain URL, has snippet
        self.assertEqual(parser.results[1].url, "https://example.com/two")
        self.assertEqual(parser.results[1].title, "Second Result Title")
        self.assertIn("second search result", parser.results[1].snippet)

        # Third result — plain URL, no snippet (empty string, not None)
        self.assertEqual(parser.results[2].url, "https://example.com/three")
        self.assertEqual(parser.results[2].title, "Third Result With No Snippet")
        self.assertEqual(parser.results[2].snippet, "")

        # Every result must carry "ddg" as the source tag
        for r in parser.results:
            self.assertEqual(r.source, "ddg")


if __name__ == "__main__":
    unittest.main()

