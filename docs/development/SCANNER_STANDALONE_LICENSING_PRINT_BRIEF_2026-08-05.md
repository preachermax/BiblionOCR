# Scanner Standalone Licensing Print Brief

Date: 2026-08-05
Owner: preachermax
Context: Pre-release decision on whether BiblionScanner binaries (Windows/Linux) can be licensed independently from BiblionOCR.

## Executive Answer

Yes, you can generally do both:

1. Keep BiblionOCR open source under Apache-2.0.
2. Develop and license BiblionScanner separately (including commercial/proprietary), if you structure reuse and dependencies correctly.

This is a common dual-track model: open-source core plus separately licensed products/support tooling.

## What Is Legally Safe in Principle

1. Apache-2.0 rights already granted in BiblionOCR remain in force for released code.
2. A new, separately developed repository can carry a different license.
3. You can monetize support, packaging, hosting, maintenance, onboarding, SLA offerings, and proprietary tooling.

## What Must Be Managed Carefully

1. Code provenance:
   - If Scanner reuses Apache-2.0 code from BiblionOCR, keep required notices and attribution.
   - Preserve LICENSE and NOTICE obligations for reused portions.
2. Dependency licensing:
   - Verify every runtime/build dependency used in Scanner binaries.
   - Qt/PyQt is a high-priority legal checkpoint before closed-source distribution.
3. Branding/trademark boundaries:
   - Trademark usage is separate from open-source copyright licensing.
4. Contributor rights:
   - Ensure you own or have rights to all contributions included in the separately licensed product.

## Critical Risk Note: PyQt5 and Binary Distribution

PyQt5 licensing can affect whether proprietary binary distribution is allowed without additional commercial licensing.

Action:

1. Confirm the exact Qt/PyQt components used in Scanner.
2. Confirm applicable license terms for your planned distribution model.
3. Do not ship proprietary binaries until this point is cleared.

## Recommended Structure (Low-Risk Path)

1. Repository separation:
   - Keep BiblionOCR and BiblionScanner in separate repos.
2. License separation:
   - Keep explicit LICENSE files per repository.
3. Provenance ledger:
   - Track each reused file/module origin and license obligations.
4. Distribution bundle compliance:
   - Include required license texts and notices in binary packages.
5. Commercial boundary docs:
   - Define what is open source vs paid support/tooling in writing.

## Go/No-Go Checklist Before First Scanner Binary Release

1. Legal model chosen and documented (open, proprietary, or mixed).
2. Full dependency license inventory completed.
3. Qt/PyQt licensing position confirmed for intended distribution.
4. Apache attribution/NOTICE obligations mapped for any reused code.
5. Binary package includes all required licenses/notices.
6. EULA/terms for paid support/tooling drafted (if used).
7. Third-party IP/trademark review completed.
8. External legal review completed (strongly recommended).

## Suggested Operating Model for Funding and Support

1. Open-source track:
   - Keep core transparency and community velocity.
2. Commercial track:
   - Offer paid support, onboarding, deployment tooling, managed builds, and service commitments.
3. Governance:
   - Publish a clear policy that explains boundaries between community and paid offerings.

## Final Recommendation

Proceed with separate Scanner development if your goal is licensing flexibility, but gate release on dependency-license clearance (especially Qt/PyQt) and documented provenance compliance.

## Finding an OSS Attorney Near Florence, AL (35630)

Primary referral channels:

1. Alabama State Bar - Get Legal Help: [https://www.alabar.org/for-the-public/get-legal-help/](https://www.alabar.org/for-the-public/get-legal-help/)
2. Alabama State Bar - Lawyer Referral Service: [https://www.alabar.org/lrs-form/](https://www.alabar.org/lrs-form/)
3. Alabama State Bar - Member Search: [https://members.alabar.org/Member_Portal/Member_Portal/Member-Search.aspx](https://members.alabar.org/Member_Portal/Member_Portal/Member-Search.aspx)

Recommended location filters:

1. City: Florence
2. County: Lauderdale
3. Expand search region to Huntsville, then Birmingham, if OSS-specific expertise is limited locally.

Recommended practice-area filters:

1. Technology law
2. Intellectual property
3. Software licensing
4. Commercial contracts
5. Business/corporate

First-call screening questions:

1. Do you handle open-source software compliance and licensing strategy?
2. Have you advised on dual-track models (Apache open-source plus separately licensed binaries/support tooling)?
3. Do you advise on Qt/PyQt licensing implications for Windows/Linux binary distribution?
4. Can you provide a fixed-fee pre-release OSS compliance memo and release checklist?

Referral service note:

1. Alabama's referral service states an initial 30-minute consultation is capped at $50 before normal rates apply.

## Disclaimer

This brief is operational guidance, not legal advice. For first public binary release, obtain an OSS-experienced attorney review of your exact dependency stack and distribution plan.
