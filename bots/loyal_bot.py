__author__ = "Sander Schulhoff"
__email__ = "sanderschulhoff@gmail.com"

import sys
sys.path.append("..")

from diplomacy import Message
from DAIDE.utils.exceptions import ParseError
from DAIDE import YES

from .random_allier_proposer_bot import RandomAllierProposerBot
from utils import parse_orr_xdo, parse_alliance_proposal, get_non_aggressive_orders, MessagesData
from .baseline_bot import BaselineMsgRoundBot

class LoyalBot(BaselineMsgRoundBot):
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
        self.orders = None

    def gen_messages(self, rcvd_messages):
        # Return data initialization
        ret_obj = MessagesData()

        # convert to list for sorting/indexing
        keys = list(rcvd_messages.keys())
        if len(keys) == 0:
            return ret_obj

        # sort from most recent to least recent
        keys.sort(reverse=True)
        # get most recent message
        last_message = rcvd_messages[keys[0]]
        if self.allies:
            # ensure message sender is an ally
            if last_message.sender in self.allies:
                try:
                    orders = get_non_aggressive_orders(parse_orr_xdo(last_message.message), self.power_name, self.game)
                    self.selected_orders.add_orders(orders)
                     
                except ParseError:
                    pass
        else:
            try:
                self.allies = parse_alliance_proposal(last_message.message, self.power_name)
                msg = YES(last_message.message)
                ret_obj.add_message(last_message.sender, str(msg))

            except ParseError:
                pass

        return ret_obj


    def gen_orders(self):
        return self.selected_orders
        
if __name__ == "__main__":
    from diplomacy import Game
    from diplomacy.utils.export import to_saved_game_format
    # game instance
    game = Game()
    powers = list(game.get_map_power_names())
    # select the first name in the list of powers
    bot_power = powers[0]
    # instantiate proposed random honest bot
    bot = LoyalBot(bot_power, game)
    # print(bot_power)
    proposer_1 = RandomAllierProposerBot(powers[1], game)
    proposer_2 = RandomAllierProposerBot(powers[2], game)

    bots = [proposer_1, proposer_2, bot]
    
    while not game.is_game_done:
        # proposer_1.act()
        # proposer_2.act()
        # bot.act()

        for bot in bots:
            bot_state = bot.act()
            messages, orders = bot_state.messages, bot_state.orders
            if messages:
                # print(bot.power_name, messages)
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

            break
        
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
        game.process()
        


    to_saved_game_format(game, output_path='LoyalBotGame.json')
