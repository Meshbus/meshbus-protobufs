# Release

This repository defines the initial Meshbus schema contract under
`package meshbus`. The `.proto` definitions, matching Nanopb `.options` and
command/transport documentation describe the current interface. Generate
firmware and client bindings from the same reviewed revision.

## Contract review

Review field numbers and types, enum values, group/command dispatch, generated
names, byte capacities, units, presence/defaults and asynchronous outcomes as
one interface. Schema compilation verifies definitions; consumer tests verify
how those definitions are used. Endpoint protocol versions and MBA metadata
versions are listed in [Field semantics](field-semantics.md).

## Local checks and CI

Use the complete commands in [Consumption](consumption.md). CI enforces:

- SPDX declarations in non-Markdown files and a tracked LICENSE;
- Buf lint and descriptor compilation;
- proto/options pairing, option matches and actual Nanopb generation;
- command and schema-index coverage, and local Markdown links/anchors;
- the offline Python wire example and validation-tool regression tests.

The checks validate the current source tree. Generated bindings and test outputs
go outside the schema repository. Runtime libraries and their licenses are
owned by consumers.

## Release checklist

1. Review the final source and documentation and confirm LICENSE inclusion with
   `git ls-files --error-unmatch LICENSE`. Preserve Apache-2.0 notices.
2. Describe the release's capabilities in CHANGELOG and validate affected
   firmware/client consumers against the reviewed schema revision.
3. Run the documented checks from a clean checkout; record tool versions and
   results. Schema checks do not qualify transport, hardware, OTA or signing.
4. Verify the private vulnerability reporting entry in SECURITY.md and confirm
   that the release's source and documentation are accessible.
5. Publish the reviewed commit with a version tag. Consumers pin that tag or
   commit and record the resolved commit in their artifacts.

Publishing, changing repository visibility/settings and creating a release are
maintainer actions, not side effects of the validation scripts.
