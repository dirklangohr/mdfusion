from mdfusion.mdfusion import run, RunParams
from pathlib import Path


def test_build_header_includes_braket(tmp_path):
    # Create a header.tex with braket package
    user_header = tmp_path / "header.tex"
    user_header.write_text(r"\usepackage{braket}")

    # Create a markdown file that uses \ket{0}
    md = tmp_path / "test.md"
    md.write_text(r"# Title $\ket{0}$")

    # Output PDF path
    out_pdf = tmp_path / "out.pdf"

    # Run with user header
    params = RunParams(
        root_dir=tmp_path,
        output=str(out_pdf),
        header_tex=user_header,
        pandoc_args=[],
    )
    run(params)
    assert out_pdf.exists()
