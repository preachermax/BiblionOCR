# Developer Extensions

Developer capabilities are installed and launched outside production application menus.

## Extension Manager

Launch the manager from a development checkout:

```bash
.venv/bin/python -m Developer.extension_manager_dialog
```

The manager discovers bundled extensions under `Developer/extensions`, installs them into the current user's application-data directory, lists services declared by installed extensions, and dynamically opens a selected service.

Default installation roots:

- Linux: `$XDG_DATA_HOME/BiblionOCR/extensions` or `~/.local/share/BiblionOCR/extensions`
- Windows: `%LOCALAPPDATA%/BiblionOCR/extensions`
- macOS: `~/Library/Application Support/BiblionOCR/extensions`

Set `BIBLIONOCR_EXTENSION_HOME` to use an explicit extension root for development or testing.

## First Extension

`developer-services` is the first bundled installable extension. Its first service is Developer Backup/Restore, which creates development snapshots and non-destructive staged restores.

## Adding Services

Each extension directory contains an `extension.json` schema-version 1 manifest. Add future services to its `services` array:

```json
{
  "id": "service-id",
  "name": "Visible Service Name",
  "description": "Short purpose statement.",
  "entry_point": "module.py:DialogClass"
}
```

Extension and service IDs use lowercase letters, digits, and hyphens. Entry-point modules must remain inside the installed extension directory. A UI service class must be constructible with `parent=<QWidget>` and behave as a Qt dialog or window.

The current installer accepts bundled extensions only. Support for third-party package trust, signatures, dependency resolution, and remote catalogs is intentionally deferred.
