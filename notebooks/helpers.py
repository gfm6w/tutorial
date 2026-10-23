"""Plot style shared by the tutorial notebooks.

`PALETTE` is the categorical order of the plots, assigned in order. It passes
the colour-vision-deficiency and contrast checks on a white background.
"""

import logging
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
    pd.set_option("display.show_dimensions", False)
    warnings.filterwarnings("ignore")
    logging.getLogger("powsybl").setLevel(logging.ERROR)
