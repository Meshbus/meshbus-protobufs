# SPDX-License-Identifier: Apache-2.0
"""Offline Clock config example. No device, credentials or network access."""

import argparse
import io
from pathlib import Path
import struct
import sys

import cbor2


def decode_response(packet, expected_operation, group, command, sequence):
    """Validate one complete version-1 SMP response before protobuf decoding."""
    if len(packet) < 8:
        raise ValueError("truncated SMP header")
    op, flags, length, got_group, got_sequence, got_command = struct.unpack(
        ">BBHHBB", packet[:8]
    )
    if (op, flags, got_group, got_command, got_sequence) != (
        expected_operation, 0, group, command, sequence
    ):
        raise ValueError("unexpected SMP version, operation or correlation")
    if len(packet) != 8 + length:
        raise ValueError("SMP length mismatch")
    stream = io.BytesIO(packet[8:])
    envelope = cbor2.CBORDecoder(stream).decode()
    if stream.read() or not isinstance(envelope, dict):
        raise ValueError("invalid CBOR envelope")
    if "err" in envelope or envelope.get("rc", 0) != 0:
        raise ValueError("SMP error response")
    if not isinstance(envelope.get("data"), bytes):
        raise ValueError("missing protobuf data byte string")
    return envelope["data"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generated", required=True, type=Path)
    args = parser.parse_args()
    sys.path.insert(0, str(args.generated.resolve()))
    from meshbus import clock_pb2

    request = clock_pb2.ClockConfigSetRequest()
    request.config.time_format = clock_pb2.ClockConfig.TIME_FORMAT_24H
    request.config.utc_offset_minutes = 480
    protobuf = request.SerializeToString()
    # Independent wire vector: nested config, enum 1, zigzag(480) = 960.
    if protobuf.hex() != "0a05080110c007":
        raise RuntimeError("Clock protobuf no longer matches the documented vector")
    body = cbor2.dumps({"data": protobuf})
    packet = struct.pack(">BBHHBB", 2, 0, len(body), 75, 1, 0) + body
    expected = "0200000e004b0100a16464617461470a05080110c007"
    if packet.hex() != expected:
        raise RuntimeError("SMP request vector mismatch")

    # Synthetic WRITE_RESPONSE (3), not a reply observed from hardware.
    response_packet = bytes.fromhex(
        "0300000e004b0100a16464617461470a05080110c007"
    )
    response = clock_pb2.ClockConfigSetResponse.FromString(
        decode_response(response_packet, 3, 75, 0, 1)
    )
    if not response.HasField("config") or response.config != request.config:
        raise RuntimeError("response config mismatch")
    print("request:", packet.hex())
    print("PASS: synthetic response uses 24-hour time and UTC offset +480 minutes")


if __name__ == "__main__":
    main()
