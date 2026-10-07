"""Check that every tool the notebooks need is installed and working.

Usage: python scripts/check_setup.py
"""

import importlib.metadata as md
import time
from pathlib import Path

IEEE14 = Path(__file__).resolve().parent.parent / "data" / "ieee14"


def versions():
    for package in ("gridfm-datakit", "pypowsybl", "zarr", "pandas"):
        try:
            print(f"{package:16s} {md.version(package)}")
        except md.PackageNotFoundError:
            print(f"{package:16s} missing")
    from gridfm_datakit.dynamic.dynawo.api import check_dynawo_available

    check_dynawo_available()
    print("dynawo           found")


def julia():
    from juliacall import Main as jl

    jl.seval("using PowerModels, Ipopt")
    print("powermodels      found")


def dynawo():
    import pypowsybl as pp
    import pypowsybl.dynamic as dyn

    network = pp.network.load(str(IEEE14 / "IEEE14.iidm"))
    pp.loadflow.run_ac(network)
    models = dyn.ModelMapping()
    models.add_synchronous_generator(
        static_id="_GEN____1_SM",
        parameter_set_id="Generator1",
        model_name="GeneratorSynchronousFourWindingsProportionalRegulations",
    )
    events = dyn.EventMapping()
    events.add_disconnection(static_id="_GEN____2_SM", start_time=1.0)
    par = str(IEEE14 / "IEEE14.par")
    parameters = dyn.Parameters(
        start_time=0.0,
        stop_time=10.0,
        provider_parameters={
            "parametersFile": par,
            "network.parametersFile": par,
            "network.parametersId": "Network",
            "solver.type": "IDA",
            "solver.parametersFile": par,
            "solver.parametersId": "IDAOrder2",
        },
    )
    start = time.perf_counter()
    result = dyn.Simulation().run(network, models, events, None, parameters)
    status = result.status().name
    print(f"dynawo run       {status} in {time.perf_counter() - start:.1f} s")
    if status != "SUCCESS":
        raise RuntimeError("the Dynawo test simulation did not succeed")


if __name__ == "__main__":
    versions()
    julia()
    dynawo()
    print("All set")
