# SPDX-License-Identifier: Apache-2.0
"""Validate source/document contracts without accessing consumers or devices."""

import argparse
import fnmatch
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit

from google.protobuf import descriptor_pb2

ROOT = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def source_files(root):
    result = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=root
    )
    return sorted({root / name for name in result.decode().split("\0") if name})


def check_license(root, files):
    subprocess.run(
        ["git", "ls-files", "--error-unmatch", "LICENSE"],
        cwd=root, check=True, stdout=subprocess.DEVNULL,
    )
    license_text = (root / "LICENSE").read_text()
    for marker in ("Apache License", "Version 2.0, January 2004",
                   "END OF TERMS AND CONDITIONS"):
        require(marker in license_text, "LICENSE is incomplete")
    for path in files:
        if path.name == "LICENSE" or path.suffix == ".md":
            continue
        text = path.read_text()
        prefix = "//" if path.suffix == ".proto" else "#"
        expected = f"{prefix} SPDX-License-Identifier: Apache-2.0"
        require(any(line.startswith(expected) for line in text.splitlines()[:3]),
                f"missing SPDX declaration: {path.relative_to(root)}")


def anchors(text):
    found, counts = set(), {}
    # Fenced examples can contain heading-like text and are not headings.
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    for title in re.findall(r"^#{1,6}\s+(.+?)\s*#*\s*$", text, re.M):
        slug = re.sub(r"[^\w\- ]", "", title.lower()).replace(" ", "-")
        count = counts.get(slug, 0)
        counts[slug] = count + 1
        found.add(slug if count == 0 else f"{slug}-{count}")
    found.update(re.findall(r'(?:id|name)="([^"]+)"', text))
    return found


def check_links(root, files):
    root = root.resolve()
    count = 0
    for path in files:
        if path.suffix != ".md":
            continue
        text = re.sub(r"```.*?```", "", path.read_text(), flags=re.S)
        for destination in re.findall(r"\]\(([^)]+)\)", text):
            parsed = urlsplit(destination.strip("<>"))
            if parsed.scheme or parsed.netloc:
                continue
            target = (path.parent / unquote(parsed.path)).resolve() if parsed.path else path.resolve()
            require(target.is_relative_to(root), f"link escapes repository: {path}: {destination}")
            require(target.exists(), f"broken link: {path}: {destination}")
            if parsed.fragment and target.suffix == ".md":
                require(unquote(parsed.fragment) in anchors(target.read_text()),
                        f"broken anchor: {path}: {destination}")
            count += 1
    return count


def descriptor_names(file):
    names = {file.name}

    def visit(message, prefix):
        name = f"{prefix}.{message.name}"
        names.add(name)
        names.update(f"{name}.{field.name}" for field in message.field)
        names.update(f"{name}.{enum.name}" for enum in message.enum_type)
        for child in message.nested_type:
            visit(child, name)

    for message in file.message_type:
        visit(message, file.package)
    names.update(f"{file.package}.{enum.name}" for enum in file.enum_type)
    return names


def check_options(root, descriptor):
    protos = {p.with_suffix("") for p in (root / "meshbus").glob("*.proto")}
    options = {p.with_suffix("") for p in (root / "meshbus").glob("*.options")}
    require(protos == options, "proto/options pairing mismatch")
    count = 0
    for file in descriptor.file:
        names = descriptor_names(file)
        for number, line in enumerate((root / file.name).with_suffix(".options").read_text().splitlines(), 1):
            if not line.strip() or line.lstrip().startswith(("#", "//")):
                continue
            pattern, _, settings = line.partition(" ")
            require(bool(settings.strip()), f"missing options: {file.name}:{number}")
            require(any(fnmatch.fnmatchcase(name, pattern) for name in names),
                    f"unmatched option: {file.name}:{number}: {pattern}")
            count += 1
    return count


def command_contract(descriptor):
    commands, messages = {}, set()
    for file in descriptor.file:
        schema = Path(file.name).stem
        messages.update(message.name for message in file.message_type)
        group = next((value.number for enum in file.enum_type for value in enum.value
                      if "GROUP_ID_MESHBUS_" in value.name), None)
        for enum in file.enum_type:
            if enum.name.endswith("CommandId"):
                for value in enum.value:
                    commands[(schema, value.name)] = (group, value.number)
    return commands, messages


def check_commands(root, descriptor):
    expected, messages = command_contract(descriptor)
    seen, operations = set(), set()
    rows = 0
    for line in (root / "docs/commands.md").read_text().splitlines():
        cells = [c.strip().strip("`") for c in line.strip("|").split("|")]
        if len(cells) != 7 or not cells[1].isdigit():
            continue
        schema, group, command_id, command, operation, request, response = cells
        require(operation in ("READ", "WRITE"), f"unknown operation: {operation}")
        key = (schema, command)
        require(key in expected, f"unknown documented command: {key}")
        require(expected[key] == (int(group), int(command_id)), f"wrong command ID: {key}")
        require(request in messages and response in messages, f"unknown request/response: {key}")
        require(request.endswith("Request") and response.endswith("Response"),
                f"wrong message direction: {key}")
        require((key, operation) not in operations, f"duplicate command operation: {key}")
        operations.add((key, operation))
        seen.add(key)
        rows += 1
    require(seen == set(expected), f"missing commands: {set(expected) - seen}")
    index = (root / "docs/schema-index.md").read_text()
    for file in descriptor.file:
        require(f"../{file.name}" in index, f"schema absent from index: {file.name}")
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    require(not output.is_relative_to(ROOT), "keep generated outputs outside this repository")
    output.mkdir(parents=True, exist_ok=True)
    files = source_files(ROOT)
    check_license(ROOT, files)
    links = check_links(ROOT, files)
    descriptor_path = output / "meshbus.pb"
    subprocess.run(
        [sys.executable, "-m", "grpc_tools.protoc", "-I", ".", "--include_imports",
         f"--descriptor_set_out={descriptor_path}",
         *sorted(str(p.relative_to(ROOT)) for p in (ROOT / "meshbus").glob("*.proto"))],
        cwd=ROOT, check=True,
    )
    descriptor = descriptor_pb2.FileDescriptorSet.FromString(descriptor_path.read_bytes())
    options = check_options(ROOT, descriptor)
    commands = check_commands(ROOT, descriptor)
    print(f"PASS: repository contracts ({len(descriptor.file)} schemas, {options} option rules, "
          f"{commands} command operations, {links} local links)")
    print(f"Artifacts: {output}")


if __name__ == "__main__":
    main()
