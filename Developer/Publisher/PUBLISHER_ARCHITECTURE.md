# PUBLISHER_ARCHITECTURE.md

---

# BiblionPublisher Architecture

**Project:** BiblionOCR

**Subsystem:** Developer / Publisher

**Status:** Design Approved

**Version:** 1.0

---

# 1. Purpose

BiblionPublisher is the static publishing engine for the BiblionOCR ecosystem.

Its responsibility is to transform project assets into a complete static website suitable for deployment on GitHub Pages, Render, or any static web host.

Unlike traditional documentation generators, BiblionPublisher treats the application itself as documentation.

Qt Designer UI files, Markdown documents, screenshots, architecture graphs, project metadata, and generated content all become publishable assets.

The desktop application remains the authoritative source.

The website becomes a generated artifact.

---

# 2. Philosophy

BiblionPublisher follows six principles.

## 2.1 Single Source of Truth

Information should never be duplicated.

Examples:

* Qt Designer defines the interface.
* Markdown defines written documentation.
* Cytoscape defines architecture.
* Project metadata defines releases.

Publisher generates everything else.

---

## 2.2 Static First

The generated website contains no server-side logic.

Output consists entirely of:

* HTML
* CSS
* JavaScript
* JSON
* Images
* SVG

This allows deployment on:

* GitHub Pages
* Render Static Sites
* Netlify
* Apache
* nginx

without modification.

---

## 2.3 Build-Time Generation

Nothing is generated during application execution.

Instead,

```text
Qt Designer
Markdown
Project Data
Screenshots
↓

Publisher

↓

docs/
```

---

## 2.4 Component Independence

Every generator performs one task.

No generator depends on another generator's implementation.

Each consumes only the UIModel.

---

## 2.5 Extensibility

Adding a new publishing target should require creating only a new generator.

No existing code should require modification.

---

## 2.6 Deterministic Output

Running Publisher twice on identical inputs should produce identical output.

---

# 3. Responsibilities

Publisher SHALL:

* Parse Qt Designer UI files
* Parse Markdown
* Parse project metadata
* Generate HTML
* Generate navigation
* Generate tutorials
* Generate screenshots
* Generate Cytoscape graphs
* Generate JSON data
* Generate search indexes
* Generate RSS
* Generate sitemap
* Generate docs folder

Publisher SHALL NOT:

* Execute Qt applications
* Modify project source
* Perform OCR
* Manage projects
* Replace Render

---

# 4. High-Level Pipeline

```text
             Qt Designer (.ui)
                    │
                    ▼
              UI Parser
                    │
                    ▼
               UI Model
                    │
     ┌──────────────┼──────────────┐
     │              │              │
     ▼              ▼              ▼
 Tutorial      HTML Pages     Cytoscape
 Generator      Generator      Generator
     │              │              │
     └──────────────┼──────────────┘
                    ▼
            Static Website
                    │
                    ▼
                  docs/
                    │
                    ▼
             GitHub Repository
                    │
                    ▼
                 Render
```

---

# 5. Directory Structure

```text
Developer/

    Publisher/

        publisher.py

        ui_parser.py

        ui_model.py

        html_generator.py

        tutorial_generator.py

        screenshot_generator.py

        markdown_generator.py

        cytoscape_generator.py

        rss_generator.py

        sitemap_generator.py

        templates/

        themes/

        assets/

        output/
```

---

# 6. UI Model

Publisher never works directly with XML.

Instead

```text
Qt XML

↓

UI Parser

↓

UIModel

↓

Generators
```

The UIModel becomes the canonical representation of the user interface.

Every generator consumes the UIModel.

---

# 7. Generator Responsibilities

## HTML Generator

Produces

* index.html
* module pages
* navigation
* search

---

## Tutorial Generator

Produces

animated tutorials.

Responsibilities:

* button order
* module descriptions
* screenshots
* animation timing

---

## Screenshot Generator

Produces

PNG assets.

Supports

* desktop screenshots
* cropped widgets
* highlight overlays

---

## Markdown Generator

Converts

```text
README.md

↓

HTML
```

Supports

* syntax highlighting
* tables
* images
* cross references

---

## Cytoscape Generator

Produces

interactive architecture graphs.

Each module becomes a node.

Dependencies become edges.

---

## RSS Generator

Produces

blog RSS feeds.

---

## Sitemap Generator

Produces

```text
sitemap.xml
```

---

# 8. Website Structure

```text
docs/

    index.html

    modules/

    tutorials/

    architecture/

    blog/

    releases/

    assets/

        css/

        js/

        images/

        icons/

        fonts/

    data/

        ui.json

        graph.json

        search.json

    rss.xml

    sitemap.xml
```

---

# 9. Module Discovery

Publisher discovers modules automatically.

Example

```text
MyServerbutton

↓

MyServer

↓

Module
```

The module becomes the published object.

---

# 10. Tutorial Metadata

Tutorial information is embedded directly inside Qt Designer.

Example

```xml
tutorial.enabled

tutorial.title

tutorial.help

tutorial.order

tutorial.image
```

Publisher reads these properties without additional configuration.

---

# 11. Screenshots

Screenshots are generated separately.

Tutorial pages reference them.

Publisher never edits screenshots.

Publisher only copies and indexes them.

---

# 12. Cytoscape Integration

Publisher exports

```text
graph.json
```

Example

```text
MyLauncher

↓

MyServer

↓

Compute Engine

↓

Hardware Providers
```

The website visualizes this interactively.

---

# 13. Themes

Themes control presentation only.

Themes never affect content.

Example

```text
Default

Dark

Documentation

Presentation
```

---

# 14. Templates

Templates define

* page layout
* navigation
* footer
* header
* module pages

Publisher injects generated data.

---

# 15. Assets

Publisher copies

* PNG
* SVG
* Fonts
* JavaScript
* CSS

into the docs folder.

Assets remain immutable.

---

# 16. Output Contract

Publisher guarantees

```text
docs/

    index.html

    assets/

    tutorials/

    modules/

    architecture/

    blog/
```

Render consumes only this folder.

---

# 17. GitHub Integration

Publisher performs no Git operations.

Workflow

```text
Publish

↓

docs updated

↓

git add

↓

git commit

↓

git push

↓

Render deploys
```

---

# 18. Render Integration

Render serves only generated content.

Publisher assumes no backend.

No Python.

No Django.

No database.

---

# 19. Future Expansion

Future generators may include

* PDF

* EPUB

* PowerPoint

* Video tutorials

* API documentation

* UML diagrams

* OpenAPI

* Interactive timelines

without changing Publisher architecture.

---

# 20. Public API

Publisher exposes one public class.

```python
Publisher
```

Primary interface

```python
Publisher.publish()
```

Everything else remains internal.

---

# 21. Design Goals

Publisher should eventually support

✓ Documentation

✓ Tutorials

✓ Blogs

✓ Architecture

✓ Releases

✓ API Reference

✓ Screenshots

✓ Cytoscape

✓ Search

✓ RSS

✓ Static Deployment

using one command.

---

# 22. Long-Term Vision

Publisher is not merely a documentation generator.

Publisher is the publishing subsystem for the entire BiblionOCR ecosystem.

The desktop applications remain the authoritative source.

Every public artifact—

documentation,

tutorials,

architecture,

website,

blogs,

release notes,

graphs,

and screenshots—

is generated automatically from those sources.

The result is a reproducible publishing pipeline in which GitHub and Render become deployment mechanisms rather than content management systems.

This architecture ensures that the public face of BiblionOCR remains synchronized with the software itself while preserving a static, portable, and platform-independent website.
