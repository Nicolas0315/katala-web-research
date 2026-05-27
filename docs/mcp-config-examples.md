# MCP Config Examples

These examples expose the same local-first research tools to agent clients:

- `kwr.search`
- `kwr.plan`
- `kwr.eval`
- `kwr.read`
- `kwr.query`
- `kwr.repos_query`
- `kwr.brief`
- `kwr.investigate`

## Codex

Observed local Codex config shape on this machine uses `[mcp_servers.<name>]` with `command`, `args`, and optional `env`.

```toml
[mcp_servers.katala_web_research]
command = "python3"
args = [
  "-m",
  "katala_web_research.cli",
  "mcp",
]

[mcp_servers.katala_web_research.env]
PYTHONPATH = "/path/to/katala-web-research/src"
KWR_SEARXNG_URL = "http://127.0.0.1:8080"
```

Add `BRAVE_SEARCH_API_KEY` or `JINA_API_KEY` only through your normal secret manager or shell environment. Do not commit secret values.

## Claude Code / Gemini CLI

Use the same stdio command when a client asks for an MCP server command:

```sh
PYTHONPATH=/path/to/katala-web-research/src \
python3 -m katala_web_research.cli mcp
```

For clients that accept JSON-style MCP server definitions, use this shape and adapt the surrounding config syntax:

```json
{
  "katala_web_research": {
    "command": "python3",
    "args": ["-m", "katala_web_research.cli", "mcp"],
    "env": {
      "PYTHONPATH": "/path/to/katala-web-research/src",
      "KWR_SEARXNG_URL": "http://127.0.0.1:8080"
    }
  }
}
```

## Smoke Test

The server speaks MCP-style framed JSON-RPC over stdio. The normal verification path is still:

```sh
scripts/verify.sh
PYTHONPATH=src python3 -m katala_web_research.cli doctor
```
