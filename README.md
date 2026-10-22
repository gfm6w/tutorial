# PowSyBl & Dynawo in Practice

Steady-state and dynamic power system datasets for grid foundation models, with [PowSyBl](https://www.powsybl.org), [Dynawo](https://dynawo.github.io) and [GridFM-Datakit](https://github.com/gridfm/gridfm-datakit). Tutorial at [GridFM 2026](https://gridfm.org/porto/), Porto, 29 October 2026. Rendered pages at <https://gfm6w.github.io>.

| Part | Notebook | Time |
|---|---|---|
| 1 | [PowSyBl & Dynawo](notebooks/01-powsybl-dynawo.ipynb) | 15 min |
| 2 | [Steady-state datasets](notebooks/02-steady-state.ipynb) | 20 min |
| 3 | [Randomized initial states](notebooks/03-dynamic-initial-state.ipynb) | 20 min |
| 4 | [Randomized dynamic events](notebooks/04-dynamic-events.ipynb) | 20 min |

## Run

Set up before the session, details on the [setup page](https://gfm6w.github.io/setup.html).

- [Open in GitHub Codespaces](https://codespaces.new/gfm6w/tutorial?quickstart=1), nothing to install.
- `docker run --rm -p 8888:8888 ghcr.io/gfm6w/tutorial`
- Locally on Linux or WSL 2.

  ```bash
  python -m venv .venv && source .venv/bin/activate
  pip install -r requirements.txt
  gridfm_datakit setup_pm
  bash scripts/install_dynawo.sh
  python scripts/check_setup.py
  jupyter lab notebooks/
  ```

Dynawo has no macOS build, so on a Mac use Codespaces or Docker.

## Edit

`site/*.qmd` is the only source. Never edit `notebooks/`, the notebooks and their solutions are generated and CI rejects a file that does not match its source.

```bash
pip install -e .    # adds the gfm6w command
gfm6w notebooks     # regenerate notebooks/ and notebooks/solutions/
gfm6w test 2        # run notebook 2, solutions filled in
gfm6w build         # render the website and the notebooks
```

Commit the notebooks and `site/_freeze` with the source. Dependencies go in `requirements.in`, then `uv pip compile requirements.in --universal --python-version 3.10 -o requirements.txt` refreshes the lock. Notebook images are PNG or JPEG. `gfm6w --help` lists the rest.

## Licence

Code (`gfm6w/`, `helpers.py`, `scripts/`) is under [Apache-2.0](LICENSE). Pages, notebooks and figures are under [CC BY 4.0](LICENSE-CC-BY-4.0). Data, fonts and libraries keep the licences listed below, and the logos belong to their owners.

## Credits

- IEEE 14-bus case and Dynawo inputs from the GridFM-Datakit dynamic example (Apache-2.0), `IDAOrder2` solver set from the Dynawo IEEE14 fault example.
- PEGASE case from [PGLib-OPF](https://github.com/power-grid-lib/pglib-opf) (CC BY 4.0), by C. Josz, S. Fliscounakis, J. Maeght and P. Panciatici.
- Fonts Space Grotesk, IBM Plex Sans and JetBrains Mono ([SIL OFL](site/assets/fonts/OFL.txt)). [svg-pan-zoom](https://github.com/bumbu/svg-pan-zoom) ([BSD-2-Clause](site/assets/js/svg-pan-zoom.LICENSE)).
