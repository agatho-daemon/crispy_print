#!/usr/bin/env python3
"""Verify immutable vendored Typst package contents and license inventory."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = ROOT / "crispy_print" / "public" / "vendor" / "typst" / "packages"
MANIFEST_PATH = PACKAGE_ROOT / "MANIFEST.json"


def package_digest(directory: Path) -> str:
	lines = []
	for path in sorted(item for item in directory.rglob("*") if item.is_file()):
		file_hash = hashlib.sha256(path.read_bytes()).hexdigest()
		relative = path.relative_to(directory).as_posix()
		lines.append(f"{file_hash}  ./{relative}\n")
	return hashlib.sha256("".join(lines).encode()).hexdigest()


def main() -> None:
	manifest = json.loads(MANIFEST_PATH.read_text())
	errors = []
	for package in manifest.get("packages", []):
		directory = PACKAGE_ROOT / package["namespace"] / package["name"] / package["version"]
		if not directory.is_dir():
			errors.append(f"Missing package directory: {directory}")
			continue
		license_files = list(directory.glob("LICENSE*"))
		if package["namespace"] != "local" and not license_files:
			errors.append(f"Missing license file: {package['name']} {package['version']}")
		actual = package_digest(directory)
		if actual != package.get("sha256"):
			errors.append(
				f"Checksum mismatch for {package['name']} {package['version']}: "
				f"expected {package.get('sha256')}, got {actual}"
			)
	if errors:
		raise SystemExit("\n".join(errors))


if __name__ == "__main__":
	main()
