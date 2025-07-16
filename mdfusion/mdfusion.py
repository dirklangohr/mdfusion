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
from pathlib import Path
from datetime import date
from tqdm import tqdm  # progress bar
import time

import toml as tomllib  # type: ignore
from dataclasses import dataclass, field
from simple_parsing import ArgumentParser

_TOML_BINARY = False

# Regex to find Markdown image links that are NOT already URLs
IMAGE_RE = re.compile(r"!\[([^\]]*)\]\((?!https?://)([^)]+)\)")


def natural_key(s: str):
    return [int(tok) if tok.isdigit() else tok.lower() for tok in re.split(r"(\d+)", s)]


def find_markdown_files(root_dir: Path) -> list[Path]:
    md_paths = list(root_dir.rglob("*.md"))
    md_paths.sort(key=lambda p: natural_key(str(p.relative_to(root_dir))))
    return md_paths


def build_header(header_tex: Path | None = None) -> Path:
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
        tmp.write("\n% --- begin user header.tex ---\n")
        tmp.write(header_tex.read_text(encoding="utf-8"))
        tmp.write("\n% --- end user header.tex ---\n")
    tmp.flush()
    hdr = Path(tmp.name)
    tmp.close()
    return hdr


def create_metadata(title: str, author: str) -> str:
    today = date.today().isoformat()
    return f'---\ntitle: "{title}"\nauthor: "{author}"\ndate: "{today}"\n---\n\n'


def merge_markdown(md_files: list[Path], merged_md: Path, metadata: str) -> None:
    with merged_md.open("w", encoding="utf-8") as out:
        if metadata:
            out.write(metadata)
        for md in tqdm(md_files, desc="Merging Markdown files", unit="file"):
            out.write(r"\newpage" + "\n")
            text = md.read_text(encoding="utf-8")

            def fix_link(m):
                alt, link = m.groups()
                return f"![{alt}]({(md.parent/ link).resolve()})"

            out.write(IMAGE_RE.sub(fix_link, text))
            out.write("\n\n")


def handle_pandoc_error(e, cmd):
    err = e.stderr or ""
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
        print(err.strip(), file=sys.stderr)
    sys.exit(1)


def run_pandoc_with_spinner(cmd, out_pdf):
    try:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        spinner_cycle = ["|", "/", "-", "\\"]
        idx = 0
        spinner_msg = "Pandoc running... "
        while proc.poll() is None:
            print(
                f"\r{spinner_msg}{spinner_cycle[idx % len(spinner_cycle)]}",
                end="",
                flush=True,
            )
            idx += 1
            time.sleep(0.15)
        print(
            "\r" + " " * (len(spinner_msg) + 2) + "\r", end="", flush=True
        )  # clear spinner line
        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            raise subprocess.CalledProcessError(
                proc.returncode, cmd, output=stdout, stderr=stderr
            )
        print(f"Merged PDF written to {out_pdf}")
    except subprocess.CalledProcessError as e:
        handle_pandoc_error(e, cmd)


@dataclass
class RunParams:
    root_dir: Path | None = None  # root directory for Markdown files
    output: str | None = None  # output PDF filename (defaults to <root_dir>.pdf)
    no_toc: bool = False  # omit table of contents
    title_page: bool = False  # include a title page
    title: str | None = None  # title for title page (defaults to dirname)
    author: str | None = None  # author for title page (defaults to OS user)
    pandoc_args: list[str] = field(default_factory=list)  # extra pandoc arguments, whitespace-separated
    config_path: Path | None = None  # path to a mdfusion.toml TOML config file
    header_tex: Path | None = None  # path to a user-defined header.tex file (default: ./header.tex)
    debug: bool = False  # if True, print all Pandoc output and use verbose mode
    # Add help strings for simple-parsing
    def __post_init__(self):
        pass  # No-op, but can be used for post-processing if needed


def run(params: "RunParams"):
    if not requirements_met():
        return

    if not params.root_dir:
        print("Error: root_dir must be specified", file=sys.stderr)
        return
    md_files = find_markdown_files(params.root_dir)
    if not md_files:
        print(f"No Markdown files found in {params.root_dir}", file=sys.stderr)
        sys.exit(1)

    title = params.title or params.root_dir.name
    author = params.author or getpass.getuser()
    metadata = (
        create_metadata(title, author)
        if (params.title_page or params.title or params.author)
        else ""
    )

    temp_dir = Path(tempfile.mkdtemp(prefix="mdfusion_"))
    try:
        # Use params.header_tex if provided, else default to cwd/header.tex
        user_header = params.header_tex
        if user_header is None:
            user_header = Path.cwd() / "header.tex"
        if not user_header.is_file():
            user_header = None
        hdr = build_header(user_header)
        merged = temp_dir / "merged.md"
        merge_markdown(md_files, merged, metadata)

        resource_dirs = {str(p.parent) for p in md_files}
        resource_path = ":".join(sorted(resource_dirs))

        out_pdf = params.output or f"{params.root_dir.name}.pdf"
        cmd = [
            "pandoc",
            str(merged),
            "-o",
            out_pdf,
            "--pdf-engine=xelatex",
            f"--include-in-header={hdr}",
            f"--resource-path={resource_path}",
        ]
        if not params.no_toc:
            cmd.append("--toc")
        if params.debug:
            cmd.append("-v")
        cmd.extend(params.pandoc_args)

        if params.debug:
            # Always print all output from Pandoc
            print(f"[DEBUG] Running: {' '.join(cmd)}")
            try:
                result = subprocess.run(cmd, check=True, text=True, capture_output=True)
                print(result.stdout)
                print(result.stderr, file=sys.stderr)
                print(f"Merged PDF written to {out_pdf}")
            except subprocess.CalledProcessError as e:
                print(e.stdout)
                print(e.stderr, file=sys.stderr)
                handle_pandoc_error(e, cmd)
        else:
            # If not running in a TTY (e.g., during tests), use subprocess.run for compatibility
            if not sys.stdout.isatty():
                try:
                    subprocess.run(cmd, check=True, capture_output=True, text=True)
                    print(f"Merged PDF written to {out_pdf}")
                except subprocess.CalledProcessError as e:
                    handle_pandoc_error(e, cmd)
            else:
                run_pandoc_with_spinner(cmd, out_pdf)
    finally:
        shutil.rmtree(temp_dir)


def load_config_defaults(cfg_path: Path | None) -> dict:
    """Load config defaults from TOML file, if present."""
    manual_defaults: dict = {}
    if cfg_path and cfg_path.is_file():
        with cfg_path.open("r", encoding="utf-8") as f:
            toml_data = tomllib.load(f)
        conf = toml_data.get("mdfusion", {})
        # Dynamically map config keys to RunParams fields
        from dataclasses import fields
        runparams_fields = {f.name: f.type for f in fields(RunParams)}
        for k, v in conf.items():
            if k in runparams_fields:
                typ = runparams_fields[k]
                # Convert to Path if needed
                if typ == Path or typ == (Path | None):
                    manual_defaults[k] = Path(v)
                else:
                    manual_defaults[k] = v
    return manual_defaults


def requirements_met() -> bool:
    """Check if requirements are met."""
    # shutil.which is a builtin cross-platform which utility
    pandoc = shutil.which("pandoc")
    xetex = shutil.which("xetex")

    if not pandoc:
        print("ERR: pandoc not found", file=sys.stderr)
    if not xetex:
        print("ERR: xetex not found", file=sys.stderr)

    return bool(pandoc and xetex)


def main():
    # 1) Find config file path
    cfg_path = None
    for i, a in enumerate(sys.argv):
        if a in ("-c", "--config") and i + 1 < len(sys.argv):
            cfg_path = Path(sys.argv[i + 1])
            break
    if cfg_path is None:
        default_cfg = Path.cwd() / "mdfusion.toml"
        if default_cfg.is_file():
            cfg_path = default_cfg

    # 2) Load config defaults
    manual_defaults = load_config_defaults(cfg_path)

    # 3) Arg parsing using simple-parsing
    parser = ArgumentParser(
        description=(
            "Merge all Markdown files under a directory into one PDF, "
            "with optional title page, TOC control, image-link rewriting, small margins."
        )
    )
    parser.add_arguments(RunParams, dest="params")

    # Parse known args, allow extra pandoc args
    args, extra = parser.parse_known_args()

    # Merge config defaults with CLI args
    params: RunParams = args.params
    for k, v in manual_defaults.items():
        if getattr(params, k, None) in (None, False, [], ""):
            setattr(params, k, v)

    # Handle extra pandoc args
    if extra:
        if not params.pandoc_args:
            params.pandoc_args = []
        if isinstance(params.pandoc_args, str):
            params.pandoc_args = params.pandoc_args.split()
        params.pandoc_args.extend(extra)

    # require root_dir after merging config and CLI
    if not params.root_dir:
        parser.error("you must specify root_dir (or provide it in the config file)")

    run(params)


if __name__ == "__main__":
    main()
