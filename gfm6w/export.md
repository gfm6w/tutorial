# PowSyBl & Dynawo in Practice

Steady-state and dynamic power system datasets for grid foundation models, with [PowSyBl](https://www.powsybl.org), [Dynawo](https://dynawo.github.io) and [GridFM-Datakit](https://github.com/gridfm/gridfm-datakit). Tutorial at [GridFM 2026](https://gridfm.org/porto/), Porto, 29 October 2026. Rendered pages at <https://gfm6w.github.io>.

This folder is a copy of [gfm6w/tutorial](https://github.com/gfm6w/tutorial) at [`{short}`](https://github.com/gfm6w/tutorial/tree/{commit}). Changes go there.

| Part | Notebook | Time |
|---|---|---|
| 1 | [PowSyBl & Dynawo](notebooks/01-powsybl-dynawo.ipynb) | 15 min |
| 2 | [Steady-state datasets](notebooks/02-steady-state.ipynb) | 20 min |
| 3 | [Randomized initial states](notebooks/03-dynamic-initial-state.ipynb) | 20 min |
| 4 | [Randomized dynamic events](notebooks/04-dynamic-events.ipynb) | 20 min |

## Run

On Linux or WSL 2, from this folder.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
gridfm_datakit setup_pm
bash scripts/install_dynawo.sh
python scripts/check_setup.py
jupyter lab notebooks/
```

Dynawo has no macOS build. On a Mac, or to install nothing, [open the tutorial in GitHub Codespaces](https://codespaces.new/gfm6w/tutorial?quickstart=1) or run `docker run --rm -p 8888:8888 ghcr.io/gfm6w/tutorial`. The [setup page](https://gfm6w.github.io/setup.html) has the details.

## Licence

Code (`notebooks/helpers.py`, `scripts/`) is under [Apache-2.0](LICENSE). Notebooks are under [CC BY 4.0](LICENSE-CC-BY-4.0). Data and libraries keep the licences listed below.

## Credits

- IEEE 14-bus case and Dynawo inputs from the GridFM-Datakit dynamic example (Apache-2.0), `IDAOrder2` solver set from the Dynawo IEEE14 fault example.
- PEGASE case from [PGLib-OPF](https://github.com/power-grid-lib/pglib-opf) (CC BY 4.0), by C. Josz, S. Fliscounakis, J. Maeght and P. Panciatici.
- Network explorer from [pypowsybl-jupyter](https://github.com/powsybl/pypowsybl-jupyter) (MPL-2.0).
