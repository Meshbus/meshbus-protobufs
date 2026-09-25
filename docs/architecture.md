# Architecture

This repository defines Protocol Buffer messages for device management, mesh
communication and loadable applications. It supplies the schema source and
field metadata used by firmware and host/mobile clients, with MeshCore
operations defined alongside the device services.

## Ownership

- `.proto` owns protobuf field types/numbers, enums and language naming options.
- Sibling `.options` owns the documented Nanopb storage profile. Consumers in
  other languages must implement relevant bounds explicitly.
- The [command table](commands.md), [transport contract](protocol.md) and
  [workflow profiles](workflows.md) define how these messages are used together.
- Consumers own runtime libraries, code generation, package publishing, hardware
  policy, credentials and transport implementation.

No generated language bindings or gRPC services are shipped. Reference examples
show a reproducible integration without defining every consumer's build pipeline.

## Organization and dispatch

All schemas are under `meshbus/`, share `package meshbus`, and currently have no
imports. Every `.proto` has a sibling `.options`; [the index](schema-index.md)
lists their responsibilities.

Management services normally use `*MgmtGroupId` and `*MgmtCommandId` enums.
`management.proto` instead uses `ManagementGroupId` and `ManagementCommandId`.
`notify.proto` defines event categories and a `oneof`, with no management group.
Request and response messages remain explicit. The MCUmgr operation is part of
the dispatch key; protobuf message names alone are insufficient for routing.

Asynchronous responses distinguish local acceptance from later delivery or
completion. Notify can prompt follow-up queries rather than duplicate full
service state. Bearer-specific delivery guarantees belong in the transport
contract, not in assumptions about protobuf reliability.

## Evolution

The package namespace is `meshbus`, without a version suffix.
Follow [Release](release.md) for public baselines and the four compatibility
surfaces. Keep bounds, comments and consumers aligned; a descriptor compile or
Buf compatibility pass alone does not establish runtime interoperability.
