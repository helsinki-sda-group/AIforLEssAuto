"""SUMO Environment for Ride-Sharing."""

from gymnasium.envs.registration import register


register(
    id="sumo-rl-rs-v0",
    entry_point="sumo_rl_rs.environment.env:SumoEnvironment",
    kwargs={"single_agent": True},
)