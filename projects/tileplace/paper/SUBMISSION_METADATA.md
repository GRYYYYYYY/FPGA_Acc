# TilePlace submission metadata checklist

## DAC 2027 call checked 2026-10-13

The [official Research Manuscript call](https://dac.com/2027/program/research-manuscript-submissions)
specifies IEEE templates, six body pages plus one references-only page,
anonymous manuscript/PDF metadata, and an approximately 100-word abstract.
Abstracts are due November 11, 2026; manuscripts November 18, 2026, both at
17:00 US Pacific. Target year/track remains awaiting user preference.
The existing ACM draft and recorded 8+1 page build do not satisfy these rules.
Use [COMPLETION_GATES.md](COMPLETION_GATES.md) for current completion criteria.

## Current IEEE working draft

`dac2027/main.tex` is the new working manuscript. Its title is
“TilePlace: Deterministic Transactional Placement Refinement with a Full-Color
Hardware Kernel.” It uses the unmodified IEEEtran conference class and
bibliography style, anonymous author text, empty PDF author metadata, and a
99-word abstract. Build and format receipts are under
`../work/dac_completion_2026-10-13/ieee_rewrite_build/`; the initial build's
missing bibliography-style error is preserved alongside successful rebuilds.
This draft explicitly says timing closure and adoption remain unresolved.
It is not a final submission and does not resolve the target year/track.

## Legacy ACM draft configuration

`dac/main.tex` preserves the previous title, abstract, CCS concepts, and
keywords. That manuscript is configured as an anonymous ACM review
submission; venue-specific metadata remains intentionally unresolved rather
than inferred.

## Legacy manuscript metadata (not the IEEE submission settings)

| Field | Current value | Submission action |
|---|---|---|
| Title | TilePlace: Deterministic Routed-Oracle Transactional Refinement for Heterogeneous FPGA Placement | Confirm capitalization against the venue form |
| Running venue | Unspecified anonymous review submission | Replace from the official call |
| Date and location | Unspecified | Replace from the official call |
| Review mode | `sigconf,anonymous,review` | Keep only if required by the venue |
| Authors and affiliations | Anonymous placeholders | Populate only after the anonymity policy permits |
| Copyright | `none` | Replace with the rights form selected by the venue |
| ISBN and DOI | Empty | Populate from the publisher, not speculatively |
| CCS | Reconfigurable computing; hardware-software codesign | Confirm in the submission portal |
| Keywords | FPGA placement; deterministic transactions; timing-driven placement; heterogeneous FPGA | Copy to the portal |
| Main-paper length | 8 body pages plus 1 references page in the current reproducible build | Recheck against the final page policy |

## Portal fields still required

- submission ID, track/topic, and corresponding-author contact;
- complete author order, affiliations, ORCIDs, and conflicts;
- abstract and keywords copied from the final compiled source;
- artifact/source availability statement and anonymized URL, if submitted;
- funding, acknowledgments, and disclosure text after de-anonymization;
- official conference dates/location, rights statement, ISBN, and DOI.

## Final anonymity and consistency checks

- Search source, PDF text, PDF metadata, acknowledgments, URLs, and artifact
  archives for names, institutions, usernames, and identifying paths.
- Regenerate all tables with `prepare_artifacts.py`; do not edit generated TeX
  fragments by hand.
- Confirm that the six-case V4 held-out aggregate, ten-case reference matrix,
  separate apex4 constrained point, and six-case conventional/AP comparison
  remain distinct.
- Confirm that no CPU, C-model, `hw_emu`, or routed-implementation timing is
  described as physical-U280 performance.
- Run the venue's PDF checker and verify fonts, page size, page count,
  references, accessibility text, and submission-system abstract formatting.

## Unresolved implementation provenance (2026-09-29)

Submission readiness is not established: a development replay exposed timing
parser drift. Resolve the source/feedback provenance described in RESULTS.md
before claiming a single frozen V4 implementation or outcome-blind held-out
validation. Preserve the archived numerical results; do not silently regenerate
or replace them using the current parser.
