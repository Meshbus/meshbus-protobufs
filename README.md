# meshbus-protobufs

Protocol Buffer definitions for Meshbus device management, mesh communication
and loadable applications. Firmware, CLI, desktop and mobile clients can
generate bindings from the same schema. The definitions cover MeshCore protocol
operations and device services.

**Status: pre-stable.** No stable compatibility baseline has been declared. Pin a
reviewed commit or public release tag and read [the changelog](CHANGELOG.md) when
updating. See [Release](docs/release.md) for the public compatibility policy.

This repository ships schema source and bounded-field metadata, not generated
SDKs or a gRPC server. Consumers own generation, runtimes and packaging. The
current management transport is SMP/CBOR carrying protobuf; BLE notifications
use a separate raw protobuf payload.

## Start here

1. [Consumption](docs/consumption.md): obtain a pinned checkout, install the
   reference tools, generate Python/Nanopb bindings and run an offline example.
2. [Schema index](docs/schema-index.md): find the relevant service among the
   19 schemas and its management group.
3. [Commands](docs/commands.md) and [Transport](docs/protocol.md): choose the
   operation/request/response and handle framing, errors and notifications.
4. [Workflows](docs/workflows.md): implement remote exchanges, updates, application
   transactions and paginated/chunked reads.

The remaining references are [Architecture](docs/architecture.md),
[Metadata](docs/metadata.md), [Field semantics](docs/field-semantics.md),
[Contributing](CONTRIBUTING.md) and [Security reporting](SECURITY.md).

## Quick validation

From the repository root, with Buf 1.73.0 and Python 3.11+ available:

```sh
schema_work="$(mktemp -d)"
python3 -m venv "$schema_work/venv"
. "$schema_work/venv/bin/activate"
python -m pip install -r requirements-dev.txt
buf lint
python scripts/check.py --output "$schema_work/check"
```

The check prints `PASS: repository contracts`. Continue with the runnable
[Python and Nanopb examples](docs/consumption.md#python-request-and-response-example)
for generation validation. Outputs stay in the temporary directory. These
offline checks cover schema and generation contracts; firmware behavior and
device interoperability require consumer validation.

## Repository layout

| Path | Responsibility |
| --- | --- |
| [meshbus/](meshbus/) | `.proto` source and companion Nanopb `.options` |
| [docs/](docs/) | Protocol, consumption, workflow and release references |
| [examples/](examples/) | Offline request/response example |
| [scripts/](scripts/) | Repository/generation checks and their regression cases |
| [zephyr/module.yml](zephyr/module.yml) | Schema-only west module discovery, without build actions |
| [requirements-dev.txt](requirements-dev.txt) | Pinned direct reference-tool dependencies |

## License

The schemas, companion `.options`, examples, validation scripts, documentation
and repository configuration are licensed under the Apache License, Version 2.0
(`Apache-2.0`). See [LICENSE](LICENSE) for the complete terms.
Keep SPDX identifiers and applicable notices when copying or modifying files,
and include the license text when redistributing them.

Keep the applicable Apache-2.0 notices for schema material incorporated into
generated bindings or descriptors. Generators and runtimes have their own
licenses; selecting one does not change this repository's license. Third-party
material retains its own terms. This project is distributed without warranty.
