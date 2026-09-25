# Schema index

Each file uses `package meshbus` and has a sibling `.options` file. All current
files are self-contained, with no imports. Message definitions are authoritative
for types and field numbers; [Metadata](metadata.md) supplies native storage
bounds and [Commands](commands.md) supplies operation dispatch.

| Schema | Group | Purpose |
| --- | --- | --- |
| [bluetooth](../meshbus/bluetooth.proto) | 73 | Bluetooth configuration, connection/security status and Companion enablement |
| [channel](../meshbus/channel.proto) | 66 | Channel secrets, names and slot storage |
| [clock](../meshbus/clock.proto) | 75 | Clock display preferences and wall-clock setting |
| [contact](../meshbus/contact.proto) | 79 | Contact records, credentials and asynchronous contact operations |
| [desktop](../meshbus/desktop.proto) | 78 | UI diagnostics, MBA sessions and package transactions |
| [display](../meshbus/display.proto) | 74 | Display settings, power state and framebuffer snapshots |
| [firmware](../meshbus/firmware.proto) | 82 | Delta update lifecycle and shared firmware update status |
| [fs](../meshbus/fs.proto) | 81 | Filesystem metadata, directory control and volume format |
| [gnss](../meshbus/gnss.proto) | 67 | GNSS configuration, cached fixes, satellites and heading status |
| [indicator](../meshbus/indicator.proto) | 68 | Lights, buzzer and feedback settings |
| [input](../meshbus/input.proto) | 76 | Input status and synthetic action/raw-event injection |
| [llext](../meshbus/llext.proto) | 77 | Extension enablement and installed host identity |
| [management](../meshbus/management.proto) | 80 | Authenticated remote SMP exchange, credential status and result polling |
| [meshcore](../meshbus/meshcore.proto) | 70 | MeshCore protocol configuration and mesh operations |
| [message](../meshbus/message.proto) | 69 | Inbound message queue and asynchronous send requests |
| [notify](../meshbus/notify.proto) | — | Asynchronous event payload variants; no MCUmgr group |
| [power](../meshbus/power.proto) | 65 | Battery/power status, shutdown policy, reboot and bootloader entry |
| [radio](../meshbus/radio.proto) | 71 | Radio settings, diagnostics and RF test commands |
| [telemetry](../meshbus/telemetry.proto) | 72 | Local sensor channels, sampling policy and scalar/vector reads |

Use [Workflows](workflows.md) for Firmware, Desktop, Filesystem and remote
management transactions, [Transport](protocol.md) for SMP/BLE framing, and
[Field semantics](field-semantics.md) for presence, units and version handling.
A group listed here can be disabled in a particular firmware build.
