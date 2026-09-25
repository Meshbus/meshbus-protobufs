# Field semantics

## Presence and updates

Proto3 ordinary scalars do not distinguish omitted input from their zero value;
`optional` scalars do. Message fields and `oneof` alternatives have presence.
Preserve it across JSON, UI and generated binding layers. See the
[Protobuf presence guide](https://protobuf.dev/programming-guides/field_presence/).

`*ConfigSetRequest` generally replaces a complete configuration, not a patch.
Read, modify and write the full object when retaining existing settings. This is
not a compare-and-swap operation: concurrent writers can overwrite each other.
Use dedicated `Enable` operations for the narrower operation where available.
A response with effective configuration does not guarantee the asynchronous
settings persistence has completed before power loss.

| Field | Meaning to preserve |
| --- | --- |
| `GnssConfig.electronic_compass` | Absent uses the firmware default (enabled); explicit false disables this preference |
| `MeshcoreNodeDiscoverRequest.filter` | Absent requests all known roles; explicit zero is a supplied mask |
| `PowerStatusResponse.voltage_mv` and other optional measurements | Absence means unavailable, not a measured zero |
| `ContactSetRequest.contact.management_secret` | Empty preserves an existing redacted credential unless `clear_management_secret` is true |
| `ManagementSmpExchangeRequest.secret` | Empty selects the stored Contact credential; supplied bytes are transient |
| `TelemetryReadRequest.channel_id` | Zero is the valid ACCEL_X channel, not an unspecified sentinel |
| `FsListRequest.limit` | Absent defaults to 8; use 1..8 for progress rather than an explicit zero |

Unknown enum values or notify variants must not be interpreted as a known
success value. Preserve unknown protobuf fields when the chosen runtime supports
it, but do not assume all embedded consumers retain them across decode/re-encode.

## Units and identities

- Clock wall time uses Unix UTC seconds/milliseconds as named; `uptime_ms` is
  monotonic time since boot, not wall time. A timezone offset changes display
  preferences rather than the timestamp epoch.
- Contact and MeshCore positions use signed microdegrees. GNSS navigation uses
  signed nanodegrees, millimeters, mm/s and millidegrees. Convert explicitly.
- SNR fields described as Q4 in this repository use quarter-dB units: divide by
  4. Do not infer a divisor of 16 from the name. Other undocumented raw trace
  state values must be treated as implementation-specific.
- `TelemetrySensorValue` is `integer + fractional_micro / 1_000_000`, including
  signed fractions. Vector channels return values in driver/service order.
- Telemetry IDs mirror the firmware's Zephyr `sensor_channel` enumeration. Use
  `TelemetryStatusResponse.channels` to discover configured channels; an enum
  entry does not guarantee a provider. The matching Zephyr
  [sensor API](https://docs.zephyrproject.org/latest/doxygen/html/group__sensor__interface.html)
  defines channel units: for example acceleration m/s², gyro rad/s, temperature
  °C, pressure kPa, humidity %, voltage V and current A. Gas, particle, gauge and
  vendor-specific channels need their matching driver's unit specification.
- `InputInject*Request.type/code` use Zephyr input event codes. Action values
  follow the Meshbus input action contract listed below, rather than the raw
  key value (press/release). Input acceptance does not prove UI consumption.
- String limits are UTF-8 bytes; byte fields contain raw bytes rather than hex
  or base64 text. JSON tooling may add a representation layer. See
  [Metadata](metadata.md) for the Nanopb profile.

Input action values: 0 = short key action, 1 = long key action,
2 = clockwise scroll, 3 = counterclockwise scroll. Raw key values represent
physical-style edges; they do not automatically synthesize these actions.

## Version and feature negotiation

Desktop MBA, Desktop package and LLEXT host-info responses currently use
`protocol_version = 1`. These versions describe those endpoints, not a global
schema version or a proof that all groups are enabled. Reject an unsupported
version before mutation. `metadata_version` and `interface_abi` are separate MBA
compatibility fields, and `image_sha256` identifies the installed host image.
A hash match is not a signature-verification assertion.

A field's presence in the schema does not guarantee endpoint support.
Firmware-specific range, hardware and role restrictions apply. Record the
schema revision and firmware identity in client diagnostics, while excluding
secrets.
