"""
Pytest smoke tests for the MCP tools in main.py.
Run with: uv run --group dev pytest scripts/test_tools.py -v
"""
import pytest

from main import get_docs_for, list_all_docs, list_docs_by_group, search_docs


class TestSearchDocs:
    async def test_known_query_returns_top_match(self):
        result = await search_docs("dialog")
        assert "framework-components-dialog" in result

    async def test_unknown_query_returns_no_results_message(self):
        result = await search_docs("xyzzy_nonsense_404")
        assert "No results found" in result

    async def test_multi_word_query(self):
        result = await search_docs("toast notification")
        assert "toast" in result.lower()

    async def test_limit_caps_results(self):
        result = await search_docs("component", limit=2)
        assert result.count("slug") <= 2

    async def test_limit_above_max_is_capped(self):
        result = await search_docs("component", limit=999)
        assert result.count("slug") <= 10


class TestListDocsByGroup:
    async def test_framework_components_contains_accordion(self):
        result = await list_docs_by_group("Framework Components")
        assert "accordion" in result.lower()

    async def test_tailwind_components_contains_buttons(self):
        result = await list_docs_by_group("Tailwind Components")
        assert "button" in result.lower()

    async def test_invalid_group_returns_error(self):
        result = await list_docs_by_group("Bogus Group")
        assert "error" in result.lower()

    async def test_invalid_group_error_includes_valid_groups(self):
        result = await list_docs_by_group("Bogus Group")
        assert "valid_groups" in result.lower()


class TestListAllDocs:
    async def test_returns_all_58_docs(self):
        result = await list_all_docs()
        assert result.count("slug:") == 58

    async def test_result_covers_all_groups(self):
        result = await list_all_docs()
        for group in ("Get Started", "Framework Components", "Design System"):
            assert group in result


class TestGetDocsFor:
    async def test_valid_slug_starts_with_frontmatter(self):
        result = await get_docs_for("framework-components-accordion")
        assert result.startswith("---")

    async def test_frontmatter_contains_title(self):
        result = await get_docs_for("framework-components-accordion")
        assert "title: Accordion" in result

    async def test_frontmatter_contains_group(self):
        result = await get_docs_for("framework-components-accordion")
        assert "group: Framework Components" in result

    async def test_frontmatter_contains_url(self):
        result = await get_docs_for("framework-components-accordion")
        assert "url: https://" in result

    async def test_body_contains_markdown_heading(self):
        result = await get_docs_for("framework-components-accordion")
        assert "# Accordion" in result

    async def test_body_contains_code_block(self):
        result = await get_docs_for("framework-components-accordion")
        assert "```" in result

    async def test_unknown_slug_returns_error_payload(self):
        result = await get_docs_for("nonexistent-slug-xyz")
        assert "error" in result.lower()

    async def test_unknown_slug_error_includes_recovery_hint(self):
        result = await get_docs_for("nonexistent-slug-xyz")
        assert "hint" in result.lower()
