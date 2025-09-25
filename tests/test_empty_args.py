import mdfusion.mdfusion as mdfusion


def test_with_config(tmp_path, monkeypatch):
    # 1) Create a docs/ tree with two markdown files
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "a.md").write_text("# First\n\nHello")
    (docs / "b.md").write_text("# Second\n\nWorld")

    # 2) Write a .mdfusion config in the cwd
    cfg = tmp_path / "mdfusion.toml"
    cfg.write_text(
        """\
[mdfusion]
"""
    )
    
    monkeypatch.chdir(tmp_path)
    
    mdfusion.run(mdfusion.RunParams(
        config_path=cfg,
    ))

    assert (tmp_path / f"{tmp_path.name}.pdf").exists()