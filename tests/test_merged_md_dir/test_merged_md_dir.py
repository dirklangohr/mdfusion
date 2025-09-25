import mdfusion.mdfusion as mdfusion
import os
from pathlib import Path

def test_with_config(tmp_path, monkeypatch):
    this_dir = os.path.dirname(__file__)
    
    input_files = Path(this_dir) / "test_markdown_files"
    
    # merged_md_path = Path(this_dir) / "merged_md"
    merged_md_path = tmp_path / "merged_md"
    os.makedirs(merged_md_path, exist_ok=True)
    
    monkeypatch.chdir(tmp_path)
    
    mdfusion.run(mdfusion.RunParams(
        root_dir=input_files,
        merged_md=merged_md_path,
    ))
    
    assert (Path(merged_md_path) / "merged.md").exists()