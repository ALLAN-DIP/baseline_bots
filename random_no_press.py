__author__ = "Kartik Shenoy"
__email__ = "kartik.shenoyy@gmail.com"

from diplomacy import Message
from baseline_bot import BaselineBot
import random
from daide_utils import ORR, XDO, get_other_powers, BotReturnData
from time import time


class RandomNoPressBot(BaselineBot):
    """
    Just execute random orders.
    """

    def __init__(self, power_name, game) -> None:
        super().__init__(power_name, game)

    def act(self):
        # Return data initialization
        ret_obj = BotReturnData()

        # Fetch latest possible moves
        self.possible_orders = self.game.get_all_possible_orders()

        orders = [random.choice(self.possible_orders[loc]) for loc in
                             self.game.get_orderable_locations(self.power_name)
                             if self.possible_orders[loc]]

        ret_obj.add_all_orders(orders)

        return ret_obj


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
