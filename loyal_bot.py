__author__ = "Sander Schulhoff"
__email__ = "sanderschulhoff@gmail.com"

from lib2to3.pgen2.parse import ParseError

from diplomacy import Message
from random_allier_proposer_bot import RandomAllierProposerBot
from daide_utils import parse_orr_xdo, parse_alliance_proposal, get_non_aggressive_orders, YES

from baseline_bot import BaselineBot

class LoyalBot(BaselineBot):
    """
    Accepts first alliance it receives. 
    Then only accepts orders bots in that alliance.
    NOTE: only executes non-aggressive actions
    """
    def __init__(self, power_name, game) -> None:
        super().__init__(power_name, game)
        # will always follow this country's orders
        self.allies = None

    def act(self):
        # get proposed orders sent by other countries
        messages = game.filter_messages(messages = game.messages, game_role=bot_power)
        # convert to list for sorting/indexing
        keys = list(messages.keys())
        # sort from most recent to least recent
        keys.sort(reverse=True)
        # get most recent message
        last_message = messages[keys[0]]
        if self.allies:
            # ensure message sender is an ally
            if last_message.sender in self.allies:
                try:
                    orders = get_non_aggressive_orders(parse_orr_xdo(last_message.message), self.power_name, self.game)
                    # set the orders
                    game.set_orders(self.power_name, orders)
                except ParseError:
                    pass
        else:
            try:
                self.allies = parse_alliance_proposal(last_message.message, self.power_name)
                msg = YES(last_message.message)
                
                self.game.add_message(Message(
                    sender=self.power_name,
                    recipient=last_message.sender,
                    # convert the random orders to a str
                    message=msg,
                    phase=game.get_current_phase(),
                ))
            except ParseError:
                pass

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
    print(bot_power)
    proposer_1 = RandomAllierProposerBot(powers[1], game)
    proposer_2 = RandomAllierProposerBot(powers[2], game)
    
    while not game.is_game_done:
        proposer_1.act()
        proposer_2.act()
        bot.act()
        
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
