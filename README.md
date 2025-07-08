# mdfusion

Merge all Markdown files in a directory tree into a single PDF with beautiful formatting via Pandoc + XeLaTeX.

---

## Features

- **Recursive Markdown merge:** Collects and sorts all `.md` files under a directory (natural sort order).
- **PDF output via Pandoc + XeLaTeX:** Produces a polished PDF with centered section headings and small margins.
- **Title page and metadata:** Optional title page with configurable title, author, and date.
- **Config file support:** Use a `.mdfusion` INI-style config file for repeatable builds.
- **Custom LaTeX header:** Inject your own LaTeX via `header.tex` if desired.
- **Image link rewriting:** Converts relative image links to absolute paths, so identically-named images in different folders don't collide.

---

## Installation

1. **Clone this repo**
2. Install Python 3.8+ and [Pandoc](https://pandoc.org/) with XeLaTeX support
3. Install the `mdfusion` package:

```sh
pip install .
```

---

## Usage

```sh
mdfusion ROOT_DIR [OPTIONS]
```

### Common options

- `-o, --output FILE`      Output PDF filename (default: `<root_dir>.pdf`)
- `--no-toc`               Omit table of contents
- `--title-page`           Include a title page
- `--title TITLE`          Set title for title page (default: directory name)
- `--author AUTHOR`        Set author for title page (default: OS user)
- `--pandoc-args ARGS`     Extra Pandoc arguments (whitespace-separated)
- `-c, --config FILE`      Path to a `.mdfusion` INI-style config file

### Example

```sh
mdfusion --title-page --title "My Book" --author "Jane Doe" docs/
```

---

## Configuration file

You can create a `.mdfusion` file in your project directory:

```ini
[mdfusion]
root_dir = docs
output = my-book.pdf
no_toc = true
title_page = true
title = My Book
author = Jane Doe
pandoc_args = --number-sections
```

Then just run:

```sh
mdfusion
```

---

## How it works

- Finds and sorts all Markdown files under the root directory
- Merges them into one file, rewriting image links to absolute paths
- Optionally adds a YAML metadata block for title/author/date
- Inserts page breaks between files
- Calls Pandoc with XeLaTeX and a custom header for formatting

---

## Testing

Run all tests with:

```sh
pytest
```

---

## Author

[ejuet](https://github.com/ejuet)
