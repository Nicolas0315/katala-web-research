import unittest

from katala_web_research.mcp_server import handle_request


class McpServerTests(unittest.TestCase):
    def test_initialize(self):
        response = handle_request({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        self.assertEqual(response["result"]["serverInfo"]["name"], "katala-web-research")
        self.assertIn("tools", response["result"]["capabilities"])

    def test_tools_list(self):
        response = handle_request({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        names = {tool["name"] for tool in response["result"]["tools"]}
        self.assertIn("kwr.search", names)
        self.assertIn("kwr.repos_query", names)
        self.assertIn("kwr.investigate", names)


if __name__ == "__main__":
    unittest.main()
