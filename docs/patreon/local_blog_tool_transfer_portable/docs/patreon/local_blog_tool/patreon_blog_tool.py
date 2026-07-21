from __future__ import annotations

import argparse
from datetime import date, timedelta
import importlib
import importlib.util
import json
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import time
from typing import Iterable
import webbrowser


ROOT = Path(__file__).resolve().parent
QUEUE_PATH = ROOT / "blog_queue.json"
OUTPUT_DIR = ROOT / "generated"
ARCHIVE_PATH = ROOT / "posted_posts.jsonl"
PLAYWRIGHT_PROFILE_DIR = ROOT / "playwright_profile"
PATREON_COMPOSE_URL = "https://www.patreon.com/posts/new"
CONFIG_PATH = ROOT / "patreon_post_config.json"
AUDIENCES = {"public", "members_only"}
GITHUB_BLOB_BASE = "https://github.com/preachermax/BiblionOCR/blob/master"
LEGACY_PUBLIC_WEBSITE_URLS = {
    "https://cdn.jsdelivr.net/gh/preachermax/BiblionOCR@master/docs/website/preview.html",
    "https://cdn.jsdelivr.net/gh/preachermax/BiblionOCR/docs/website/preview.html",
    "https://github.com/preachermax/BiblionOCR/blob/master/docs/website/preview.html",
    "https://github.com/preachermax/BiblionOCR/blob/master/docs/website/index.html",
}
QUEUE_REPO_DIR = PurePosixPath("docs/patreon/local_blog_tool")
MARKDOWN_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
PLAIN_REPO_PATH_PATTERN = re.compile(r"(?P<path>(?:\.\.?/)+[A-Za-z0-9_./-]+\.[A-Za-z0-9]+|docs/[A-Za-z0-9_./-]+\.[A-Za-z0-9]+)")
URL_PATTERN = re.compile(r"https?://\S+")

DEFAULT_POSTING_CONFIG = {
    "compose_url": PATREON_COMPOSE_URL,
    "public_website_url": "",
    "post_success_url_patterns": [r"/posts/(?!new)"],
    "selectors": {
        "title": [
            "input[placeholder*='title' i]",
            "textarea[placeholder*='title' i]",
            "[contenteditable='true']",
        ],
        "body": [
            "textarea[placeholder*='write' i]",
            "textarea[placeholder*='text' i]",
            "div[contenteditable='true'][role='textbox']",
            "textarea",
            "[contenteditable='true']",
        ],
    },
    "buttons": {
        "access": [
            "Who can see this post",
            "Edit access",
            "Public",
            "Members only",
            "Paid members only",
        ],
        "publish": ["Publish now", "Publish"],
    },
    "visibility_options": {
        "public": ["Anyone can see this post", "Public", "Anyone can view"],
        "members_only": ["Paid members only", "Members only", "Patrons only"],
    },
}


@dataclass
class BlogLink:
    label: str
    path: str
    note: str


@dataclass
class BlogSection:
    heading: str
    paragraphs: list[str]


@dataclass
class BlogPost:
    scheduled_date: str
    slug: str
    title: str
    audience_intent: str
    visibility: str
    excerpt: str
    tags: list[str]
    call_to_action: str
    links: list[BlogLink]
    sections: list[BlogSection]
    pre_post_body: str = ""

    @classmethod
    def from_dict(cls, payload: dict) -> "BlogPost":
        audience_intent = payload["audience_intent"]
        visibility = payload["visibility"]
        validate_audience(audience_intent)
        validate_audience(visibility)
        return cls(
            scheduled_date=payload["scheduled_date"],
            slug=payload["slug"],
            title=payload["title"],
            audience_intent=audience_intent,
            visibility=visibility,
            excerpt=payload["excerpt"],
            tags=list(payload.get("tags", [])),
            call_to_action=payload.get("call_to_action", ""),
            links=[BlogLink(**link) for link in payload.get("links", [])],
            sections=[BlogSection(**section) for section in payload.get("sections", [])],
            pre_post_body=payload.get("pre_post_body", "").strip(),
        )

    def to_dict(self) -> dict:
        return {
            "scheduled_date": self.scheduled_date,
            "slug": self.slug,
            "title": self.title,
            "audience_intent": self.audience_intent,
            "visibility": self.visibility,
            "excerpt": self.excerpt,
            "tags": self.tags,
            "call_to_action": self.call_to_action,
            "links": [link.__dict__ for link in self.links],
            "sections": [section.__dict__ for section in self.sections],
            "pre_post_body": self.pre_post_body,
        }


def validate_audience(value: str) -> None:
    if value not in AUDIENCES:
        raise ValueError(f"Unsupported audience '{value}'. Expected one of: {sorted(AUDIENCES)}")


def load_queue() -> list[BlogPost]:
    payload = json.loads(QUEUE_PATH.read_text(encoding="utf-8"))
    return [BlogPost.from_dict(entry) for entry in payload]


def save_queue(posts: Iterable[BlogPost]) -> None:
    serializable = [post.to_dict() for post in posts]
    QUEUE_PATH.write_text(json.dumps(serializable, indent=2) + "\n", encoding="utf-8")


def load_posting_config() -> dict:
    config = json.loads(json.dumps(DEFAULT_POSTING_CONFIG))
    if not CONFIG_PATH.exists():
        return config
    user_config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    deep_merge_dict(config, user_config)
    return config


def deep_merge_dict(target: dict, source: dict) -> None:
    for key, value in source.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            deep_merge_dict(target[key], value)
        else:
            target[key] = value


def collapse_posix_path(path: PurePosixPath) -> PurePosixPath:
    parts: list[str] = []
    for part in path.parts:
        if part in {"", "."}:
            continue
        if part == "..":
            if parts:
                parts.pop()
            continue
        parts.append(part)
    return PurePosixPath(*parts)


def repo_blob_url(path: str) -> str:
    cleaned = path.strip()
    if not cleaned or re.match(r"^[a-z]+://", cleaned, flags=re.IGNORECASE):
        return cleaned
    if cleaned.startswith("docs/"):
        repo_path = collapse_posix_path(PurePosixPath(cleaned))
    else:
        repo_path = collapse_posix_path(QUEUE_REPO_DIR / PurePosixPath(cleaned))
    return f"{GITHUB_BLOB_BASE}/{repo_path.as_posix()}"


def normalize_repo_text(text: str) -> str:
    def replace_markdown_link(match: re.Match[str]) -> str:
        label, path = match.group(1), match.group(2)
        return f"[{label}]({repo_blob_url(path)})"

    normalized = MARKDOWN_LINK_PATTERN.sub(replace_markdown_link, text)
    protected_urls: list[str] = []

    def protect_url(match: re.Match[str]) -> str:
        protected_urls.append(match.group(0))
        return f"__URL_PLACEHOLDER_{len(protected_urls) - 1}__"

    protected = URL_PATTERN.sub(protect_url, normalized)
    rewritten = PLAIN_REPO_PATH_PATTERN.sub(lambda match: repo_blob_url(match.group("path")), protected)

    for index, url in enumerate(protected_urls):
        rewritten = rewritten.replace(f"__URL_PLACEHOLDER_{index}__", url)
    return rewritten


def resolve_public_website_url() -> str:
    posting_config = load_posting_config()
    return str(posting_config.get("public_website_url", "")).strip()


def rewrite_public_website_url(text: str) -> str:
    public_website_url = resolve_public_website_url()
    if not public_website_url:
        return text

    rewritten = text
    for legacy_url in LEGACY_PUBLIC_WEBSITE_URLS:
        rewritten = rewritten.replace(legacy_url, public_website_url)
    return rewritten


def render_link_path(path: str) -> str:
    rewritten_path = rewrite_public_website_url(path.strip())
    if rewritten_path != path.strip():
        return rewritten_path
    return repo_blob_url(rewritten_path)


def build_post_markdown(post: BlogPost) -> str:
    composer_body = build_composer_body(post)
    link_lines = []
    for link in post.links:
        link_lines.append(f"- [{link.label}]({render_link_path(link.path)})")
        if link.note:
            link_lines.append(f"  - {rewrite_public_website_url(link.note)}")

    section_lines = []
    for section in post.sections:
        section_lines.append(f"## {section.heading}")
        section_lines.append("")
        for paragraph in section.paragraphs:
            section_lines.append(normalize_repo_text(paragraph))
            section_lines.append("")

    lead_lines = [
        f"# {post.title}",
        "",
        *build_intro_paragraphs(post),
        "",
        f"- Scheduled date: {post.scheduled_date}",
        f"- Intended audience: {format_audience(post.audience_intent)}",
        f"- Current visibility: {format_audience(post.visibility)}",
        f"- Tags: {', '.join(post.tags) if post.tags else 'none'}",
        "",
        "## Excerpt",
        "",
        post.excerpt,
        "",
        "## Key Links",
        "",
    ]

    if not link_lines:
        link_lines.append("- No external links attached to this draft yet.")

    content = "\n".join(
        [
            *lead_lines,
            composer_body,
            "",
            *link_lines,
            "",
            *section_lines,
            "## Call To Action",
            "",
            normalize_repo_text(post.call_to_action),
            "",
        ]
    ).rstrip() + "\n"
    return content


def build_composer_body(post: BlogPost) -> str:
    if post.pre_post_body.strip():
        return rewrite_public_website_url(normalize_repo_text(post.pre_post_body.strip()))

    paragraphs = []
    paragraphs.extend(build_intro_paragraphs(post))
    paragraphs.append(normalize_repo_text(post.excerpt))
    for section in post.sections:
        paragraphs.append(section.heading + ":")
        paragraphs.extend(rewrite_public_website_url(normalize_repo_text(paragraph)) for paragraph in section.paragraphs)
    if post.links:
        paragraphs.append("Useful links:")
        for link in post.links:
            paragraphs.append(f"- {link.label}: {render_link_path(link.path)}")
    if post.call_to_action:
        paragraphs.append(rewrite_public_website_url(normalize_repo_text(post.call_to_action)))
    return "\n\n".join(paragraphs).strip()


def build_composer_packet(post: BlogPost) -> str:
    body = build_composer_body(post)
    return f"TITLE: {post.title}\nVISIBILITY: {format_audience(post.visibility)}\n\n{body}\n"


def render_composer_packet(post: BlogPost) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{post.scheduled_date}-{post.slug}-composer.txt"
    output_path.write_text(build_composer_packet(post), encoding="utf-8")
    return output_path


def copy_text_to_clipboard(text: str) -> bool:
    try:
        import tkinter as tk
    except ImportError:
        return False

    root = tk.Tk()
    root.withdraw()
    root.clipboard_clear()
    root.clipboard_append(text)
    root.update()
    root.destroy()
    return True


def prepare_manual_post(post: BlogPost, posting_config: dict, open_browser: bool = True) -> tuple[Path, Path, bool, str]:
    markdown_path = render_post(post)
    composer_path = render_composer_packet(post)
    clipboard_ok = copy_text_to_clipboard(build_composer_packet(post))
    compose_url = posting_config.get("compose_url", PATREON_COMPOSE_URL)
    if open_browser:
        webbrowser.open(compose_url)
    return markdown_path, composer_path, clipboard_ok, compose_url


def render_post(post: BlogPost) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{post.scheduled_date}-{post.slug}.md"
    content = build_post_markdown(post)
    output_path.write_text(content, encoding="utf-8")
    return output_path


def build_intro_paragraphs(post: BlogPost) -> list[str]:
    paragraphs = []
    if post.audience_intent != post.visibility:
        paragraphs.append(
            "This draft was planned as a members-only Patreon post, but it is being published publicly for now so the current stage of the work is easier to inspect from outside the membership wall."
        )
    elif post.visibility == "members_only":
        paragraphs.append(
            "This draft is written for members, so it stays closer to the active build surface and assumes interest in the day-to-day engineering and editorial decisions behind Biblion."
        )
    else:
        paragraphs.append(
            "This draft is written as a public-facing Patreon update, with enough context for someone following the project without needing to track every internal implementation detail."
        )
    paragraphs.append(
        f"Today’s focus is {post.title.lower()}, which sits at the intersection of the project’s public story and the practical work needed to keep the platform moving."
    )
    return paragraphs


def format_audience(value: str) -> str:
    return "Members only" if value == "members_only" else "Public"


def find_post(posts: list[BlogPost], slug: str | None) -> BlogPost:
    if slug is None:
        return posts[0]
    for post in posts:
        if post.slug == slug:
            return post
    raise SystemExit(f"No post found for slug '{slug}'.")


def queue_dates(posts: list[BlogPost]) -> list[date]:
    return [date.fromisoformat(post.scheduled_date) for post in posts]


def build_placeholder_post(posts: list[BlogPost]) -> BlogPost:
    next_day = max(queue_dates(posts)) + timedelta(days=1)
    next_day_text = next_day.isoformat()
    return BlogPost(
        scheduled_date=next_day_text,
        slug=f"draft-{next_day_text}",
        title=f"Draft Patreon Post for {next_day_text}",
        audience_intent="public",
        visibility="public",
        excerpt="Replace this placeholder with the next Patreon draft before the queue date arrives.",
        tags=["draft", "queue"],
        call_to_action="Replace this placeholder call to action with the real support ask for the next post.",
        links=[],
        sections=[
            BlogSection(
                heading="Draft Notes",
                paragraphs=[
                    "Decide whether this next post should be public or members only.",
                    "Turn the current week’s concrete progress into a publishable narrative before this date arrives.",
                ],
            )
        ],
    )


def archive_post(post: BlogPost, published_url: str) -> None:
    ARCHIVE_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "scheduled_date": post.scheduled_date,
        "slug": post.slug,
        "title": post.title,
        "audience_intent": post.audience_intent,
        "visibility": post.visibility,
        "published_url": published_url,
        "archived_at": date.today().isoformat(),
    }
    with ARCHIVE_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")


def roll_queue_after_post(posts: list[BlogPost], posted_slug: str) -> list[BlogPost]:
    remaining_posts = [post for post in posts if post.slug != posted_slug]
    if len(remaining_posts) == len(posts):
        raise SystemExit(f"No post found for slug '{posted_slug}'.")
    remaining_posts.append(build_placeholder_post(remaining_posts))
    return remaining_posts


def publish_to_patreon(post: BlogPost, body_markdown: str, headless: bool, posting_config: dict) -> str:
    try:
        playwright_sync_api = importlib.import_module("playwright.sync_api")
        PlaywrightTimeoutError = getattr(playwright_sync_api, "TimeoutError")
        sync_playwright = getattr(playwright_sync_api, "sync_playwright")
    except ImportError as exc:
        raise SystemExit(
            "The post command requires Playwright. Install it locally with 'pip install playwright' and 'python -m playwright install chromium'."
        ) from exc

    with sync_playwright() as playwright:
        launch_kwargs = {
            "user_data_dir": str(PLAYWRIGHT_PROFILE_DIR),
            "headless": headless,
        }
        if re.match(r"win", __import__("sys").platform, re.IGNORECASE):
            launch_kwargs["channel"] = "msedge"
        context = playwright.chromium.launch_persistent_context(**launch_kwargs)
        page = context.pages[0] if context.pages else context.new_page()
        compose_url = posting_config.get("compose_url", PATREON_COMPOSE_URL)
        page.goto(compose_url, wait_until="domcontentloaded")
        print("Complete Patreon login or 2FA in the opened browser if Patreon asks for it.")
        print("If Patreon does not return you to the composer automatically, navigate back to the new-post page after login.")

        title_field, body_field = wait_for_compose_ready(page, posting_config, compose_url)
        overwrite_editable(title_field, post.title)
        overwrite_editable(body_field, body_markdown)
        set_post_visibility(page, post.visibility, posting_config)
        click_publish(page, posting_config)

        try:
            wait_for_publish_confirmation(page, posting_config)
        except PlaywrightTimeoutError as exc:
            raise SystemExit(
                "The browser composer did not confirm publication. Review the Patreon window and rerun if the post did not publish."
            ) from exc

        published_url = page.url
        context.close()
        return published_url


def wait_for_compose_ready(page, posting_config: dict, compose_url: str):
    deadline = time.monotonic() + 1800
    title_selectors = posting_config.get("selectors", {}).get("title", DEFAULT_POSTING_CONFIG["selectors"]["title"])
    body_selectors = posting_config.get("selectors", {}).get("body", DEFAULT_POSTING_CONFIG["selectors"]["body"])
    last_hint_time = 0.0

    while time.monotonic() < deadline:
        title_field = find_first_visible_locator(page, title_selectors)
        body_field = find_first_visible_locator(page, body_selectors, disallow_placeholder_text="title")
        if title_field is not None and body_field is not None:
            return title_field, body_field

        now = time.monotonic()
        if now - last_hint_time > 15:
            print(f"Waiting for Patreon composer. Current page: {page.url}")
            last_hint_time = now

        page.wait_for_timeout(1500)

    raise SystemExit(
        f"Timed out waiting for Patreon composer at {compose_url}. Finish login and reopen the post flow when ready."
    )


def wait_for_publish_confirmation(page, posting_config: dict) -> None:
    url_patterns = posting_config.get("post_success_url_patterns", DEFAULT_POSTING_CONFIG["post_success_url_patterns"])
    for pattern in url_patterns:
        try:
            page.wait_for_url(re.compile(pattern), timeout=45000)
            return
        except Exception:
            continue
    raise SystemExit("Could not confirm the Patreon post publish redirect.")


def resolve_title_field(page, posting_config: dict):
    selectors = posting_config.get("selectors", {}).get("title", DEFAULT_POSTING_CONFIG["selectors"]["title"])
    locator = find_first_visible_locator(page, selectors)
    if locator is None:
        raise SystemExit("Could not find the Patreon title field.")
    return locator


def resolve_body_field(page, posting_config: dict):
    selectors = posting_config.get("selectors", {}).get("body", DEFAULT_POSTING_CONFIG["selectors"]["body"])
    locator = find_first_visible_locator(page, selectors, disallow_placeholder_text="title")
    if locator is not None:
        return locator

    editable_locator = page.locator("textarea, [contenteditable='true']")
    count = editable_locator.count()
    for index in range(count):
        locator = editable_locator.nth(index)
        if locator_is_visible(locator):
            placeholder = (locator.get_attribute("placeholder") or "").lower()
            if "title" not in placeholder:
                return locator
    raise SystemExit("Could not find the Patreon body field.")


def find_first_visible_locator(page, selectors: list[str], disallow_placeholder_text: str | None = None):
    for selector in selectors:
        matches = page.locator(selector)
        count = matches.count()
        for index in range(count):
            locator = matches.nth(index)
            if not locator_is_visible(locator):
                continue
            if disallow_placeholder_text:
                placeholder = (locator.get_attribute("placeholder") or "").lower()
                if disallow_placeholder_text.lower() in placeholder:
                    continue
            return locator
    return None


def locator_is_visible(locator) -> bool:
    try:
        locator.wait_for(state="visible", timeout=3000)
        return True
    except Exception:
        return False


def overwrite_editable(locator, value: str) -> None:
    locator.click()
    locator.press("Control+A")
    locator.press("Backspace")
    locator.type(value, delay=8)


def set_post_visibility(page, visibility: str, posting_config: dict) -> None:
    visibility_labels = posting_config.get("visibility_options", DEFAULT_POSTING_CONFIG["visibility_options"])
    access_button_patterns = posting_config.get("buttons", {}).get("access", DEFAULT_POSTING_CONFIG["buttons"]["access"])
    click_first_named_button(page, access_button_patterns)
    for label in visibility_labels[visibility]:
        option = page.get_by_text(label, exact=False)
        if option.count() > 0:
            option.first.click()
            return
    raise SystemExit(f"Could not set Patreon visibility to {visibility}.")


def click_publish(page, posting_config: dict) -> None:
    publish_patterns = posting_config.get("buttons", {}).get("publish", DEFAULT_POSTING_CONFIG["buttons"]["publish"])
    if not click_first_named_button(page, publish_patterns):
        raise SystemExit("Could not find the Patreon publish button.")


def click_first_named_button(page, patterns: list[str]) -> bool:
    for pattern in patterns:
        button = page.get_by_role("button", name=re.compile(pattern, re.IGNORECASE))
        if button.count() > 0:
            button.first.click()
            return True
    return False


def command_doctor(_: argparse.Namespace) -> int:
    posting_config = load_posting_config()
    print(f"CONFIG_PATH {CONFIG_PATH}")
    print(f"COMPOSE_URL {posting_config.get('compose_url', PATREON_COMPOSE_URL)}")
    print(f"TITLE_SELECTORS {len(posting_config.get('selectors', {}).get('title', []))}")
    print(f"BODY_SELECTORS {len(posting_config.get('selectors', {}).get('body', []))}")
    print(f"PUBLISH_BUTTON_PATTERNS {len(posting_config.get('buttons', {}).get('publish', []))}")
    print(f"ACCESS_BUTTON_PATTERNS {len(posting_config.get('buttons', {}).get('access', []))}")
    print(f"SUCCESS_URL_PATTERNS {len(posting_config.get('post_success_url_patterns', []))}")
    try:
        if importlib.util.find_spec("playwright") is None:
            raise ImportError("playwright")
        print("PLAYWRIGHT installed")
    except ImportError:
        print("PLAYWRIGHT missing")
    return 0


def command_list(_: argparse.Namespace) -> int:
    posts = load_queue()
    for index, post in enumerate(posts, start=1):
        print(
            f"{index}. {post.scheduled_date} | {post.slug} | "
            f"intent={post.audience_intent} | visibility={post.visibility} | {post.title}"
        )
    return 0


def command_render(args: argparse.Namespace) -> int:
    posts = load_queue()
    targets = posts if not args.slug else [find_post(posts, args.slug)]
    for post in targets:
        markdown_path = render_post(post)
        composer_path = render_composer_packet(post)
        print(markdown_path)
        print(composer_path)
    return 0


def command_set_visibility(args: argparse.Namespace) -> int:
    validate_audience(args.visibility)
    posts = load_queue()
    updated = False
    for post in posts:
        if post.slug == args.slug:
            post.visibility = args.visibility
            updated = True
            break
    if not updated:
        raise SystemExit(f"No post found for slug '{args.slug}'.")
    save_queue(posts)
    print(f"Updated {args.slug} visibility to {args.visibility}")
    return 0


def command_seed_week(args: argparse.Namespace) -> int:
    template_posts = json.loads((ROOT / "blog_queue.template.json").read_text(encoding="utf-8"))
    if QUEUE_PATH.exists() and not args.force:
        raise SystemExit("Queue already exists. Use --force to overwrite it.")
    start_date = date.fromisoformat(args.start_date) if args.start_date else date.today()
    for offset, post in enumerate(template_posts):
        post["scheduled_date"] = (start_date + timedelta(days=offset)).isoformat()
    QUEUE_PATH.write_text(json.dumps(template_posts, indent=2) + "\n", encoding="utf-8")
    print(QUEUE_PATH)
    return 0


def command_post(args: argparse.Namespace) -> int:
    posts = load_queue()
    post = find_post(posts, args.slug)
    rendered_path = render_post(post)
    body_markdown = build_post_markdown(post)
    posting_config = load_posting_config()

    if args.dry_run:
        rolled_queue = roll_queue_after_post(posts, post.slug)
        print(f"DRY_RUN render={rendered_path}")
        print(f"DRY_RUN publish_title={post.title}")
        print(f"DRY_RUN visibility={post.visibility}")
        print(f"DRY_RUN compose_url={posting_config.get('compose_url', PATREON_COMPOSE_URL)}")
        print(f"DRY_RUN next_queue_head={rolled_queue[0].slug}")
        print(f"DRY_RUN appended={rolled_queue[-1].slug}")
        return 0

    if args.automated:
        published_url = publish_to_patreon(post, body_markdown, headless=args.headless, posting_config=posting_config)
        archive_post(post, published_url)
        save_queue(roll_queue_after_post(posts, post.slug))
        print(f"POSTED {published_url}")
        return 0

    markdown_path, composer_path, clipboard_ok, compose_url = prepare_manual_post(
        post,
        posting_config,
        open_browser=not args.no_browser,
    )
    print(f"PREPARED render={markdown_path}")
    print(f"PREPARED composer_packet={composer_path}")
    print(f"PREPARED compose_url={compose_url}")
    print(f"PREPARED clipboard={'ok' if clipboard_ok else 'unavailable'}")
    print("Paste the packet into Patreon after login, then run `complete-post` for this slug to archive it and roll the queue.")
    return 0


def command_complete_post(args: argparse.Namespace) -> int:
    posts = load_queue()
    post = find_post(posts, args.slug)
    published_url = args.url or "manual://patreon-posted"
    archive_post(post, published_url)
    save_queue(roll_queue_after_post(posts, post.slug))
    print(f"COMPLETED {post.slug}")
    print(f"ARCHIVED {published_url}")
    return 0


def command_gui(_: argparse.Namespace) -> int:
    try:
        import tkinter as tk
        from tkinter import messagebox
        from tkinter import scrolledtext
    except ImportError as exc:
        raise SystemExit("Tkinter is not available in this Python environment. Use the CLI commands instead.") from exc

    def load_posts() -> list[BlogPost]:
        return load_queue()

    posts_cache = load_posts()
    root = tk.Tk()
    root.title("Patreon Blog Tool")
    root.geometry("1300x760")

    title_label = tk.Label(root, text="Patreon Blog Queue", font=("Segoe UI", 14, "bold"))
    title_label.pack(padx=12, pady=(12, 6), anchor="w")

    hint_label = tk.Label(
        root,
        text="Use Render or Post actions on the selected row. Running the script bare now opens this launcher.",
        font=("Segoe UI", 8),
    )
    hint_label.pack(padx=12, pady=(0, 8), anchor="w")

    content_frame = tk.Frame(root)
    content_frame.pack(fill="both", expand=True, padx=12, pady=6)

    listbox_frame = tk.Frame(content_frame)
    listbox_frame.pack(side="left", fill="both", expand=True)

    scrollbar = tk.Scrollbar(listbox_frame)
    scrollbar.pack(side="right", fill="y")

    listbox = tk.Listbox(
        listbox_frame,
        font=("Consolas", 9),
        activestyle="dotbox",
        selectmode=tk.SINGLE,
        yscrollcommand=scrollbar.set,
    )
    listbox.pack(side="left", fill="both", expand=True)
    scrollbar.config(command=listbox.yview)

    right_panel = tk.Frame(content_frame)
    right_panel.pack(side="left", fill="both", expand=True, padx=(12, 0))

    details_var = tk.StringVar()
    details_label = tk.Label(right_panel, textvariable=details_var, justify="left", anchor="w", font=("Segoe UI", 9))
    details_label.pack(fill="x", pady=(0, 8))

    preview_label = tk.Label(right_panel, text="Ready-To-Paste Composer Body", font=("Segoe UI", 11, "bold"))
    preview_label.pack(anchor="w", pady=(4, 6))

    preview_text = scrolledtext.ScrolledText(right_panel, wrap=tk.WORD, font=("Segoe UI", 9), height=24)
    preview_text.pack(fill="both", expand=True)
    preview_text.configure(state="disabled")

    button_row = tk.Frame(root)
    button_row.pack(fill="x", padx=12, pady=(0, 12))

    slow_button_row = tk.Frame(button_row)
    slow_button_row.pack(side="left")

    fast_button_row = tk.Frame(button_row)
    fast_button_row.pack(side="right")

    def selected_post() -> BlogPost | None:
        selection = listbox.curselection()
        if not selection:
            return None
        index = selection[0]
        if index < 0 or index >= len(posts_cache):
            return None
        return posts_cache[index]

    def update_details(*_args) -> None:
        post = selected_post()
        if post is None:
            details_var.set("Select a queued post to inspect or act on it.")
            preview_text.configure(state="normal")
            preview_text.delete("1.0", tk.END)
            preview_text.configure(state="disabled")
            return
        details_var.set(
            f"Title: {post.title}\n"
            f"Date: {post.scheduled_date} | Intent: {post.audience_intent} | Visibility: {post.visibility}\n"
            f"Slug: {post.slug}\n"
            f"Excerpt: {post.excerpt}"
        )
        preview_text.configure(state="normal")
        preview_text.delete("1.0", tk.END)
        preview_text.insert("1.0", build_composer_body(post))
        preview_text.configure(state="disabled")

    def refresh_posts(select_slug: str | None = None) -> None:
        nonlocal posts_cache
        posts_cache = load_posts()
        listbox.delete(0, tk.END)
        selected_index = 0
        for index, post in enumerate(posts_cache):
            listbox.insert(
                tk.END,
                f"{index + 1}. {post.scheduled_date} | {post.slug} | intent={post.audience_intent} | visibility={post.visibility} | {post.title}",
            )
            if select_slug and post.slug == select_slug:
                selected_index = index
        if posts_cache:
            listbox.selection_clear(0, tk.END)
            listbox.selection_set(selected_index)
            listbox.activate(selected_index)
        update_details()

    def render_selected() -> None:
        post = selected_post()
        if post is None:
            messagebox.showinfo("Patreon Blog Tool", "Select a post first.")
            return
        markdown_path = render_post(post)
        composer_path = render_composer_packet(post)
        messagebox.showinfo("Patreon Blog Tool", f"Rendered draft:\n{markdown_path}\n\nComposer packet:\n{composer_path}")

    def copy_title() -> None:
        post = selected_post()
        if post is None:
            messagebox.showinfo("Patreon Blog Tool", "Select a post first.")
            return
        root.clipboard_clear()
        root.clipboard_append(post.title)
        root.update()
        messagebox.showinfo("Patreon Blog Tool", "Copied title to clipboard.")

    def copy_body() -> None:
        post = selected_post()
        if post is None:
            messagebox.showinfo("Patreon Blog Tool", "Select a post first.")
            return
        root.clipboard_clear()
        root.clipboard_append(build_composer_body(post))
        root.update()
        messagebox.showinfo("Patreon Blog Tool", "Copied composer body to clipboard.")

    def copy_packet() -> None:
        post = selected_post()
        if post is None:
            messagebox.showinfo("Patreon Blog Tool", "Select a post first.")
            return
        root.clipboard_clear()
        root.clipboard_append(build_composer_packet(post))
        root.update()
        messagebox.showinfo("Patreon Blog Tool", "Copied title + body packet to clipboard.")

    def dry_run_selected() -> None:
        post = selected_post()
        if post is None:
            messagebox.showinfo("Patreon Blog Tool", "Select a post first.")
            return
        result = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "post", "--slug", post.slug, "--dry-run"],
            capture_output=True,
            text=True,
            check=False,
        )
        output = (result.stdout or "") + ("\n" + result.stderr if result.stderr else "")
        messagebox.showinfo("Patreon Dry Run", output.strip() or "Dry run completed.")

    def open_compose() -> None:
        compose_url = load_posting_config().get("compose_url", PATREON_COMPOSE_URL)
        webbrowser.open(compose_url)
        messagebox.showinfo("Patreon Blog Tool", f"Opened Patreon composer:\n{compose_url}")

    def post_selected() -> None:
        post = selected_post()
        if post is None:
            messagebox.showinfo("Patreon Blog Tool", "Select a post first.")
            return
        posting_config = load_posting_config()
        _, composer_path, clipboard_ok, compose_url = prepare_manual_post(post, posting_config, open_browser=True)
        messagebox.showinfo(
            "Patreon Blog Tool",
            (
                f"Prepared manual post workflow for {post.slug}.\n\n"
                f"Composer packet: {composer_path}\n"
                f"Composer URL: {compose_url}\n"
                f"Clipboard: {'ready' if clipboard_ok else 'unavailable'}\n\n"
                "Log in using your normal browser, paste the packet into Patreon, then click 'Complete Post' here after it is published."
            ),
        )

    def complete_post_selected() -> None:
        post = selected_post()
        if post is None:
            messagebox.showinfo("Patreon Blog Tool", "Select a post first.")
            return
        answer = messagebox.askyesno(
            "Patreon Blog Tool",
            f"Mark '{post.title}' as posted and roll the queue forward?",
        )
        if not answer:
            return
        command_complete_post(argparse.Namespace(slug=post.slug, url="manual://patreon-posted"))
        refresh_posts()
        messagebox.showinfo("Patreon Blog Tool", f"Marked {post.slug} as posted and rolled the queue.")

    def run_doctor() -> None:
        result = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "doctor"],
            capture_output=True,
            text=True,
            check=False,
        )
        output = (result.stdout or "") + ("\n" + result.stderr if result.stderr else "")
        messagebox.showinfo("Patreon Doctor", output.strip() or "Doctor check completed.")

    def refresh_button_action() -> None:
        current = selected_post()
        refresh_posts(current.slug if current else None)

    button_font = ("Segoe UI", 8)

    tk.Button(slow_button_row, text="Refresh", command=refresh_button_action, width=11, font=button_font).pack(side="left", padx=(0, 8))
    tk.Button(slow_button_row, text="Render", command=render_selected, width=11, font=button_font).pack(side="left", padx=(0, 8))
    tk.Button(slow_button_row, text="Copy Title", command=copy_title, width=11, font=button_font).pack(side="left", padx=(0, 8))
    tk.Button(slow_button_row, text="Copy Body", command=copy_body, width=11, font=button_font).pack(side="left", padx=(0, 8))
    tk.Button(slow_button_row, text="Dry Run", command=dry_run_selected, width=11, font=button_font).pack(side="left", padx=(0, 8))
    tk.Button(slow_button_row, text="Open Compose", command=open_compose, width=13, font=button_font).pack(side="left", padx=(0, 8))
    tk.Button(slow_button_row, text="Doctor", command=run_doctor, width=11, font=button_font).pack(side="left")

    tk.Button(fast_button_row, text="Copy Packet", command=copy_packet, width=11, font=button_font).pack(side="left", padx=(0, 8))
    tk.Button(fast_button_row, text="Post", command=post_selected, width=11, font=button_font).pack(side="left", padx=(0, 8))
    tk.Button(fast_button_row, text="Complete Post", command=complete_post_selected, width=13, font=button_font).pack(side="left")

    listbox.bind("<<ListboxSelect>>", update_details)
    refresh_posts()
    root.mainloop()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Maintain a local Patreon blog queue.")
    subparsers = parser.add_subparsers(dest="command")

    gui_parser = subparsers.add_parser("gui", help="Open the local Patreon blog launcher window.")
    gui_parser.set_defaults(handler=command_gui)

    list_parser = subparsers.add_parser("list", help="List the current seven-post queue.")
    list_parser.set_defaults(handler=command_list)

    render_parser = subparsers.add_parser("render", help="Render one or all Markdown drafts.")
    render_parser.add_argument("--slug", help="Render only the specified slug.")
    render_parser.set_defaults(handler=command_render)

    visibility_parser = subparsers.add_parser("set-visibility", help="Change the current visibility for a post.")
    visibility_parser.add_argument("slug", help="Slug of the post to update.")
    visibility_parser.add_argument("visibility", choices=sorted(AUDIENCES), help="New visibility value.")
    visibility_parser.set_defaults(handler=command_set_visibility)

    seed_parser = subparsers.add_parser("seed-week", help="Reset the queue from the saved weekly template.")
    seed_parser.add_argument("--start-date", help="Optional ISO date for the first post in the seven-day queue.")
    seed_parser.add_argument("--force", action="store_true", help="Overwrite the current queue.")
    seed_parser.set_defaults(handler=command_seed_week)

    doctor_parser = subparsers.add_parser("doctor", help="Inspect the local Patreon posting configuration and environment.")
    doctor_parser.set_defaults(handler=command_doctor)

    post_parser = subparsers.add_parser("post", help="Prepare a Patreon post in your normal browser, or use automation only when explicitly requested.")
    post_parser.add_argument("--slug", help="Optional slug to publish. Defaults to the first queued post.")
    post_parser.add_argument("--dry-run", action="store_true", help="Preview the publish and queue-roll behavior without touching Patreon.")
    post_parser.add_argument("--automated", action="store_true", help="Use the Playwright automation flow instead of the manual browser workflow.")
    post_parser.add_argument("--headless", action="store_true", help="Run browser automation headlessly after the Patreon session is already established.")
    post_parser.add_argument("--no-browser", action="store_true", help="Prepare the packet without opening Patreon in the browser.")
    post_parser.set_defaults(handler=command_post)

    complete_post_parser = subparsers.add_parser("complete-post", help="Archive a manually published Patreon post and roll the queue forward.")
    complete_post_parser.add_argument("slug", help="Slug of the post that has already been published manually.")
    complete_post_parser.add_argument("--url", help="Optional published Patreon URL to archive with the post record.")
    complete_post_parser.set_defaults(handler=command_complete_post)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not hasattr(args, "handler"):
        args.handler = command_gui
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())