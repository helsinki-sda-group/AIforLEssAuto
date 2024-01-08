"""Observation functions for ride pooling controller."""
from abc import abstractmethod

import numpy as np
from gymnasium import spaces

from .ridepool_controller import RidePoolController


class ObservationFunction:
    """Abstract base class for observation functions."""

    def __init__(self, dispatcher: RidePoolController):
        """Initialize observation function."""
        self.dispatcher = dispatcher

    @abstractmethod
    def __call__(self):
        """Subclasses must override this method."""
        pass

    @abstractmethod
    def observation_space(self):
        """Subclasses must override this method."""
        pass


class DefaultObservationFunction(ObservationFunction):
    """Default observation function for traffic signals."""

    def __init__(self, dispatcher: RidePoolController):
        """Initialize default observation function."""
        super().__init__(dispatcher)

    def __call__(self) -> np.ndarray:
        """Return the default observation."""
      
        observation = self.dispatcher.get_observation()
        return observation

    def observation_space(self) -> spaces.Box:
        """Return the observation space."""

        low=np.zeros(self.dispatcher.observations_dim, dtype=np.float32)
        
        high = self.dispatcher.get_max_observations()

        return spaces.Box(
            low,
            high
        )
