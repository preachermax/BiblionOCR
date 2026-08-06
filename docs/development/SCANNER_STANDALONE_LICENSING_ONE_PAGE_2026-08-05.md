# Scanner Standalone Licensing One-Page Handout

Date: 2026-08-05

## Bottom Line

Yes, you can generally:

1. Keep BiblionOCR under Apache-2.0.
2. Develop and license BiblionScanner separately (including proprietary/commercial), if compliance and dependency licensing are handled correctly.

## What You Can Do

1. Run open-source and commercial tracks in parallel.
2. Charge for support, tooling, onboarding, deployment, and managed services.
3. Maintain separate repositories and separate license files.

## Non-Negotiable Compliance Points

1. If Scanner reuses Apache-licensed code from BiblionOCR:
   - Keep attribution and required notices.
   - Preserve applicable LICENSE/NOTICE obligations.
2. You cannot revoke Apache rights already granted in published BiblionOCR code.
3. Track provenance of reused files/modules.

## Highest-Risk Gate Before Binary Release

Qt/PyQt licensing must be cleared for your exact Windows/Linux binary distribution model.

Do not ship first proprietary binaries until this is confirmed.

## Go/No-Go Checklist

1. Separate repo and license strategy documented.
2. Dependency license audit complete.
3. Qt/PyQt distribution rights confirmed.
4. Attribution/NOTICE bundle prepared for reused OSS components.
5. Binary package contains required third-party license texts.
6. Paid support/tooling boundaries documented.
7. Final legal review completed.

## Recommended Release Posture

1. Keep BiblionOCR as open-source reference/core track.
2. Build Scanner as a cleanly separated product track.
3. Publish a clear policy on what is free/community vs paid/support.

## Finding an OSS Attorney Near Florence, AL (35630)

1. Start with Alabama State Bar referral links:
2. Get Legal Help: [https://www.alabar.org/for-the-public/get-legal-help/](https://www.alabar.org/for-the-public/get-legal-help/)
3. Lawyer Referral Service: [https://www.alabar.org/lrs-form/](https://www.alabar.org/lrs-form/)
4. Member Search: [https://members.alabar.org/Member_Portal/Member_Portal/Member-Search.aspx](https://members.alabar.org/Member_Portal/Member_Portal/Member-Search.aspx)
5. Use search filters: Florence, Lauderdale County, then expand to Huntsville and Birmingham.
6. Ask for practice focus: technology law, software licensing, IP, and commercial contracts.
7. Ask screening questions: OSS compliance experience, dual-track licensing experience, Qt/PyQt binary distribution experience, and fixed-fee compliance memo availability.
8. Referral note: Alabama referral service states initial 30-minute consultation is capped at $50 before normal rates apply.

## Disclaimer

Operational guidance only, not legal advice. Obtain attorney review before first public binary release.
