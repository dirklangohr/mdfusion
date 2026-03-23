"""Helpers for turning Pandoc failures into readable CLI diagnostics."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

from .error_handling import report_source_error


@dataclass(frozen=True)
class SourceLineSpan:
    """Map a contiguous range of merged lines back to one source file.

    Each span represents a block of lines copied from a single Markdown file
    without interruption. Translating a merged line inside the span is simple
    arithmetic based on the recorded start lines.
    """

    merged_start_line: int
    merged_end_line: int
    source_path: Path
    source_start_line: int

def handle_pandoc_error(e, cmd, source_spans: list[SourceLineSpan] | None = None) -> None:
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
    resolved_location = _resolve_original_location(location, source_spans)

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
        if resolved_location:
            report_source_error(
                resolved_location["path"],
                resolved_location["line"],
                resolved_location.get("column"),
                source="Pandoc",
            )
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


def _resolve_original_location(
    location: dict | None, source_spans: list[SourceLineSpan] | None
) -> dict | None:
    """Translate a merged-file location back to the original source file."""

    if not location or not source_spans:
        return location

    merged_line = location["line"]
    for span in source_spans:
        if span.merged_start_line <= merged_line <= span.merged_end_line:
            source_line = span.source_start_line + (merged_line - span.merged_start_line)
            return {
                "path": span.source_path,
                "line": source_line,
                "column": location.get("column"),
            }

    return location


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
