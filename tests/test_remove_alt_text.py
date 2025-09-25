import mdfusion.mdfusion as mdfusion
import os
from pathlib import Path

def test_remove_alt(tmp_path, monkeypatch):
    # 1) Create a docs/ tree with two markdown files
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "a.md").write_text("# First\n\nHello\n\n![alt text](https://images.unsplash.com/photo-1504208434309-cb69f4fe52b0?ixid=M3wxMTI1OHwwfDF8cmFuZG9tfHx8fHx8fHx8MTc1ODc5ODQwNHw&ixlib=rb-4.1.0&q=85&w=2400)")
    (docs / "b.md").write_text("# Second\n\nWorld\n\n![Beautiful](https://images.unsplash.com/photo-1504208434309-cb69f4fe52b0?ixid=M3wxMTI1OHwwfDF8cmFuZG9tfHx8fHx8fHx8MTc1ODc5ODQwNHw&ixlib=rb-4.1.0&q=85&w=2400)")
    (docs / "c.md").write_text("# Third\n\n![RemoveMe](https://images.unsplash.com/photo-1504208434309-cb69f4fe52b0?ixid=M3wxMTI1OHwwfDF8cmFuZG9tfHx8fHx8fHx8MTc1ODc5ODQwNHw&ixlib=rb-4.1.0&q=85&w=2400)")
    
    monkeypatch.chdir(tmp_path)
    
    merged_md_path = tmp_path / "merged_md"
    os.makedirs(merged_md_path, exist_ok=True)
    
    mdfusion.run(mdfusion.RunParams(
        root_dir=docs,
        merged_md=merged_md_path,
        remove_alt_texts=["alt text", "RemoveMe"],
    ))

    assert (Path(merged_md_path) / "merged.md").exists()
    merged_content = (Path(merged_md_path) / "merged.md").read_text()
    assert "![alt text]" not in merged_content
    assert "![Beautiful]" in merged_content
    assert "![RemoveMe]" not in merged_content