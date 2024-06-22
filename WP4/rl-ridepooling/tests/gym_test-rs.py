import gymnasium as gym
from gymnasium.utils.env_checker import check_env

import sys

# sys.path.append("C:\\Users\\bochenin\\RL project\\materials\\ridesharing\\sumo-rs-gym\\sumo-rl-main")
sys.path.append("C:\\Users\\bochenin\\RL project\\materials\\ridesharing\\sumo-rs-gym\\\sumo-rl-main-paper\\sumo-rl-main")
sys.path.append("C:\\Program Files (x86)\\Eclipse\\Sumo\\tools\\libsumo")
sys.path.append("C:\\users\\bochenin\\anaconda3\\lib\\site-packages\\libsumo")

#print(sys.path)

import os

from stable_baselines3.dqn.dqn import DQN
from sumo_rl_rs import SumoEnvironment

import numpy as np
import matplotlib.pyplot as plt
import random

from stable_baselines3.common.monitor import Monitor


if "SUMO_HOME" in os.environ:
    os.add_dll_directory("C:\\users\\bochenin\\anaconda3\\lib\\site-packages\\libsumo")



import sumo_rl_rs
import sys
import itertools

from stable_baselines3.common.evaluation import evaluate_policy

# step of policy applying (delta=1 means one simulation iteration)
delta = 1

# these functions implement a number of baseline policies
# when a fixed action is applied to predefined windows

def test_env_fixed(timesteps, action):
    
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
    # check_env(env.unwrapped, skip_render_check=True)
    accumulated_reward = 0
    for i in range(0,int(timesteps/delta)):
        obs, rewards, terminated, truncated, info = env.step(action)
        accumulated_reward += rewards
    print("Accumulated reward, max_capacity = ", action, ": ", accumulated_reward)

    env.close()

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

def test_env_random(timesteps, max_action=1):
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
    # check_env(env.unwrapped, skip_render_check=True)
    accumulated_reward = 0
    for i in range(0,int(timesteps/delta)):
        obs, rewards, terminated, truncated, info = env.step(random.randint(0, max_action))
        accumulated_reward += rewards
    print("Accumulated reward, random action: ", accumulated_reward)

    env.close()

def test_varying(timesteps, border1, border2):

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
    accumulated_reward = 0
    for i in range(0,int(border1/delta)):
        obs, rewards, terminated, truncated, info = env.step(0)
        accumulated_reward += rewards

    for i in range(int(border1/delta),int(border2/delta)):
        obs, rewards, terminated, truncated, info = env.step(1)
        accumulated_reward += rewards

    for i in range(int(border2/delta),int(timesteps/delta)):
        obs, rewards, terminated, truncated, info = env.step(0)
        accumulated_reward += rewards

    print("Accumulated reward, borders (", border1, "," , border2 , "): ", accumulated_reward)
    env.close()

if __name__ == "__main__":
    sys.stdout = open('stdout.txt', 'w')

    # to test RL training, we do not need launch baselines so this flag is false
    TEST_BASELINE = False

    if TEST_BASELINE:
        # borders1 = [510, 520, 530, 540, 550, 560, 570, 580, 590, 600]
        # borders2 = [1700, 1800] 
        # for border1 in borders1:
        #     for border2 in borders2:
        #         test_varying(3000, border1, border2)
        # test_env_fixed(3000, 0)
        # test_env_fixed(3000, 1)
        # test_env_fixed(3000, 2)
        # test_env_fixed(3000, 3)
        # test_env_fixed(3000, 4)
        # test_env_fixed(3000, 5)
        # test_varying(3000, 500, 2000)
        # test_env_random(3000)
        test_exhaustive(3000,3,1)
    
    # if train is True, we train the model and save it to zip archive
    TRAIN = True
    # for test regime, we load the model from zip archive and evaluate it 
    TEST = True

    log_dir = "C:\\Users\\bochenin\\RL project\\materials\\ridesharing\\sumo-rs-gym\\sumo-rl-main\\nets\\ridepooling\\logs"
    os.makedirs(log_dir, exist_ok=True)

    
    if TRAIN:   
        # wrapping it with monitor
        # Logs will be saved in log_dir/monitor.csv

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

        env = Monitor(env, log_dir)
 

        # print("Creating model") 
        model = DQN(
            env=env,
            policy="MlpPolicy",
            learning_rate=0.001,
            learning_starts=1,
            train_freq=1,
            target_update_interval=1,
            exploration_fraction=0.1,
            exploration_initial_eps=0.05,
            exploration_final_eps=0.01,
            verbose=0,
        )

        # timesteps = 30000 means that we use 10 simulation instances (episodes) for training (3000 steps for one episode * 10 = 30000 steps)
        # for this example, I usually trained for 100-300 episodes but for debugging it is OK to start with smaller number of episodes
        model.learn(total_timesteps=30000)
   
        model.save("ridepooling_DQN")

        env.close()


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

        env = Monitor(env, log_dir)
        
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
    



