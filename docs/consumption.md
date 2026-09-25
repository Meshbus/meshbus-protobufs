# Consumption

Consumers own generation, runtime libraries and packaging. This repository
provides reference examples and validation tools, not prebuilt language SDKs.
Keep `.proto` and `.options` at the same pinned revision. Generated output goes
outside the schema tree and must not be committed here.

## Get a reproducible checkout

```sh
git clone https://github.com/Meshbus/meshbus-protobufs.git
cd meshbus-protobufs
# Replace this with the reviewed commit or release tag you intend to consume.
schema_ref='<reviewed-commit-or-tag>'
git checkout --detach "$schema_ref"
git rev-parse HEAD
```

There is no stable release baseline declared yet. Select an actual reviewed
commit; do not copy the placeholder as a revision or assume a v1.0.0 tag exists.

## Toolchain

The reference checks use Python 3.11 or newer and the direct dependency versions
in [requirements-dev.txt](../requirements-dev.txt): grpcio-tools 1.68.0 (bundled
protoc 28.1), protobuf runtime 5.29.6, Nanopb 0.4.9.1 and cbor2 5.6.5. CI uses
Python 3.11 and Buf 1.73.0. The requirements file pins direct reference tools;
transitive dependencies are resolved during installation.

Install Buf using its [official installation instructions](https://buf.build/docs/installation/)
and select 1.73.0 for parity with CI. The Python setup below is isolated and does
not require a system protoc. Use a generator with proto3 optional support;
for generated Python bindings, keep the compiler/runtime pair compatible.

Run from this repository root in a POSIX shell:

```sh
schema_work="$(mktemp -d)"
python3 -m venv "$schema_work/venv"
. "$schema_work/venv/bin/activate"
python -m pip install -r requirements-dev.txt
buf --version
python -m grpc_tools.protoc --version
buf lint
python scripts/check.py --output "$schema_work/check"
```

A successful run prints `PASS: repository contracts` and the artifact directory.
The validator checks licenses, relative Markdown links/anchors, descriptor
compilation, proto/options pairing and patterns, and command/index coverage.
It does not contact devices or check external links.

## Python request and response example

Continue in the same activated shell:

```sh
mkdir -p "$schema_work/python"
python -m grpc_tools.protoc -I . --python_out="$schema_work/python" meshbus/*.proto
python examples/roundtrip.py --generated "$schema_work/python"
```

The output is a fixed Clock CONFIG write packet followed by a PASS line. It
constructs a protobuf request, wraps it in CBOR/SMP, then decodes an independent
synthetic response vector. It opens no transport and changes no clock. Read
[Transport](protocol.md) before adding UART/BLE or remote management; raw SMP
packets still need the selected bearer's framing.

## Nanopb example

With the same pinned environment:

```sh
mkdir -p "$schema_work/nanopb"
python -m grpc_tools.protoc -I . \
  --plugin="protoc-gen-nanopb=$(command -v protoc-gen-nanopb)" \
  --nanopb_opt=-I.,--error-on-unmatched \
  --nanopb_out="$schema_work/nanopb" meshbus/*.proto
python scripts/check_generated.py "$schema_work/nanopb"
```

The explicit `-I.` plugin option makes the sibling `.options` discoverable.
Unmatched option names fail generation; the second command also checks selected
capacity-sensitive generated structures, so silently missing all options does
not pass. Link the resulting `.pb.c` files with a compatible Nanopb runtime in
your consumer. Validate the selected generator/runtime pair in the target build;
the example checks generation without qualifying a target C ABI or firmware
integration.

## Zephyr/west integration

[zephyr/module.yml](../zephyr/module.yml) declares a discoverable, schema-only
module with no build actions. Merely adding it to west does not generate code.
A consumer manifest can include the following, replacing the revision:

```yaml
manifest:
  projects:
    - name: meshbus-protobufs
      url: https://github.com/Meshbus/meshbus-protobufs
      revision: <reviewed-commit-or-tag>
      path: modules/lib/meshbus-protobufs
```

After module discovery, `ZEPHYR_MESHBUS_PROTOBUFS_MODULE_DIR` locates the schemas.
An application can call Zephyr's Nanopb integration from its own CMake code:

```cmake
list(APPEND CMAKE_MODULE_PATH ${ZEPHYR_BASE}/modules/nanopb)
include(nanopb)
set(MESHBUS_PROTO_ROOT ${ZEPHYR_MESHBUS_PROTOBUFS_MODULE_DIR})
set(NANOPB_GENERATE_CPP_STANDALONE OFF)
nanopb_generate_cpp(PROTO_SRCS PROTO_HDRS
  RELPATH ${MESHBUS_PROTO_ROOT}
  ${MESHBUS_PROTO_ROOT}/meshbus/clock.proto)
target_sources(app PRIVATE ${PROTO_SRCS})
target_include_directories(app PRIVATE ${CMAKE_CURRENT_BINARY_DIR})
```

The application must enable/configure its compatible Nanopb runtime and add every
schema it consumes. These snippets do not initialize a complete Zephyr workspace
or replace a product's module/library dependency ordering.

## Other languages

The file options set C# namespace `Meshbus.Protobufs`, Java package
`org.meshbus.proto`, per-file Java outer classes, Go import path
`github.com/meshbus/go/generated`, and an empty Swift prefix. They are generation
conventions, not evidence that a matching package is published. Go consumers
can map imports with their protoc plugin's `M` options or managed configuration;
record overrides alongside the pinned schema version. Do not mutate upstream
options merely to select a local output directory.

Non-Nanopb runtimes must apply the [metadata bounds](metadata.md) and
[field semantics](field-semantics.md). After updating a dependency, review the
[changelog](../CHANGELOG.md), regenerate bindings, and test your consumer.
