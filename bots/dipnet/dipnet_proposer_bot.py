__authors__ = "Wichayaporn Wongkamjan"
__email__ = "w.wongkamjan@gmail.com"

import random
import sys
from diplomacy_research.players.benchmark_player import DipNetRLPlayer
from bots.dipnet.dipnet_bot import DipnetBot
from diplomacy import Game, Message
from utils import OrdersData, MessagesData, get_order_tokens, get_other_powers
from DAIDE import ORR, XDO
from typing import List
from tornado import gen

sys.path.append("..")
sys.path.append("../..")

from utils import get_order_tokens

class ProposerDipBot(DipnetBot):
    """execute orders computed by dipnet and propose orders computed by dipnet"""
    def __init__(self, power_name:str, game:Game, stance:StanceExtraction) -> None:
        super().__init__(power_name, game)
        self.brain = DipNetRLPlayer()
        self.n_proposal_orders = 5
        self.stance_class = stance()

    @gen.coroutine
    def gen_messages(self, _) -> MessagesData:
        # Return data initialization
        ret_obj = MessagesData()

        # For each power, randomly sample a valid order
        
        for other_power in get_other_powers([self.power_name], self.game):
            # get stance of other_power
            stance = self.stance_class.stance[self.power_name][other_power]

            # if other_power = neutral or ally 
            if stance >= 0:
                suggested_orders = yield self.brain.get_orders(self.game, other_power)
                suggested_orders = suggested_orders[:min(self.n_proposal_orders, len(suggested_orders()))]
                suggested_orders = ORR([XDO(order) for order in suggested_orders])
                # send the other power a message containing the orders
                ret_obj.add_message(other_power, str(suggested_orders))

    @gen.coroutine
    def gen_orders(self):
        orders = yield self.brain.get_orders(self.game, self.power_name)
        self.orders.add_orders(orders, overwrite=True)
        return self.orders.get_list_of_orders()

