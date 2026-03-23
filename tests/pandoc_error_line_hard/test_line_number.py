import shutil

import pytest

import mdfusion.mdfusion as mdfusion


@pytest.mark.skipif(
    not shutil.which("pandoc") or not shutil.which("xelatex"),
    reason="pandoc and xelatex are required for this integration test",
)
def test_run_reports_correct_line_for_wrong_filetype_included_as_image(tmp_path, capsys):
    docs = tmp_path / "docs"
    docs.mkdir()
    broken = docs / "broken.md"
    broken.write_text(
        "Hello\n"
        "Hihihi\n"
        "![Not an image](not_an_image.md)\n",
        encoding="utf-8",
    )
    not_an_image = docs / "not_an_image.md"
    not_an_image.write_text(
        "This is a markdown file, not an image\n",
        encoding="utf-8",
    )
    
    
    params = mdfusion.RunParams(
        root_dir=docs
    )

    with pytest.raises(SystemExit) as exc_info:
        mdfusion.run(params)

    assert exc_info.value.code == 1

    stderr = capsys.readouterr().err
    assert f"mdfusion failed near {broken}:3:1" in stderr
    assert "line 3: ![Not an image](not_an_image.md)" in stderr


@pytest.mark.skipif(
    not shutil.which("pandoc") or not shutil.which("xelatex"),
    reason="pandoc and xelatex are required for this integration test",
)
def test_run_reports_correct_line_for_wrong_filetype_included_as_image_remote(tmp_path, capsys):
    docs = tmp_path / "docs"
    docs.mkdir()
    broken = docs / "broken.md"
    broken.write_text(
        "Hello\n"
        "Hihihi\n"
        "![Not an image](https://github.com/ejuet/mdfusion/blob/master/README.md)\n",
        encoding="utf-8",
    )
    not_an_image = docs / "not_an_image.md"
    not_an_image.write_text(
        "This is a markdown file, not an image\n",
        encoding="utf-8",
    )
    
    
    params = mdfusion.RunParams(
        root_dir=docs
    )

    with pytest.raises(SystemExit) as exc_info:
        mdfusion.run(params)

    assert exc_info.value.code == 1

    stderr = capsys.readouterr().err
    assert f"mdfusion failed near {broken}:3:1" in stderr
    assert "line 3: ![Not an image](https://github.com/ejuet/mdfusion/blob/master/README.md)" in stderr
