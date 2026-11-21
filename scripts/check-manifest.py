#!/usr/bin/env python3
"""Check manifest.json is a valid Jellyfin plugin repository manifest. Run by CI and pre-commit-style by hand."""

import json
import re
import sys
from pathlib import Path

GUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
MD5 = re.compile(r"^[0-9a-f]{32}$", re.IGNORECASE)
VERSION = re.compile(r"^\d+\.\d+\.\d+\.\d+$")
TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")
PLUGIN_KEYS = ("guid", "name", "description", "overview", "owner", "category", "versions")
VERSION_KEYS = ("version", "changelog", "targetAbi", "sourceUrl", "checksum", "timestamp")


def problems(data: object) -> list[str]:
    if not isinstance(data, list):
        return ["manifest must be a JSON list of plugins"]
    out: list[str] = []
    seen: set[str] = set()
    for plugin in data:
        name = plugin.get("name", "?") if isinstance(plugin, dict) else "?"
        if not isinstance(plugin, dict):
            out.append("every entry must be an object")
            continue
        out += [f"{name}: missing '{k}'" for k in PLUGIN_KEYS if k not in plugin]
        guid = str(plugin.get("guid", ""))
        if not GUID.match(guid):
            out.append(f"{name}: guid is not a lowercase GUID")
        if guid in seen:
            out.append(f"{name}: duplicate guid")
        seen.add(guid)
        versions = plugin.get("versions", [])
        if not isinstance(versions, list):
            out.append(f"{name}: 'versions' must be a list")
            versions = []
        for i, v in enumerate(versions):
            if not isinstance(v, dict):
                out.append(f"{name}: versions[{i}] must be an object")
                continue
            label = f"{name} {v.get('version', '?')}"
            out += [f"{label}: missing '{k}'" for k in VERSION_KEYS if k not in v]
            if not VERSION.match(str(v.get("version", ""))):
                out.append(f"{name}: version must have four numbers, got {v.get('version')!r}")
            if not VERSION.match(str(v.get("targetAbi", ""))):
                out.append(f"{label}: targetAbi must have four numbers, got {v.get('targetAbi')!r}")
            if not MD5.match(str(v.get("checksum", ""))):
                out.append(f"{label}: checksum must be an MD5 hex string")
            url = str(v.get("sourceUrl", ""))
            if not url.startswith("https://github.com/Lombo-Forge/"):
                out.append(f"{label}: sourceUrl must be a Lombo-Forge release")
            if not url.endswith(".zip"):
                out.append(f"{label}: sourceUrl must end in .zip")
            if not TIMESTAMP.match(str(v.get("timestamp", ""))):
                out.append(f"{label}: timestamp must be ISO 8601")
    return out


def main(path: str = "manifest.json") -> int:
    found = problems(json.loads(Path(path).read_text(encoding="utf-8")))
    for line in found:
        print(f"manifest: {line}", file=sys.stderr)
    if not found:
        print("Manifest OK.")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:2]))
