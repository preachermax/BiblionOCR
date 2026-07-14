import os

import requests


class PortalFeedClient:
    def __init__(self, get_url=None, post_url=None, timeout=5):
        self.get_url = get_url or os.environ.get("BIBLION_PORTAL_FEED_URL", "")
        self.post_url = post_url or os.environ.get("BIBLION_PORTAL_POST_URL", "")
        self.timeout = timeout

    def fetch_html(self):
        if not self.get_url:
            raise ValueError("No Django feed URL configured.")

        response = requests.get(self.get_url, timeout=self.timeout)
        response.raise_for_status()
        return response.text

    def fetch_feed(self):
        if not self.get_url:
            raise ValueError("No Django feed URL configured.")

        response = requests.get(
            self.get_url,
            headers={"Accept": "application/json, text/html;q=0.9"},
            timeout=self.timeout,
        )
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "")
        if "application/json" in content_type:
            return self._normalize_feed_payload(response.json())

        return self._normalize_feed_payload(response.text)

    def post_html(self, html_content):
        if not self.post_url:
            raise ValueError("No Django post URL configured.")

        response = requests.post(
            self.post_url,
            data={"html_content": html_content},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response

    def _normalize_feed_payload(self, payload):
        default_panels = {
            "main": "",
            "secondary": "",
            "tertiary": "",
        }

        if isinstance(payload, str):
            return {
                "title": "Biblion Portal Feed",
                "panels": {**default_panels, "main": payload},
            }

        if not isinstance(payload, dict):
            raise ValueError("Unsupported portal feed payload.")

        panels = dict(default_panels)
        payload_panels = payload.get("panels", {})
        if isinstance(payload_panels, dict):
            for name, value in payload_panels.items():
                if isinstance(value, dict):
                    panels[name] = value.get("html", "")
                elif isinstance(value, str):
                    panels[name] = value

        for source_key, target_key in (
            ("main_html", "main"),
            ("secondary_html", "secondary"),
            ("tertiary_html", "tertiary"),
        ):
            value = payload.get(source_key)
            if isinstance(value, str) and value:
                panels[target_key] = value

        return {
            "title": payload.get("title", "Biblion Portal Feed"),
            "panels": panels,
        }


DjangoHtmlClient = PortalFeedClient