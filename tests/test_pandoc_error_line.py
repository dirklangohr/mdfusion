import shutil

import pytest

import mdfusion.mdfusion as mdfusion


@pytest.mark.skipif(
    not shutil.which("pandoc") or not shutil.which("xelatex"),
    reason="pandoc and xelatex are required for this integration test",
)
def test_run_reports_correct_line_for_missing_dollar_error(tmp_path, capsys):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "broken.md").write_text(
        "Hello\n"
        "\\texttt{a_b}\n",
        encoding="utf-8",
    )

    # define where merged file will be so we can check the error message properly
    merged_dir = tmp_path / "merged"
    merged_dir.mkdir()
    merged = merged_dir / "merged.md"

    params = mdfusion.RunParams(
        root_dir=docs,
        merged_md=merged_dir,
    )

    with pytest.raises(SystemExit) as exc_info:
        mdfusion.run(params)

    assert exc_info.value.code == 1

    stderr = capsys.readouterr().err
    assert f"Pandoc failed near {merged}:2:1" in stderr
    assert r"line 2: \texttt{a_b}" in stderr