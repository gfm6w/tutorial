"""Convert a Quarto page of the tutorial into a participant notebook.

A `.solution` callout, its code and its text, goes to solutions/NAME-K.py next
to the notebook, the text as comments. The notebook gets an exercise cell that
can `%load` it and a link to it, since GitHub shows a <details> block open.
`solutions` puts the code back as a plain cell instead. Cells with
`eval: false` are dropped. Quarto
markup becomes plain Markdown: callouts turn into quotes, chip spans into a
dotted line, a `.center` div becomes an `align="center"` HTML block with no
blank line inside, since GitHub left-aligns a paragraph, other div fences go.
Local images resolve against the folder of the page and are inlined as data
URIs at the width the page gives them, rasters downscaled to twice that width,
so a notebook shows them wherever it is opened. They are PNG or JPEG, since
GitHub drops SVG data URIs. Links between parts point at the notebooks, other
pages at the site. `#|` options are dropped and cell IDs are numbered, so a
rebuild only diffs what changed. Files are UTF-8 with LF line ends on every
platform. `formatted` runs the code chunks of a page through ruff format as
notebook cells, which keeps the trailing semicolon that hides a plot's repr.
"""

import base64
import io
import re
import subprocess
import sys
import textwrap

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
SOLUTION = re.compile(
    r"^:::+\s*\{\.callout-\w+[^}]*\.solution[^}]*\}\s*\n(.*?)^:::+\s*$", re.S | re.M
)
CALLOUT = re.compile(r"^:::+\s*\{\.callout-(\w+)([^}]*)\}\s*$")
TITLE = re.compile(r'title="([^"]*)"')
FENCE = re.compile(r"^:::+\s*(\{[^}]*\})?\s*$")
CENTER = re.compile(r"\.center\b")
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
    lines, quote, divs = [], False, []
    for line in text.splitlines():
        callout = CALLOUT.match(line)
        if callout:
            divs.append(False)
        if callout:
            kind, attrs = callout.groups()
            title = TITLE.search(attrs)
            label = title.group(1) if title else LABELS.get(kind, kind.title())
            icon = "✎ " if ".exercise" in attrs else ""
            lines.append(f"> **{icon}{label}**")
            lines.append(">")
            quote = True
            continue
        fence = FENCE.match(line)
        if fence and fence.group(1):
            center = bool(CENTER.search(fence.group(1)))
            divs.append(center)
            lines.extend(['<div align="center">'] if center else [])
            continue
        if fence:
            quote = False
            if divs and divs.pop():
                lines.append("</div>")
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
    lines.append(f"Rendered version with every output: [{html}]({html})")
    return "\n\n".join(lines)


def comment(text):
    return "\n".join(
        textwrap.fill(paragraph, 77, initial_indent="# ", subsequent_indent="# ")
        for paragraph in text.split("\n\n")
    )


def blocks(body):
    found = [(m.start(), m.end(), "solution", m) for m in SOLUTION.finditer(body)]
    for chunk in CHUNK.finditer(body):
        if not any(start <= chunk.start() < end for start, end, _, _ in found):
            found.append((chunk.start(), chunk.end(), "chunk", chunk))
    return sorted(found, key=lambda block: block[0])


def build(source, solutions=False):
    meta, body = split_front_matter(source.read_text(encoding="utf-8"))
    cells = [nbformat.v4.new_markdown_cell(header(meta, source))]
    files = {}
    position = 0
    for start, end, kind, match in blocks(body):
        text = markdown(body[position:start], source.parent)
        if text:
            cells.append(nbformat.v4.new_markdown_cell(text))
        position = end
        if kind == "solution":
            inner = match.group(1)
            code = "\n\n".join(options(c.group(1))[1] for c in CHUNK.finditer(inner))
            if solutions:
                cells.append(nbformat.v4.new_code_cell(code))
                continue
            name = f"solutions/{source.stem}-{len(files) + 1}.py"
            prose = markdown(CHUNK.sub("", inner), source.parent)
            files[name] = code + ("\n\n" + comment(prose) if prose else "") + "\n"
            cells.append(
                nbformat.v4.new_code_cell(
                    "# Your turn. To load a solution, uncomment the next line and"
                    f" run the cell.\n# %load {name}\n"
                )
            )
            cells.append(
                nbformat.v4.new_markdown_cell(f"A solution is in [{name}]({name}).")
            )
            continue
        opts, code = options(match.group(1))
        if opts.get("include") is False or opts.get("eval") is False:
            continue
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
    files[source.with_suffix(".ipynb").name] = nbformat.writes(notebook) + "\n"
    return notebook, files


def convert(source, solutions=False):
    return build(source, solutions)[0]


def outputs(source):
    return build(source)[1]


def write(source, out):
    paths = []
    for name, text in outputs(source).items():
        path = out / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        paths.append(path)
    return paths


def formatted(source):
    text = source.read_text(encoding="utf-8")
    chunks = list(CHUNK.finditer(text))
    heads, codes = [], []
    for chunk in chunks:
        lines = chunk.group(1).splitlines()
        count = next(
            (i for i, line in enumerate(lines) if not line.startswith("#|")), len(lines)
        )
        heads.append(lines[:count])
        codes.append("\n".join(lines[count:]))
    book = nbformat.v4.new_notebook(cells=[nbformat.v4.new_code_cell(c) for c in codes])
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ruff",
            "format",
            "--stdin-filename",
            "chunks.ipynb",
            "-",
        ],
        input=nbformat.writes(book),
        capture_output=True,
        text=True,
        check=True,
    )
    cells = nbformat.reads(result.stdout, as_version=4).cells
    parts, position = [], 0
    for chunk, head, cell in zip(chunks, heads, cells, strict=True):
        parts.append(text[position : chunk.start(1)])
        parts.append("\n".join([*head, cell.source]) + "\n")
        position = chunk.end(1)
    parts.append(text[position:])
    return "".join(parts)
