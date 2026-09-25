# Stateful workflows

These profiles describe the service exchanges associated with the
[command table](commands.md) and [field definitions](schema-index.md). Device
builds can disable services or impose tighter limits. Keep the profiles and
their schema revision together, and validate endpoint behavior separately.

## Remote management exchange

1. Select a Contact by its configured public-key prefix. Use its stored
   credential or supply a transient `secret` on the initial request.
2. For a small request, set `total_length=0` and send the complete target CBOR
   payload. For a larger request, set the complete CBOR length, `offset=0` and
   `transfer_id=0`; send contiguous nonempty chunks of at most 504 bytes.
3. Partial-upload responses return a nonzero `transfer_id` and `next_offset`.
   Continue at that offset with the same total length and an empty `secret`.
   Partial upload is not remote acceptance. Only the final local submission
   returns `accepted=true` and a correlation `tag`.
4. Poll `SMP_RESULT` using that tag and offset 0. Once `ready=true`, inspect
   `status`. On success, assemble response bytes using `total_length` and the
   received chunk length (at most 448 bytes), then decode the complete inner
   SMP response as described in [Transport](protocol.md).
5. Keep `consume=false` while retrieving/retrying data. A request with
   `consume=true` deletes a cached failure or the final response chunk before
   its reply is transmitted; losing that reply can lose the result. Retrieve
   and retain the result before issuing a separate final consume request.

There is one RAM upload slot. Starting a new transfer replaces it. Stale IDs,
noncontiguous offsets and a credential on continuation are rejected; arbitrary
upload-chunk replay is not guaranteed idempotent. Upload inactivity uses the
firmware SMP timeout (default 60 seconds). Completed results occupy a bounded
cache (default two entries), which is reused when full and lost on reboot.
`ready=false` can mean pending, unknown, consumed or evicted: it is not proof a
remote operation never ran. Set a client deadline and reconcile target state
before resubmitting a mutation. BLE notify is a best-effort alternative signal.

## Firmware delta update

Full-image upload retains standard MCUmgr image-management CBOR operations.
The custom Firmware group handles the signed delta workflow and reports the
shared lifecycle through `update_kind`.

The normal delta path is begin → write chunks → finish → apply → activate →
boot health/confirmation. States progress through RECEIVING, STAGED, VERIFIED,
APPLYING, PENDING_REBOOT and TESTING, then CONFIRMED or ROLLED_BACK; errors can
produce FAILED. Each operation must inspect `result`, `state`, `detail` and the
power/shutdown flags. Acceptance of apply/activate is not proof of a successful
new-image boot.

`DELTA_BEGIN` accepts the following **exact 20-key** CBOR map, in ascending key
order, using shortest integer/length encodings and definite lengths. There are
no extra keys or trailing bytes. All integers below are unsigned 32-bit values.
The encoded manifest is at most 384 bytes; `signature` is a detached 64-byte
Ed25519 signature over those exact bytes. The 32-byte transfer ID is SHA-256 of
the encoded manifest. Re-encoding changes the signed input if bytes differ.

| Key | Value | Constraint |
| --- | --- | --- |
| 1 | Protocol version | 1 |
| 2 | Campaign ID | Byte string, exactly 16 bytes |
| 3 | Target role | 1 repeater, 2 room, 3 sensor |
| 4 | Board ID | Text, at most 31 bytes; exact target match |
| 5 | SoC ID | Text, at most 15 bytes; exact target match |
| 6 | Minimum hardware revision | Inclusive |
| 7 | Maximum hardware revision | Inclusive |
| 8 | Partition ABI | 1 in the current profile |
| 9 | Source version | Four integers: major, minor, patch, build |
| 10 | Target version | Same four-integer array; must be newer |
| 11 | Source image SHA-256 | Exactly 32 bytes |
| 12 | Target image SHA-256 | Exactly 32 bytes |
| 13 | Patch SHA-256 | Exactly 32 bytes |
| 14 | Patch size | 89..24576 bytes |
| 15 | Chunk size | 448 |
| 16 | Image key ID | Must match the provisioned image key |
| 17 | Manifest key ID | Must match the provisioned manifest key |
| 18 | Security counter | Must meet the target anti-downgrade policy |
| 19 | Downgrade permission | Boolean false only |
| 20 | Patch format | 1, current NEWP delta profile |

Image hashes identify the complete signed MCUboot image through its ordinary
TLVs, excluding slot padding/trailer. Manifest authentication and MCUboot image
authentication use separate keys. Schema availability does not provision keys
or authorize an unsigned update. Patch construction is a consumer responsibility;
use a package producer matching format 1 rather than an arbitrary binary diff.

Write sequential 448-byte chunks, except the final remainder. In RECEIVING,
replaying already accepted bytes is checked against stored bytes; conflicting
bytes fail. `next_offset` tracks accepted progress, while `durable_received`
tracks checkpointed progress. After reconnect/reboot, query status and follow
the returned state and offset instead of assuming a previously sent chunk was
checkpointed. Repeated abort of an already aborted matching transfer succeeds;
abort is rejected during APPLYING, PENDING_REBOOT or TESTING. Do not treat every
command as safe to retry blindly.

## Desktop MBA sessions and packages

MBA means Meshbus Application; LLEXT is Zephyr's Linkable Loadable Extension
mechanism; EDK means Extension Development Kit. Query LLEXT HOST_INFO and match
`target`, `build_revision`, `metadata_version`, `interface_abi` and
`image_sha256` before selecting an EDK/application. The endpoint protocol version
is 1. A missing command must not be replaced by a guessed identity.

For a foreground session, submit MBA_START, retain its `session_id`, and poll
MBA_STATUS. ID 0 selects the latest session; a stale nonzero ID is rejected.
MBA_STOP uses a cooperative deadline of 1..30000 ms. Wait for
`resources_reclaimed=true` before mutating packages, even after an app has
stopped producing UI. States distinguish ACCEPTED, STARTING, RUNNING, STOPPING,
ENDED and FAILED.

Package transfers use standard MCUmgr FS upload, followed by the custom
Desktop PACKAGE command. Both SMP read/write dispatch slots exist for PACKAGE;
clients should use READ only with STATUS and WRITE for mutations. The action
field drives the current handler; a READ opcode alone is not a safety boundary.

A package installation proceeds as follows:

1. Upload the JSON installation record to `/extra/apps/.meshbus/incoming.json`.
2. Send PREPARE with that exact `manifest_path`, the app ID and explicit
   `replace` policy. Inspect `detail` and capacity before uploading app files.
3. Upload the declared files to their declared paths through MCUmgr FS.
4. Send COMMIT, which verifies file lengths/hashes and switches the package
   record. Re-query STATUS after interruption before deciding how to recover.

The record is at most 32768 bytes. Its schema-1 fields are:

| Field | Value |
| --- | --- |
| `schema`, `operation`, `purge_saves` | 1, 0 and false for a new installation; operation 1/2 are recovery records for rollback/uninstall |
| `id`, `version` | App ID: starts with lowercase letter, then lowercase letters/digits/underscore/hyphen/dot, at most 31 bytes; nonempty version at most 15 bytes |
| `bundle`, `image` | 64 lowercase hex digits: package identity and exact host image hash |
| `target`, `firmware` | Target and build revision matching HOST_INFO |
| `metadata_version`, `interface_abi` | Positive values matching the installed host |
| `mba_path` | Path to the single `.mba` entry in `files` |
| `atomic` | Whether files are placed under a versioned package root |
| `files` | 1..32 entries with `path`, integer `length` (0..64 MiB) and 64-lowercase-hex `sha256` |
| `requires` | Up to 128 required host symbol names, each 1..127 bytes |

Paths are bounded to 191 bytes under `/extra/apps/`. Atomic installs put files
under `/extra/apps/<id>/versions/<first-32-bundle-hex>/`; no duplicate file paths
or extra `.mba` entries are allowed. Components use ASCII letters/digits,
underscore, hyphen or dot and cannot begin with dot. Atomic multi-file apps
must require `mbs_desktop_app_resource_path` so assets remain relocatable.
The bundle identity is assigned by the package producer; file hashes are still
verified independently. Do not invent an identity from a display version alone.

Response states are `absent`, `committed`, `installing`, `committed-recovery`,
`uninstalling`, or `unknown` when no usable snapshot was obtained. A nonzero
`detail` forbids automatically advancing to the next mutation. COMMIT can finish
a pending recovery; ABORT is for an uncommitted installation, not a universal
undo. UNINSTALL preserves saves unless `remove_saves=true`. ROLLBACK requires
the desired previous bundle identity; a repeat targeting the already current
bundle is idempotent. Pending uninstalls must finish before unrelated mutations.

## Filesystem and display snapshots

Filesystem operations accept absolute paths under `/extra`; relative paths,
empty paths, backslashes and `.`/`..` segments are rejected. Volume ID empty or
absent selects `extra` for status. LIST starts at offset 0, defaults to 8 entries
and caps a page at 8. Follow `next_offset`; zero means no next page for normal
positive limits. Directory mutation between reads can change pagination: the
listing is not a frozen snapshot. FORMAT requires volume `extra` and the exact
confirmation token `FORMAT`; it is destructive and the current MCUmgr handler
schedules a reboot after success. Filesystem control does not replace standard
MCUmgr FS file upload/download.

Display DUMP uses snapshot ID 0 and offset 0 to capture. Retain the returned ID
for all subsequent chunks; a new capture by another client invalidates it.
Length 0 selects 256 bytes, otherwise use 1..256. Stop at `total_size`, not by
requesting an offset equal to it. Stale IDs return an error. SSD1306 page bytes
already use physical coordinates; do not rotate them again. Apply `inverted`
when rendering. A software snapshot does not prove physical panel behavior.

## Notifications and message delivery

A message send returns local acceptance and, for direct messages, an ACK token.
Only a corresponding ACK event establishes that acknowledgment was observed.
`MessageNextRequest` consumes the next inbound entry, so repeating after a lost
response can consume a different message. Store-change events prompt a fresh
query; they are not a complete change log.

Trace state is reserved/implementation-defined, not a portable success enum.
Contact telemetry notifications carry opaque remote telemetry bytes, distinct
from local `TelemetryReadResponse`; select a decoder for the remote protocol
and firmware version. This repository does not define that opaque telemetry
format. Unsupported payload formats should remain raw rather than be decoded
using the unrelated local sensor message. See [Transport](protocol.md) for BLE
loss and MTU behavior.
