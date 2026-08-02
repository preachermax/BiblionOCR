from PyQt5 import QtWidgets as qtw

from print_handlerUI import ProjectPrintHandler


class _PrintTarget:
    def __init__(self, kind, getter, empty_title, empty_message):
        self.kind = kind
        self.getter = getter
        self.empty_title = empty_title
        self.empty_message = empty_message


def image_target(getter, empty_message, empty_title="No File Loaded"):
    return _PrintTarget("image", getter, empty_title, empty_message)


def document_target(getter, empty_message, empty_title="No Text Loaded"):
    return _PrintTarget("document", getter, empty_title, empty_message)


def install_print_menu_support(window, action_targets, default_target=None):
    if not action_targets:
        return

    if not hasattr(window, "print_handler") or window.print_handler is None:
        window.print_handler = ProjectPrintHandler(window)

    window._print_action_targets = dict(action_targets)
    target_order = list(action_targets.keys())
    window._active_print_target = default_target or target_order[0]

    for action_name, target_key in action_targets.items():
        action = getattr(window.ui, action_name, None)
        if action is None:
            continue
        action.triggered.connect(
            lambda checked=False, key=target_key: _print_target(window, key, preview=False)
        )

    preview_action = getattr(window.ui, "actionPrint_Preview", None)
    if preview_action is not None:
        preview_action.triggered.connect(lambda checked=False: _print_preview(window))

    exit_action = getattr(window.ui, "actionExit", None)
    if exit_action is not None:
        exit_action.triggered.connect(window.close)


def _document_has_content(document):
    if document is None or document.isEmpty():
        return False

    plain_text = document.toPlainText() if hasattr(document, "toPlainText") else ""
    html_text = document.toHtml() if hasattr(document, "toHtml") else ""
    return bool(plain_text.strip() or html_text.strip())


def _target_payload(target):
    payload = target.getter()
    if target.kind == "image":
        return payload is not None and not payload.isNull()
    if target.kind == "document":
        return _document_has_content(payload)
    return False


def _show_empty(window, target):
    qtw.QMessageBox.information(
        window,
        target.empty_title,
        target.empty_message,
    )


def _print_target(window, target_key, preview=False):
    target = window._print_action_targets[target_key]
    payload = target.getter()

    if target.kind == "image":
        if payload is None or payload.isNull():
            _show_empty(window, target)
            return False
        window._active_print_target = target_key
        window.print_handler.handle_image(payload, window, preview=preview)
        return True

    if target.kind == "document":
        if not _document_has_content(payload):
            _show_empty(window, target)
            return False
        window._active_print_target = target_key
        window.print_handler.handle_document(payload, window, preview=preview)
        return True

    return False


def _print_preview(window):
    active_target = getattr(window, "_active_print_target", None)
    if active_target in getattr(window, "_print_action_targets", {}):
        if _print_target(window, active_target, preview=True):
            return

    for target_key, target in window._print_action_targets.items():
        if _target_payload(target):
            _print_target(window, target_key, preview=True)
            return

    qtw.QMessageBox.information(
        window,
        "No File Loaded",
        "Load an image or text document before opening print preview.",
    )
