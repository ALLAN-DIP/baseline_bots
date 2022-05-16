__authors__ = "Wichayaporn Wongkamjan"
__email__ = "w.wongkamjan@gmail.com"


import random
import sys
import ujson as json

sys.path.append("..")
sys.path.append("../..")
sys.path.append("../../..")
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
from diplomacy_research.utils.cluster import start_io_loop, stop_io_loop
from bots.baseline_bot import BaselineMsgRoundBot

class ProposerDipBot(DipnetBot):
    """execute orders computed by dipnet and propose orders computed by dipnet"""
    def __init__(self, power_name:str, game:Game) -> None:
        super().__init__(power_name, game)
        self.brain = DipNetRLPlayer()
        self.n_proposal_orders = 5
        self.stance= None

    @gen.coroutine
    def gen_messages(self, _) -> MessagesData:
        # Return data initialization
        ret_obj = MessagesData()

        # For each power, randomly sample a valid order
        
        for other_power in get_other_powers([self.power_name], self.game):
            # get stance of other_power
            stance = self.stance[other_power]

            # if other_power = neutral or ally 
            if stance >= 0:
                suggested_orders = yield self.brain.get_orders(self.game, other_power)
                suggested_orders = suggested_orders[:min(self.n_proposal_orders, len(suggested_orders))]
                suggested_orders = ORR([XDO(order) for order in suggested_orders])
                # send the other power a message containing the orders
                ret_obj.add_message(other_power, str(suggested_orders))
        return ret_obj

    @gen.coroutine
    def gen_orders(self):
        orders = yield self.brain.get_orders(self.game, self.power_name)
        self.orders.add_orders(orders, overwrite=True)
        return self.orders.get_list_of_orders()

@gen.coroutine
def test_bot():
    bots = [ProposerDipBot(bot_power, game) for bot_power in powers]
    while not game.is_game_done:
        for bot in bots:
            if isinstance(bot, BaselineMsgRoundBot):
                bot.phase_init()

        sc = {bot_power: len(game.get_centers(bot_power)) for bot_power in powers}
        stance_vec = stance.get_stance(game_rec= sc, game_rec_type='game')
        if game.get_current_phase()[-1] == 'M':
            for bot in bots:
                # update stance 
                bot.stance = stance_vec[bot.power_name]
                messages = yield bot.gen_messages(None)
                orders = yield bot.gen_orders()
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
                
                game.set_orders(power_name=bot.power_name, orders=orders)
        
        game.process()

    # to_saved_game_format(game, output_path='DipNetProposerBot.json')
    game_history_name = 'DipNetProposerBot.json'
    with open(game_history_name, 'w') as file:
        file.write(json.dumps(to_saved_game_format(game)))
    stop_io_loop()

if __name__ == "__main__":
    from diplomacy.utils.export import to_saved_game_format

    # game instance
    game = Game()
    powers = list(game.get_map_power_names())
    
    # identity does not matter
    stance = ScoreBasedStance('', powers)

    start_io_loop(test_bot)
