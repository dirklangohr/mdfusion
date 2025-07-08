from mdfusion.mdfusion import build_header

def test_build_header_includes_braket(tmp_path):
    # Create a header.tex with braket package
    user_header = tmp_path / "header.tex"
    user_header.write_text(r"\usepackage{braket}")

    # Build header with user header
    hdr_path = build_header(user_header)
    content = hdr_path.read_text(encoding="utf-8")
    assert "\\usepackage{braket}" in content  # check for actual string, not double-escaped
    hdr_path.unlink()

    # Build header without user header
    hdr_path2 = build_header(None)
    content2 = hdr_path2.read_text(encoding="utf-8")
    assert "\\usepackage{braket}" not in content2
    hdr_path2.unlink()

    # Simulate markdown file using \ket{0} (not a full Pandoc run, just check header)
    md = tmp_path / "test.md"
    md.write_text(r"$\\ket{0}$")
    # If you want to check Pandoc integration, you would need to run Pandoc here,
    # but for a unit test, verifying the header is sufficient.
