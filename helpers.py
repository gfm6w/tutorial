"""Plot style shared by the tutorial notebooks.

`PALETTE` is the categorical order of the plots, assigned in order. It passes
the colour-vision-deficiency and contrast checks on a white background.
`area_diagram` pulls the default network area diagram layout together by
`spread` and shows it inline with svg-pan-zoom. The site serves its own copy
of the library, a notebook loads it from the CDN. Under RequireJS the library
registers as the AMD module `svg-pan-zoom` instead of a global.
"""

import json
import logging
import re
import uuid
import warnings

import matplotlib.pyplot as plt
import pandas as pd

PALETTE = ["#1486c2", "#e07a1f", "#0f9b8e", "#a8285a", "#7a5cc9"]
INK = "#1b2a3a"
MUTED = "#5a6b7e"
GRID = "#e3e8ee"


def setup():
    """Apply the plot style and silence library warnings."""
    plt.rcParams.update(
        {
            "figure.figsize": (9, 4),
            "figure.dpi": 110,
            "axes.prop_cycle": plt.cycler(color=PALETTE),
            "axes.edgecolor": GRID,
            "axes.labelcolor": INK,
            "axes.titlecolor": INK,
            "axes.titlesize": 11,
            "axes.titlelocation": "left",
            "axes.labelsize": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.color": GRID,
            "grid.linewidth": 0.8,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "lines.linewidth": 1.8,
            "legend.frameon": False,
            "legend.fontsize": 9,
        }
    )
    pd.set_option("display.max_columns", 12)
    pd.set_option("display.width", 120)
    warnings.filterwarnings("ignore")
    logging.getLogger("powsybl").setLevel(logging.ERROR)


SVG_PAN_ZOOM = "https://cdn.jsdelivr.net/npm/svg-pan-zoom@3.6.2/dist/svg-pan-zoom.min.js"


class Zoomable:
    """An SVG shown inline with wheel zoom, drag pan and zoom buttons."""

    def __init__(self, svg, height=560):
        self.svg = svg
        self.height = height

    def _repr_html_(self):
        uid = f"zoom-{uuid.uuid4().hex[:8]}"
        svg = re.sub(r"<\?xml[^>]*>", "", self.svg, count=1)
        svg = re.sub(
            r"<svg[^>]*?\swidth=\"[^\"]*\"\s+height=\"[^\"]*\"",
            lambda m: m.group(0).split(" width=")[0],
            svg,
            count=1,
        )
        svg = svg.replace("<svg", f'<svg id="{uid}" width="100%" height="100%"', 1)
        return f"""
<div style="height:{self.height}px;border:1px solid {GRID};border-radius:6px;overflow:hidden">{svg}</div>
<p style="font-size:0.8rem;color:{MUTED};margin-top:0.3rem">Scroll to zoom, drag to pan.</p>
<script>
(function () {{
  var start = function (panZoom) {{
    panZoom("#{uid}", {{controlIconsEnabled: true, fit: true, center: true,
                        minZoom: 0.5, maxZoom: 40, zoomScaleSensitivity: 0.3,
                        dblClickZoomEnabled: false}});
  }};
  if (window.svgPanZoom) {{
    start(window.svgPanZoom);
  }} else if (typeof define === "function" && define.amd) {{
    require.config({{paths: {{"svg-pan-zoom": "{SVG_PAN_ZOOM[:-3]}"}}}});
    require(["svg-pan-zoom"], start);
  }} else {{
    var script = document.createElement("script");
    script.src = "{SVG_PAN_ZOOM}";
    script.onload = function () {{ start(window.svgPanZoom); }};
    document.head.appendChild(script);
  }}
}})();
</script>"""


def area_diagram(network, voltage_level_ids=None, depth=0, spread=0.45, height=560):
    """Zoomable network area diagram with its nodes pulled together."""
    first = network.get_network_area_diagram(voltage_level_ids, depth)
    nodes = json.loads(first.metadata)["nodes"]
    positions = pd.DataFrame(
        {
            "id": [node["equipmentId"] for node in nodes],
            "x": [spread * node["x"] for node in nodes],
            "y": [spread * node["y"] for node in nodes],
        }
    ).set_index("id")
    diagram = network.get_network_area_diagram(
        voltage_level_ids, depth, fixed_positions=positions
    )
    return Zoomable(diagram.svg, height)
