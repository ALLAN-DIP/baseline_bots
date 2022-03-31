__author__ = "Sander Schulhoff"
__email__ = "sanderschulhoff@gmail.com"

from diplomacy import Message
from baseline_bot import BaselineBot
import random
from daide_utils import ORR, XDO, get_other_powers, BotReturnData


class RandomProposerBot(BaselineBot):
    """
    Just sends random order proposals to other bots.
    """

    def __init__(self, power_name, game) -> None:
        super().__init__(power_name, game)

    def act(self):
        # Return data initialization
        ret_obj = BotReturnData()

        # for all other powers
        for other_power in get_other_powers([self.power_name], self.game):
            # generate some random moves to suggest to them
            suggested_random_orders = [random.choice(self.possible_orders[loc]) for loc in self.game.get_orderable_locations(other_power)
                        if self.possible_orders[loc]]

            suggested_random_orders = ORR(XDO(suggested_random_orders))

            # send the other power a message containing the orders
            ret_obj.add_message(other_power, str(suggested_random_orders))

        return ret_obj
        
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

    to_saved_game_format(game, output_path='RandomProposerBotGame.json')
