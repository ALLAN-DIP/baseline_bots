__authors__ = "Wichayaporn Wongkamjan"
__email__ = "wwongkam@umd.edu"

import sys

sys.path.append("..")
sys.path.append("../..")
sys.path.append("../../..")
sys.path.append("../../../dipnet_press")

import random
from abc import ABC, abstractmethod
from typing import List

from diplomacy import Game, Message
from diplomacy_research.players.benchmark_player import DipNetRLPlayer
from DiplomacyEnv import DiplomacyEnv
from pytorch_DRL.MAA2C import MAA2C
from tornado import gen
from utils import MessagesData, OrdersData, get_order_tokens

from baseline_bots.bots.baseline_bot import BaselineMsgRoundBot

EPISODES_BEFORE_TRAIN = 2
# roll out n steps
ROLL_OUT_N_STEPS = 20
# only remember the latest 2 ROLL_OUT_N_STEPS
MEMORY_CAPACITY = 10 * ROLL_OUT_N_STEPS
# only use the latest 2 ROLL_OUT_N_STEPS for training A2C
BATCH_SIZE = 2 * ROLL_OUT_N_STEPS

REWARD_DISCOUNTED_GAMMA = 0.99
ENTROPY_REG = 0.00

DONE_PENALTY = 0

CRITIC_LOSS = "mse"
MAX_GRAD_NORM = None

EPSILON_START = 0.99
EPSILON_END = 0.05
EPSILON_DECAY = 500

RANDOM_SEED = 1000
N_AGENTS = 7


class RLOrderBot(BaselineMsgRoundBot, ABC):
    """Abstract Base Class for RL derivitive bots"""

    def __init__(
        self, power_name: str, game: Game, env: DiplomacyEnv, total_msg_rounds=3
    ) -> None:
        super().__init__(power_name, game, total_msg_rounds)
        self.brain = DipNetRLPlayer()
        self.env = env
        state_dim = env.observation_space.shape[0]
        if len(env.action_space.shape) > 1:
            action_dim = env.action_space.shape[0]
        else:
            action_dim = env.action_space.n
        self.maa2c = MAA2C(
            env=env,
            n_agents=N_AGENTS,
            state_dim=state_dim,
            action_dim=action_dim,
            memory_capacity=MEMORY_CAPACITY,
            batch_size=BATCH_SIZE,
            entropy_reg=ENTROPY_REG,
            done_penalty=DONE_PENALTY,
            roll_out_n_steps=ROLL_OUT_N_STEPS,
            reward_gamma=REWARD_DISCOUNTED_GAMMA,
            epsilon_start=EPSILON_START,
            epsilon_end=EPSILON_END,
            epsilon_decay=EPSILON_DECAY,
            max_grad_norm=MAX_GRAD_NORM,
            episodes_before_train=EPISODES_BEFORE_TRAIN,
            training_strategy="centralized",
            critic_loss=CRITIC_LOSS,
            actor_parameter_sharing=True,
            critic_parameter_sharing=True,
        )

    def load_model(self, actor_path, critic_path):
        self.maa2c.load_model(actor_path, critic_path)

    def gen_messages(self, rcvd_messages: List[Message]) -> MessagesData:
        return None

    @gen.coroutine
    def gen_orders(self) -> OrdersData:
        self.orders = OrdersData()
        orders = yield self.brain.get_orders(self.game, self.power_name)
        self.orders.add_orders(orders, overwrite=True)
        return self.orders.get_list_of_orders()
