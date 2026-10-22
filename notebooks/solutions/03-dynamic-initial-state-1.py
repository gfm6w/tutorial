nadir = pd.Series(
    {key: curve(key, "_GEN____1_SM_generator_omegaPu_value")[1].min() for key in slice_of}
)
nadir.index.names = KEYS
table = pd.DataFrame({"demand": demand, "nadir": nadir}).dropna().reset_index()

fig, ax = plt.subplots(figsize=(6.5, 3.8))
for p, group in table.groupby("perturbation_index"):
    ax.scatter(group.demand, group.nadir, s=36, color=PALETTE[p], label=f"variant {p}")
ax.set(title="Speed nadir of generator 1", xlabel="total demand (MW)", ylabel="pu")
ax.legend();
