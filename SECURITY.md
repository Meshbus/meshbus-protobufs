# Security

## Report a vulnerability privately

Use [GitHub private vulnerability reporting](https://github.com/Meshbus/meshbus-protobufs/security/advisories/new).
Include the affected schema revision, consumer/runtime versions, impact and a
minimal reproducer. Redact credentials, private keys, personal information and
production identifiers. Do not open a public issue with vulnerability details.

If the private reporting form is unavailable, open a content-free issue asking
a maintainer to enable private reporting, then wait for a private channel before
sending technical details.

## Support scope

The project is pre-stable and currently evaluates fixes against the latest main
revision; there are no declared long-term-support branches. Report affected
pinned revisions so maintainers can identify impacted consumers. A schema fix
does not update deployed devices automatically.

## Consumer responsibilities

Protobuf encoding does not authenticate or encrypt traffic. Consumers own bearer
authentication, authorization, secret storage, redaction, replay handling and
resource limits. The schema includes identity and credential fields because
some boundaries need them; their presence does not grant permission to expose
them in read responses or logs.

Preserve redacted Contact credentials on unrelated updates; explicit clearing
requires its dedicated flag. Management secret status does not return credential
bytes. Treat remote management, filesystem mutation, application installation,
reboot and firmware update as privileged operations. Evaluate both transport
errors and service results before proceeding. See [Transport](docs/protocol.md)
and [Metadata](docs/metadata.md) for framing and bounded-input expectations.
