"""Generate the participant notebooks of notebooks/ from the Quarto sources of site/.

A code cell tagged `solution` becomes an empty cell followed by the solution in
a <details> block. Quarto markup becomes plain Markdown: callouts turn into
quotes, chip spans into a dotted line, div fences and image attributes go,
asset paths point into site/, links between parts point at the notebooks.
`#|` cell options are dropped.

Usage: python scripts/make_notebooks.py [NAME.qmd ...]
"""

import re
import sys
from pathlib import Path

import nbformat
import yaml

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
OUT = ROOT / "notebooks"
SITE_URL = "https://gfm6w.github.io"
SOURCES = [
    "01-powsybl-dynawo.qmd",
    "02-steady-state.qmd",
    "03-dynamic-initial-state.qmd",
    "04-dynamic-events.qmd",
]

CHUNK = re.compile(r"^```\{python\}\s*\n(.*?)^```\s*$", re.S | re.M)
CALLOUT = re.compile(r'^:::+\s*\{\.callout-(\w+)([^}]*)\}\s*$')
TITLE = re.compile(r'title="([^"]*)"')
FENCE = re.compile(r"^:::+\s*(\{[^}]*\})?\s*$")
SPAN = re.compile(r"(?<!!)\[([^\]]+)\]\{\.[^}]*\}")
QMD_LINK = re.compile(r"\]\((\d\d-[\w-]+)\.qmd")
IMAGE_ATTRS = re.compile(r"(!\[[^\]]*\]\([^)]*\))\{[^}]*\}")
LABELS = {
    "note": "Note",
    "tip": "Tip",
    "warning": "Warning",
    "important": "Important",
    "caution": "Caution",
}


def split_front_matter(text):
    if not text.startswith("---"):
        return {}, text
    _, head, body = text.split("---", 2)
    return yaml.safe_load(head), body


def markdown(text):
    lines, quote = [], False
    for line in text.splitlines():
        callout = CALLOUT.match(line)
        if callout:
            kind, attrs = callout.groups()
            title = TITLE.search(attrs)
            label = title.group(1) if title else LABELS.get(kind, kind.title())
            icon = "✎ " if ".exercise" in attrs else ""
            lines.append(f"> **{icon}{label}**")
            lines.append(">")
            quote = True
            continue
        if FENCE.match(line):
            quote = False
            continue
        spans = SPAN.findall(line)
        if spans and not SPAN.sub("", line).strip():
            line = " · ".join(spans)
        line = IMAGE_ATTRS.sub(r"\1", SPAN.sub(r"\1", line))
        line = line.replace("](assets/", "](../site/assets/")
        line = QMD_LINK.sub(r"](\1.ipynb", line)
        lines.append(("> " + line).rstrip() if quote else line)
    return "\n".join(lines).strip()


def options(source):
    opts, code = {}, []
    for line in source.splitlines():
        if line.startswith("#|"):
            opts.update(yaml.safe_load(line[2:]) or {})
        else:
            code.append(line)
    return opts, "\n".join(code).strip()


def header(meta, name):
    html = f"{SITE_URL}/{Path(name).with_suffix('.html')}"
    lines = [f"# {meta['title']}"]
    if meta.get("subtitle"):
        lines.append(f"**{meta['subtitle']}**")
    if meta.get("description"):
        lines.append(meta["description"])
    lines.append(
        f"Rendered version with every output: [{html}]({html})"
    )
    return "\n\n".join(lines)


def convert(name):
    meta, body = split_front_matter((SITE / name).read_text())
    cells = [nbformat.v4.new_markdown_cell(header(meta, name))]
    position = 0
    for chunk in CHUNK.finditer(body):
        text = markdown(body[position:chunk.start()])
        if text:
            cells.append(nbformat.v4.new_markdown_cell(text))
        position = chunk.end()
        opts, code = options(chunk.group(1))
        if opts.get("include") is False:
            continue
        if "solution" in (opts.get("tags") or []):
            cells.append(nbformat.v4.new_code_cell("# Your turn\n"))
            cells.append(
                nbformat.v4.new_markdown_cell(
                    "<details><summary><b>Show a solution</b></summary>\n\n"
                    f"```python\n{code}\n```\n\n</details>"
                )
            )
        else:
            cells.append(nbformat.v4.new_code_cell(code))
    tail = markdown(body[position:])
    if tail:
        cells.append(nbformat.v4.new_markdown_cell(tail))
    notebook = nbformat.v4.new_notebook(cells=cells)
    notebook.metadata["kernelspec"] = {
        "name": "python3",
        "display_name": "Python 3",
        "language": "python",
    }
    notebook.metadata["language_info"] = {"name": "python"}
    target = OUT / Path(name).with_suffix(".ipynb")
    nbformat.write(notebook, target)
    return target


def main():
    OUT.mkdir(exist_ok=True)
    for name in sys.argv[1:] or SOURCES:
        print(convert(name).relative_to(ROOT))


if __name__ == "__main__":
    main()
