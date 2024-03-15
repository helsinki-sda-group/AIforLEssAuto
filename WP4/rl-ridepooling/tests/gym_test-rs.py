import gymnasium as gym
from gymnasium.utils.env_checker import check_env
import multiprocessing as mp

import sys
import time

sys.path.append('.')

import os

from stable_baselines3.dqn.dqn import DQN
from stable_baselines3.common.vec_env import VecMonitor

import numpy as np
import matplotlib.pyplot as plt
import random

from stable_baselines3.common.monitor import Monitor


import sumo_rl_rs
import sys
import itertools

from stable_baselines3.common.vec_env import SubprocVecEnv
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3.common.callbacks import EventCallback

# step of policy applying (delta=1 means one simulation iteration)
delta = 1
NUM_ENVS = 4

# these functions implement a number of baseline policies
# when a fixed action is applied to predefined windows

def make_env():
    def _init():
        env = gym.make(
            "sumo-rl-rs-v0",
            #num_seconds=100,
            use_gui=False,
            delta_time=delta,
            cfg_file="nets/ridepooling/MySUMO.sumocfg",
            additional_sumo_cmd="--log sumolog.txt",
            sumo_seed=4220,
            verbose=True,
            #route_file="nets/single-intersection/single-intersection.rou.xml",
        )
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
    env = gym.make(
        "sumo-rl-rs-v0",
        #num_seconds=100,
        use_gui=False,
        delta_time=delta,
        cfg_file="nets/ridepooling/MySUMO.sumocfg",
        additional_sumo_cmd="--log sumolog.txt",
        sumo_seed=4220,
        verbose=False,
        #route_file="nets/single-intersection/single-intersection.rou.xml",
    )

    env.reset()
    # print("Num periods: ", num_periods)
    policies = generatePolicies(num_periods, max_action)

    for policy in policies:
        accumulated_reward = 0
        deltaE = int(timesteps/num_periods)
        for period in range(0, num_periods):
        
            for i in range(period * deltaE, (period+1) * deltaE):
                # print("Step: ", i)
                action = policy[period]
                # print("Action: ", action)
                obs, rewards, terminated, truncated, info = env.step(action)
                accumulated_reward += rewards
        print("Policy: ", policy, " accumulated reward: ", accumulated_reward)
        env.reset()

    env.close()

if __name__ == "__main__":
    mp.set_start_method("spawn")
    sys.stdout = open('stdout.txt', 'w')

    # to test RL training, we do not need launch baselines so this flag is false
    TEST_BASELINE = False

    if TEST_BASELINE:
        test_exhaustive(3000,3,1)
    
    # if train is True, we train the model and save it to zip archive
    TRAIN = True
    # for test regime, we load the model from zip archive and evaluate it 
    TEST = True

    train_log_dir = os.path.join('nets', 'ridepooling', 'logs', 'train')
    test_log_dir = os.path.join('nets', 'ridepooling', 'logs', 'test')
    os.makedirs(train_log_dir, exist_ok=True)
    os.makedirs(test_log_dir, exist_ok=True)

    if TRAIN:   
        # wrapping it with monitor
        # Logs will be saved in log_dir/monitor.csv

        # # creating Gym environment
        env = gym.make(
            "sumo-rl-rs-v0",
            #num_seconds=100,
            use_gui=False,
            delta_time=delta,
            cfg_file="nets/ridepooling/MySUMO.sumocfg",
            additional_sumo_cmd="--log sumolog.txt",
            sumo_seed=4220,
            verbose=False,
        )
    

        start_time = time.time()

        vec_env = SubprocVecEnv([make_env() for i in range(NUM_ENVS)])
        vec_env = VecMonitor(vec_env, train_log_dir)
 
        # print("Creating model") 
        model = DQN(
            env=vec_env,
            policy="MlpPolicy",
            learning_rate=0.001,
            learning_starts=1,
            train_freq=1,
            gradient_steps=-1,
            target_update_interval=NUM_ENVS,
            exploration_fraction=0.1,
            exploration_initial_eps=0.05,
            exploration_final_eps=0.01,
            verbose=1,
        )




        # timesteps = 30000 means that we use 10 simulation instances (episodes) for training (3000 steps for one episode * 10 = 30000 steps)
        # for this example, I usually trained for 100-300 episodes but for debugging it is OK to start with smaller number of episodes
        model.learn(total_timesteps=30000)
   
        model.save("ridepooling_DQN")

        vec_env.close()
        
        end_time = time.time()

        with open('time.txt', 'w') as f:
            print(f"Training time: {end_time - start_time} seconds", file=f)


    if TEST:

        # creating Gym environment
        env = gym.make(
            "sumo-rl-rs-v0",
            #num_seconds=100,
            use_gui=False,
            delta_time=delta,
            cfg_file="nets/ridepooling/MySUMO.sumocfg",
            additional_sumo_cmd="--log sumolog.txt",
            sumo_seed=4220,
            verbose=False,
        )

        env = Monitor(env, test_log_dir)
        
        model = DQN.load("ridepooling_DQN", env=env)

        # number of test instances
        num_tests = 5

        for i in range(0, num_tests):
            print("Test ", str(i+1))

            obs, info = env.reset()
        
            accumulated_reward = 0
            # 3000 is a number of iterations which during the training is read from nets\ridepooling\MySUMO.sumocfg
            for step in range(0, 3000):
                # print("Step: ", step)
                action, _states = model.predict(obs)
                obs, rewards, terminated, truncated, info = env.step(action)
                # print("Action:\t", action)
                accumulated_reward += rewards
                
            print("Accumulated reward, DQN test ", str(i+1), ":", accumulated_reward)
    
        env.close()
    
    sys.stdout.close()
    



