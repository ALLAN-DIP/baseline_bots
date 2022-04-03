__author__ = "Kartik Shenoy"
__email__ = "kartik.shenoyy@gmail.com"

from diplomacy import Message
from baseline_bot import BaselineBot
import random
from daide_utils import get_other_powers, BotReturnData
from time import time

class RandomNoPressBot(BaselineBot):
    """
    Just execute random orders.
    """

    def __init__(self, power_name, game) -> None:
        super().__init__(power_name, game)

    def gen_messages(self, rcvd_messages):
        return None

    def gen_orders(self):
        orders = [random.choice([ord for ord in self.possible_orders[loc] if not self.bad_move(ord)]) for loc in
                             self.game.get_orderable_locations(self.power_name)
                             if self.possible_orders[loc]]

        self.selected_orders.add_all_orders(orders)

        return self.selected_orders.get_final_orders()


if __name__ == "__main__":
    from diplomacy import Game
    from diplomacy.utils.export import to_saved_game_format
    from random_allier_proposer_bot import RandomAllierProposerBot

    # game instance
    game = Game()
    powers = list(game.get_map_power_names())
    # select the first name in the list of powers
    bots = [RandomNoPressBot(bot_power, game) for bot_power in powers]
    start = time()
    while not game.is_game_done:
        for bot in bots:
            bot_state = bot.act()
            messages, orders = bot_state.messages, bot_state.orders
            # if messages:
            #     # print(power_name, messages)
            #     for msg in messages:
            #         msg_obj = Message(
            #             sender=power_name,
            #             recipient=msg[1],
            #             message=msg[2],
            #             phase=game.get_current_phase(),
            #         )
            #         game.add_message(message=msg_obj)
            # print("Submitted orders")
            if orders is not None:
                game.set_orders(power_name=bot.power_name, orders=orders)
        game.process()
    print(time() - start)
    to_saved_game_format(game, output_path='RandomNoPressBotGame.json')
