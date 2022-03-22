__author__ = "Sander Schulhoff"
__email__ = "sanderschulhoff@gmail.com"

from diplomacy import Message
from baseline_bot import BaselineBot
import random

class RandomHonestBot(BaselineBot):
    """
    This bot always acts randomly and truthfully communicates
    its intended moves in messages to all of its opponents
    """
    def __init__(self, power_name, game) -> None:
        super().__init__(power_name, game)

    def act(self):
        # select random orders
        random_orders = [random.choice(self.possible_orders[loc]) for loc in self.game.get_orderable_locations(self.power_name)
                         if self.possible_orders[loc]]
        # set the orders
        game.set_orders(self.power_name, random_orders)
        
        # for all other powers
        for other_power in [name for name in self.game.get_map_power_names() if name != self.power_name]:
            # send the other power a message containing the orders
            game.add_message(Message(
                sender=self.power_name,
                recipient=other_power,
                # convert the random orders to a str
                message=str(random_orders),
                phase=game.get_current_phase(),
            ))

if __name__ == "__main__":
    from diplomacy import Game
    from diplomacy.utils.export import to_saved_game_format
    # game instance
    game = Game()
    # select the first name in the list of powers
    bot_power = list(game.get_map_power_names())[0]
    # instantiate random honest bot
    bot = RandomHonestBot(bot_power, game)
    while not game.is_game_done:
        bot.act()
        game.process()

    to_saved_game_format(game, output_path='RandomHonestBotGame.json')
