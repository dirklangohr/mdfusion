import subprocess
import tempfile
import shutil
from pathlib import Path
import pytest
import mdfusion.mdfusion as mdfusion


def make_long_md_file(path, n_sections=50, section_len=100):
    with open(path, "w", encoding="utf-8") as f:
        for i in range(n_sections):
            f.write(f"# Section {i+1}\n")
            f.write(
                ("Lorem ipsum dolor sit amet, consectetur adipiscing elit. " + "\n")
                * section_len
            )


def test_merge_many_long_markdown_files(tmp_path):
    # Create a temp directory with many long markdown files
    md_dir = tmp_path / "mds"
    md_dir.mkdir()
    n_files = 2
    for i in range(n_files):
        make_long_md_file(md_dir / f"file_{i+1}.md", n_sections=5, section_len=30)

    # Output PDF path
    out_pdf = tmp_path / "output.pdf"

    # Use RunParams and run() directly
    params = mdfusion.RunParams(
        root_dir=md_dir,
        output=str(out_pdf),
        no_toc=False,
        title_page=False,
        title="Test PDF",
        author="UnitTest",
        pandoc_args=[],
        config_path=None,
    )
    mdfusion.run(params)

    assert (
        out_pdf.exists() and out_pdf.stat().st_size > 0
    ), "Output PDF not created or empty"

    assert (
        out_pdf.exists() and out_pdf.stat().st_size > 0
    ), "Output PDF not created or empty"
