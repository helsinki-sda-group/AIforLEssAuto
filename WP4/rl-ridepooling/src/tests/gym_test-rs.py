import gymnasium as gym
from gymnasium.utils.env_checker import check_env
import multiprocessing as mp

import sys
import time

sys.path.append('./src')

import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

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
from stable_baselines3.common.callbacks import EvalCallback

import datetime

from omegaconf import OmegaConf
import argparse
from pathlib import Path

from typing import cast
from sumo_rl_rs.environment import SumoEnvironment

# these functions implement a number of baseline policies
# when a fixed action is applied to predefined windows

def make_env(rank: int = 0, policy = None):
    """
    Returns the SUMO gym environment. The policy argument is optional and can be used when testing baselines
    """
    sumo_log_file = os.path.join(OUTPUT_DIR, f'sumolog_rank{rank}.txt')

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
        sumo_seed=cfg.env.sumo_seed + rank,
        verbose=cfg.env.verbose,
        taxi_reservations_logger=TaxiReservationsLogger(log_taxis, log_reservations, show_graph),
        observations_dim = cfg.env.obs_dim
        #route_file="nets/single-intersection/single-intersection.rou.xml",
    )
    return env

def env_factory(rank: int, base_seed: int):
    def _init():
        env = make_env(rank)
        env.reset(seed=base_seed + rank)
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

    env_unwrapped = cast(SumoEnvironment, env.unwrapped)

    for policy in policies:
        accumulated_reward = 0.0
        deltaE = int(timesteps/num_periods)
        env_unwrapped.taxi_reservations_logger.output_path = os.path.join(OUTPUT_DIR, 'baselines' ,f'{now}_{policy}')
        for period in range(0, num_periods):
        
            for i in range(period * deltaE, (period+1) * deltaE):
                # print("Step: ", i)
                action = policy[period]
                # print("Action: ", action)
                obs, reward, terminated, truncated, info = env.step(action)
                accumulated_reward += float(reward)
        print("Policy: ", policy, " accumulated reward: ", accumulated_reward)
        env.reset()

    # Set output path to None to prevent logging empty graph
    env_unwrapped.taxi_reservations_logger.output_path = None
    env.close()

def curr_datetime():
    return datetime.datetime.now().strftime('%Y-%m-%dT%H-%M-%S')

if __name__ == "__main__":
    mp.set_start_method("spawn")
    
    # get current timestep
    now = curr_datetime()

    # parser args
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-c", "--config", type=str, required=True, help="Path to the main config file used to provide most arguments to the script.")
    parser.add_argument('-ne', '--num-envs', type=int, help="Number of SUMO environments that can be launched in parallel. (overwrites config file env.num_envs argument)")
    parser.add_argument('-p', '--postfix', type=str, help="Postfix string for the output directory name (will be appended to current date). If not provided, name of the config file will be used by default")
    parser.add_argument('-be', '--basic-episodes', type=int, help="Number of episodes for delta =1 (overwrites config file env.basic_episodes from config file)")
    args = parser.parse_args()
    cfg_path = args.config.strip()
    cfg = OmegaConf.load(cfg_path)

    # if num-envs is specified, update cfg.env.num_envs
    if args.num_envs is not None:
        cfg.env.num_envs = args.num_envs

    # determine postfix for the directory name
    if args.postfix is not None:
        dir_postfix = args.postfix
    else:
        dir_postfix = Path(cfg_path).stem

    # if basic episodes count is specified, update cfg.env.basic_episodes
    if args.basic_episodes is not None:
        cfg.env.basic_episodes = args.basic_episodes

    # make dirs
    OUTPUT_DIR = os.path.join('src', 'tests', 'output', f'{now}_{dir_postfix}')
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print('Output folder set to', OUTPUT_DIR)

    # print config to output folder
    with open(os.path.join(OUTPUT_DIR, 'config.yaml'), 'w+') as cfg_copy:
        print(OmegaConf.to_yaml(cfg), file=cfg_copy)

    sys.stdout = open(os.path.join(OUTPUT_DIR, 'stdout.txt'), 'w+')

    # sumo steps per episode (e.g. 3000 sec)
    sumo_steps = cfg.env.sumo_steps 
    # number of episodes
    basic_episodes = cfg.env.basic_episodes
    # scaling coefficient for the number of episodes
    episodes_scaling_coeff = cfg.env.episodes_scaling_coeff
    # delta - duration of decision step (e.g. 30 sec)
    delta = cfg.env.delta
    # number of episodes
    episodes = basic_episodes*(1 + episodes_scaling_coeff * (delta-1))
    # rl decision steps per episode (e.g. 100)
    rl_steps = int(sumo_steps / delta)

    base_seed = cfg.env.seed
    random.seed(base_seed)
    np.random.seed(base_seed)


    # baseline with static scheduling (exhaustive search for large number of decision steps)
    if cfg.test_baseline:
        test_exhaustive(rl_steps,cfg.baseline.num_periods,cfg.baseline.num_actions)
   
    # trained model is saved to ridepooling_DQN.zip
    # during training, the model is also periodically evaluated in greedy (deterministic) regime
    if cfg.train:
        train_log_dir = os.path.join(OUTPUT_DIR, 'train')
        eval_log_dir = os.path.join(OUTPUT_DIR, 'eval')
        os.makedirs(train_log_dir, exist_ok=True)
        os.makedirs(eval_log_dir, exist_ok=True)

        start_time = time.time()

        # ------- TRAIN ENV ------- #
        vec_env = SubprocVecEnv([env_factory(rank=i, base_seed=base_seed) for i in range(cfg.env.num_envs)])
        vec_env = VecMonitor(vec_env, train_log_dir)

        # ------- EVAL ENV ------- #
        eval_vec_env = SubprocVecEnv([env_factory(rank = 0, base_seed=10_000)])  # always 1 eval env
        eval_vec_env = VecMonitor(eval_vec_env, eval_log_dir)
 
        # print("Creating model") 
        model = DQN(
            env=vec_env,
            policy=cfg.dqn.policy,
            learning_rate=cfg.dqn.learning_rate,
            learning_starts=cfg.dqn.learning_starts,
            buffer_size=cfg.dqn.buffer_size,
            # after every train_freq calls to env.step(), call the learner
            train_freq=cfg.dqn.train_freq,
            # in vectorized environments, 
            # one call to env.step() produces n_env transitions
            # we scale number of gradient updates to keep 
            # the same ratio of gradient steps to transitions
            gradient_steps=cfg.dqn.gradient_steps * cfg.env.num_envs,
            # in environment steps (global), does not depend on num_env
            # target_update_interval cannot be smaller than 100 (for the stability)
            target_update_interval=max (100, int(cfg.dqn.target_update_interval/delta)),    
            exploration_fraction=cfg.dqn.exploration_fraction,
            exploration_initial_eps=cfg.dqn.exploration_initial_eps,
            exploration_final_eps=cfg.dqn.exploration_final_eps,
            verbose=cfg.dqn.verbose,
        )

        # -------- EVAL CALLBACK --------
        eval_callback = EvalCallback(
            eval_vec_env,
            best_model_save_path=os.path.join(OUTPUT_DIR, "best_model"),
            log_path=eval_log_dir,
            # evaluation will be triggered after the same number of sumo_steps for all delta
            # each env.step() num_envs transitions is added 
            # so we need to scale down eval_freq by num_env as well
            eval_freq=int(cfg.eval.eval_freq/delta/cfg.env.num_envs),        
            n_eval_episodes=1,       # fixed batch for eval
            deterministic=True,
            render=False,
        )

        # total_timesteps in model.learn(total_timesteps) are _RL steps_ (not SUMO steps) 
                
        # example for delta = 1 (sumo_steps = rl_steps): 
        #   sumo_steps = 3000, delta = 1, rl_steps = 3000, basic_episodes = 120
        #   total_timesteps = 3000 x 120 (3000 rl_steps per episode, 120 episodes)

        # for delta = 1, basic_episodes is usually in [100;300]

        # two bordeline options for training with delta > 1 (e.g. delta = 30)

        # (1) keep the total number of episodes: episodes = basic_episodes
        #   sumo_steps = 3000, delta = 30, basic_episodes = 120
        #   rl_steps = 3000 / 30 = 100, episodes = 120
        #   total_timesteps = 100 x 120 (100 rl_steps per episode, 120 episodes) 
        #   delta time less samples available for RL algorithm
        
        # (2) keep the total number of RL samples
        #   sumo_steps = 3000, delta = 30, basic_episodes = 120
        #   rl_steps = 100, episodes = 120 * 30 = 3600
        #   total_timesteps = 100 x 3600 (100 rl_steps per episode, 3600 episodes) 
        #   training will slow down up to delta times (more SUMO instances)

        # episodes_scaling_coeff in [0;1] controls the number of episodes
        # compared to basic_episodes
        #   0 - no scaling (option (1) above)
        #   1 - full scaling (option (2) above)


        # according to notations in the paper:
        # rl_steps = I / Delta, total_iters = E_1, so rl_steps * total_iters = K_1/Delta (as K_1 = E_1 * I)
        # this is total number of env.steps() for all vectorized environments
        model.learn(total_timesteps=rl_steps*episodes, callback=eval_callback)
   
        model.save(os.path.join(OUTPUT_DIR, 'ridepooling_DQN'))

        vec_env.close()
        eval_vec_env.close()
        
        end_time = time.time()

        with open(os.path.join(OUTPUT_DIR, 'time.txt'), 'w+') as time_f:
            print(f"Training time: {end_time - start_time} seconds", file=time_f)

    # for test regime, we load the model from zip archive and evaluate it 
    if cfg.test:
        test_log_dir = os.path.join(OUTPUT_DIR, 'test')
        os.makedirs(test_log_dir, exist_ok=True)

        env = Monitor(make_env(), test_log_dir)

        # model = DQN.load("src/tests/output/eval2/ridepooling_DQN.zip", env=env) 
       
        # model = DQN.load("src/tests/output/eval2/best_model/best_model.zip", env=env)
       
        model = DQN.load(os.path.join(OUTPUT_DIR, 'ridepooling_DQN'), env=env)

        # number of test instances
        num_tests = cfg.tests.num_tests

        for i in range(0, num_tests):
            print("Test ", str(i+1))

            obs, info = env.reset()
        
            accumulated_reward = 0
            for step in range(0, rl_steps):
                # print("Step: ", step)
                action, _states = model.predict(obs)
                obs, reward, terminated, truncated, info = env.step(action)
                # print("Action:\t", action)
                accumulated_reward += float(reward)
                
            print("Accumulated reward, DQN test ", str(i+1), ":", accumulated_reward)
    
        env.close()
    
    # test with random actions
    if cfg.test_random:
        random_log_dir = os.path.join(OUTPUT_DIR, 'test_random')  
        os.makedirs(random_log_dir, exist_ok=True)
        # Make the environment (use the same env_factory as in gym_test-rs.py)
        env = Monitor(make_env(), random_log_dir)

        num_tests = 10      # number of random episodes to run
        all_rewards = []

        for i in range(num_tests):
            obs, info = env.reset()
            done = False
            truncated = False
            ep_reward = 0.0

            while not (done or truncated):
                action = env.action_space.sample()     # <-- COMPLETELY RANDOM ACTION
                obs, reward, done, truncated, info = env.step(action)
                ep_reward += float(reward)

            print(f"Random episode {i}: reward = {ep_reward}")
            all_rewards.append(ep_reward)

        env.close()

        print("\nRandom baseline:")
        print("Mean reward:", np.mean(all_rewards))
        print("Std:", np.std(all_rewards))
        print("All results:", all_rewards)


    print(f'Output saved to {OUTPUT_DIR}')
    sys.stdout.close()
    



