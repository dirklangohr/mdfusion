#!/usr/bin/env python3
"""
Script to merge all Markdown files under a directory into one .md, rewriting
relative image links to absolute paths so that identically-named images
in different folders don’t collide, then convert that merged.md → PDF via
Pandoc + XeLaTeX with centered section headings and small margins.
Supports optional title page with metadata, plus config-file support.
"""

import sys
import re
import subprocess
import tempfile
import shutil
import getpass
import configparser
from pathlib import Path
from datetime import date

# Regex to find Markdown image links that are NOT already URLs
IMAGE_RE = re.compile(r"!\[([^\]]*)\]\((?!https?://)([^)]+)\)")


def natural_key(s: str):
    # Split into digit vs nondigit chunks, converting digit chunks to int
    return [int(tok) if tok.isdigit() else tok.lower() for tok in re.split(r"(\d+)", s)]


def find_markdown_files(root_dir: Path) -> list[Path]:
    """Recursively find all .md files, sorted “naturally” like VS Code."""
    md_paths = list(root_dir.rglob("*.md"))
    md_paths.sort(key=lambda p: natural_key(str(p.relative_to(root_dir))))
    return md_paths


def build_header(header_tex: Path | None = None) -> Path:
    """
    Write a temp .tex file that sets geometry, float placement, sectsty, etc.
    If a user header.tex exists, append it.
    Returns the Path to the temp .tex.
    """
    header_content = (
        r"\usepackage[margin=1in]{geometry}"
        "\n"
        r"\usepackage{float}"
        "\n"
        r"\floatplacement{figure}{H}"
        "\n"
        r"\usepackage{sectsty}"
        "\n"
        r"\sectionfont{\centering\fontsize{16}{18}\selectfont}"
        "\n"
    )

    tmp = tempfile.NamedTemporaryFile(
        "w", suffix=".tex", delete=False, encoding="utf-8"
    )
    tmp.write(header_content)

    if header_tex and header_tex.is_file():
        user_hdr = header_tex.read_text(encoding="utf-8")
        tmp.write("\n% --- begin user header.tex ---\n")
        tmp.write(user_hdr)
        tmp.write("\n% --- end user header.tex ---\n")

    tmp.flush()
    hdr_path = Path(tmp.name)
    tmp.close()
    return hdr_path


def create_metadata(title: str, author: str) -> str:
    """
    Build a Pandoc‐style YAML metadata block for a title page.
    """
    today = date.today().isoformat()
    return (
        f"---\n"
        f'title: "{title}"\n'
        f'author: "{author}"\n'
        f'date: "{today}"\n'
        f"---\n\n"
    )


def merge_markdown(md_files: list[Path], merged_md: Path, metadata: str) -> None:
    """
    Concatenate all md_files into merged_md, rewriting image links.
    If metadata is non‐empty, prepend it as a Pandoc YAML block.
    """
    with merged_md.open("w", encoding="utf-8") as out:
        if metadata:
            out.write(metadata)

        for md in md_files:
            out.write(r"\newpage" + "\n")
            text = md.read_text(encoding="utf-8")

            def fix_link(match: re.Match) -> str:
                alt_text, rel_link = match.groups()
                img_abs = (md.parent / rel_link).resolve()
                return f"![{alt_text}]({img_abs})"

            fixed_text = IMAGE_RE.sub(fix_link, text)
            out.write(fixed_text)
            out.write("\n\n")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Merge all Markdown files under a directory into one PDF, "
        "with optional title page, per-file section headings, image-link rewriting, small margins."
    )
    parser.add_argument(
        "-c", "--config", type=Path, help="Path to a .mdfusion INI-style config file"
    )
    parser.add_argument(
        "root_dir",
        nargs="?",
        type=Path,
        help="Root directory to search for Markdown files (required unless --config specifies everything)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output PDF filename (defaults to <root_dir>.pdf)",
    )
    parser.add_argument(
        "--no-toc",
        action="store_true",
        help="Do not include a table of contents in the PDF",
    )
    parser.add_argument(
        "--title-page",
        action="store_true",
        help="Include a title page using title/author metadata",
    )
    parser.add_argument(
        "--title",
        default=None,
        help="Title to use on title page (default: directory name)",
    )
    parser.add_argument(
        "--author", default=None, help="Author to use on title page (default: OS user)"
    )

    # Capture unknown args to forward to Pandoc
    args, pandoc_args = parser.parse_known_args()

    # --- CONFIG FILE LOADING ------------------------------------------------
    cfg_path = None
    # 1) If user explicitly passed --config
    if args.config:
        cfg_path = args.config
    # 2) If no args at all (len == 1), look for ./​.mdfusion
    elif len(sys.argv) == 1:
        cfg_path = Path.cwd() / ".mdfusion"

    if cfg_path:
        if not cfg_path.is_file():
            print(f"Config file not found: {cfg_path}", file=sys.stderr)
            sys.exit(1)
        cfg = configparser.ConfigParser()
        cfg.read(cfg_path)
        if "mdfusion" not in cfg:
            print(f"[mdfusion] section missing in {cfg_path}", file=sys.stderr)
            sys.exit(1)
        conf = cfg["mdfusion"]
        # Only set a value if it wasn't passed on CLI
        if not args.root_dir and "root_dir" in conf:
            args.root_dir = Path(conf["root_dir"])
        if not args.output and "output" in conf:
            args.output = conf["output"]
        if not args.no_toc and conf.getboolean("no_toc", fallback=False):
            args.no_toc = True
        if not args.title_page and conf.getboolean("title_page", fallback=False):
            args.title_page = True
        if not args.title and "title" in conf:
            args.title = conf["title"]
        if not args.author and "author" in conf:
            args.author = conf["author"]
        # allow extra pandoc args in config, whitespace-separated
        if "pandoc_args" in conf:
            pandoc_args += conf["pandoc_args"].split()

    # root_dir is now required
    if not args.root_dir:
        parser.error("you must specify root_dir (or provide it in the config file)")

    # -------------------------------------------------------------------------

    md_files = find_markdown_files(args.root_dir)
    if not md_files:
        print(f"No Markdown files found in {args.root_dir}", file=sys.stderr)
        sys.exit(1)

    title = args.title or args.root_dir.name
    author = args.author or getpass.getuser()
    metadata = (
        create_metadata(title, author)
        if (args.title_page or args.title or args.author)
        else ""
    )

    temp_dir = Path(tempfile.mkdtemp(prefix="md2pdf_"))
    try:
        user_header = Path(__file__).parent / "header.tex"
        if not user_header.is_file():
            user_header = None
        hdr_path = build_header(user_header)

        merged_md = temp_dir / "merged.md"
        merge_markdown(md_files, merged_md, metadata)

        resource_dirs = {str(p.parent) for p in md_files}
        resource_path = ":".join(sorted(resource_dirs))

        out_pdf = args.output or f"{args.root_dir.name}.pdf"
        cmd = [
            "pandoc",
            str(merged_md),
            "-o",
            out_pdf,
            "--pdf-engine=xelatex",
            f"--include-in-header={hdr_path}",
            f"--resource-path={resource_path}",
        ]
        if not args.no_toc:
            cmd.append("--toc")
        cmd.extend(pandoc_args)

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"Merged PDF written to {out_pdf}")
        except subprocess.CalledProcessError as e:
            err = e.stderr or ""
            m = re.search(r"unrecognized option `([^']+)'", err) or re.search(
                r"Unknown option (--\S+)", err
            )
            if m:
                bad_arg = m.group(1)
                print(
                    f"Error: Neither this script nor Pandoc recognizes the argument '{bad_arg}'.\n"
                    "If you wanted to pass an argument to pandoc, try:\n"
                    "    pandoc --help",
                    file=sys.stderr,
                )
            else:
                print(err.strip(), file=sys.stderr)
            sys.exit(1)

    finally:
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    main()
