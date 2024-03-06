"""SUMO Environment for Ride-Sharing."""

from gymnasium.envs.registration import register


register(
    id="sumo-rl-rs-v0",
    entry_point="sumo_rl_rs.environment.env:SumoEnvironment",
    kwargs={"single_agent": True},
)


register(
    id="vec-sumo-rl-rs-v0",
    entry_point="sumo_rl_rs.environment.vectorized_env:VectorizedSumoEnvironment",
    kwargs={"num_envs": 8, "single_agent": True},
)