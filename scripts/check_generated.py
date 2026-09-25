# SPDX-License-Identifier: Apache-2.0
"""Check representative Nanopb layouts to detect missing options files."""

from pathlib import Path
import sys


def check(root):
    expected = {
        "channel": ("char name[32];", "PB_BYTES_ARRAY_T(32)"),
        "desktop": ("char app_id[32];", "char path[192];"),
        "fs": ("meshbus_FsEntry entries[8];",),
        "gnss": ("meshbus_GnssSatellite satellites[64];",),
        "notify": ("meshbus_Notify_NotifyNodeTelemetry",),
    }
    for schema, markers in expected.items():
        text = (root / "meshbus" / f"{schema}.pb.h").read_text()
        for marker in markers:
            if marker not in text:
                raise ValueError(f"missing generated contract in {schema}: {marker}")
    print("PASS: Nanopb options applied and corrected Notify type generated")


if __name__ == "__main__":
    check(Path(sys.argv[1]))
