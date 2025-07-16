
from pathlib import Path
import os
import mdfusion.mdfusion as mdfusion

def test_presentation():
    path_to_md = os.path.join(os.path.dirname(__file__), "my_presentation.md")
    output_pdf = os.path.splitext(path_to_md)[0] + ".html"
    css_path = os.path.join(os.path.dirname(__file__), "custom.css")

    params = mdfusion.RunParams(
        root_dir=Path(os.path.dirname(path_to_md)),
        output=output_pdf,
        no_toc=False,
        title_page=False,
        title=None,
        author=None,
        pandoc_args=["-t", "revealjs", "-V", "revealjs-url=https://cdn.jsdelivr.net/npm/reveal.js@4", "-c", css_path, "--slide-level", "6"],
        config_path=None,
        header_tex=None
    )
    mdfusion.run(params)