# Contributing

Use [GitHub issues](https://github.com/Meshbus/meshbus-protobufs/issues) for
non-sensitive questions and proposed changes. Use [Security](SECURITY.md) for
vulnerability reports. Include the schema commit, generator/runtime versions,
expected behavior and a small reproducer with credentials removed.

## Propose a schema change

1. Identify the service owner and intended wire behavior. Explain why an existing
   message/command cannot express it. List known consumers and migration needs.
2. Consult [Commands](docs/commands.md) before allocating group or command IDs.
   Propose an unused ID and request maintainer review; never reuse a published
   value or renumber neighboring entries to make the list contiguous.
3. Update `.proto`, `.options`, relevant protocol/workflow documentation and the
   command/index tables together. Specify units, presence, byte limits, errors
   and retry behavior. Keep implementation details out unless interoperability
   requires them. Maintain `package meshbus` and existing generation options
   unless an explicit migration is intended.
4. Run [Consumption](docs/consumption.md)'s checks, Python example and Nanopb
   example, plus `python -m unittest discover -s scripts -p 'test_*.py'`.
   Compare with the published baseline as described in [Release](docs/release.md).
5. Regenerate the reference bindings and report the tests actually performed.
   Report any additional consumer build or device tests separately.
6. Add a CHANGELOG entry, including source/API versus binary-wire compatibility.
   Submit a focused pull request with the motivation, migration and validation.

Keep generated bindings and temporary outputs outside this repository. New
source, scripts and configuration carry an Apache-2.0 SPDX identifier in an
appropriate comment. Markdown documentation uses the root LICENSE without a
per-file SPDX header. Preserve existing notices and include LICENSE when
redistributing repository files. Contributions are reviewed under the repository's
existing license; a change of licensing policy requires explicit maintainer
agreement.

Communicate respectfully, describe observable behavior, and avoid posting
private user data, credentials or device keys in examples and test fixtures.
