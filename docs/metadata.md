# Metadata and bounds

The sibling `.options` files use the [Nanopb options format](https://jpa.kapsi.fi/nanopb/docs/reference.html#generator-options).
They are versioned with the `.proto` files. Ordinary protoc language generators
do not read them: non-Nanopb clients must enforce the relevant bounds themselves.

| Option | Meaning | Example in this repository |
| --- | --- | --- |
| `max_size:N` on `string` | C storage of N bytes including the terminating NUL; at most N-1 UTF-8 content bytes | `Channel.name max_size:32` permits 31 content bytes |
| `max_size:N` on `bytes` | Maximum byte payload storage; no string terminator | `Channel.secret max_size:32` |
| `max_length:N` | String content capacity of N bytes, allocating N+1 bytes | `DesktopMbaStartRequest.app_id max_length:31` |
| `max_count:N` | Maximum number of repeated entries | `FsListResponse.entries max_count:8` |
| `int_size:8/16` on integer fields | Narrow native storage without changing the protobuf field type or wire encoding | `uint32` narrowed to 8 bits admits 0..255; signed 8-bit storage admits -128..127 |

Enum allocation behavior depends on the Nanopb version and C/C++ mode. An
`int_size` rule on an enum must not be read as a portable C ABI guarantee.
Consumers must keep generator and runtime versions compatible.

Patterns such as `*Contact.name` match qualified descriptor names. Keep every
proto/options pair together, and check for unmatched patterns after renaming a
message or field. The generation example in [Consumption](consumption.md)
passes the options search path explicitly and fails on unmatched rules.

## Storage, encoding and business limits

Storage capacity is not an exact-length requirement or permission to use every
representable value. For example:

- Channel secrets have a 32-byte capacity, but the current service accepts
  exactly 16 or 32 bytes.
- `Contact.management_secret` has a 64-byte Nanopb payload capacity;
  the management service profile limits credentials to 8..16 bytes. Do not infer
  a 64-character password limit.
- A public-key prefix has capacity 5; firmware chooses its exact width, normally
  4, through `CONFIG_MBS_CONTACT_PREFIX_BYTES` (supported range 3..5).
- A message can fit its field buffers but still exceed the selected transport's
  payload budget after protobuf, CBOR and SMP framing.

Lengths are UTF-8 byte counts, not Unicode character counts. Host-side bounds
checks should reject oversized input rather than silently truncate it. For fixed
identities and credentials, use the exact protocol length required by the
endpoint. Bounds alone do not validate UTF-8 or authenticate a message.

## Changing metadata

Update the `.proto`, matching `.options`, field comments and consumer checks in
one change. Review reductions in accepted sizes/counts, widened generated
structures and changed integer ranges even if `buf breaking` passes. See the
four compatibility surfaces in [Release](release.md).
