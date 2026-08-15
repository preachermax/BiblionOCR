# Stand-Alone Release Order Reference

Date: 2026-08-05

## Summary

The strongest early stand-alone release candidates are:

1. MyScanner
2. MyPixler
3. MyTrainer
4. MyWriter
5. MyReader

This order gives BiblionOCR a simple outside story:

- acquire
- prepare
- train
- publish
- review

That story is easier to explain to outside supporters than releasing the more specialized middle modules first.

## Best First-Release Candidates

### MyScanner

MyScanner is an excellent first-release candidate because it has immediate practical value and a clear demonstration path.

Strengths:

- easy to explain
- visible user benefit
- close to document acquisition, which outside users immediately understand
- good fit for stand-alone support generation

### MyPixler

MyPixler is one of the strongest additional stand-alone candidates.

Why:

- image cleanup and preparation have value even outside the full OCR suite
- users can understand and support document-image preparation without needing to understand the whole BiblionOCR architecture
- it strengthens the early-release story between scanning and training

### MyTrainer

MyTrainer is also a strong early release candidate.

Why:

- it supports the technical credibility of the project
- it is attractive to users interested in OCR model improvement
- it helps demonstrate that BiblionOCR is more than a viewer or converter

### MyWriter

MyWriter is a strong output-side candidate.

Why:

- it sits close to completed text handling and publication/export workflow
- it is easier to explain than some of the specialized middle modules
- it supports a practical “from scanned source to usable text” public story

### MyReader

MyReader is a reasonable second-tier early release.

Why:

- it can function as an OCR review/check utility
- it works best when presented as inspect, compare, and correct rather than as the whole pipeline

## Second-Tier Candidate

### MyExplorer

MyExplorer is useful, but not a strong headline release by itself.

Why:

- it is more of a support utility than a flagship module
- it may work better bundled with another early release than positioned alone

## Poor First-Release Candidates

These are not ideal as first outside-facing releases:

- MyServer
- MyLauncher
- MyBoxer
- MyGlypher
- MyGrounder
- MyLexer
- MyResolver
- MyVersifier

Why not:

- too suite-dependent
- too domain-specific
- too tightly coupled to the broader workflow story
- harder to explain to outside supporters without significant project context

## Recommended Early Release Order

1. MyScanner
2. MyPixler
3. MyTrainer
4. MyWriter
5. MyReader

## Rationale For Fundraising And Outside Support

This sequence creates a staged public narrative:

1. MyScanner proves source acquisition value.
2. MyPixler proves document preparation value.
3. MyTrainer proves OCR-engine development seriousness.
4. MyWriter proves usable output and publishing direction.
5. MyReader proves review and correction value.

That progression is stronger for outside support than releasing the more specialized middle modules first.

## Commercial Implementation Language Guidance

For a BiblionOCR-C++ commercial binary track on Windows and Linux:

1. Prefer Qt6 C++.
2. Port modules in this same release order to reduce risk and preserve milestone visibility.
3. Keep license/provenance tracking attached to each module migration step.

Reasoning summary:

1. Qt6 C++ gives the closest continuity with the current Qt Designer `.ui` architecture.
2. Native Qt6 C++ supports release-grade desktop packaging across Windows and Linux.
3. Qt6 C++ keeps UI lockstep practical between `.ui` sources and generated/runtime bindings.

Implementation reference:

1. See docs/development/BIBLIONOCR_CPP_QT6_MIGRATION_PLAN_2026-08-06.md for the detailed phase plan and quality gates.
