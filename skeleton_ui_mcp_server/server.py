import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("skeleton-ui-docs")
BASE_DIR = Path(__file__).parent


def _load_index() -> list:
    with open(BASE_DIR / "static" / "_index_list.json") as f:
        return json.load(f)


VALID_GROUPS: list[str] = sorted({entry["group"] for entry in _load_index()})


@mcp.tool()
async def search_docs(query: str, limit: int = 5) -> str:
    """
    Search Skeleton UI documentation by keyword. Returns matching docs with slug,
    title, group, and excerpt. Use this to find the right slug before calling
    get_docs_for. Examples: "dialog", "toast notification", "dark mode", "color theme".
    Returns at most `limit` results (default 5, max 10).
    """
    index = _load_index()
    keywords = query.lower().split()
    scored = []
    for entry in index:
        score = 0
        title = entry["title"].lower()
        slug = entry["slug"].lower()
        group = entry["group"].lower()
        excerpt = " ".join(entry["excerpt"]).lower()
        for kw in keywords:
            if kw in title:   score += 10
            if kw in slug:    score += 5
            if kw in excerpt: score += 3
            if kw in group:   score += 1
        if score > 0:
            scored.append((score, entry))
    scored.sort(key=lambda x: -x[0])
    cap = min(max(limit, 1), 10)
    results = [
        {"slug": e["slug"], "title": e["title"], "group": e["group"], "excerpt": e["excerpt"]}
        for _, e in scored[:cap]
    ]
    if not results:
        return json.dumps({"message": "No results found", "query": query}, ensure_ascii=False)
    return json.dumps(results, ensure_ascii=False)


@mcp.tool()
async def list_docs_by_group(group: str) -> str:
    """
    List all Skeleton UI docs in a specific category. Valid groups: "Get Started",
    "Guides", "Design System", "Tailwind Components", "Framework Components",
    "Integrations", "Resources". Returns slug, title, and excerpt for each doc.
    Use this to browse all options in a category rather than searching by keyword.
    """
    if group not in VALID_GROUPS:
        return json.dumps({"error": "Invalid group", "valid_groups": VALID_GROUPS}, ensure_ascii=False)
    index = _load_index()
    results = [
        {"slug": e["slug"], "title": e["title"], "excerpt": e["excerpt"]}
        for e in index if e["group"] == group
    ]
    return json.dumps(results, ensure_ascii=False)


@mcp.tool()
async def list_all_docs() -> str:
    """
    List all 58 available Skeleton UI docs with slug, title, group, and excerpt.
    Prefer search_docs for keyword lookup or list_docs_by_group to browse a category.
    Use this only when you need a complete index of all available documentation.
    """
    return json.dumps(_load_index(), ensure_ascii=False)


@mcp.tool()
async def get_docs_for(slug: str) -> str:
    """
    Get the full Markdown documentation for a Skeleton UI component or page by slug.
    Use search_docs or list_docs_by_group to find the correct slug first.
    Example slugs: "framework-components-dialog", "get-started-installation",
    "design-system-themes", "tailwind-components-buttons".
    """
    try:
        with open(BASE_DIR / "static" / f"{slug}.json") as f:
            j = json.load(f)
    except FileNotFoundError:
        return json.dumps({
            "error": "Unknown slug",
            "slug": slug,
            "hint": "Call search_docs or list_docs_by_group to find valid slugs.",
        }, ensure_ascii=False)
    frontmatter = f"---\ntitle: {j['title']}\ngroup: {j['group']}\nurl: {j['url']}\n---\n\n"
    return frontmatter + j["content"]


def run() -> None:
    mcp.run()


if __name__ == "__main__":
    run()
