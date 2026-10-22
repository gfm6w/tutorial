voltage_step = yaml.safe_load("""
name: voltage_step
start_time: {distribution: uniform, low: 0.5, high: 2.0}
events:
  - type: ReferenceVoltageVariation
    target: {static_id: _GEN____1_SM}
    params:
      delta_u: {distribution: uniform, low: -0.05, high: 0.05}
""")
extended = {
    **event_perturbation,
    "scenarios": event_perturbation["scenarios"] + [voltage_step],
}
spec = parse_event_perturbation(extended, start_time=0.0, stop_time=10.0)

rng = np.random.default_rng(0)
draws = [draw_events(spec, graph, rng) for _ in range(20)]
pd.Series([d.scenario.iloc[0] for d in draws]).value_counts()
