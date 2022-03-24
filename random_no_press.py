__author__ = "Kartik Shenoy"
__email__ = "kartik.shenoyy@gmail.com"

from diplomacy import Message
from baseline_bot import BaselineBot
import random
from daide_utils import ORR, XDO, get_other_powers


class RandomNoPressBot(BaselineBot):
    """
    Just execute random orders.
    """

    def __init__(self, power_name, game) -> None:
        super().__init__(power_name, game)

    def act(self):
        random_orders = [random.choice(self.possible_orders[loc]) for loc in
                         self.game.get_orderable_locations(self.power_name)
                         if self.possible_orders[loc]]

        return {
            'messages': [],
            'orders': random_orders,
            'stance': None
        }


if __name__ == "__main__":
    from diplomacy import Game
    from diplomacy.utils.export import to_saved_game_format
    from random_allier_proposer_bot import RandomAllierProposerBot

    # game instance
    game = Game()
    powers = list(game.get_map_power_names())
    # select the first name in the list of powers
    bots = [(bot_power, RandomNoPressBot(bot_power, game)) for bot_power in powers]

    while not game.is_game_done:
        for power_name, bot in bots:
            bot_state = bot.act()
            messages, orders = bot_state['messages'], bot_state['orders']
            # if messages is not None:
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
                game.set_orders(power_name=power_name, orders=orders)
        game.process()

    to_saved_game_format(game, output_path='RandomNoPressBotGame.json')
