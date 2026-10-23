"""Run pypowsybl-jupyter's network explorer on the static site.

`install` swaps `pypowsybl_jupyter.network_explorer` for `network_explorer`
below, which builds the real explorer with dummy comms and no display, drives
its voltage level list and depth slider over every level and every depth until
the shown area stops growing, and records what its NAD, SLD and map widgets and
its hover function receive. The diagrams go to explorer/HASH/ as gzip JSON, one
file each, so a reader downloads only the views opened. The cell output is a
bare div, since Quarto adds RequireJS to a page whose output holds a script;
the site template loads assets/js/explorer.js, which rebuilds the explorer
around pypowsybl-jupyter's own widget scripts. Switch toggling and NAD expand
and remove need a kernel and are left out. `copy_widgets` copies those scripts
into the site with their MPL-2.0 notice.
"""

import gzip
import hashlib
import json
import shutil
from pathlib import Path

import comm
import ipywidgets
import pypowsybl_jupyter
from pypowsybl_jupyter import networkexplorer

DATA = Path("explorer")
WIDGETS = Path("assets/js/pypowsybl-jupyter")
SCRIPTS = ("nadwidget", "sldwidget", "networkmapwidget")
MAX_DEPTH = 20
MAP_TRAITS = (
    "spos",
    "lpos",
    "smap",
    "lmap",
    "tlmap",
    "hlmap",
    "use_name",
    "nvls",
    "params",
    "dark_mode",
    "hover_enabled",
)
HOVER_TYPES = {
    "get_lines": ["LINE"],
    "get_2_windings_transformers": [
        "TWO_WINDINGS_TRANSFORMER",
        "PHASE_SHIFT_TRANSFORMER",
    ],
    "get_3_windings_transformers": [
        "THREE_WINDINGS_TRANSFORMER",
        "THREE_WINDINGS_TRANSFORMER_LEG",
    ],
    "get_loads": ["LOAD"],
    "get_generators": ["GENERATOR"],
    "get_shunt_compensators": [
        "CAPACITOR",
        "INDUCTOR",
        "SHUNT_COMPENSATOR_INDUCTOR",
        "SHUNT_COMPENSATOR_CAPACITOR",
    ],
    "get_static_var_compensators": ["STATIC_VAR_COMPENSATOR"],
    "get_switches": [
        "DISCONNECTOR",
        "BREAKER",
        "LOAD_BREAK_SWITCH",
        "GROUND_DISCONNECTION",
    ],
    "get_tie_lines": ["TIE_LINE"],
    "get_dangling_lines": ["DANGLING_LINE"],
    "get_hvdc_lines": ["HVDC_LINE", "LCC_CONVERTER_STATION", "VSC_CONVERTER_STATION"],
    "get_batteries": ["BATTERY"],
    "get_busbar_sections": ["BUSBAR_SECTION"],
    "get_bus_breaker_view_buses": ["BUSBAR_SECTION"],
}

_original = networkexplorer.network_explorer


def _packed(value):
    text = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return gzip.compress(text.encode(), mtime=0)


def _parts(box):
    left, right = box.children
    found = left.children[1].children[1]
    nad_panel = right.children[1].children[0]
    slider = nad_panel.children[0].children[0]
    nad, sld, network_map = (panel.children[1] for panel in right.children[1].children)
    return found, slider, nad, sld, network_map


def _hover(network, function):
    tables = {}
    if function is None:
        return tables
    for getter, types in HOVER_TYPES.items():
        for equipment in getattr(network, getter)().index:
            for kind in types:
                try:
                    html = function(str(equipment), kind)
                except Exception as error:
                    html = f"ERROR {error!r}"
                tables.setdefault(kind, {})[str(equipment)] = html
    return tables


def _displayed(network, vl, depth):
    return tuple(
        sorted(
            network.get_network_area_diagram_displayed_voltage_levels(
                voltage_level_ids=vl, depth=depth
            )
        )
    )


class StaticExplorer:
    def __init__(self, folder):
        self.folder = folder

    def _repr_html_(self):
        return f'<div class="static-explorer" data-explorer="{self.folder}"></div>'


def network_explorer(network, **kwargs):
    shown, create = networkexplorer.display, comm.create_comm
    networkexplorer.display = lambda *args, **kwargs: None
    comm.create_comm = comm.DummyComm
    try:
        return _record(network, **kwargs)
    finally:
        networkexplorer.display, comm.create_comm = shown, create
        ipywidgets.Widget.close_all()


def _record(network, **kwargs):
    box = _original(network, **kwargs)
    found, slider, nad, sld, network_map = _parts(box)
    start, depth = found.value, slider.value
    vls = [value for _, value in found.options]
    nads, keys, slds = {}, {}, {}
    for vl in vls:
        found.value = vl
        slds[vl] = {
            "value": sld.diagram_data["value"],
            "value_meta": sld.diagram_data.get("value_meta") or "",
        }
        keys[vl] = []
        previous = None
        for level in range(MAX_DEPTH + 1):
            area = _displayed(network, vl, level)
            if area == previous:
                break
            name = hashlib.sha1("|".join(area).encode()).hexdigest()[:12]
            if name not in nads:
                slider.value = level
                nads[name] = {
                    "svg_data": nad.diagram_data["svg_data"],
                    "metadata": nad.diagram_data["metadata"],
                }
            keys[vl].append(name)
            previous = area
    vl_subs = {vl: sub for vl, sub in network_map.vl_subs.items() if vl in set(vls)}
    index = {
        "options": [[label, value] for label, value in found.options],
        "start": start,
        "depth": depth,
        "max_depth": MAX_DEPTH,
        "nad": keys,
        "sld": {vl: i for i, vl in enumerate(vls)},
        "map": {trait: getattr(network_map, trait) for trait in MAP_TRAITS},
        "vl_subs": vl_subs,
        "hover": _hover(network, nad._on_hover_func),
    }
    files = {"index.json.gz": _packed(index)}
    files.update({f"nad/{k}.json.gz": _packed(v) for k, v in nads.items()})
    files.update({f"sld/{i}.json.gz": _packed(slds[vl]) for i, vl in enumerate(vls)})
    digest = hashlib.sha1()
    for name in sorted(files):
        digest.update(name.encode() + files[name])
    folder = DATA / digest.hexdigest()[:16]
    for name, content in files.items():
        path = folder / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    return StaticExplorer(folder.as_posix())


def install():
    pypowsybl_jupyter.network_explorer = network_explorer
    networkexplorer.network_explorer = network_explorer


def copy_widgets(site="."):
    source = Path(pypowsybl_jupyter.__file__).parent / "static"
    target = Path(site) / WIDGETS
    target.mkdir(parents=True, exist_ok=True)
    for script in SCRIPTS:
        for suffix in (".js", ".css"):
            shutil.copyfile(source / f"{script}{suffix}", target / f"{script}{suffix}")
    (target / "NOTICE").write_text(
        "Widget scripts of pypowsybl-jupyter, copied unmodified from the installed\n"
        "package. Source and licence (MPL-2.0):\n"
        "https://github.com/powsybl/pypowsybl-jupyter\n"
        "https://mozilla.org/MPL/2.0/\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    copy_widgets()
