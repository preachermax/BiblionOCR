# BIBLION ECOSYSTEM ARCHITECTURE

## Applications, APIs, Extensions, OSS/Commercial Boundaries, and Portal

**Status:** Conceptual Architecture  
**Purpose:** Strategic direction for the Biblion application ecosystem and future commercial/OSS releases.

---

## 1. Vision

Biblion should evolve from an OCR application into an **extensible digital-humanities ecosystem**.

The ecosystem consists of focused applications that share common project, content, workflow, compute, and interoperability infrastructure.

Each application should be extensible at two levels:

1. **Biblion APIs** — capabilities intentionally exposed and maintained by the Biblion development team.
2. **Third-party extensions** — capabilities developed by outside developers against those APIs.

The same principle should eventually apply to the entire Biblion suite.

```text
                    BIBLION PORTAL
                MyLauncher + MyServer
                         │
                         ▼
                 BIBLION SUITE APIs
                         │
          ┌──────────────┼──────────────┐
          │              │              │
     Applications    Workflows       Services
          │
    ┌─────┼───────────────────────────────┐
    │     │       │       │       │       │
 Scanner Reader Writer Trainer Pixler  Glypher ...
    │
    └── Application APIs
             │
       Third-Party Extensions
             │
     External Applications
```

The guiding principle is:

> **Biblion owns the workflow, project model, domain models, APIs, and user experience. Specialized external software can participate through extensions.**

---

## 2. The Extensibility Model

Biblion should have three levels of extensibility.

## 2.1 Application Extensibility

Every mature Biblion application should expose an intentional API.

```text
Biblion Application
        │
        ├── Biblion-maintained capabilities
        │
        └── Application API
                  │
                  └── Third-party extensions
```

Examples:

- MyScanner acquisition API
- MyReader content API
- MyWriter publishing API
- MyTrainer training API
- MyLexer linguistic API
- MyPixler image-processing API
- MyGlypher glyph/font API

---

## 2.2 Suite Extensibility

The suite should eventually expose APIs that allow applications to participate in broader workflows.

Potential suite APIs include:

- Project APIs
- Workflow APIs
- Content exchange APIs
- Event APIs
- Compute APIs
- Resource APIs
- Application registration
- Extension discovery
- Inter-application communication

This permits developers to build extensions that operate **across multiple Biblion applications**, rather than being limited to one application.

---

## 2.3 Portal Extensibility

The Biblion Portal should eventually provide APIs for:

- Projects
- Services
- Applications
- Extensions
- Institutional resources
- Documentation
- Tutorials
- Public content
- Remote processing
- Remote hardware

This makes the Portal itself an extensible platform rather than merely a launcher.

---

## 3. Application Portfolio

The Biblion applications have different responsibilities and different OSS/commercial opportunities.

| Application | Primary Role | OSS | Commercial | Extension Potential |
| --- | --- | :---: | :---: | :---: |
| **MyScanner** | Image acquisition | Yes | **Yes** | Scanner/device APIs |
| **MyPixler** | Image processing | Yes | Possible | GIMP, scripts |
| **MyGlypher** | Glyph/font work | Yes | Possible | FontForge, scripts |
| **OCR Processing Layer** | OCR processing capability across the suite, not a current standalone repo module | Yes | Yes | OCR engines/processors |
| **MyTrainer** | OCR training | Yes | **Yes** | Training engines/data |
| **MyGrounder** | OCR ground-truth creation | Yes | **Yes** | Training workflows |
| **MyReader** | Reading/study | **Yes** | Possible | Module importers |
| **MyWriter** | Authoring/publishing | Yes | Possible | Module exporters |
| **MyLexer** | Lexical/language analysis | **Yes** | **Yes** | Linguistic extensions |
| **MyVersifier** | Versification | **Yes** | No | Open research extensions |
| **MyResolver** | Reference/entity resolution | **Yes** | No | Open research extensions |
| **MyBoxer** | Page/layout analysis | Yes | Possible | Processing extensions |
| **MyServer** | Project/workflow management | Yes | Possible | Suite/Portal APIs |
| **MyLauncher** | Portal presentation | Yes | Possible | Portal extensions |

The exact licensing and commercial boundaries remain subject to future business and legal decisions. This table represents the **current strategic direction**, not a final licensing commitment.

---

## 4. MyScanner — Commercial Entry Point

MyScanner is currently the planned **first commercial Biblion release**.

Its primary responsibility is image acquisition.

It should expose a stable acquisition API rather than attempting to hard-code every possible scanner or camera.

Potential extensions:

- Scanner drivers
- Camera acquisition
- Network scanners
- Specialized imaging equipment
- Institutional scanning systems

The commercial release can provide:

- Polished binaries
- Installation
- Hardware support
- Documentation
- Production packaging
- Support
- Stable APIs

Third-party developers can build scanner extensions against the supported API.

---

## 5. MyPixler

MyPixler provides Biblion-specific image preparation and processing.

It should not attempt to replace GIMP.

Potential extension:

```text
MyPixler
    │
    ▼
Biblion Image Model
    │
    ▼
GIMP Extension
    │
    ▼
GIMP
    │
    ▼
Biblion Image Model
```

MyPixler can also expose Python processing APIs for automation.

---

## 6. MyGlypher

MyGlypher handles glyph extraction, preparation, and font-oriented workflows.

It should not attempt to replace FontForge.

Potential extension:

```text
MyGlypher
    │
    ▼
Biblion Glyph Model
    │
    ▼
FontForge Extension
    │
    ▼
FontForge
    │
    ▼
Biblion Glyph/Font Model
```

FontForge therefore becomes a specialized external capability participating in a Biblion workflow.

---

## 7. OCR Training Ecosystem

OCR training is a particularly important example of the Biblion OSS/commercial model.

Two applications are involved:

- **MyTrainer**
- **MyGrounder**

They have distinct responsibilities but naturally work together.

---

## 7.1 MyGrounder

MyGrounder creates and manages the ground truth required for OCR training.

Responsibilities may include:

- Ground-truth creation
- Image/text alignment
- Character/glyph association
- Annotation
- Correction
- Training-data management
- Dataset preparation

MyGrounder has both **OSS and commercial value**.

Its OSS form can remain an independent application useful to researchers and developers.

Its commercial form can participate in a more integrated OCR-training product.

---

## 7.2 MyTrainer

MyTrainer manages OCR model training.

Potential responsibilities:

- Training configuration
- Training datasets
- Training execution
- Training monitoring
- Model management
- Evaluation
- Training profiles
- Compute-resource utilization

MyTrainer likewise has both **OSS and commercial value**.

---

## 7.3 Commercial OCR Trainer

MyTrainer and MyGrounder can be combined into a commercial OCR-training product.

Conceptually:

```text
             COMMERCIAL OCR TRAINER
                       │
          ┌────────────┴────────────┐
          │                         │
      MyGrounder                MyTrainer
          │                         │
      Ground Truth              Training
          │                         │
          └────────────┬────────────┘
                       │
                  OCR Models
```

The important distinction is that the **commercial product is a composed workflow**, while the underlying applications can remain independently useful OSS projects.

This gives Biblion two markets simultaneously:

### OSS

Researchers and developers can use:

```text
MyGrounder
     +
MyTrainer
```

independently.

### Commercial

Users who want an integrated, supported OCR-training environment can purchase the composed product.

This pattern can become a model for other Biblion commercial products.

---

## 8. MyLexer

MyLexer analyzes lexical and linguistic structure.

It has both **OSS and commercial potential**.

Possible capabilities include:

- Tokenization
- Lexical analysis
- Language-specific processing
- Morphological analysis
- Dictionary integration
- Linguistic data exchange
- Research tooling

The OSS implementation can support research and community development.

Commercial components could provide:

- Specialized linguistic datasets
- Advanced processing
- Supported language packages
- Production workflows
- Institutional features

---

## 9. MyVersifier

MyVersifier is currently envisioned as **OSS-only**.

Its purpose is to provide open tools for versification and textual structure.

Potential capabilities include:

- Verse identification
- Verse mapping
- Cross-tradition versification
- Structural comparison
- Research tooling

Keeping MyVersifier open reinforces Biblion's role as a research platform.

---

## 10. MyResolver

MyResolver is also envisioned as **OSS-only**.

Its purpose is reference and entity resolution.

Potential uses include:

- Person identification
- Place identification
- Textual references
- Cross-document relationships
- Entity normalization
- Reference mapping

MyResolver can provide an open research foundation upon which other Biblion applications build.

---

## 11. MyReader

MyReader is envisioned as an **OSS Bible/text reader with OCR-aware capabilities**.

It should provide a clean alternative to highly dense Bible-study interfaces while remaining extensible.

MyReader consumes external content.

Potential extensions:

- e-Sword importer
- theWord importer
- Other module importers
- Native Biblion module support
- Search extensions
- Study tools

The architectural rule is:

> **MyReader brings external content into Biblion.**

External modules are converted into the Biblion content model.

---

## 12. MyWriter

MyWriter is the complementary authoring and publishing application.

It produces content.

Potential extensions:

- e-Sword exporter
- theWord exporter
- Other module exporters
- Native Biblion module generation
- Publishing workflows

The fundamental relationship is:

> **MyReader consumes.  
> MyWriter produces.**

This creates a two-way bridge between Biblion and existing Bible-study ecosystems.

```text
External Module
      │
      ▼
   MyReader
      │
      ▼
Biblion Content Model
      │
      ▼
   MyWriter
      │
      ▼
External Module
```

---

## 13. Canonical Biblion Content Model

External formats should never become the internal architecture of Biblion.

Biblion should maintain a canonical content model.

```text
e-Sword ──► MyReader ──┐
                       │
theWord ──► MyReader ──┤
                       ▼
               Biblion Content
                       │
                    MyWriter
                       │
              ┌────────┴────────┐
              ▼                 ▼
         e-Sword             theWord
```

This allows additional formats to be added without contaminating the core architecture with format-specific assumptions.

---

## 14. MyServer

MyServer remains the **project and workflow workhorse** of the Biblion Portal.

Responsibilities include:

- Project creation
- Project lifecycle
- Project milestones
- Workflow state
- Project resources
- Compute resources
- Processing orchestration
- Inter-application coordination
- Future institutional services

The architectural boundary remains:

> **MyServer governs projects.**

MyServer should be the authoritative owner of project creation and project lifecycle.

---

## 15. MyLauncher

MyLauncher is the primary **presentation and public interface** to the Biblion ecosystem.

Responsibilities include:

- Application discovery
- Project access
- Tutorials
- Documentation
- Help
- Extension discovery
- Portal content
- Public-facing information
- Access to Biblion services

The architectural boundary remains:

> **MyLauncher presents the ecosystem.  
> MyServer governs its projects.**

Together they form the primary Biblion Portal interface.

---

## 16. Presentation Layer

The emerging architecture suggests that the presentation layer deserves independent architectural treatment.

There are three conceptual levels:

```text
┌─────────────────────────────────────────────┐
│                BIBLION PORTAL               │
│                                             │
│          MyLauncher + MyServer              │
│                                             │
│   Projects • Applications • Services        │
│   Tutorials • Extensions • Institutions     │
└──────────────────────┬──────────────────────┘
                       │
┌──────────────────────▼──────────────────────┐
│             BIBLION APPLICATIONS            │
│                                             │
│ Scanner • Reader • Writer • OCR • Trainer  │
│ Grounder • Pixler • Glypher • Lexer • etc. │
└──────────────────────┬──────────────────────┘
                       │
┌──────────────────────▼──────────────────────┐
│        EXTERNAL SPECIALIZED SOFTWARE        │
│                                             │
│ GIMP • FontForge • Scanners • Printers     │
│ e-Sword • theWord • Institutional Systems  │
└─────────────────────────────────────────────┘
```

The exact presentation architecture remains conceptual.

The important principle is that **the Portal should eventually present the capabilities of the entire ecosystem rather than merely launch individual applications**.

---

## 17. Future Institutional Infrastructure

A longer-term opportunity is to allow Biblion to interface with resources already owned by libraries, universities, archives, and other institutions.

Potential services include:

- Remote scanning
- Network scanning
- Institutional printing
- Document preparation
- Image processing
- OCR processing
- Compute resources
- Digital repositories
- Specialized archival services

Conceptually:

```text
                    BIBLION PORTAL
                          │
              ┌───────────┼───────────┐
              │           │           │
              ▼           ▼           ▼
          Scanner      Compute      Printer
              │           │           │
              └───────────┼───────────┘
                          ▼
                    Biblion Project
```

A potential future partnership with copier/printer dealers and institutional equipment providers could provide access to professional scanning and printing resources.

The objective would be to allow institutions to expose existing physical and digital resources through controlled Biblion workflows.

This is **future conceptual architecture only**.

No implementation or business commitment is implied.

---

## 18. The Full Digital-Humanities Workflow

The ecosystem can ultimately support a complete workflow:

```text
                         BIBLION PORTAL
                    MyLauncher + MyServer
                              │
                              ▼
                       Project Creation
                              │
                              ▼
                         MyScanner
                              │
                              ▼
                          MyPixler
                              │
                              ▼
                      OCR Processing
                              │
                     ┌────────┴────────┐
                     ▼                 ▼
                MyGrounder        MyGlypher
                     │                 │
                     ▼                 ▼
                 MyTrainer        FontForge
                     │
                     ▼
                   MyLexer
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
     MyVersifier           MyResolver
          │                     │
          └──────────┬──────────┘
                     ▼
                  MyReader
                     │
                     ▼
                  MyWriter
                     │
                     ▼
               Published Content
```

External applications can participate at appropriate points through extensions.

---

## 19. OSS/Commercial Composition

Biblion should not assume that every application needs the same business model.

Instead, applications can occupy different positions within the ecosystem.

### OSS-first

Examples:

- MyReader
- MyVersifier
- MyResolver

### OSS + Commercial

Examples:

- MyScanner
- MyTrainer
- MyGrounder
- MyLexer

Potentially:

- MyPixler
- MyGlypher
- MyWriter
- MyBoxer

### Commercially Composed Products

Multiple OSS-capable applications can be combined into supported commercial workflows.

The OCR Trainer is the first clear example:

```text
OSS MyGrounder
       +
OSS MyTrainer
       │
       ▼
Commercial OCR Trainer
```

This is an important strategic pattern.

**Commercial value does not require every underlying component to become proprietary.**

Biblion can sell:

- Integration
- Packaging
- Support
- Workflows
- Specialized capabilities
- Hardware integration
- Institutional services
- Production tooling

while preserving useful OSS components.

---

## 20. Intellectual Property and Interoperability

Compatibility with external formats must be distinguished from redistribution of external content.

Supporting an e-Sword or theWord format does not imply redistribution of copyrighted modules.

The preferred model is:

> **Biblion provides compatibility; users and institutions provide content for which they have appropriate rights.**

This applies equally to external software integrations.

Biblion extensions should provide interoperability without assuming ownership of external applications or their content.

---

## 21. Commercial Strategy

The initial commercial target remains:

## MyScanner

MyScanner provides a natural first commercial entry point because it connects directly to physical acquisition hardware and has a clear API/extension boundary.

The broader ecosystem then provides opportunities for additional commercial products.

Potential future products include:

- Commercial OCR Trainer
- Specialized MyTrainer packages
- Specialized MyGrounder packages
- MyLexer commercial language packages
- Institutional scanning services
- Institutional printing services
- Managed compute services
- Supported Biblion Portal deployments

The commercial strategy should emerge from the value of **workflow integration**, not from unnecessarily closing the entire ecosystem.

---

## 22. Architectural Philosophy

The central philosophy is:

> **Biblion does not need to replace excellent specialized software. It needs to make excellent specialized software participate in Biblion workflows.**

Therefore:

- MyPixler does not need to become GIMP.
- MyGlypher does not need to become FontForge.
- MyReader does not need to become theWord.
- MyReader does not need to become e-Sword.
- MyScanner does not need to contain every scanner driver.
- MyWriter does not need to own every publishing format.
- MyTrainer does not need to monopolize OCR training.
- MyGrounder does not need to monopolize ground-truth creation.

Instead, Biblion owns:

- Workflow
- Project model
- Domain models
- APIs
- Extension architecture
- Interoperability
- Presentation
- Portal experience

External applications, developers, institutions, and researchers become participants in that ecosystem.

---

## 23. Long-Term Vision

The result is no longer adequately described as an OCR application.

Biblion becomes an **extensible digital-humanities platform** supporting:

- Historical document acquisition
- Image preparation
- OCR
- OCR training
- Ground-truth creation
- Glyph and font development
- Lexical analysis
- Reference resolution
- Versification
- Text reading
- Text authoring
- Module conversion
- Publishing
- Research
- Project management
- Institutional resource access
- Remote scanning
- Remote printing
- Specialized external software

The architecture can ultimately be summarized as:

```text
                     BIBLION
                        │
          ┌─────────────┼─────────────┐
          │             │             │
     Applications     APIs       Extensions
          │             │             │
          └─────────────┼─────────────┘
                        │
                 Biblion Suite
                        │
                 Suite APIs
                        │
              Suite Extensions
                        │
                        ▼
               BIBLION PORTAL
              MyLauncher + MyServer
                        │
          ┌─────────────┼─────────────┐
          │             │             │
      Researchers   Developers   Institutions
          │             │             │
          └─────────────┼─────────────┘
                        ▼
              Digital-Humanities
                   Ecosystem
```

The **individual applications**, the **Biblion suite**, and the **Biblion Portal** should all become extensible layers.

The architecture remains conceptual until individual API contracts, canonical data models, licensing boundaries, security requirements, and presentation-layer architecture are formally designed.

---

## 24. Immediate Architectural Implication

The current development strategy should therefore continue to separate:

1. **Core application capabilities**
2. **Public Biblion APIs**
3. **Extension interfaces**
4. **Suite-level services**
5. **Portal presentation**
6. **Commercial packaging**
7. **OSS implementations**
8. **External integrations**

The upcoming Python-to-C++ conversion and binary-production work should preserve these boundaries rather than collapsing them.

The objective is not simply to produce a collection of binaries.

The objective is to produce a **coherent, extensible Biblion ecosystem whose applications can evolve independently while remaining part of a larger platform.**
