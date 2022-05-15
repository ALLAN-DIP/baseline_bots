__authors__ = ["Sander Schulhoff", "Kartik Shenoy"]
__email__ = "sanderschulhoff@gmail.com"

import random
import sys

from bots.dipnet.dipnet_bot import DipnetBot
from diplomacy import Game, Message
from utils import OrdersData, MessagesData, get_order_tokens
from typing import List
from tornado import gen

sys.path.append("..")
sys.path.append("../..")

from utils import get_order_tokens

class NoPressDipBot(DipnetBot):
    """just execute orders computed by dipnet"""

    @gen.coroutine
    def gen_messages(self, rcvd_messages:List[Message]) -> MessagesData:
        """query dipnet for orders"""
        return None

    @gen.coroutine
    def gen_orders(self):
        orders = yield self.brain.get_orders(self.game, self.power_name)
        self.orders.add_orders(orders, overwrite=True)
        return self.orders.get_list_of_orders()