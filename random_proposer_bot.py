__author__ = "Sander Schulhoff"
__email__ = "sanderschulhoff@gmail.com"

from diplomacy import Message
from baseline_bot import BaselineBot
import random
from DAIDE import ORR, XDO
from daide_utils import get_other_powers, BotReturnData


class RandomProposerBot(BaselineBot):
    """
    Just sends random order proposals to other bots.
    """

    def __init__(self, power_name, game) -> None:
        super().__init__(power_name, game)
    
    def gen_messages(self, _) -> BotReturnData:
        # Return data initialization
        ret_obj = BotReturnData()

        # for all other powers
        for other_power in get_other_powers([self.power_name], self.game):
            # generate some random moves to suggest to them
            suggested_random_orders = [random.choice(self.possible_orders[loc]) for loc in self.game.get_orderable_locations(other_power)
                        if self.possible_orders[loc]]

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
