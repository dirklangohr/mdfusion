"""Shared source-anchored error reporting and input validation helpers."""

from __future__ import annotations

import mimetypes
import re
import sys
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen


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
    """Fail early for Markdown image links that clearly are not images."""

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
                link = raw_link.strip("<>")
                if _looks_like_supported_image(link, md.parent, allowed_suffixes):
                    continue

                report_source_error(
                    md,
                    line_number,
                    match.start() + 1,
                    f"Referenced file is not a supported image: {link}",
                    source="mdfusion",
                )


def _looks_like_supported_image(
    link: str, base_dir: Path, allowed_suffixes: set[str]
) -> bool:
    """Return True when a Markdown image target appears to be a supported image."""

    if link.startswith(("http://", "https://")):
        return _looks_like_supported_remote_image(link, allowed_suffixes)

    candidate = (base_dir / link).resolve()
    if not candidate.exists() or candidate.is_dir():
        return True

    return _has_supported_image_type(str(candidate), allowed_suffixes)


def _looks_like_supported_remote_image(link: str, allowed_suffixes: set[str]) -> bool:
    """Best-effort validation for remote image URLs.

    We first inspect the URL path itself so obvious non-image targets such as
    `.md` files fail fast. If the path is ambiguous, we try an HTTP HEAD request
    and fall back to GET for servers that do not support HEAD. Network issues are
    treated as inconclusive so Pandoc can still handle the download attempt.
    """

    parsed = urlparse(link)
    if _has_supported_image_type(parsed.path, allowed_suffixes):
        return True

    path_suffix = Path(parsed.path).suffix.lower()
    if path_suffix:
        return False

    remote_mime_type = _fetch_remote_mime_type(link)
    if not remote_mime_type:
        return True

    return remote_mime_type.startswith("image/") or remote_mime_type == "application/pdf"


def _fetch_remote_mime_type(link: str) -> str | None:
    """Return a normalized remote Content-Type value when one is available."""

    for method in ("HEAD", "GET"):
        request = Request(link, method=method, headers={"User-Agent": "mdfusion"})
        try:
            with urlopen(request, timeout=5) as response:
                content_type = response.headers.get_content_type()
                if content_type:
                    return content_type.lower()
        except Exception:
            continue

    return None


def _has_supported_image_type(candidate: str, allowed_suffixes: set[str]) -> bool:
    """Check filename/URL-path based image type hints."""

    suffix = Path(candidate).suffix.lower()
    mime_type, _ = mimetypes.guess_type(candidate)
    return (
        suffix in allowed_suffixes
        or (mime_type or "").startswith("image/")
        or mime_type == "application/pdf"
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
