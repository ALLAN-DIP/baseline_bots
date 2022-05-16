__authors__ = "Wichayaporn Wongkamjan"
__email__ = "w.wongkamjan@gmail.com"


import random
import sys

sys.path.append("..")
sys.path.append("../..")
sys.path.append("../../..")
sys.path.append("../../../dipnet_press")

from diplomacy_research.players.benchmark_player import DipNetRLPlayer
from bots.dipnet.dipnet_proposer_bot import ProposerDipBot
from diplomacy import Game, Message
from utils import OrdersData, MessagesData, get_order_tokens, get_other_powers
from DAIDE import ORR, XDO, FCT
from typing import List
from tornado import gen
from utils import get_order_tokens


class TransparentProposerDipBot(ProposerDipBot):
    """
    Execute orders computed by dipnet 
    Send out some of them randomly
    Propose orders computed by dipnet
    """

    @gen.coroutine
    def gen_messages(self, _) -> MessagesData:
        ret_obj = MessagesData()
        if self.curr_msg_round == 1:
            # Fetch list of orders from DipNet
            orders = yield from self.brain.get_orders(self.game, self.power_name)
            self.orders.add_orders(orders, overwrite=True)
            self.my_orders_informed = True
            shared_orders = self.orders.get_list_of_orders()
            shared_orders = FCT(ORR([XDO(order) for order in shared_orders]))
            final_order=shared_orders

        if self.curr_msg_round ==2:
            suggested_orders = yield self.brain.get_orders(self.game, other_power)
            suggested_orders = suggested_orders[:min(self.n_proposal_orders, len(suggested_orders))]
            suggested_orders = ORR([XDO(order) for order in suggested_orders])
            final_order=suggested_orders
        
        # For each power, randomly sample a valid order
        for other_power in get_other_powers([self.power_name], self.game):
            # get stance of other_power
            stance = self.stance[other_power]
            # if other_power = neutral or ally 
            if stance >= 0:
                # send the other power a message containing the proposals
                ret_obj.add_message(other_power, str(final_order))

        self.curr_msg_round += 1
        return ret_obj

