#!/usr/bin/env bash
# Render site/ with Quarto and regenerate notebooks/ from the same sources.
# PYTHON selects the interpreter that executes the pages (default: python).
# --publish DIR mirrors site/_site into DIR, a checkout of gfm6w.github.io.
set -euo pipefail

caller="$PWD"
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python="$(command -v "${PYTHON:-python}")"
python="$(cd "$(dirname "$python")" && pwd)/$(basename "$python")"
export QUARTO_PYTHON="$python"

cd "$root/site"
quarto render
"$python" "$root/scripts/make_notebooks.py"

if [ "${1:-}" = "--publish" ]; then
  dest="$(cd "$caller" && mkdir -p "${2:?usage: build.sh --publish DIR}" && cd "$2" && pwd)"
  rsync -a --delete --exclude .git --exclude CNAME "$root/site/_site/" "$dest/"
  touch "$dest/.nojekyll"
  echo "Site copied to $dest"
fi
