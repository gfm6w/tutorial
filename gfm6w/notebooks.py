"""Convert a Quarto page of the tutorial into a participant notebook.

A code cell tagged `solution` becomes an empty cell followed by the solution in
a <details> block, and its collapsed callout goes, unless `solutions` asks for
the solution as a plain cell. Cells with `eval: false` are dropped. Quarto
markup becomes plain Markdown: callouts turn into quotes, chip spans into a
dotted line, div fences go. Local images resolve against the folder of the
page and are inlined as data URIs at the width the page gives them, rasters
downscaled to twice that width, so a notebook shows them wherever it is opened.
They are PNG or JPEG, since GitHub drops SVG data URIs. Links between parts
point at the notebooks, other pages at the site. `#|` options are dropped and
cell IDs are numbered, so a rebuild only diffs what changed. Files are UTF-8
with LF line ends on every platform.
"""

import base64
import io
import re
from pathlib import Path

import nbformat
import yaml
from PIL import Image

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
PART_LINK = re.compile(r"\]\((\d\d-[\w-]+)\.qmd")
PAGE_LINK = re.compile(r"\]\(([\w-]+)\.qmd")
IMAGE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)\)(\{[^}]*\})?")
WIDTH = re.compile(r"\bwidth=\"?(\d+)")
FIG_ALT = re.compile(r'fig-alt="([^"]*)"')
MIME = {".png": "image/png", ".jpg": "image/jpeg"}
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


def image(match, folder):
    alt, path, attrs = match.group(1), match.group(2), match.group(3) or ""
    if "://" in path:
        return match.group(0)
    source = folder / path
    if source.suffix not in MIME:
        raise ValueError(f"{path}: notebook images are PNG or JPEG")
    width = WIDTH.search(attrs)
    data = source.read_bytes()
    if width:
        picture = Image.open(source)
        size = 2 * int(width.group(1))
        if picture.width > size:
            picture = picture.resize(
                (size, round(picture.height * size / picture.width)),
                Image.LANCZOS,
            )
            buffer = io.BytesIO()
            picture.save(buffer, format="PNG", optimize=True)
            data = buffer.getvalue()
    uri = f"data:{MIME[source.suffix]};base64,{base64.b64encode(data).decode()}"
    size = f'width="{width.group(1)}"' if width else 'style="width:100%"'
    fig_alt = FIG_ALT.search(attrs)
    tag = f'<img src="{uri}" alt="{fig_alt.group(1) if fig_alt else alt}" {size}>'
    return (
        f"{tag}\n\n*{alt}*" if alt and match.group(0) == match.string.strip() else tag
    )


def markdown(text, folder):
    lines, quote = [], False
    for line in text.splitlines():
        callout = CALLOUT.match(line)
        if callout and ".solution" in callout.group(2):
            continue
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
        line = IMAGE.sub(lambda m: image(m, folder), SPAN.sub(r"\1", line))
        line = PART_LINK.sub(r"](\1.ipynb", line)
        line = PAGE_LINK.sub(rf"]({SITE_URL}/\1.html", line)
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


def header(meta, source):
    html = f"{SITE_URL}/{source.with_suffix('.html').name}"
    lines = [f"# {meta['title']}"]
    if meta.get("subtitle"):
        lines.append(f"**{meta['subtitle']}**")
    if meta.get("description"):
        lines.append(meta["description"])
    lines.append(
        f"Rendered version with every output: [{html}]({html})"
    )
    return "\n\n".join(lines)


def convert(source, solutions=False):
    meta, body = split_front_matter(source.read_text(encoding="utf-8"))
    cells = [nbformat.v4.new_markdown_cell(header(meta, source))]
    position = 0
    for chunk in CHUNK.finditer(body):
        text = markdown(body[position : chunk.start()], source.parent)
        if text:
            cells.append(nbformat.v4.new_markdown_cell(text))
        position = chunk.end()
        opts, code = options(chunk.group(1))
        if opts.get("include") is False or opts.get("eval") is False:
            continue
        if "solution" in (opts.get("tags") or []) and not solutions:
            cells.append(nbformat.v4.new_code_cell("# Your turn\n"))
            cells.append(
                nbformat.v4.new_markdown_cell(
                    "<details><summary><b>Show a solution</b></summary>\n\n"
                    f"```python\n{code}\n```\n\n</details>"
                )
            )
        else:
            cells.append(nbformat.v4.new_code_cell(code))
    tail = markdown(body[position:], source.parent)
    if tail:
        cells.append(nbformat.v4.new_markdown_cell(tail))
    for i, cell in enumerate(cells):
        cell.id = f"cell-{i:03d}"
    notebook = nbformat.v4.new_notebook(cells=cells)
    notebook.metadata["kernelspec"] = {
        "name": "python3",
        "display_name": "Python 3",
        "language": "python",
    }
    notebook.metadata["language_info"] = {"name": "python"}
    return notebook


def target(source, out):
    return out / source.with_suffix(".ipynb").name


def text(source):
    return nbformat.writes(convert(source)) + "\n"


def write(source, out):
    out.mkdir(parents=True, exist_ok=True)
    target(source, out).write_text(text(source), encoding="utf-8", newline="\n")
    return target(source, out)
