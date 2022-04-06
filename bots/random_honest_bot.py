__author__ = "Sander Schulhoff"
__email__ = "sanderschulhoff@gmail.com"

from diplomacy import Message
from baseline_bot import BaselineBot
import random

from daide_utils import BotReturnData


class RandomHonestBot(BaselineBot):
    """
    This bot always acts randomly and truthfully communicates
    its intended moves in messages to all of its opponents
    """
    def __init__(self, power_name, game) -> None:
        super().__init__(power_name, game)

    def act(self):
        # Return data initialization
        ret_obj = BotReturnData()
        possible_orders = game.get_all_possible_orders()
        # select random orders
        random_orders = [random.choice(possible_orders[loc]) for loc in self.game.get_orderable_locations(self.power_name)
                         if possible_orders[loc]]
        # set the orders
        ret_obj.add_all_orders(random_orders)
        
        # for all other powers
        for other_power in [name for name in self.game.get_map_power_names() if name != self.power_name]:
            # send the other power a message containing the orders
            ret_obj.add_message(other_power, str(random_orders))

        return ret_obj

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

    to_saved_game_format(game, output_path='RandomHonestBotGame.json')
