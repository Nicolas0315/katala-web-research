import unittest

from katala_web_research.providers import _DuckDuckGoHTMLParser
from katala_web_research.text import SimpleHTMLTextExtractor, normalize_url


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


if __name__ == "__main__":
    unittest.main()

