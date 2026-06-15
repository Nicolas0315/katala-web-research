import unittest
from io import StringIO
from unittest.mock import patch

from katala_web_research.cli import main


class CliDoctorTests(unittest.TestCase):
    def test_doctor_can_run_searxng_preflight(self):
        probe = {
            "provider": "searxng",
            "status": "ok",
            "url": "http://localhost:8080/search",
            "status_code": 200,
            "result_count": 2,
        }
        with patch("katala_web_research.cli.searxng_preflight", return_value=probe):
            with patch("sys.stdout", new_callable=StringIO) as stdout:
                code = main(["doctor", "--check-searxng"])

        self.assertEqual(code, 0)
        self.assertIn("searxng_preflight: ok - results=2 status=200", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
