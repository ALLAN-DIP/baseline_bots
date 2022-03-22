__author__ = "Sander Schulhoff"
__email__ = "sanderschulhoff@gmail.com"

from diplomacy import Message
from baseline_bot import BaselineBot
import random
from daide_utils import parse_orr_xdo, ORR, XDO, YES, get_non_aggressive_orders

class RandomHonestAccepterBot(BaselineBot):
    """
    This bot reads proposed order messages from other powers.
    It then randomly selects some to take and messages the proposing powers
    with whichever proposed orders of theirs it selected.
    NOTE: It will only execute non-aggressive moves
    """
    def __init__(self, power_name, game) -> None:
        super().__init__(power_name, game)

    def act(self):
        # get proposed orders sent by other countries
        messages = game.filter_messages(messages = game.messages, game_role=bot_power)
        proposed_orders = []
        proposed_orders_by_country = {}
        for key in messages:
            message = messages[key]
            # parse_orr_xdo could fail if the message type isnt right
            try:
                parsed = parse_orr_xdo(message.message)
                proposed_orders += parsed
                proposed_orders_by_country[message.sender] = parsed
            except:
                pass
        
        # remove aggressive orders
        orders = get_non_aggressive_orders(proposed_orders, self.power_name, self.game)
        
        # keep ~3/4 of the remaining orders at random
        orders = [order for order in proposed_orders if random.random() > 0.25]

        # set orders
        self.game.set_orders(self.power_name, orders)

        # not all intended orders can be set at the same time: some overlap
        # thus, get the orders that are currently set
        orders_set = self.game.get_orders(self.power_name)

        # send messages to other powers if this bot has taken some 
        # of their messages
        for other_power in proposed_orders_by_country:
            # construct list of orders which other_power proposed
            # which this bot has taken
            orders_taken = []
            for order in orders_set:
                if order in proposed_orders_by_country[other_power]:
                    orders_taken.append(order)

            # if none of the country's suggested orders were taken
            if not orders_taken:
                break
            
            # encode orders taken with daide syntax
            msg = YES(ORR(XDO(orders_taken)))

            # send messages
            self.game.add_message(Message(
                sender=self.power_name,
                recipient=other_power,
                message=msg,
                phase=self.game.get_current_phase(),
            ))

if __name__ == "__main__":
    from diplomacy import Game
    from diplomacy.utils.export import to_saved_game_format
    from random_allier_proposer_bot import RandomAllierProposerBot
    # game instance
    game = Game()
    powers = list(game.get_map_power_names())
    # select the first name in the list of powers
    bot_power = powers[0]
    # instantiate proposed random honest bot
    bot = RandomHonestAccepterBot(bot_power, game)
    proposer_1 = RandomAllierProposerBot(powers[1], game)
    proposer_2 = RandomAllierProposerBot(powers[2], game)
    while not game.is_game_done:
        proposer_1.act()
        proposer_2.act()
        bot.act()

        game.process()
        break

    to_saved_game_format(game, output_path='RandomHonestOrderAccepterBotGame.json')
