# Skeleton UI MCP Server

An MCP server that exposes the [Skeleton UI](https://www.skeleton.dev) documentation as tools for coding agents. 
Documentation is served from pre-fetched static files — no live network calls during tool use.

## Tools

| Tool                         | Description                                                                                       |
|------------------------------|---------------------------------------------------------------------------------------------------|
| `search_docs(query, limit?)` | Keyword search across titles, slugs, excerpts, and groups. Use this first to find the right slug. |
| `list_docs_by_group(group)`  | List all docs in a category (e.g. `"Framework Components"`).                                      |
| `list_all_docs()`            | Full index of all 58 docs. Prefer the tools above.                                                |
| `get_docs_for(slug)`         | Returns full Markdown documentation for a slug.                                                   |

## Installation

Requires [uv](https://docs.astral.sh/uv/).

```bash
git clone <repo>
cd skeleton-ui-mcp-server
uv sync
```

## Claude Desktop Configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "skeleton-ui-docs": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/skeleton-ui-mcp-server",
        "run",
        "python",
        "main.py"
      ]
    }
  }
}
```

## Refreshing the Static Files

The `static/` directory contains pre-fetched documentation from `skeleton.dev`. To refresh it manually:

```bash
uv run --extra fetch python index.py
```

This re-fetches all pages listed in `static/_llms.txt` and regenerates the individual JSON files.

A GitHub Actions workflow (`.github/workflows/update-static.yml`) runs this automatically every night at 03:00 UTC and commits any changes back to the repository. It can also be triggered manually via **Actions → Update static docs → Run workflow**. The integrity tests (`tests/test_audit.py`) run as part of the workflow before committing — if they fail the commit is skipped.

## Quality Assurance

Install dev dependencies first:

```bash
uv sync --group dev
```

| Command                                            | What it does                                        |
|----------------------------------------------------|-----------------------------------------------------|
| `uv run --group dev pytest -v`                     | Run all tests (tool smoke tests + static integrity) |
| `uv run --group dev pytest tests/test_tools.py -v` | MCP tool tests only                                 |
| `uv run --group dev pytest tests/test_audit.py -v` | Static data + `_llms.txt` format tests only         |
| `uv run --group dev pyright`                       | Type-check `main.py` and `index.py`                 |
| `uv run --group dev pip-audit`                     | Scan dependencies for known vulnerabilities         |
