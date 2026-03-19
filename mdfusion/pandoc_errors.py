"""Helpers for turning Pandoc failures into readable CLI diagnostics."""

from __future__ import annotations

import re
import sys
from pathlib import Path


def handle_pandoc_error(e, cmd) -> None:
    """Print a focused Pandoc error message and exit with a failure status.

    The handler prefers actionable output over raw subprocess details:
    unknown Pandoc flags are reported directly, and source-based failures
    include the best line and column location we can infer from Pandoc's
    stderr/stdout.
    """

    err = (e.stderr or "").strip()
    out = (e.stdout or "").strip()
    combined_output = "\n".join(part for part in (err, out) if part).strip()

    source_path = _extract_pandoc_input_path(cmd)
    location = _parse_pandoc_error_location(combined_output, source_path)

    m = re.search(r"unrecognized option `([^']+)'", err) or re.search(
        r"Unknown option (--\\S+)", err
    )
    if m:
        bad = m.group(1)
        print(
            f"Error: argument '{bad}' not recognized.\n Try: pandoc --help",
            file=sys.stderr,
        )
    else:
        if location:
            line_info = f"{location['path']}:{location['line']}"
            if location.get("column") is not None:
                line_info += f":{location['column']}"
            print(f"Pandoc failed near {line_info}", file=sys.stderr)

            excerpt = _read_line_excerpt(location["path"], location["line"])
            if excerpt:
                print(f"  {excerpt}", file=sys.stderr)
    sys.exit(1)


def _extract_pandoc_input_path(cmd) -> Path | None:
    """Return the Markdown input path passed to Pandoc, if present.

    The current CLI builds the Pandoc command with `-s <merged.md>`, so this
    helper finds that positional input file without needing to understand the
    entire command structure.
    """

    for idx, arg in enumerate(cmd[:-1]):
        if arg in {"-s", "--standalone"}:
            candidate = cmd[idx + 1]
            if isinstance(candidate, str) and not candidate.startswith("-"):
                return Path(candidate)
    return None


def _parse_pandoc_error_location(
    err: str, source_path: Path | None = None
) -> dict | None:
    """Extract the most useful source location we can find from Pandoc output.

    Pandoc and the underlying LaTeX toolchain report locations in a few
    different textual formats. This parser tries explicit line/column patterns
    first and then falls back to matching LaTeX context against the merged
    Markdown source.
    """

    if not err:
        return None

    patterns = [
        re.compile(r"line\s+(?P<line>\d+),\s*column\s+(?P<column>\d+)", re.IGNORECASE),
        re.compile(r"line\s+(?P<line>\d+)\s+column\s+(?P<column>\d+)", re.IGNORECASE),
        re.compile(r"source\s+line\s+(?P<line>\d+)\s+column\s+(?P<column>\d+)", re.IGNORECASE),
        re.compile(r":(?P<line>\d+):(?P<column>\d+)(?:\D|$)"),
        re.compile(r"line\s+(?P<line>\d+)(?:\D|$)", re.IGNORECASE),
    ]

    for pattern in patterns:
        match = pattern.search(err)
        if match:
            line = int(match.group("line"))
            column = match.groupdict().get("column")
            return {
                "path": source_path if source_path else Path("<pandoc-input>"),
                "line": line,
                "column": int(column) if column is not None else None,
            }

    latex_context_location = _infer_location_from_latex_context(err, source_path)
    if latex_context_location:
        return latex_context_location

    return None


def _infer_location_from_latex_context(
    err: str, source_path: Path | None
) -> dict | None:
    """Map a LaTeX `l.<line>` snippet back to the original Markdown source.

    Some Pandoc failures only provide a LaTeX snippet rather than an explicit
    Markdown line number. When that happens, we search the merged source for
    the reported snippet, then fall back to significant tokens from it.
    """

    if not source_path or not source_path.is_file():
        return None

    match = re.search(r"^l\.(?P<latex_line>\d+)\s(?P<snippet>.+)$", err, re.MULTILINE)
    if not match:
        return None

    snippet = match.group("snippet").strip()
    if not snippet:
        return None

    exact_match = _find_source_line_by_snippet(source_path, snippet)
    if exact_match:
        return exact_match

    for token in sorted(_extract_search_tokens(snippet), key=len, reverse=True):
        token_match = _find_source_line_by_snippet(source_path, token)
        if token_match:
            return token_match

    return None


def _extract_search_tokens(snippet: str) -> list[str]:
    """Return meaningful search tokens from a LaTeX error snippet."""

    tokens = re.findall(r"\\[A-Za-z@]+(?:\{[^}]+\})?|[^\s{}\\]+", snippet)
    return [token for token in tokens if len(token) >= 4]


def _find_source_line_by_snippet(path: Path, snippet: str) -> dict | None:
    """Locate the first source line whose normalized text contains `snippet`."""

    normalized_snippet = " ".join(snippet.split())
    if not normalized_snippet:
        return None

    try:
        with path.open("r", encoding="utf-8") as f:
            for current_line, text in enumerate(f, start=1):
                normalized_line = " ".join(text.split())
                if normalized_snippet in normalized_line:
                    column = normalized_line.find(normalized_snippet) + 1
                    return {
                        "path": path,
                        "line": current_line,
                        "column": column,
                    }
    except OSError:
        return None

    return None


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
