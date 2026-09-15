"""Read-only conflict check: python check_patch.py /path/to/existing/AUSA.

Run from an extracted patch folder before copying its files into the project.
Checks source payload integrity and compares only files listed in PATCH_MANIFEST.json.
"""
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    patch = Path(__file__).resolve().parent
    target = Path(sys.argv[1]).resolve()
    if not (target / "backend").is_dir() or not (target / "frontend").is_dir():
        raise SystemExit("The target must be the existing AUSA root containing backend and frontend.")
    manifest = json.loads((patch / "PATCH_MANIFEST.json").read_text(encoding="utf-8"))
    conflicts = 0
    for entry in manifest["files"]:
        relative = PurePosixPath(entry["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise SystemExit("Invalid manifest path")
        if digest(patch / relative) != entry["sha256"]:
            raise SystemExit(f"Patch file is missing or modified: {relative}")
        current = digest(target / relative)
        if current == entry["sha256"]:
            status = "ALREADY APPLIED"
        elif current in [entry["original_sha256"], *entry.get("accepted_original_sha256", [])] and not (target / relative).is_dir():
            status = "ADD" if current is None else "REPLACE"
        else:
            status = "CONFLICT - merge first"
            conflicts += 1
        print(f"{status}: {relative}")
    print(f"{len(manifest['files'])} files checked; {conflicts} conflicts. No files were changed.")
    return int(conflicts > 0)


if __name__ == "__main__":
    raise SystemExit(main())
