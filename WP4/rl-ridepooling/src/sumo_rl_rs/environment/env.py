"""SUMO Environment for Ride-Sharing."""
import os
import sys
from pathlib import Path
from typing import Callable, Optional, Tuple, Union


if "SUMO_HOME" in os.environ:
    tools = os.path.join(os.environ["SUMO_HOME"], "tools")
    sys.path.append(tools)
else:
    raise ImportError("Please declare the environment variable 'SUMO_HOME'")
import gymnasium as gym
import numpy as np
import pandas as pd
import sumolib
# import traci
import libsumo as traci
from gymnasium.utils import EzPickle, seeding


from .observations import DefaultObservationFunction, ObservationFunction
from .ridepool_controller import RidePoolController
from .taxi_reservations_logger import TaxiReservationsLogger

from bs4 import BeautifulSoup

# LIBSUMO = "LIBSUMO_AS_TRACI" in os.environ
LIBSUMO = True




# !NB: this environment was created based on Lucas Alegre example for traffic lights signals
# https://github.com/LucasAlegre/sumo-rl
# some ot the parameters of the environment may be copied from the example and are actually not used 
class SumoEnvironment(gym.Env):
    
    metadata = {
        "render_modes": ["human", "rgb_array"],
    }

    CONNECTION_LABEL = 0  # For traci multi-client support

    def _read_sim_max_time(self, cfg_file: str):
        ''' Reads simulation time from SUMO configuration file (*.sumocfg)
        '''
        with open(cfg_file, "r") as f:
            data = f.read()
        f.close()

        cfg_soup = BeautifulSoup(data, "xml")
        time_tag = cfg_soup.find("time")

        end_tag = time_tag.find("end")
              
        assert end_tag is not None
        
        sim_max_time = int(float(end_tag["value"]))
        return sim_max_time

    def _read_max_capacity(self, cfg_file: str):
        ''' Reads maximum possible capacity of taxis from SUMO route file (*.rou.xml)

        The name of route file is obtained from configuration file.
        '''
        # get name of route file from cfg file
        with open(cfg_file, "r") as f:
            data = f.read()
        f.close()

        # get relative path to sumo files
        cfg_arr = cfg_file.split("/")
        cfg_len = len(cfg_arr)
        cfg_path = ""

        for i in range(0, cfg_len-1):
            cfg_path += cfg_arr[i] + "/"

        cfg_soup = BeautifulSoup(data, "xml")
        input_tag = cfg_soup.find("input")

        route_file_tag = input_tag.find("route-files")
              
        assert route_file_tag is not None
        
        route_file = route_file_tag["value"]
        route_file = cfg_path + route_file
                
        # from route file parse parameter personCapacity of vType
        with open( route_file, "r") as f:
            data = f.read()
        f.close()

        route_soup = BeautifulSoup(data, "xml")

        vtype_tag = route_soup.find("vType", {"vClass": "taxi"})
        
        assert vtype_tag is not None
    
        max_capacity = int(float(vtype_tag["personCapacity"]))

        return max_capacity

    def __init__(
        self,
        cfg_file: str,
        out_csv_name: Optional[str] = None,
        use_gui: bool = False,
        virtual_display: Tuple[int, int] = (3200, 1800),
        delta_time: int = 180,
        single_agent: bool = False,
        reward_fn: str = "emissions-nonserved",
        observation_class: ObservationFunction = DefaultObservationFunction,
        add_system_info: bool = True,
        add_per_agent_info: bool = True,
        sumo_seed: Union[str, int] = 42,
        sumo_warnings: bool = True,
        additional_sumo_cmd: Optional[str] = None,
        render_mode: Optional[str] = None,
        verbose: bool = False,
        taxi_reservations_logger: TaxiReservationsLogger = None,
    ) -> None:
        """Initialize the environment."""
        assert render_mode is None or render_mode in self.metadata["render_modes"], "Invalid render mode."
        self.render_mode = render_mode
        self.virtual_display = virtual_display
        self.disp = None
        self.verbose = verbose
        self._cfg = cfg_file
       
        self.use_gui = use_gui
        if self.use_gui or self.render_mode is not None:
            self._sumo_binary = sumolib.checkBinary("sumo-gui")
        else:
            self._sumo_binary = sumolib.checkBinary("sumo")

        self.delta_time = delta_time  # seconds on sumo at each step
        self.single_agent = single_agent
        self.reward_fn = reward_fn
        self.sumo_seed = sumo_seed
        self.sumo_warnings = sumo_warnings
        self.additional_sumo_cmd = additional_sumo_cmd
        self.add_system_info = add_system_info
        self.add_per_agent_info = add_per_agent_info
        self.label = str(SumoEnvironment.CONNECTION_LABEL)
        SumoEnvironment.CONNECTION_LABEL += 1
        self.sumo = None

        # Adding taxi logger that logs taxi counts and also reservation counts
        self.taxi_reservations_logger = taxi_reservations_logger

        if LIBSUMO:
            traci.start([sumolib.checkBinary("sumo"), "-c", self._cfg])  # (test connection)
            conn = traci
        else:
            traci.start([sumolib.checkBinary("sumo"), "-c", self._cfg], label="init_connection" + self.label)
            conn = traci.getConnection("init_connection" + self.label)

        self.observation_class = observation_class
        # we read two parameters (default maximum capacity of the taxi and a length of one episode (i.e. 3000) from SUMO configuration file)
        self.max_capacity = self._read_max_capacity(self._cfg)
        self.sim_max_time = self._read_sim_max_time(self._cfg)
        self.current_step = 0
        self.avg_action = 0

        self.ridepool_controller = RidePoolController(self, self.max_capacity, self.reward_fn, conn, self.taxi_reservations_logger, verbose)

        conn.close()

        self.vehicles = dict()
        self.reward_range = (0, -np.inf)
        self.episode = 0
        self.metrics = []
        self.out_csv_name = out_csv_name
        self.observations = None
        self.rewards = None
        self.total_reward = 0

    def _start_simulation(self):
        sumo_cmd = [
            self._sumo_binary,
            "-c",
            self._cfg,
            
        ]
        
        if self.sumo_seed == "random":
            sumo_cmd.append("--random")
        else:
            sumo_cmd.extend(["--seed", str(self.sumo_seed)])
        if not self.sumo_warnings:
            sumo_cmd.append("--no-warnings")
        if self.additional_sumo_cmd is not None:
            sumo_cmd.extend(self.additional_sumo_cmd.split())
        if self.use_gui or self.render_mode is not None:
            sumo_cmd.extend(["--start", "--quit-on-end"])
            if self.render_mode == "rgb_array":
                sumo_cmd.extend(["--window-size", f"{self.virtual_display[0]},{self.virtual_display[1]}"])
                from pyvirtualdisplay.smartdisplay import SmartDisplay

                print("Creating a virtual display.")
                self.disp = SmartDisplay(size=self.virtual_display)
                self.disp.start()
                print("Virtual display started.")

        if LIBSUMO:
            traci.start(sumo_cmd)
            self.sumo = traci
        else:
            traci.start(sumo_cmd, label=self.label)
            self.sumo = traci.getConnection(self.label)

        if self.use_gui or self.render_mode is not None:
            self.sumo.gui.setSchema(traci.gui.DEFAULT_VIEW, "real world")

    def reset(self, seed: Optional[int] = None, **kwargs):
        """Reset the environment."""
        # print("reset sumo")
        super().reset(seed=seed, **kwargs)

        if self.episode != 0:
            self.close()
            # self.save_csv(self.out_csv_name, self.episode)
        self.episode += 1
        self.metrics = []
        self.total_reward = 0

        if seed is not None:
            self.sumo_seed = seed
        self._start_simulation()

        # reset logger
        self.taxi_reservations_logger.reset()

        self.ridepool_controller = RidePoolController(self, self.max_capacity, self.reward_fn, self.sumo, self.taxi_reservations_logger, self.verbose)

        self.vehicles = dict()
        self.current_step = 0
        self.avg_action = 0

        return self._compute_observations(), self._compute_info()

    def step(self, action: Union[dict, int]):
        """Apply the action(s) and then step the simulation for delta_time seconds.

        """
        self.current_step += 1
        self.avg_action += action
        
       
        for _ in range(self.delta_time):
            if action is None:
                # in this case, maximum occupancy will be set to 1
                self.ridepool_controller.dispatch(1)
            else:
                self.ridepool_controller.dispatch(action+1)
            self.sumo.simulationStep()

        observations = self._compute_observations()
        rewards = self._compute_rewards()
        self.total_reward += rewards
        terminated = False  # there are no 'terminal' states in this environment
        truncated = self.sim_step >= self.sim_max_time  # episode ends when sim_step >= max_steps
        info = self._compute_info()

        '''
        print("Observations: ", observations)
        print("Rewards: ", rewards)
        print("Terminated: ", terminated)
        print("Truncated: ", truncated)
        print("Info: ", info)
        '''

        return observations, rewards, terminated, truncated, info


    @property
    def sim_step(self) -> float:
        """Return current simulation second on SUMO."""
        return self.sumo.simulation.getTime()

    # function is not used
    def _sumo_step(self):
        self.sumo.simulationStep()

    def _compute_observations(self):
        return self.ridepool_controller.get_observation()

    def _compute_rewards(self):
        reward = self.ridepool_controller.compute_reward()
        return reward

    def _compute_info(self):
        info = {"step": self.sim_step}
        if self.add_system_info:
            info.update(self._get_system_info())
        if self.add_per_agent_info:
            info.update(self._get_per_agent_info())
        self.metrics.append(info.copy())
        return info

    # copied from traffic light example
    def _get_system_info(self):
        vehicles = self.sumo.vehicle.getIDList()
        speeds = [self.sumo.vehicle.getSpeed(vehicle) for vehicle in vehicles]
        waiting_times = [self.sumo.vehicle.getWaitingTime(vehicle) for vehicle in vehicles]
        return {
            # In SUMO, a vehicle is considered halting if its speed is below 0.1 m/s
            "system_total_stopped": sum(int(speed < 0.1) for speed in speeds),
            "system_total_waiting_time": sum(waiting_times),
            "system_mean_waiting_time": 0.0 if len(vehicles) == 0 else np.mean(waiting_times),
            "system_mean_speed": 0.0 if len(vehicles) == 0 else np.mean(speeds),
        }

    # copied from traffic light example
    def _get_per_agent_info(self):
        info = {}
        return info

    @property
    def action_space(self):
        """Return the action space.

        Only used in case of single-agent environment.
        """
        return self.ridepool_controller.action_space
    
    @property
    def observation_space(self):
        """Return the observation space.

        Only used in case of single-agent environment.
        """
        return self.ridepool_controller.observation_space
    
    def close(self):
        """Close the environment and stop the SUMO simulation."""
        if self.sumo is None:
            return

        self.taxi_reservations_logger.log(self.sim_step)

        if not LIBSUMO:
            traci.switch(self.label)
        traci.close()

        if self.disp is not None:
            self.disp.stop()
            self.disp = None

        self.sumo = None

    def __del__(self):
        """Close the environment and stop the SUMO simulation."""
        self.close()

