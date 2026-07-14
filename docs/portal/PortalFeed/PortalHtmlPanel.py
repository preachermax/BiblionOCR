from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QTextBrowser, QVBoxLayout, QWidget

try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView
except ImportError:
    QWebEngineView = None


class HtmlPortalPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.browser = self._create_browser()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.browser)

    def _create_browser(self):
        if QWebEngineView is not None:
            return QWebEngineView(self)

        fallback = QTextBrowser(self)
        fallback.setOpenExternalLinks(True)
        return fallback

    def set_html(self, html_content, base_url=None):
        base = QUrl(base_url) if isinstance(base_url, str) else base_url
        if hasattr(self.browser, "setHtml"):
            if base is not None and QWebEngineView is not None and isinstance(self.browser, QWebEngineView):
                self.browser.setHtml(html_content, base)
            else:
                self.browser.setHtml(html_content)

    def set_url(self, url):
        if hasattr(self.browser, "load"):
            self.browser.load(QUrl(url))
        else:
            self.browser.setSource(QUrl(url))


def mount_html_panel(placeholder, panel=None):
    if panel is None:
        panel = HtmlPortalPanel(placeholder)

    layout = placeholder.layout()
    if layout is None:
        layout = QVBoxLayout(placeholder)
        layout.setContentsMargins(0, 0, 0, 0)
    else:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)

    layout.addWidget(panel)
    return panel