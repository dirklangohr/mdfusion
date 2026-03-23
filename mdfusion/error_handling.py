"""Shared source-anchored error reporting and input validation helpers."""

from __future__ import annotations

import mimetypes
import re
import sys
from pathlib import Path


def report_source_error(
    path: Path,
    line: int,
    column: int | None = None,
    reason: str | None = None,
    source: str = "Pandoc",
) -> None:
    """Print a source-anchored error message and exit with failure status."""

    line_info = f"{path}:{line}"
    if column is not None:
        line_info += f":{column}"

    print(f"{source} failed near {line_info}", file=sys.stderr)

    excerpt = _read_line_excerpt(path, line)
    if excerpt:
        print(f"  {excerpt}", file=sys.stderr)
    if reason:
        print(f"  {reason}", file=sys.stderr)
    sys.exit(1)


def validate_local_image_links(md_files: list[Path]) -> None:
    """Fail early for local Markdown image links that clearly are not images."""

    image_re = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
    allowed_suffixes = {
        ".apng",
        ".bmp",
        ".eps",
        ".gif",
        ".ico",
        ".jpeg",
        ".jpg",
        ".pdf",
        ".png",
        ".svg",
        ".tga",
        ".tif",
        ".tiff",
        ".webp",
    }

    for md in md_files:
        text = md.read_text(encoding="utf-8")
        for line_number, line in enumerate(text.splitlines(), start=1):
            for match in image_re.finditer(line):
                raw_link = match.group(2).strip()
                if raw_link.startswith(("http://", "https://")):
                    continue

                link = raw_link.strip("<>")
                candidate = (md.parent / link).resolve()
                if not candidate.exists() or candidate.is_dir():
                    continue

                suffix = candidate.suffix.lower()
                mime_type, _ = mimetypes.guess_type(str(candidate))
                looks_like_image = (
                    suffix in allowed_suffixes
                    or (mime_type or "").startswith("image/")
                    or mime_type == "application/pdf"
                )
                if looks_like_image:
                    continue

                report_source_error(
                    md,
                    line_number,
                    match.start() + 1,
                    f"Referenced file is not a supported image: {candidate}",
                    source="mdfusion",
                )


def _read_line_excerpt(path: Path, line_number: int) -> str | None:
    """Read a single formatted source line for error reporting."""

    if not path or not path.is_file() or line_number < 1:
        return None

    try:
        with path.open("r", encoding="utf-8") as f:
            for current_line, text in enumerate(f, start=1):
                if current_line == line_number:
                    return f"line {line_number}: {text.rstrip()}"
    except OSError:
        return None

    return None
