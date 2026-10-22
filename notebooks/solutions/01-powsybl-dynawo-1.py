network = pp.network.load("../data/ieee14/IEEE14.iidm")
pp.loadflow.run_ac(network)

trip = dyn.EventMapping()
trip.add_disconnection(static_id="_GEN____2_SM", start_time=1.0)
parameters = dyn.Parameters(
    start_time=0.0,
    stop_time=30.0,
    provider_parameters=parameters.provider_parameters,
)
result = simulation.run(network, models, trip, outputs, parameters)

curves = result.curves()
curves.index = (curves.index - curves.index[0]).total_seconds()
ax = curves["_GEN____1_SM_generator_omegaPu_value"].plot(color=PALETTE[0])
ax.set(title="Rotor speed of generator 1 after tripping generator 2",
       xlabel="time (s)", ylabel="pu");

# Losing a machine is a lasting power imbalance. The speed drops and settles
# at a new value set by the governors, where a cleared fault leaves the
# system where it started.
