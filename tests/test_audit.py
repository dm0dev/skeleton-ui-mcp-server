"""
Pytest integrity tests for static/ data and _llms.txt format.
Run with: uv run --group dev pytest tests/test_audit.py -v
"""
import json
import os
import re

import pytest

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "skeleton_ui_mcp_server", "static")

with open(os.path.join(STATIC_DIR, "_index_list.json")) as _f:
    _INDEX: list[dict] = json.load(_f)

with open(os.path.join(STATIC_DIR, "_llms.txt")) as _f:
    _LLMS_LINES: list[str] = _f.read().splitlines()

ALL_SLUGS = [e["slug"] for e in _INDEX]
ENTRY_LINES = [l for l in _LLMS_LINES if l.strip().startswith("- [")]
GROUP_LINES = [l for l in _LLMS_LINES if l.strip().startswith("### ")]

REQUIRED_DOC_FIELDS = ("title", "group", "url", "content")
REQUIRED_INDEX_FIELDS = ("title", "group", "url", "slug", "excerpt")


# ---------------------------------------------------------------------------
# _llms.txt format — these guard against upstream format changes that would
# silently break index.py's parser if skeleton.dev changes its llms.txt layout
# ---------------------------------------------------------------------------

class TestLlmsTxtFormat:
    def test_file_is_not_empty(self):
        assert any(l.strip() for l in _LLMS_LINES)

    def test_has_group_headers(self):
        assert len(GROUP_LINES) >= 1, "Expected at least one ### group header"

    def test_all_entries_have_svelte_in_path(self):
        bad = [l for l in ENTRY_LINES if "/svelte/" not in l]
        assert not bad, f"Entries missing /svelte/ in URL: {bad}"

    def test_entry_url_format_matches_parser_expectation(self):
        # index.py splits on '](' and strips trailing ')', so format must be
        # exactly: - [Title](/docs/svelte/category/page.md)
        pattern = re.compile(r"^- \[.+\]\(/docs/svelte/.+\.md\)$")
        bad = [l for l in ENTRY_LINES if not pattern.match(l.strip())]
        assert not bad, f"Entries with unexpected URL format: {bad}"

    def test_every_entry_belongs_to_a_group(self):
        current_group = None
        for line in _LLMS_LINES:
            stripped = line.strip()
            if stripped.startswith("### "):
                current_group = stripped
            if stripped.startswith("- ["):
                assert current_group is not None, f"Entry without preceding group: {line!r}"

    def test_urls_are_relative_not_absolute(self):
        # index.py prepends BASE_URL, so entries must use relative paths starting with /
        bad = [l for l in ENTRY_LINES if "https://" in l]
        assert not bad, f"Entries with absolute URLs (should be relative): {bad}"


# ---------------------------------------------------------------------------
# Index ↔ file consistency
# ---------------------------------------------------------------------------

class TestIndexFileConsistency:
    def test_all_index_slugs_have_json_files(self):
        missing = [e["slug"] for e in _INDEX
                   if not os.path.exists(os.path.join(STATIC_DIR, f"{e['slug']}.json"))]
        assert not missing, f"Missing JSON files for slugs: {missing}"

    def test_no_orphaned_json_files(self):
        slugs = {e["slug"] for e in _INDEX}
        on_disk = {f[:-5] for f in os.listdir(STATIC_DIR)
                   if f.endswith(".json") and not f.startswith("_")}
        orphans = on_disk - slugs
        assert not orphans, f"JSON files with no index entry: {orphans}"


# ---------------------------------------------------------------------------
# Index entry completeness — parametrized per field so failures are precise
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("field", REQUIRED_INDEX_FIELDS)
def test_index_entries_have_field(field: str):
    missing = [e.get("slug", "?") for e in _INDEX if not e.get(field)]
    assert not missing, f"Index entries missing '{field}': {missing}"


# ---------------------------------------------------------------------------
# Doc file content integrity — one test per slug so failures are precise
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("slug", ALL_SLUGS)
def test_doc_file_has_required_fields(slug: str):
    with open(os.path.join(STATIC_DIR, f"{slug}.json")) as f:
        doc = json.load(f)
    for field in REQUIRED_DOC_FIELDS:
        assert doc.get(field), f"{slug}: missing or empty '{field}'"
