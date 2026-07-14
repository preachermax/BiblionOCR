# TipTap Integration Sketch

TipTap should own browser-side authoring. The portal preview harness should own browser-side rendering of the normalized feed contract.

## Recommended Split

- TipTap editor: author and revise the content for each portal panel
- Django view layer: persist content, sanitize it, and publish it through the JSON feed contract
- Portal preview harness: render the published feed exactly as portal consumers will see it

## Content Flow

1. A TipTap editor session edits one logical panel at a time such as `main`, `secondary`, or `tertiary`.
2. TipTap exports HTML or structured JSON depending on what you want to store.
3. Django validates and sanitizes the submitted content.
4. Django publishes normalized panel payloads through the same `panels` JSON shape used by `PortalFeedViews.py`.
5. The portal preview harness, the eventual portal pages, and any Qt-based preview clients all consume that same published feed.

## Storage Recommendation

- Store canonical authoring content in a structured format when possible.
- Publish sanitized HTML in the feed contract for straightforward rendering.

That means TipTap can keep richer editing semantics while the published portal feed remains simple:

```json
{
  "title": "Biblion Portal Feed",
  "panels": {
    "main": { "html": "<h1>Portal Landing Feed</h1>" },
    "secondary": { "html": "<p>Status content</p>" },
    "tertiary": { "html": "<p>Activity content</p>" }
  }
}
```

## Suggested API Shape

- `GET /portal/feed/`: return the published JSON feed for renderers
- `GET /portal/editor/<panel>/`: return editor bootstrap data for one panel
- `POST /portal/editor/<panel>/`: accept TipTap output, validate it, and save a draft or published revision

## Why This Split Is Better Than Reusing HTMLUIMain.py

- It matches the eventual browser runtime instead of a Qt-only preview shell.
- It separates authoring from rendering.
- It keeps the feed contract stable across Django pages, TipTap authoring tools, and any remaining desktop preview utilities.