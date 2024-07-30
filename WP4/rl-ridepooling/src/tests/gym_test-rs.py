import gymnasium as gym
from gymnasium.utils.env_checker import check_env
import multiprocessing as mp

import sys
import time

sys.path.append('./src')

import os

from stable_baselines3.dqn.dqn import DQN
from stable_baselines3.common.vec_env import VecMonitor

import numpy as np
import matplotlib.pyplot as plt
import random

from stable_baselines3.common.monitor import Monitor


from sumo_rl_rs.environment.taxi_reservations_logger import TaxiReservationsLogger
import sys
import itertools

from stable_baselines3.common.vec_env import SubprocVecEnv
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3.common.callbacks import EventCallback
import datetime

from omegaconf import OmegaConf
import argparse
from pathlib import Path

# these functions implement a number of baseline policies
# when a fixed action is applied to predefined windows

def make_env(policy = None):
    """
    Returns the SUMO gym environment. The policy argument is optional and can be used when testing baselines
    """
    sumo_log_file = os.path.join(OUTPUT_DIR, 'sumolog.txt')

    # Get the taxi_logger configuration with default values
    cfg_taxi_logger = cfg.env.get('taxi_reservations_logger', {})
    log_taxis = cfg_taxi_logger.get('log_taxis', False)
    log_reservations = cfg_taxi_logger.get('log_reservations', False)
    show_graph = cfg_taxi_logger.get('show_graph', False)

    env = gym.make(
        "sumo-rl-rs-v0",
        #num_seconds=100,
        use_gui=cfg.env.use_gui,
        delta_time=cfg.env.delta,
        cfg_file=cfg.env.sumocfg,
        additional_sumo_cmd=f"--log {sumo_log_file}",
        sumo_seed=cfg.env.sumo_seed,
        verbose=cfg.env.verbose,
        taxi_reservations_logger=TaxiReservationsLogger(log_taxis, log_reservations, show_graph)
        #route_file="nets/single-intersection/single-intersection.rou.xml",
    )
    return env

def env_factory():
    def _init():
        env = make_env()
        env.reset()
        return env

    return _init

def generatePolicies(num_periods, max_action):
    actions = []
    for i in range(0, max_action+1):
        actions.append(i)
    policies = [item for item in itertools.product(actions, repeat=num_periods)]
    return policies


def test_exhaustive(timesteps, num_periods=5, max_action=1):
    env = make_env()
    env.reset()
    # print("Num periods: ", num_periods)
    policies = generatePolicies(num_periods, max_action)

    for policy in policies:
        accumulated_reward = 0
        deltaE = int(timesteps/num_periods)
        env.unwrapped.taxi_reservations_logger.output_path = os.path.join(OUTPUT_DIR, 'baselines' ,f'{now}_{policy}')
        for period in range(0, num_periods):
        
            for i in range(period * deltaE, (period+1) * deltaE):
                # print("Step: ", i)
                action = policy[period]
                # print("Action: ", action)
                obs, rewards, terminated, truncated, info = env.step(action)
                accumulated_reward += rewards
        print("Policy: ", policy, " accumulated reward: ", accumulated_reward)
        env.reset()

    # Set output path to None to prevent logging empty graph
    env.unwrapped.taxi_reservations_logger.output_path = None
    env.close()

def curr_datetime():
    return datetime.datetime.now().strftime('%Y-%m-%dT%H-%M-%S')

if __name__ == "__main__":
    mp.set_start_method("spawn")
    
    # get current timestep
    now = curr_datetime()

    # parser args
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", type=str, required=True)
    args = parser.parse_args()
    cfg_path = args.config.strip()
    cfg = OmegaConf.load(cfg_path)

    # make dirs
    OUTPUT_DIR = os.path.join('nets', 'ridepooling', 'output', f'{now}_{Path(cfg_path).stem}')
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # copy config to output folder
    with open(os.path.join(OUTPUT_DIR, 'config.yaml'), 'w+') as cfg_copy:
        print(OmegaConf.to_yaml(cfg), file=cfg_copy)

    sys.stdout = open(os.path.join(OUTPUT_DIR, 'stdout.txt'), 'w+')

    # this is a number of iterations which during the training is read from nets\ridepooling\MySUMO.sumocfg
    timesteps = cfg.env.timesteps
    total_iters = cfg.env.total_iters

    # to test RL training, we do not need launch baselines so this flag is false
    if cfg.test_baseline:
        test_exhaustive(timesteps,cfg.baseline.num_periods,cfg.baseline.num_actions)
   
    # Logs will be saved in train/monitor.csv and test/monitor.csv
    train_log_dir = os.path.join(OUTPUT_DIR, 'train')
    test_log_dir = os.path.join(OUTPUT_DIR, 'test')
    os.makedirs(train_log_dir, exist_ok=True)
    os.makedirs(test_log_dir, exist_ok=True)

    # if train is True, we train the model and save it to zip archive
    if cfg.train:
        # wrapping it with monitor  

        start_time = time.time()

        vec_env = SubprocVecEnv([env_factory() for i in range(cfg.env.num_envs)])
        vec_env = VecMonitor(vec_env, train_log_dir)
 
        # print("Creating model") 
        model = DQN(
            env=vec_env,
            policy=cfg.dqn.policy,
            learning_rate=cfg.dqn.learning_rate,
            learning_starts=cfg.dqn.learning_starts,
            train_freq=cfg.dqn.train_freq,
            gradient_steps=cfg.dqn.gradient_steps,
            target_update_interval=cfg.env.num_envs,
            exploration_fraction=cfg.dqn.exploration_fraction,
            exploration_initial_eps=cfg.dqn.exploration_initial_eps,
            exploration_final_eps=cfg.dqn.exploration_final_eps,
            verbose=cfg.dqn.verbose,
        )

        # total_timesteps = 30000 means that we use 10 simulation instances (episodes) for training if we use 3000 steps (3000 steps for one episode * 10 = 30000 steps)
        # for this example, I usually trained for 100-300 episodes but for debugging it is OK to start with smaller number of episodes
        model.learn(total_timesteps=timesteps*total_iters)
   
        model.save(os.path.join(OUTPUT_DIR, 'ridepooling_DQN'))

        vec_env.close()
        
        end_time = time.time()

        with open(os.path.join(OUTPUT_DIR, 'time.txt'), 'w+') as time_f:
            print(f"Training time: {end_time - start_time} seconds", file=time_f)

    # for test regime, we load the model from zip archive and evaluate it 
    if cfg.test:
        env = Monitor(make_env(), test_log_dir)
        
        model = DQN.load(os.path.join(OUTPUT_DIR, 'ridepooling_DQN'), env=env)

        # number of test instances
        num_tests = cfg.tests.num_tests

        for i in range(0, num_tests):
            print("Test ", str(i+1))

            obs, info = env.reset()
        
            accumulated_reward = 0
            for step in range(0, timesteps):
                # print("Step: ", step)
                action, _states = model.predict(obs)
                obs, rewards, terminated, truncated, info = env.step(action)
                # print("Action:\t", action)
                accumulated_reward += rewards
                
            print("Accumulated reward, DQN test ", str(i+1), ":", accumulated_reward)
    
        env.close()
    
    print(f'Output saved to {OUTPUT_DIR}')
    sys.stdout.close()
    



