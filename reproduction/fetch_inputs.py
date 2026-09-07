#!/usr/bin/env python3
"""Download the two public CSV inputs and verify their pinned SHA-256 values."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = Path(__file__).with_name("input_manifest.json")
INPUT_DIR = ROOT / "inputs"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    INPUT_DIR.mkdir(exist_ok=True)
    for entry in manifest["inputs"]:
        with urlopen(entry["url"], timeout=30) as response:
            data = response.read()
        actual = sha256(data)
        if actual != entry["sha256"]:
            raise ValueError(f"SHA-256 mismatch for {entry['path']}: {actual}")
        (INPUT_DIR / entry["path"]).write_bytes(data)
        print(f"verified {entry['path']}: {actual}")


if __name__ == "__main__":
    main()
