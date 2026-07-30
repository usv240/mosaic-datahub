from __future__ import annotations

from pathlib import Path

ROOTS = (
    Path("README.md"),
    Path("SUBMISSION.md"),
    Path("docs"),
    Path("src/mosaic/web"),
    Path("skills"),
)
SUFFIXES = {".md", ".html", ".css", ".js", ".py", ".yaml", ".yml"}
MOJIBAKE = ("Ã", "Â", "â€", "â€”", "â†", "ðŸ", "�")


def main() -> int:
    paths = []
    for root in ROOTS:
        if root.is_file():
            paths.append(root)
        elif root.exists():
            paths.extend(path for path in root.rglob("*") if path.suffix.lower() in SUFFIXES)
    findings = []
    for path in sorted(paths):
        text = path.read_text(encoding="utf-8")
        for marker in MOJIBAKE:
            if marker in text:
                findings.append(f"{path}: contains {marker!r}")
    if findings:
        print("\n".join(findings))
        return 1
    print(f"UTF-8/mojibake check passed: {len(paths)} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
