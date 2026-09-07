# A Safer Startup and a Real Theme System

This draft is written as a public-facing Patreon update, with enough context for someone following the project without needing to track every internal implementation detail.

Today’s focus is a safer startup and a real theme system, which sits at the intersection of the project’s public story and the practical work needed to keep the platform moving.

BiblionOCR now handles missing local project data more gracefully and has a catalog-driven theme system with guarded editing instead of scattered stylesheet assumptions.

Startup should fail gracefully:

A development checkout does not always contain a fully populated local project. BiblionOCR now tolerates missing local project data in startup paths that previously assumed those files were present, with regression coverage for launcher compatibility.

That sounds modest, but it removes a class of confusing first-run and clean-checkout failures. Reliability begins before the first project is opened.

Themes became managed resources:

The visual layer also moved from loosely related stylesheets toward an aligned theme catalog and manifest. A guarded editor provides a safer way to inspect and alter themes, while tests check catalog integrity and editor behavior.

The result is not merely more color choices. It is a maintainable ownership model for appearance, including the resources each theme depends on.

Support helps turn this foundational reliability work into a calmer, more consistent application for everyone who uses BiblionOCR.
