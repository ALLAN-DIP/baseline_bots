__author__ = "Sander Schulhoff"
__email__ = "sanderschulhoff@gmail.com"

from diplomacy import Message
from DAIDE import ParseError
import DAIDE 
DAIDE.config.ORDERS_DAIDE = False

from baseline_bot import BaselineBot
from utils import parse_orr_xdo, get_non_aggressive_orders, OrdersData

class PushoverBot(BaselineBot):
    """
    Does whatever the last message/bot told it to do
    NOTE: only executes non-aggressive action
    """
    def __init__(self, power_name, game) -> None:
        super().__init__(power_name, game)
        self.orders = None

    def gen_messages(self, rcvd_messages):
        # Return data initialization
        ret_obj = OrdersData()
        
        sorted_rcvd_messages = sort_messages_by_most_recent(rcvd_messages)

        # parse may fail
        try:
            orders = get_non_aggressive_orders(parse_orr_xdo(last_message.message), self.power_name, self.game)
            # set the orders
            ret_obj.add_all_orders(orders)
        except e as ParseError:
            pass

        return ret_obj
        return None

    def gen_orders(self):
        return self.orders

# if __name__ == "__main__":
#     from diplomacy import Game
#     from diplomacy.utils.export import to_saved_game_format
#     from random_proposer_bot import RandomProposerBot
#     # game instance
#     game = Game()
#     powers = list(game.get_map_power_names())
#     # select the first name in the list of powers
#     bot_power = powers[0]
#     # instantiate proposed random honest bot
#     bot = PushoverBot(bot_power, game)
#     proposer_1 = RandomProposerBot(powers[1], game)
#     proposer_2 = RandomProposerBot(powers[2], game)

#     bots = [proposer_1, proposer_2, bot]

#     while not game.is_game_done:
#         # proposer_1.act()
#         # proposer_2.act()
#         # bot.act()

#         for bot in bots:
#             bot_state = bot.act()
#             messages, orders = bot_state.messages, bot_state.orders
#             if messages:
#                 # print(power_name, messages)
#                 for msg in messages:
#                     msg_obj = Message(
#                         sender=bot.power_name,
#                         recipient=msg['recipient'],
#                         message=msg['message'],
#                         phase=game.get_current_phase(),
#                     )
#                     game.add_message(message=msg_obj)
#             # print("Submitted orders")
#             if orders is not None:
#                 game.set_orders(power_name=bot.power_name, orders=orders)

#         game.process()


#     to_saved_game_format(game, output_path='PushoverBotGame.json')
