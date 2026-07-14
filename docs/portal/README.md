# Biblion Portal Staging

This directory now serves two roles:

1. long-range portal planning for BiblionPortal
2. short-range staging for transfer-ready portal/editor assets being prepared inside BiblionOCR before migration

## Primary Planning Document

- [portal.md](portal.md)

## Transfer Bundles

### `HTMLEditorStandalone/`

Portable PyQt editor bundle prepared so it can be copied into the BiblionPortal project without dragging in unrelated desktop application files.

Contents include:

- `HTMLeditor.py`
- `HTMLeditorUI.py`
- `HTMLeditor.ui`
- `gui_runtime_env.py`

### `PortalFeed/`

Reference portal feed components copied together for transfer planning.

Contents currently include:

- `PortalFeedClient.py`: fetch/post client and payload normalization logic
- `PortalFeedViews.py`: sample Django-side feed views
- `PortalHtmlPanel.py`: reusable Qt-side HTML panel for desktop preview surfaces

### `PortalPreviewHarness/`

Browser-based preview harness for the portal feed contract.

This is the preferred bridge into the eventual web runtime because it previews the same JSON feed shape that Django pages and future browser-side editing flows can consume.

## Why These Bundles Exist Here

These folders are staging artifacts, not final placement decisions.

The current approach is:

- prepare and validate portable pieces inside BiblionOCR
- copy them into BiblionPortal with the OS file manager
- decide final Django app, template, static, and editor placement there against the actual portal project structure

## Current Direction

- Keep the HTML editor portable and self-contained.
- Treat the portal feed contract as the stable integration seam.
- Use the browser preview harness as the closest approximation of the eventual portal runtime.
- Treat TipTap as a likely browser-side authoring layer, not as the feed-rendering layer itself.