import random
from typing import List

from DAIDE import FCT, ORR, XDO
from diplomacy import Game, Message
from diplomacy_research.players.benchmark_player import DipNetRLPlayer
from tornado import gen

from baseline_bots.bots.dipnet.dipnet_proposer_bot import ProposerDipBot
from baseline_bots.utils import (
    MessagesData,
    OrdersData,
    get_order_tokens,
    get_other_powers,
)


class TransparentProposerDipBot(ProposerDipBot):
    """
    Execute orders computed by dipnet
    Share orders computed by dipnet
    Propose orders computed by dipnet
    """

    @gen.coroutine
    def gen_messages(self, _) -> MessagesData:
        ret_obj = MessagesData()
        final_order = {
            other_power: None
            for other_power in get_other_powers([self.power_name], self.game)
        }
        if self.curr_msg_round == 1:
            # Fetch list of orders from DipNet
            orders = yield from self.brain.get_orders(self.game, self.power_name)
            self.orders.add_orders(orders, overwrite=True)
            self.my_orders_informed = True
            shared_orders = self.orders.get_list_of_orders()
            if len(shared_orders):
                shared_orders = FCT(ORR([XDO(order) for order in shared_orders]))
                final_order = {
                    other_power: shared_orders
                    for other_power in get_other_powers([self.power_name], self.game)
                }

        if self.curr_msg_round == 2:
            for other_power in get_other_powers([self.power_name], self.game):
                suggested_orders = yield self.brain.get_orders(self.game, other_power)
                suggested_orders = suggested_orders[
                    : min(self.n_proposal_orders, len(suggested_orders))
                ]
                if len(suggested_orders):
                    suggested_orders = ORR([XDO(order) for order in suggested_orders])
                    final_order[other_power] = suggested_orders

        # For each power, randomly sample a valid order
        for other_power in get_other_powers([self.power_name], self.game):
            # get stance of other_power
            stance = self.stance[other_power]
            # if other_power = neutral or ally
            if stance >= 0:
                # send the other power a message containing the proposals
                if final_order[other_power]:
                    ret_obj.add_message(other_power, str(final_order[other_power]))

        self.curr_msg_round += 1
        return ret_obj
