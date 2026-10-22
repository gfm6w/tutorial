lines_only = {
    **config,
    "topology_perturbation": {
        "type": "random",
        "k": 1,
        "n_topology_variants": 5,
        "elements": ["branch"],
    },
    "settings": {**config["settings"], "data_dir": "outputs/part2/lines_only"},
}
Path("outputs/part2/lines_only.yaml").write_text(yaml.safe_dump(lines_only))

import subprocess

command = [sys.executable, "-m", "gridfm_datakit.cli", "generate", "outputs/part2/lines_only.yaml"]
subprocess.run(command, check=True, capture_output=True)

b2 = pd.read_parquet("outputs/part2/lines_only/pegase89/raw/branch_data.parquet")
b2 = b2[(b2.br_status == 1) & (b2.rate_a > 0)]
b2["loading"] = np.hypot(b2.pf, b2.qf) / b2.rate_a
print(f"{b2.groupby('scenario').loading.max().gt(1.0).mean():.0%} of samples overloaded")
