__author__ = "Sander Schulhoff"
__email__ = "sanderschulhoff@gmail.com"

import random
import sys
sys.path.append("..")

from diplomacy import Message
from DAIDE import ORR, XDO

from . import baseline_bot
from utils import get_other_powers, MessagesData

class RandomProposerBot(baseline_bot.BaselineBot):
    """
    Just sends random order proposals to other bots.
    """

    def __init__(self, power_name, game) -> None:
        super().__init__(power_name, game)
    
    def gen_messages(self, _) -> MessagesData:
        # Return data initialization
        ret_obj = MessagesData()

        # Getting the list of possible orders for all locations
        possible_orders = self.game.get_all_possible_orders()

        # For each power, randomly sample a valid order
        for other_power in get_other_powers([self.power_name], self.game):
            suggested_random_orders = [random.choice(possible_orders[loc]) for loc in self.game.get_orderable_locations(self.power_name)
                        if possible_orders[loc]]
            suggested_random_orders = ORR([XDO(order) for order in suggested_random_orders])
            # send the other power a message containing the orders
            ret_obj.add_message(other_power, str(suggested_random_orders))

        return ret_obj

    def gen_orders(self):
        return None
        
if __name__ == "__main__":
    from diplomacy import Game
    from diplomacy.utils.export import to_saved_game_format
    # game instance
    game = Game()
    # select the first name in the list of powers
    bot_power = list(game.get_map_power_names())[0]
    # instantiate random honest bot
    bot = RandomProposerBot(bot_power, game)
    while not game.is_game_done:
        messages = bot.gen_messages(None).messages
        for msg in messages:
            msg_obj = Message(
                sender=bot.power_name,
                recipient=msg['recipient'],
                message=msg['message'],
                phase=game.get_current_phase(),
            )
            game.add_message(message=msg_obj)

        game.process()

    to_saved_game_format(game, output_path='RandomProposerBotGame.json')
