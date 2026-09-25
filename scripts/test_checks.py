# SPDX-License-Identifier: Apache-2.0
"""Regression cases for documentation and example failure boundaries."""

import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest

import cbor2
from google.protobuf import descriptor_pb2

import check

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("roundtrip", ROOT / "examples/roundtrip.py")
roundtrip = importlib.util.module_from_spec(spec)
spec.loader.exec_module(roundtrip)


class Checks(unittest.TestCase):
    def test_links_and_anchor_failures(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "target.md"
            target.write_text("# Existing title\n")
            doc = root / "README.md"
            doc.write_text("[ok](target.md#existing-title)\n")
            self.assertEqual(check.check_links(root, [doc]), 1)
            for link in ("target.md#missing", "missing.md", "../outside.md"):
                doc.write_text(f"[bad]({link})\n")
                with self.subTest(link=link), self.assertRaises(ValueError):
                    check.check_links(root, [doc])

    def test_headings_ignore_code_and_number_duplicates(self):
        self.assertEqual(check.anchors("# A\n# A\n```sh\n# Not heading\n```"), {"a", "a-1"})

    def test_options_match_only_own_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "meshbus").mkdir()
            (root / "meshbus/a.proto").touch()
            options = root / "meshbus/a.options"
            descriptor = descriptor_pb2.FileDescriptorSet()
            file = descriptor.file.add(name="meshbus/a.proto", package="meshbus")
            message = file.message_type.add(name="A")
            message.field.add(name="value", number=1, type=9)
            options.write_text("*A.value max_size:32\n")
            self.assertEqual(check.check_options(root, descriptor), 1)
            options.write_text("*Missing.value max_size:32\n")
            with self.assertRaises(ValueError):
                check.check_options(root, descriptor)

    def test_smp_errors_never_decode_as_success(self):
        def packet(envelope):
            body = cbor2.dumps(envelope)
            return struct.pack(">BBHHBB", 3, 0, len(body), 75, 1, 0) + body
        for envelope in ({"rc": 2}, {"err": {"group": 75, "rc": 1}}, {"data": "wrong"}):
            with self.subTest(envelope=envelope), self.assertRaises(ValueError):
                roundtrip.decode_response(packet(envelope), 3, 75, 0, 1)
        valid = packet({"data": b""})
        self.assertEqual(roundtrip.decode_response(valid, 3, 75, 0, 1), b"")
        for bad in (valid[:7], valid[:-1], valid + b"\x00"):
            with self.subTest(packet=bad), self.assertRaises(ValueError):
                roundtrip.decode_response(bad, 3, 75, 0, 1)
        with self.assertRaises(ValueError):
            roundtrip.decode_response(valid, 3, 75, 0, 2)

    def test_command_table_detects_missing_wrong_and_duplicate_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs/schema-index.md").write_text("[clock](../meshbus/clock.proto)")
            descriptor = descriptor_pb2.FileDescriptorSet()
            file = descriptor.file.add(name="meshbus/clock.proto", package="meshbus")
            file.enum_type.add(name="ClockMgmtGroupId").value.add(
                name="CLOCK_MGMT_GROUP_ID_MESHBUS_CLOCK", number=75
            )
            file.enum_type.add(name="ClockMgmtCommandId").value.add(
                name="CLOCK_MGMT_COMMAND_ID_STATUS", number=1
            )
            file.message_type.add(name="ClockStatusRequest")
            file.message_type.add(name="ClockStatusResponse")
            row = ("| clock | 75 | 1 | CLOCK_MGMT_COMMAND_ID_STATUS | READ | "
                   "ClockStatusRequest | ClockStatusResponse |\n")
            table = root / "docs/commands.md"
            table.write_text(row)
            self.assertEqual(check.check_commands(root, descriptor), 1)
            for invalid in ("", row.replace("| 75 |", "| 76 |"), row + row,
                            row.replace("READ", "UNKNOWN"), row.replace("ClockStatusRequest", "Gone")):
                table.write_text(invalid)
                with self.subTest(table=invalid), self.assertRaises(ValueError):
                    check.check_commands(root, descriptor)


if __name__ == "__main__":
    unittest.main()
