import os
import htmlark
from pathlib import Path

# pack everything into a single HTML string
bundled_html = htmlark.convert_page(
    "my_presentation.html",
    ignore_errors=False,   # raise on broken links
    ignore_images=False,
    ignore_css=False,
    ignore_js=False
)

with open("bundled.html", "w", encoding="utf-8") as f:
    f.write(bundled_html)
