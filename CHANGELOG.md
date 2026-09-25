# Changelog

## Initial version

- Nineteen Protocol Buffer schemas for device management, mesh communication,
  telemetry, notifications, firmware updates and loadable applications.
- Companion Nanopb metadata defining field capacities and native storage bounds.
- Command, transport, workflow and field-semantics references.
- Python and Nanopb generation examples, including an offline SMP/CBOR exchange.
- Checks for schema compilation, command coverage, metadata, generated bounds,
  licenses and documentation links.
- Schema-only Zephyr module discovery and a configurable CI compatibility
  baseline for subsequent releases.

Repository-owned material uses Apache-2.0. See [LICENSE](LICENSE) and the
[release policy](docs/release.md). Generated bindings and runtime libraries are
provided by consumers.
