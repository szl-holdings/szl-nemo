# Changelog

## 0.5.0 (unreleased)

### Added

- Add the unsigned triad interface that binds a proposal, energy evidence, and
  Lambda disposition (#27).

### Fixed

- Block overflowing numeric inputs and redact rejected metadata from triad
  decision records (#28, #29).
- Reject malformed inference-envelope containers (#30).
- Match complete numeric claim tokens, including claims split across token
  boundaries (#21).
- Check installed distributions with isolated Python and verify dependency
  consistency in the canonical release gate.

### Changed

- Declare the canonical JSON receipt profile while preserving its encoded bytes
  (#18).

Earlier releases are documented in GitHub Releases.
