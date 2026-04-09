import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("skeleton-ui-docs")
BASE_DIR = Path(__file__).parent


def _load_index() -> list:
    with open(BASE_DIR / "static" / "_index_list.json") as f:
        return json.load(f)


def _load_themes() -> dict:
    with open(BASE_DIR / "static" / "_themes.json") as f:
        return json.load(f)


VALID_GROUPS: list[str] = sorted({entry["group"] for entry in _load_index()})


@mcp.tool()
async def list_themes() -> str:
    """
    List all available Skeleton UI preset themes.
    Returns a list of theme names that can be used with get_theme_info.
    """
    themes = _load_themes()
    return json.dumps(list(themes.keys()), ensure_ascii=False)


@mcp.tool()
async def get_theme_info(theme: str) -> str:
    """
    Get detailed design token information for a specific Skeleton UI theme.
    Includes colors, fonts, border radius, and spacing.
    """
    themes = _load_themes()
    if theme not in themes:
        return json.dumps({
            "error": "Unknown theme",
            "theme": theme,
            "available_themes": list(themes.keys())
        }, ensure_ascii=False)
    return json.dumps(themes[theme], indent=2, ensure_ascii=False)


@mcp.tool()
async def get_theme_guide() -> str:
    """
    Get guidance on where to find the currently used theme and where to place custom themes.
    Covers both Skeleton v2 and v3 (Next) patterns.
    """
    guide = """
# Skeleton UI Theme Guide

## Finding the Current Theme

### Skeleton v3 (Next)
Themes are registered as Tailwind plugins in your `tailwind.config.ts` (or `tailwind.config.js`).
Look for the `skeleton` plugin registration:

```typescript
// tailwind.config.ts
import { skeleton } from '@skeletonlabs/skeleton/plugin';
import * as themes from '@skeletonlabs/skeleton/themes';

export default {
    // ...
    plugins: [
        skeleton({
            themes: [ themes.cerberus, themes.modern ] // Active themes listed here
        })
    ]
}
```

The active theme is typically set on the `<body>` or a wrapper element via `data-theme`:
`<body data-theme="cerberus">`

### Skeleton v2 (Legacy)
Themes are imported as CSS files, usually in your root layout: `src/routes/+layout.svelte`.

```html
<script>
    import '@skeletonlabs/skeleton/themes/theme-skeleton.css';
    // ...
</script>
```

## Custom Themes

### Skeleton v3 (Next)
Custom themes in v3 are defined as TypeScript objects. You can place them anywhere, but `src/themes.ts` is a common convention.

```typescript
// src/my-custom-theme.ts
import type { CustomThemeConfig } from '@skeletonlabs/skeleton/plugin';
export const myCustomTheme: CustomThemeConfig = {
    name: 'my-custom-theme',
    properties: {
        // ... design tokens
    }
};
```

Then register it in `tailwind.config.ts`.

### Skeleton v2 (Legacy)
Custom themes in v2 are CSS files. You can generate them using the [Skeleton Theme Generator](https://www.skeleton.dev/docs/generator).
Conventionally placed in `src/theme.css`.

Import it in `src/routes/+layout.svelte` instead of a preset theme.
"""
    return guide


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


@mcp.tool()
async def get_component_examples(slug: str) -> str:
    """
    Extract only the svelte code blocks from the documentation for a given slug.
    Developers often only need the copy-pasteable boilerplate.
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
    
    examples = j.get("examples", [])
    if not examples:
        return json.dumps({"message": "No examples found for this component."}, ensure_ascii=False)
    
    return json.dumps(examples, ensure_ascii=False)

@mcp.tool()
async def get_doc_section(slug: str, heading: str) -> str:
    """
    Instead of fetching the whole page, fetch just a specific section like "API Reference" or "Installation".
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
    
    sections = j.get("sections", {})
    if heading not in sections:
        return json.dumps({
            "error": "Heading not found",
            "heading": heading,
            "available_headings": [s["heading"] for s in j.get("outline", [])]
        }, ensure_ascii=False)
    
    return sections[heading]

@mcp.tool()
async def get_doc_outline(slug: str) -> str:
    """
    A quick way to see the table of contents for a doc so the LLM can decide which specific section to fetch.
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
    
    outline = j.get("outline", [])
    return json.dumps(outline, ensure_ascii=False)


def run() -> None:
    mcp.run()


if __name__ == "__main__":
    run()
