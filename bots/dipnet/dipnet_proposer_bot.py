__authors__ = "Wichayaporn Wongkamjan"
__email__ = "w.wongkamjan@gmail.com"


import random
import sys

sys.path.append("..")
sys.path.append("../..")
sys.path.append("../../../dipnet_press")

from diplomacy_research.players.benchmark_player import DipNetRLPlayer
from bots.dipnet.dipnet_bot import DipnetBot
from diplomacy import Game, Message
from utils import OrdersData, MessagesData, get_order_tokens, get_other_powers
from DAIDE import ORR, XDO
from typing import List
from tornado import gen
from stance.stance_extraction import StanceExtraction, ScoreBasedStance



from utils import get_order_tokens

class ProposerDipBot(DipnetBot):
    """execute orders computed by dipnet and propose orders computed by dipnet"""
    def __init__(self, power_name:str, game:Game, stance:StanceExtraction) -> None:
        super().__init__(power_name, game)
        self.brain = DipNetRLPlayer()
        self.n_proposal_orders = 5
        self.stance_class = stance(power_name, game.powers)

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

if __name__ == "__main__":
    from diplomacy.utils.export import to_saved_game_format

    # game instance
    game = Game()
    powers = list(game.get_map_power_names())
    stance = ScoreBasedStance()
    # select the first name in the list of powers
    bots = [ProposerDipBot(bot_power, game, stance) for bot_power in powers]

    while not game.is_game_done:
        for bot in bots:
            # update stance 
            sc = {bot_power: len(game.get_centers(bot_power)) for bot_power in powers}
            bot.stance_class.get_stance(game_rec= sc, game_rec_type='game')
            bot_state = bot.act()
            messages, orders = bot_state.messages, bot_state.orders
            if messages:
                # print(power_name, messages)
                for msg in messages:
                    msg_obj = Message(
                        sender=bot.power_name,
                        recipient=msg['recipient'],
                        message=msg['message'],
                        phase=game.get_current_phase(),
                    )
                    game.add_message(message=msg_obj)
            # print("Submitted orders")
            if orders is not None:
                game.set_orders(power_name=bot.power_name, orders=orders)
        
        game.process()

    to_saved_game_format(game, output_path='DipNetProposerBot.json')
