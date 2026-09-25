# Release and compatibility

No stable compatibility baseline has been declared. `package meshbus` is
unversioned. The first public tag establishes a reproducible consumer baseline,
including during 0.x development; public consumers cannot be updated atomically
with this repository.

## Versions and identifiers

- Use `v0.MINOR.PATCH` while stabilizing. A breaking change increments MINOR and
  requires a migration entry; PATCH is for changes compatible with that minor.
- Declare `v1.0.0` only after the published contract and consumers are validated.
  Thereafter use MAJOR for intentional breaks, MINOR for compatible additions,
  and PATCH for compatible corrections.
- Keep published field numbers, command/group IDs and enum values stable. Do not
  renumber to close gaps. Reserve removed protobuf field/enum numbers and names;
  do not reuse command/group IDs for unrelated operations.
- A message/type rename can preserve binary encoding while breaking generated
  APIs and JSON type names. Document both effects.
- Release tags are immutable. Pin dependencies by reviewed commit or tag and
  record the exact resolved commit in consumer artifacts.

## Four compatibility surfaces

| Surface | Review |
| --- | --- |
| Binary wire | Field numbers/types, enum values, group/command dispatch and encoding |
| Generated API | Message/field names, package and language options, source imports |
| Metadata/native storage | Options, capacity/count/range changes and C layout assumptions |
| Runtime semantics | Units, presence/defaults, access, retries, state transitions and error meaning |

`buf.yaml` selects the FILE breaking policy, which includes generated-code
compatibility constraints. [Buf's checks](https://buf.build/docs/breaking/)
complement manual review; they do not interpret sibling options or firmware
behavior. Growing a bound can require receiver updates too.

## Local checks and CI

Use the complete commands in [Consumption](consumption.md). CI enforces:

- SPDX declarations in non-Markdown files and a tracked LICENSE;
- Buf lint and descriptor compilation;
- proto/options pairing, option matches and actual Nanopb generation;
- command and schema-index coverage, and local Markdown links/anchors;
- the offline Python wire example and validation-tool regression tests.

CI additionally enforces `buf breaking` when repository variable
`SCHEMA_COMPATIBILITY_BASELINE` names a published tag or full commit SHA in this
repository. For the initial public release, validate the source, create its tag,
then configure that tag as the baseline for subsequent checks. When the variable
is unset, the workflow reports that compatibility checking is inactive.

The workflow checks out full history and compares against the local Git ref.
For local review:

```sh
buf breaking . --against '.git#tag=<published-baseline-tag>'
```

For an intentional breaking release, record the failing compatibility rules and
migration in the changelog, coordinate known consumers, and have a maintainer
approve the next baseline. Do not silently remove the CI gate to merge a break.

## Release checklist

1. Review the final diff and LICENSE inclusion with `git ls-files --error-unmatch LICENSE`.
   Preserve the Apache-2.0 policy; generator/runtime licensing is
   separately owned, and this repository grants no extra generated-code exception.
2. Update CHANGELOG with the release's capabilities. For subsequent releases,
   include changed APIs/options, compatibility impact and any required migration.
3. Run the documented checks from a clean checkout; record versions/results.
   Passing schema checks does not qualify transport, hardware, OTA or signing.
4. Verify the GitHub private vulnerability reporting entry in SECURITY.md works
   and confirm that the release's source and documentation are accessible.
5. Publish only the reviewed commit/tag; configure or deliberately advance the
   compatibility baseline and preserve prior release notes.

Publishing, changing repository visibility/settings and creating a release are
maintainer actions, not side effects of the validation scripts.
