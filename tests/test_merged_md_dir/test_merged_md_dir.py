import mdfusion.mdfusion as mdfusion
import os
from pathlib import Path

def test_with_config(tmp_path, monkeypatch):
    # 1) Create a docs/ tree with two markdown files
    tmp_path = Path(os.path.dirname(__file__))
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "a.md").write_text("# First\n\nHello")
    (docs / "b.md").write_text("# Second\n\nWorld")

    # 2) Write a .mdfusion config in the cwd
    cfg = tmp_path / "mdfusion.toml"
    # use posix path for windows compatibility
    merged_md_path = os.path.dirname(__file__)
    merged_md_path = merged_md_path.replace("\\", "/")
    cfg.write_text(
        f"""\
[mdfusion]
merged_md = "{merged_md_path}"
"""
    )
    
    monkeypatch.chdir(tmp_path)
    
    mdfusion.run(mdfusion.RunParams(
        config_path=cfg,
    ))
    
    assert (Path(merged_md_path) / "merged.md").exists()