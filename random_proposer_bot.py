__author__ = "Sander Schulhoff"
__email__ = "sanderschulhoff@gmail.com"

from diplomacy import Message
from baseline_bot import BaselineBot
import random
from daide_utils import ORR, XDO, get_other_powers

class RandomProposerBot(BaselineBot):
    """
    Just sends random order proposals to other bots.
    """

    def __init__(self, power_name, game) -> None:
        super().__init__(power_name, game)

    def act(self):
        # for all other powers
        for other_power in get_other_powers([self.power_name], self.game):
            # generate some random moves to suggest to them
            suggested_random_orders = [random.choice(self.possible_orders[loc]) for loc in self.game.get_orderable_locations(other_power)
                        if self.possible_orders[loc]]

            suggested_random_orders = ORR(XDO(suggested_random_orders))

            # send the other power a message containing the orders
            self.game.add_message(Message(
                sender=self.power_name,
                recipient=other_power,
                # convert the random orders to a str
                message=str(suggested_random_orders),
                phase=self.game.get_current_phase(),
            ))
        
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
        bot.act()
        game.process()

    to_saved_game_format(game, output_path='RandomProposerBotGame.json')
