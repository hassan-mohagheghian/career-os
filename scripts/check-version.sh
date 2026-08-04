#!/usr/bin/env bash
# Check that every version reference in the repo matches the VERSION file.
# Usage: scripts/check-version.sh [--tag]   # --tag also asserts a matching git tag
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 - "$repo_root" "$@" <<'EOF'
import re
import subprocess
import sys
from pathlib import Path

root = Path(sys.argv[1])
check_tag = "--tag" in sys.argv[2:]

version_file = root / "VERSION"
if not version_file.exists():
    print("ERROR: missing VERSION file at repo root")
    sys.exit(1)

version = version_file.read_text().strip()
if not re.fullmatch(r"\d+\.\d+\.\d+", version):
    print(f"ERROR: VERSION file has invalid SemVer: {version!r}")
    sys.exit(1)

errors = []


def check(label, value):
    if value != version:
        errors.append(f"{label}: found {value!r}, expected {version!r}")


pyproject = (root / "pyproject.toml").read_text()
m = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, re.MULTILINE)
check("pyproject.toml", m.group(1) if m else "<missing>")

package_json = (root / "apps/frontend/package.json").read_text()
m = re.search(r'"version"\s*:\s*"([^"]+)"', package_json)
check("apps/frontend/package.json", m.group(1) if m else "<missing>")

changelog = (root / "CHANGELOG.md").read_text()
m = re.search(r"^## \[([\d.]+)\]", changelog, re.MULTILINE)
check("CHANGELOG.md (latest)", m.group(1) if m else "<missing>")

if check_tag:
    tag = subprocess.run(
        ["git", "tag", "--points-at", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    if f"v{version}" not in tag.split():
        errors.append(f"git tag: expected a tag 'v{version}' on HEAD")

if errors:
    print("ERROR: version mismatch detected:\n  " + "\n  ".join(errors))
    print("VERSION file: " + version)
    sys.exit(1)

print(f"OK: all version references match {version}")
EOF
