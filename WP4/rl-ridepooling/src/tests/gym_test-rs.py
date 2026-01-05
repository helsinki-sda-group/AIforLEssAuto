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
        taxi_reservations_logger=TaxiReservationsLogger(log_taxis, log_reservations, show_graph),
        observations_dim = cfg.env.obs_dim
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
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-c", "--config", type=str, required=True, help="Path to the main config file used to provide most arguments to the script.")
    parser.add_argument('-ne', '--num-envs', type=int, help="Number of SUMO environments that can be launched in parallel. (overwrites config file env.num_envs argument)")
    parser.add_argument('-post', '--postfix', type=str, help="Postfix string for the output directory name (will be appended to current date). If not provided, name of the config file will be used by default")
    parser.add_argument('-pre', '--prefix', type=str, help="Optional prefix string for the output directory name (will be before current date).")
    parser.add_argument('-ti', '--total-iters', type=int, help="Number of SUMO iterations to launch in total. (overwrites config file env.total_iters from config file)")
    parser.add_argument('--train-freq', help="Same as train_freq for DQN in stable baselines. Updates the model every train_freq steps")
    parser.add_argument('--delta', help="The length of one step of the RL algorithm in SUMO steps. The action is applied to a SUMO environment every delta steps")
    parser.add_argument('--gradient-steps', type=int, help="Number of gradient steps per update. -1 means num_envs. (overwrites config file dqn.gradient_steps)")
    parser.add_argument('--scaling-coef', type=float, help="Episode scaling coefficient in [0,1]. 0=no scaling, 1=full scaling. (overwrites hardcoded episodes_scaling_coeff)")
    parser.add_argument('--sumocfg', type=str, help="Path to SUMO config file. (overwrites config file env.sumocfg)")
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

    # if total-iters is specified, update cfg.env.total_iters
    if args.total_iters is not None:
        cfg.env.total_iters = args.total_iters

    if args.train_freq:
        try:
            cfg.dqn.train_freq = int(args.train_freq)
        except:
            cfg.dqn.train_freq = args.train_freq

    if args.delta:
        cfg.env.delta = int(args.delta)

    if args.gradient_steps is not None:
        cfg.dqn.gradient_steps = args.gradient_steps

    if args.sumocfg is not None:
        cfg.env.sumocfg = args.sumocfg

    # make dirs
    if args.prefix:
        dir_name = f'{args.prefix}_{now}_{dir_postfix}'
    else:
        dir_name = f'{now}_{dir_postfix}'
    OUTPUT_DIR = os.path.join('src', 'tests', 'output', dir_name)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print('Output folder set to', OUTPUT_DIR)

    # print config to output folder
    with open(os.path.join(OUTPUT_DIR, 'config.yaml'), 'w+') as cfg_copy:
        print(OmegaConf.to_yaml(cfg), file=cfg_copy)

    sys.stdout = open(os.path.join(OUTPUT_DIR, 'stdout.txt'), 'w+')

    # sumo steps per episode (e.g. 3000 sec)
    sumo_steps = cfg.env.timesteps 
    # delta - duration of decision step (e.g. 30 sec)
    delta = cfg.env.delta
    # rl decision steps per episode (e.g. 100)
    rl_steps = int(cfg.env.timesteps / delta)
    # number of episodes
    total_iters = cfg.env.total_iters

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
        vec_env = SubprocVecEnv([env_factory() for i in range(cfg.env.num_envs)])
        vec_env = VecMonitor(vec_env, train_log_dir)

        # ------- EVAL ENV ------- #
        eval_vec_env = SubprocVecEnv([env_factory()])  # always 1 eval env
        eval_vec_env = VecMonitor(eval_vec_env, eval_log_dir)
 
        # print("Creating model") 
        model = DQN(
            env=vec_env,
            policy=cfg.dqn.policy,
            learning_rate=cfg.dqn.learning_rate,
            learning_starts=cfg.dqn.learning_starts,
            buffer_size=cfg.dqn.buffer_size,
            train_freq=cfg.dqn.train_freq,
            gradient_steps=cfg.dqn.gradient_steps,
            target_update_interval=5000/delta,    # NB: decoupled from env number
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
            eval_freq=int(10_000/delta),        # adjust to your timesteps; 10k is a decent start
            n_eval_episodes=1,       # fixed batch for eval
            deterministic=True,
            render=False,
        )


        # total_timesteps = 30000 means that we use 10 simulation instances (episodes) for training if we use 3000 steps (3000 steps for one episode * 10 = 30000 steps)
        # for this example, I usually trained for 100-300 episodes but for debugging it is OK to start with smaller number of episodes
        
        # example for delta = 1 (sumo_steps = rl_steps): 
        #   rl_steps = 3000, total_iters = 120, total_timesteps = 3000 x 120 = 120 episodes and 3000 decisions per episode

        # two options for training with larger delta
        # (1) keep the total number of episodes
        #   delta = 30, rl_steps = 100, total_iters = 120, total_timesteps = 12000 = 120 episodes and 100 decisions per episode
        #   this will be delta time less samples available for RL algorithm
        #   NB: there may be a need to scale total_iters, especially for a large delta, to compensate for low number of training samples
        # (2) keep the total number of RL samples
        #   delta = 30, rl_steps = 100, (!)total_iters -> 120 * 30 = 3600, total_timesteps = 360000 = 3600 episodes and 100 decisions per episode
        #   compared to delta = 1, this will slow down training up to x delta times (more SUMO instances)
        # in practice, in can be intermediate option between (1) and (2)
        # for this, episodes_scaling_coeff is added
        #   in [0;1]
        #   0 - no scaling (option (1) above)
        #   1 - full scaling (option (2) above)
        episodes_scaling_coeff = args.scaling_coef if args.scaling_coef is not None else 0

        model.learn(total_timesteps=rl_steps*total_iters*(1 + episodes_scaling_coeff * (delta-1)), callback=eval_callback)
   
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
                obs, rewards, terminated, truncated, info = env.step(action)
                # print("Action:\t", action)
                accumulated_reward += rewards
                
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
                ep_reward += reward

            print(f"Random episode {i}: reward = {ep_reward}")
            all_rewards.append(ep_reward)

        env.close()

        print("\nRandom baseline:")
        print("Mean reward:", np.mean(all_rewards))
        print("Std:", np.std(all_rewards))
        print("All results:", all_rewards)


    print(f'Output saved to {OUTPUT_DIR}')
    sys.stdout.flush()
    
    os._exit(0)



