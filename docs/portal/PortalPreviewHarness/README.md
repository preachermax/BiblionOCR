# Portal Preview Harness

This folder provides a separate, web-native harness for the Biblion Portal feed contract.

It replaces the narrow preview role of `HTMLUIMain.py` with something closer to the eventual portal runtime:

- browser-rendered HTML panels
- a JSON feed contract matching `PortalFeedViews.py`
- a structure that can be hosted directly by Django or adapted into a TipTap-backed editing workflow

## Files

- `index.html`: preview shell for main, secondary, and tertiary portal panels
- `app.js`: fetches a Django JSON feed and renders the panels
- `feed-contract-example.json`: example payload shape matching the current sample Django feed

## How To Use

For local preview without Django, open `index.html` in a browser and click `Load Sample`.

For Django-backed preview, serve this page as a template or static file and point the endpoint field at a JSON-producing view such as the sample `get_html_view()` in `ViewController/0-MainUI/PortalFeedViews.py`.

## TipTap Relationship

TipTap is a better fit for authoring and editing rich content in the browser.

This harness is not an editor. It is the rendering and integration harness around the feed contract. If you later introduce TipTap, TipTap can own content creation while this harness remains the browser-side preview surface for the resulting HTML.