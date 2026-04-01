import re
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: bump_version.py path/to/__init__.py")
        return 2

    path = Path(sys.argv[1])
    text = path.read_text()
    pattern = r"\"version\"\s*:\s*\((\d+),\s*(\d+),\s*(\d+)\)"
    match = re.search(pattern, text)
    if not match:
        print("Could not find bl_info version tuple")
        return 1

    major, minor, patch = map(int, match.groups())
    patch += 1
    new = f"\"version\": ({major}, {minor}, {patch})"
    text = re.sub(pattern, new, text, count=1)
    path.write_text(text)
    print(f"Bumped version to {major}.{minor}.{patch}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
