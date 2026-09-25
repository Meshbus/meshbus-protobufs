# Transport contract

These are protobuf message definitions, not gRPC service definitions. Management
requests use the command mapping in [Commands](commands.md).
Firmware can omit groups at build time; a schema definition is not proof that a
device supports its command. Check the target firmware identity and handle
unsupported groups/operations explicitly.

## Management requests and responses

The framing is:

```text
bearer framing (UART, BLE SMP, or authenticated remote management)
  SMP header: operation, version, length, group, sequence, command
    CBOR map: {"data": byte-string}
      serialized request or response protobuf
```

SMP has an 8-byte header; length and group use network byte order. The raw SMP
operations are READ=0, READ_RESPONSE=1, WRITE=2, WRITE_RESPONSE=3. See the
[Zephyr SMP specification](https://docs.zephyrproject.org/latest/services/device_mgmt/smp_protocol.html)
for header version bits, bearer framing and the standard error envelope.
The [Python example](../examples/roundtrip.py) creates a version-1 SMP packet
and decodes a synthetic response without opening a transport.

For a Meshbus command, select the request type by **group + command + operation**.
For example group 75, command 0 uses `ClockConfigGetRequest` on READ and
`ClockConfigSetRequest` on WRITE. Both successful responses contain `config`,
but the request shapes differ. There is no protobuf RPC envelope that performs
this dispatch for you.

Send exactly one CBOR `data` byte-string entry. An empty protobuf serializes to
zero bytes, represented as `{"data": h''}`. The implementation additionally
accepts a completely empty SMP body for selected no-argument handlers. Do not
assume every command accepts it, or substitute an empty CBOR map. Even all-zero
scalar messages can serialize to zero bytes; handlers which disallow empty
input may reject them. Optional field presence can be significant.

Inspect the SMP response header and CBOR error envelope before decoding `data`.
An SMP error is not a protobuf response containing default-valued success fields.
The MCUmgr version determines whether the error is a legacy `rc` or a grouped
`err` map. Do not assume internal negative errno values and SMP error numbers
are interchangeable.

## Four distinct outcomes

| Signal | Interpretation |
| --- | --- |
| SMP/CBOR error | Request dispatch, decoding, authorization or handler failure; do not decode a success protobuf |
| `FirmwareResponse.result` | Firmware service result; inspect `state`, `detail` and retry flags too |
| `DesktopPackageResponse.detail`, `ManagementSmpResultResponse.status` | Zero or a negative target errno; nonzero is a business failure even in a successful SMP response |
| `accepted`, `triggered`, `started` | Only the guarantee documented for that operation; an asynchronous queue acknowledgment is not remote completion |

An SMP sequence identifies a transport request/response pair. A management
`tag`, message `ack_token`, upload `transfer_id`, MBA `session_id`, and display
`snapshot_id` identify different lifetimes. Never substitute one for another.
Read [Workflows](workflows.md) before retrying state-changing commands.

## Remote SMP tunneling

`ManagementSmpExchangeRequest.op` is a convenience selector: 0 means read,
1 means write, and the firmware also accepts raw write operation 2. In
particular, value 1 here does **not** mean READ_RESPONSE.

Its `payload` is the target command's raw CBOR body, excluding the inner SMP
header. For a Meshbus target that body itself contains a protobuf `data` entry;
standard MCUmgr groups retain their own CBOR schemas. The firmware constructs
the inner SMP header. The returned asynchronous `response`, after chunk
assembly, includes the complete inner SMP header and CBOR response. The result
must therefore pass through SMP error handling before protobuf decoding.

Read local `ManagementSecretGetResponse.effective_max_len` for the effective
remote SMP capacity. Field capacities of 504-byte request chunks, 448-byte
polled response chunks and 608-byte notify responses do not guarantee that a
particular bearer can transport a message of that size.

## Notify delivery

`NotifyType` is metadata on the firmware's internal ZBus event. Its numeric
values are not the `oneof` field numbers. The current BLE bridge sends only the
serialized `Notify` message, without an SMP header, CBOR wrapper, or leading
`NotifyType` byte. External BLE clients dispatch on `payload_variant`.

Subscribe to the Meshbus notify characteristic after establishing the required
authenticated connection. The characteristic and service identifiers are listed
below; this endpoint is distinct from both the standard SMP service and the
MeshCore Companion Nordic UART Service.

The bridge sends one complete protobuf per GATT notification. It does not
fragment messages larger than ATT MTU minus 3 bytes. Oversized payloads, queue
exhaustion and disconnected clients can lose events; there is no replay cursor
or delivery acknowledgment in this schema. Re-query stores after reconnect and
use management result polling when available. A message cache read can consume
an entry, so it is not a replay-safe state query.

- Service: `9d8e9f10-6137-4c6a-9a6a-9f3ad4c00100`
- Notify characteristic: `9d8e9f10-6137-4c6a-9a6a-9f3ad4c00101`

## Authentication and visibility

The protobuf format provides no encryption or authorization by itself. Firmware
bearers enforce access. Local credential status reads return whether a credential
is configured, not its bytes; the remote management policy forbids remote reads
of the secret command but permits authenticated rotation. Clients must preserve
redacted credentials during unrelated Contact edits; explicit clearing uses
`clear_management_secret`. Avoid logging key material or request credentials.
See [Security](../SECURITY.md) for reporting and consumer responsibilities.
