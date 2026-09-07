import argparse
import json

import docs.patreon.local_blog_tool.patreon_blog_tool as blog_tool
from docs.patreon.local_blog_tool.patreon_blog_tool import (
    BlogPost,
    BlogSection,
    build_editable_markdown,
    build_post_markdown,
    import_markdown_post,
    parse_markdown_post,
    save_edited_markdown,
)


def _post(*, sections: list[BlogSection], pre_post_body: str = "") -> BlogPost:
    return BlogPost(
        scheduled_date="2026-09-08",
        slug="test-post",
        title="Test Post",
        audience_intent="public",
        visibility="public",
        excerpt="A focused excerpt.",
        tags=["test"],
        call_to_action="Keep following the work.",
        links=[],
        sections=sections,
        pre_post_body=pre_post_body,
    )


def test_structured_post_renders_each_section_once():
    markdown = build_post_markdown(
        _post(sections=[BlogSection("What changed", ["A concrete improvement landed."])])
    )

    assert markdown.count("## What changed") == 1
    assert markdown.count("A concrete improvement landed.") == 1
    assert "## Post Body" not in markdown
    assert markdown.index("## Key Links") < markdown.index("## What changed")


def test_full_body_post_renders_body_once_without_structured_sections():
    markdown = build_post_markdown(_post(sections=[], pre_post_body="Full imported body."))

    assert markdown.count("Full imported body.") == 1
    assert "## Post Body\n\nFull imported body." in markdown
    assert markdown.index("## Post Body") < markdown.index("## Key Links")


def test_imported_markdown_replaces_content_but_preserves_queue_metadata(tmp_path):
    source = tmp_path / "External Case Study.md"
    source.write_text("# External Title\n\nFirst paragraph.\n\n## Detail\n\nMore text.\n", encoding="utf-8")
    post = _post(sections=[BlogSection("Old", ["Old body."])])

    imported = import_markdown_post(source, post)

    assert imported.scheduled_date == "2026-09-08"
    assert imported.audience_intent == "public"
    assert imported.title == "External Title"
    assert imported.slug == "external-case-study"
    assert imported.pre_post_body == "First paragraph.\n\n## Detail\n\nMore text."
    assert imported.sections == []
    assert build_editable_markdown(imported) == source.read_text(encoding="utf-8")


def test_parse_markdown_uses_filename_when_h1_is_absent():
    title, body = parse_markdown_post("Opening paragraph.\n", "Filename Title")

    assert title == "Filename Title"
    assert body == "Opening paragraph."


def test_save_edited_markdown_updates_queue_content_and_file(tmp_path, monkeypatch):
    monkeypatch.setattr(blog_tool, "OUTPUT_DIR", tmp_path)
    post = _post(sections=[BlogSection("Old", ["Old body."])])

    output_path = save_edited_markdown(post, "# Revised Title\n\nRevised body.\n")

    assert post.title == "Revised Title"
    assert post.pre_post_body == "Revised body."
    assert post.sections == []
    assert output_path.read_text(encoding="utf-8") == "# Revised Title\n\nRevised body.\n"


def test_import_command_defaults_to_external_folder_and_first_queue_slot(tmp_path, monkeypatch):
    external_dir = tmp_path / "external"
    external_dir.mkdir()
    (external_dir / "outside.md").write_text("# Imported\n\nImported body.\n", encoding="utf-8")
    queue_path = tmp_path / "queue.json"
    queue_path.write_text(json.dumps([_post(sections=[]).to_dict()]), encoding="utf-8")
    monkeypatch.setattr(blog_tool, "EXTERNAL_DIR", external_dir)
    monkeypatch.setattr(blog_tool, "QUEUE_PATH", queue_path)
    monkeypatch.setattr(blog_tool, "OUTPUT_DIR", tmp_path / "generated")

    result = blog_tool.command_import_markdown(argparse.Namespace(path="outside.md", replace_slug=None))

    imported = json.loads(queue_path.read_text(encoding="utf-8"))[0]
    assert result == 0
    assert imported["scheduled_date"] == "2026-09-08"
    assert imported["title"] == "Imported"
    assert imported["pre_post_body"] == "Imported body."
    assert (tmp_path / "generated" / "2026-09-08-outside.md").is_file()