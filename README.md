# PowSyBl & Dynawo in Practice

**Generating steady-state and dynamic power system datasets for foundation models.**
Tutorial at [GridFM 2026](https://gridfm.org/porto/), Porto, 29 October 2026.

Hands-on tutorial on [PowSyBl](https://www.powsybl.org) and [Dynawo](https://dynawo.github.io), two open-source, industrial-grade tools for power system simulation, and on how they combine in [GridFM-Datakit](https://github.com/gridfm/gridfm-datakit) to generate steady-state and dynamic datasets, including randomized initial states and randomized dynamic events, for training grid foundation models. No prior experience with PowSyBl or Dynawo is required.

**Rendered pages with every output: <https://gfm6w.github.io>**

## Programme

| Part | Topic | Time | Notebook | Page |
|---|---|---|---|---|
| 1 | PowSyBl & Dynawo, what they are and why GridFM-Datakit integrates them | 15 min | [01-powsybl-dynawo.ipynb](notebooks/01-powsybl-dynawo.ipynb) | [view](https://gfm6w.github.io/01-powsybl-dynawo.html) |
| 2 | Steady-state datasets from a transmission grid with PowSyBl | 20 min | [02-steady-state.ipynb](notebooks/02-steady-state.ipynb) | [view](https://gfm6w.github.io/02-steady-state.html) |
| 3 | Dynamic datasets with randomized initial states (Dynawo) | 20 min | [03-dynamic-initial-state.ipynb](notebooks/03-dynamic-initial-state.ipynb) | [view](https://gfm6w.github.io/03-dynamic-initial-state.html) |
| 4 | Dynamic datasets with randomized dynamic events (Dynawo) | 20 min | [04-dynamic-events.ipynb](notebooks/04-dynamic-events.ipynb) | [view](https://gfm6w.github.io/04-dynamic-events.html) |

## Run it

Set up before the session, the downloads take a few minutes. The [setup page](https://gfm6w.github.io/setup.html) has the details.

- **Codespaces.** [Open in GitHub Codespaces](https://codespaces.new/gfm6w/tutorial?quickstart=1). Nothing to install.
- **Dev container.** Open the folder in VS Code and choose *Reopen in Container*, or build `.devcontainer/Dockerfile` with Docker.
- **Local, Linux or WSL 2.**

  ```bash
  python -m venv .venv && source .venv/bin/activate
  pip install -r requirements.txt
  gridfm_datakit setup_pm
  bash scripts/install_dynawo.sh
  python scripts/check_setup.py
  jupyter lab notebooks/
  ```

Dynawo ships Linux and Windows builds only. On macOS use Codespaces or the dev container.

## Repository layout

```
notebooks/        the four notebooks, exercises left to fill in
helpers.py        plot style shared by the notebooks
data/ieee14/      IEEE 14-bus case with its Dynawo models and parameters
scripts/          setup check and Dynawo installer
gfm6w/            the gfm6w command, builds the notebooks and the site
site/             Quarto sources of the notebooks and of the website
.devcontainer/    container with Python, Julia, PowerModels and Dynawo
```

## Editing the tutorial

`site/*.qmd` is the only source. The notebooks and the website are both built from it by the `gfm6w` command, so never edit a notebook by hand: CI rejects a notebook that does not match its source.

```bash
pip install -e .        # once, in the tutorial environment, adds the gfm6w command
gfm6w notebooks         # regenerate notebooks/, seconds, nothing runs
gfm6w test 2            # run notebook 2 as a participant would, solutions filled in
gfm6w build             # execute the pages, render the website, regenerate notebooks/
gfm6w publish -o ../gfm6w.github.io
```

Every command reads the pages from `-i` (default `site/`) and writes to `-o` (default `notebooks/` or `site/_site`), `gfm6w COMMAND --help` gives the details. Run `notebooks` and `test` while writing, `build` before opening a pull request, and commit the notebooks and `site/_freeze` with the source. Images go in `site/assets/` and are embedded in the notebooks at the width set in the source, `![](assets/logo.png){width=150}`.

## Credits and data

- IEEE 14-bus network, Dynawo input tables and parameters from the GridFM-Datakit dynamic example (Apache-2.0). The `IDAOrder2` solver set follows the Dynawo IEEE14 fault example.
- PEGASE case from [PGLib-OPF](https://github.com/power-grid-lib/pglib-opf) (CC BY 4.0), originally published with MATPOWER by C. Josz, S. Fliscounakis, J. Maeght and P. Panciatici.
- Built with PowSyBl and Dynawo, projects of [LF Energy](https://lfenergy.org). Fonts Space Grotesk, IBM Plex Sans and JetBrains Mono, under the SIL Open Font License. Zoomable diagrams with [svg-pan-zoom](https://github.com/bumbu/svg-pan-zoom) (BSD-2-Clause).
