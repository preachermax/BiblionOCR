# BiblionPortal

**Operational Headquarters of the BiblionOCR Ecosystem**

---

## Mission

Develop BiblionPortal as the canonical home for BiblionOCR, unifying software, documentation, releases, media, and community into a single platform.

The portal will be developed privately until it is ready for public launch.

---

## Design Goals (Priority Order)

### 1. Launch the BiblionOCR Workspace

Provide authenticated users with the ability to:

- Create projects
- Launch MyServer
- Operate their own BiblionOCR workspace
- Experience an observable software architecture

---

### 2. Commerce

Develop sustainable project funding through:

- Merchandise
- Memberships
- Premium services
- Hosted OCR workspaces

---

### 3. Automated Publishing

Publish from a single source to:

- GitHub
- Patreon
- YouTube
- Search engines
- Public homepage

---

### 4. Platform Independence

Use GitHub, Patreon, YouTube, and other services as integrated platforms—not as the project's permanent home.

BiblionPortal remains the canonical public presence.

---

## Guiding Principle

> Develop privately. Publish intentionally.

---

## Initial Milestone (v0.1.0-alpha)

- Django operational
- Apache integration
- MySQL configured
- Base template
- Navigation shell
- Landing page
- Architecture established

No feature development before the foundation is complete.

---

## Current Migration Staging

The current portal-related implementation work is being staged inside the BiblionOCR repository before being moved into the dedicated BiblionPortal project.

The active staging bundles are:

- `HTMLEditorStandalone/`: portable PyQt HTML editor bundle
- `PortalFeed/`: reference feed client, sample Django feed views, and reusable panel code
- `PortalPreviewHarness/`: browser-native preview harness for the feed contract

This staging work is intentionally provisional. Final placement decisions will be made inside BiblionPortal after the assets are copied over and evaluated against the real Django project structure.

The working architectural direction is:

- Django publishes normalized portal feed payloads
- browser surfaces render that feed contract
- TipTap is the likely browser-side authoring surface for panel content
- desktop preview utilities remain secondary to the eventual browser runtime

---

*"Making systems visible."*