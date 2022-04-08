__author__ = "Sander Schulhoff"
__email__ = "sanderschulhoff@gmail.com"

import sys
sys.path.append("..")

from diplomacy import Message
from DAIDE import ParseError
from DAIDE.utils.exceptions import ParseError
from DAIDE import YES, ALY

from utils import parse_orr_xdo, get_non_aggressive_orders, MessagesData, OrdersData, sort_messages_by_most_recent
import bots.baseline_bot as baseline_bot

class LoyalBot(baseline_bot.BaselineBot):
    """
    Accepts first alliance it receives. 
    Then only accepts orders bots in that alliance.
    NOTE: only executes non-aggressive actions
    """
    def __init__(self, power_name, game) -> None:
        super().__init__(power_name, game)
        # will always follow this country's orders
        self.allies = None
        # orders to be provided by allies
        self.orders = OrdersData()

    def gen_messages(self, rcvd_messages):
        # Return data initialization
        ret_obj = MessagesData()

        if len(rcvd_messages) == 0:
            return ret_obj

        # sort from most recent to least recent
        sorted_rcvd_messages = sort_messages_by_most_recent(rcvd_messages)
        # get most recent message
        last_message = sorted_rcvd_messages[0]
        if self.allies:
            # ensure message sender is an ally
            if last_message.sender in self.allies:
                try:
                    orders = get_non_aggressive_orders(parse_orr_xdo(last_message.message), self.power_name, self.game)
                    self.orders.add_orders(orders)
                     
                except ParseError as e:
                    pass
        else:
            try:
                alliance_proposal = ALY.parse(last_message.message)
                if self.power_name in alliance_proposal.allies:
                    self.allies = alliance_proposal.allies
                    msg = YES(last_message.message)
                    ret_obj.add_message(last_message.sender, str(msg))

            except ParseError as e:
                pass

        return ret_obj


    def gen_orders(self):
        return self.orders

# if __name__ == "__main__":
#     import sys 
#     sys.path.append()
#     from diplomacy import Game
#     from diplomacy.utils.export import to_saved_game_format
#     # game instance
#     game = Game()
#     powers = list(game.get_map_power_names())
#     # select the first name in the list of powers
#     bot_power = powers[0]
#     # instantiate proposed random honest bot
#     bot = LoyalBot(bot_power, game)
#     # print(bot_power)
#     proposer_1 = RandomAllierProposerBot(powers[1], game)
#     proposer_2 = RandomAllierProposerBot(powers[2], game)

#     bots = [proposer_1, proposer_2, bot]
    
#     while not game.is_game_done:
#         # proposer_1.act()
#         # proposer_2.act()
#         # bot.act()

#         for bot in bots:
#             bot_state = bot.act()
#             messages, orders = bot_state.messages, bot_state.orders
#             if messages:
#                 # print(bot.power_name, messages)
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

#             break
        
        # p1_messages = list(game.filter_messages(messages = game.messages, game_role=proposer_1.power_name).values())
        # p1m = next(msg for msg in p1_messages if msg.recipient == bot_power)
        # p2_messages = list(game.filter_messages(messages = game.messages, game_role=proposer_2.power_name).values())
        # p2m = next(msg for msg in p2_messages if msg.recipient == bot_power)
        # bot_messages = list(game.filter_messages(messages = game.messages, game_role=bot.power_name).values())
        # bot_m = bot_messages[0]
        # print("Proposer_1 message to bot\n", p1m.message)
        # print("Proposer_2 message to bot\n", p2m.message)
        # print("Bot message\n", bot_m.sender)
        # print("---------------------")
        # exit()
    #     game.process()
        


    # to_saved_game_format(game, output_path='LoyalBotGame.json')
