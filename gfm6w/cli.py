"""The gfm6w command, which builds the tutorial from its Quarto pages.

    gfm6w notebooks        regenerate the notebooks and solutions, nothing runs
    gfm6w check            fail if the notebooks, solutions or frozen outputs
                           are out of date
    gfm6w test [N ...]     run notebooks N (1 to 4, default all), solutions
                           filled in
    gfm6w format           format the code of the pages with ruff
    gfm6w html             execute the pages and render the website
    gfm6w build            html, then notebooks
    gfm6w publish -o DIR   build, then mirror the website into DIR, a checkout
                           of gfm6w.github.io, keeping its .git, .github and CNAME

Every command reads the pages from -i (default site/). The notebooks go to -o
(default notebooks/). Quarto renders the website into site/_site, html copies
it to -o if given. build takes --notebooks and --html instead. test runs the
notebooks from -o, which sits next to data/ for their relative paths to
resolve. The interpreter gfm6w is installed in runs the pages and the
notebooks. Quarto reuses site/_freeze for pages whose source did not change,
`quarto render site/NAME.qmd` reruns one. Defaults resolve from the package,
so gfm6w is installed editable from the clone.
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError

from gfm6w import notebooks as nb

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
NOTEBOOKS = ROOT / "notebooks"
HTML = SITE / "_site"
KEEP = {".git", ".github", "CNAME"}


def pages(site, parts=()):
    return [site / nb.SOURCES[n - 1] for n in parts] or [site / n for n in nb.SOURCES]


def notebooks(site, out):
    for source in pages(site):
        for path in nb.write(source, out):
            print(path)


def frozen(site, source):
    page = source.relative_to(site).with_suffix("")
    path = site / "_freeze" / page / "execute-results" / "html.json"
    if not path.exists():
        return False
    digest = hashlib.md5(source.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    return json.loads(path.read_text(encoding="utf-8"))["hash"] == digest


def check(site, out):
    stale = [
        out / name
        for source in pages(site)
        for name, text in nb.outputs(source).items()
        if not (out / name).exists() or (out / name).read_text(encoding="utf-8") != text
    ]
    unrendered = [source for source in pages(site) if not frozen(site, source)]
    for path in stale:
        print(f"{path} is out of date")
    for source in unrendered:
        print(f"{source} changed since its frozen outputs")
    if stale:
        print("Run `gfm6w notebooks` and commit the result.")
    if unrendered:
        print("Run `quarto render` on each page and commit site/_freeze.")
    if stale or unrendered:
        sys.exit(1)
    print("Notebooks and frozen outputs match the sources")


def test(site, out, parts):
    out.mkdir(parents=True, exist_ok=True)
    failed = []
    for source in pages(site, parts):
        client = NotebookClient(
            nb.convert(source, solutions=True),
            timeout=1800,
            kernel_name="python3",
            resources={"metadata": {"path": str(out)}},
        )
        start = time.perf_counter()
        try:
            client.execute()
            print(f"{source.name:32s} ok in {time.perf_counter() - start:.0f} s")
        except CellExecutionError as error:
            print(f"{source.name:32s} FAILED\n{error}")
            failed.append(source.name)
    if failed:
        sys.exit(f"{len(failed)} notebook(s) failed")


def html(site, out):
    env = dict(os.environ, QUARTO_PYTHON=sys.executable)
    subprocess.run(["quarto", "render"], cwd=site, env=env, check=True)
    if out != site / "_site":
        shutil.copytree(site / "_site", out, dirs_exist_ok=True)
        print(f"Website copied to {out}")


def format_pages(site):
    for source in pages(site):
        text = nb.formatted(source)
        if text != source.read_text(encoding="utf-8"):
            source.write_text(text, encoding="utf-8", newline="\n")
            print(f"{source} reformatted")


def build(site, html_out, notebooks_out):
    html(site, html_out)
    notebooks(site, notebooks_out)


def publish(site, out):
    build(site, site / "_site", NOTEBOOKS)
    out.mkdir(parents=True, exist_ok=True)
    for path in out.iterdir():
        if path.name in KEEP:
            continue
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
    shutil.copytree(site / "_site", out, dirs_exist_ok=True)
    (out / ".nojekyll").touch()
    print(f"Site copied to {out}")


def folder(text):
    return Path(text).resolve()


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    commands = parser.add_subparsers(dest="command", required=True)
    inputs = argparse.ArgumentParser(add_help=False)
    inputs.add_argument(
        "-i",
        "--input",
        type=folder,
        default=SITE,
        help="folder of the Quarto pages (default site/)",
    )
    notebooks_out = argparse.ArgumentParser(add_help=False)
    notebooks_out.add_argument(
        "-o",
        "--output",
        type=folder,
        default=NOTEBOOKS,
        help="folder of the notebooks (default notebooks/)",
    )
    commands.add_parser("notebooks", parents=[inputs, notebooks_out])
    commands.add_parser("check", parents=[inputs, notebooks_out])
    commands.add_parser("test", parents=[inputs, notebooks_out]).add_argument(
        "parts", nargs="*", type=int, choices=range(1, len(nb.SOURCES) + 1)
    )
    commands.add_parser("format", parents=[inputs])
    commands.add_parser("html", parents=[inputs]).add_argument(
        "-o",
        "--output",
        type=folder,
        default=HTML,
        help="folder of the website (default site/_site)",
    )
    build_parser = commands.add_parser("build", parents=[inputs])
    build_parser.add_argument(
        "--html",
        type=folder,
        default=HTML,
        help="folder of the website (default site/_site)",
    )
    build_parser.add_argument(
        "--notebooks",
        type=folder,
        default=NOTEBOOKS,
        help="folder of the notebooks (default notebooks/)",
    )
    commands.add_parser("publish", parents=[inputs]).add_argument(
        "-o",
        "--output",
        type=folder,
        required=True,
        help="checkout of gfm6w.github.io",
    )
    args = parser.parse_args()
    if not (args.input / "_quarto.yml").exists():
        sys.exit(f"{args.input} has no _quarto.yml, pass the pages with -i")
    if args.command == "notebooks":
        notebooks(args.input, args.output)
    elif args.command == "check":
        check(args.input, args.output)
    elif args.command == "test":
        test(args.input, args.output, args.parts)
    elif args.command == "format":
        format_pages(args.input)
    elif args.command == "html":
        html(args.input, args.output)
    elif args.command == "build":
        build(args.input, args.html, args.notebooks)
    else:
        publish(args.input, args.output)


if __name__ == "__main__":
    main()
