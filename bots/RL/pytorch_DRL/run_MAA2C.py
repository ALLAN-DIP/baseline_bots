
from MAA2C import MAA2C
from common.utils import ma_agg_double_list

import sys
import numpy as np
import matplotlib.pyplot as plt

import random

import ray
from ray.rllib.env.multi_agent_env import MultiAgentEnv, make_multi_agent
# from ray.rllib.examples.env.multi_agent import MultiAgentCartPole


MAX_EPISODES = 5000
EPISODES_BEFORE_TRAIN = 10
EVAL_EPISODES = 10
EVAL_INTERVAL = 100

# roll out n steps
ROLL_OUT_N_STEPS = 10
# only remember the latest ROLL_OUT_N_STEPS
MEMORY_CAPACITY = ROLL_OUT_N_STEPS
# only use the latest ROLL_OUT_N_STEPS for training A2C
BATCH_SIZE = ROLL_OUT_N_STEPS

REWARD_DISCOUNTED_GAMMA = 0.99
ENTROPY_REG = 0.00
#
DONE_PENALTY = -10.

CRITIC_LOSS = "mse"
MAX_GRAD_NORM = None

EPSILON_START = 0.99
EPSILON_END = 0.05
EPSILON_DECAY = 500

RANDOM_SEED = 2017
N_AGENTS = 2

def run(env_id="CartPole-v0"):
    env_class = make_multi_agent("CartPole-v0")
    env = env_class({"num_agents": 2})
    # env.seed(RANDOM_SEED)
    env_eval_class = make_multi_agent("CartPole-v0")
    env_eval = env_eval_class({"num_agents": 2})
    # env_eval.seed(RANDOM_SEED)
    state_dim = env.observation_space.shape[0]
    if len(env.action_space.shape) > 1:
        action_dim = env.action_space.shape[0]
    else:
        action_dim = env.action_space.n

    maa2c = MAA2C(env=env, n_agents=N_AGENTS, 
              state_dim=state_dim, action_dim=action_dim, memory_capacity=MEMORY_CAPACITY,
              batch_size=BATCH_SIZE, entropy_reg=ENTROPY_REG,
              done_penalty=DONE_PENALTY, roll_out_n_steps=ROLL_OUT_N_STEPS,
              reward_gamma=REWARD_DISCOUNTED_GAMMA,
              epsilon_start=EPSILON_START, epsilon_end=EPSILON_END,
              epsilon_decay=EPSILON_DECAY, max_grad_norm=MAX_GRAD_NORM,
              episodes_before_train=EPISODES_BEFORE_TRAIN, training_strategy="centralized",
              critic_loss=CRITIC_LOSS, actor_parameter_sharing=True, critic_parameter_sharing=True)

    episodes =[]
    eval_rewards =[]
    while maa2c.n_episodes < MAX_EPISODES:
        maa2c.interact()
        if maa2c.n_episodes >= EPISODES_BEFORE_TRAIN:
            maa2c.train()
        if maa2c.episode_done and ((maa2c.n_episodes+1)%EVAL_INTERVAL == 0):
            rewards, _ = maa2c.evaluation(env_eval, EVAL_EPISODES)
            rewards_mu, rewards_std = ma_agg_double_list(rewards)
            for agent_id in range (N_AGENTS):
                print("Episode %d, Agent %d, Average Reward %.2f" % (maa2c.n_episodes+1, agent_id, rewards_mu[agent_id]))
            episodes.append(maa2c.n_episodes+1)
            eval_rewards.append(rewards_mu)

    episodes = np.array(episodes)
    eval_rewards = np.array(eval_rewards)
    np.savetxt("./output/%s_maa2c_episodes.txt"%env_id, episodes)
    np.savetxt("./output/%s_maa2c_eval_rewards.txt"%env_id, eval_rewards)

    plt.figure()
    for agent_id in range (N_AGENTS):
        plt.plot(episodes, eval_rewards[:,agent_id], label='agent '+str(agent_id))
    plt.title("%s"%env_id)
    plt.xlabel("Episode")
    plt.ylabel("Average Reward")
    plt.legend(["MAA2C"])
    plt.savefig("./output/%s_maa2c.png"%env_id)


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        run(sys.argv[1])
    else:
        run()
