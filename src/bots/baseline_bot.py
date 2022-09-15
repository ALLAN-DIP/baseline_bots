"""Abstract base classes for baseline bots"""

__authors__ = ["Sander Schulhoff", "Kartik Shenoy"]
__email__ = "sanderschulhoff@gmail.com"

import sys
sys.path.append("..")
from abc import ABC, abstractmethod
from typing import List

from diplomacy import Game, Message

from baseline_bots.utils import OrdersData, MessagesData, get_order_tokens

class BaselineBot(ABC):
    """Abstract Base Class for baselines bots"""
    def __init__(self, power_name:str, game:Game) -> None:
        self.power_name = power_name
        self.game = game
        
    @abstractmethod
    def gen_messages(self, rcvd_messages:List[Message]) -> MessagesData:
        """
        :return: messages to be sent
        """
        raise NotImplementedError()

    @abstractmethod
    def gen_orders(self) -> OrdersData:
        """
        :return: orders to be executed
        """
        raise NotImplementedError()

    def __call__(self, rcvd_messages:List[Message]) -> dict:
        """
        :return: dict containing messages and orders
        """
        messages = self.gen_messages(rcvd_messages)
        orders = self.gen_orders()
        # maintain current orders
        self.orders = orders
        return {"messages": messages, "orders": orders}

class BaselineMsgRoundBot(BaselineBot, ABC):
    """
    Abstract Base Class for bots which execute
    multiple rounds of communication before setting
    orders
    """
    def __init__(self, power_name:str, game:Game, total_msg_rounds=3) -> None:
        """
        :param num_msg_rounds: the number of communication rounds the bot
        will go through
        """
        super().__init__(power_name, game)
        self.total_msg_rounds = total_msg_rounds
        self.orders = OrdersData()
    
    def gen_orders(self) -> OrdersData:
        """finalizes moves"""
        return self.orders

    def phase_init(self) -> None:
        """reset information after each order round complete"""
        # the current message round, which is reset after each order round
        self.curr_msg_round = 1
        # reset selected orders
        self.orders = OrdersData()

    def are_msg_rounds_done(self) -> bool:
        return self.curr_msg_round == self.total_msg_rounds + 1