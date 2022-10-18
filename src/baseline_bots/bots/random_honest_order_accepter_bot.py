__author__ = "Sander Schulhoff"
__email__ = "sanderschulhoff@gmail.com"

import random

from DAIDE import ORR, XDO, YES
from diplomacy import Message

from baseline_bots.bots.baseline_bot import BaselineMsgRoundBot
from baseline_bots.utils import (
    MessagesData,
    OrdersData,
    get_non_aggressive_orders,
    parse_arrangement,
)


class RandomHonestOrderAccepterBot(BaselineMsgRoundBot):
    """
    This bot reads proposed order messages from other powers.
    It then randomly selects some to take and messages the proposing powers
    with whichever proposed orders of theirs it selected.
    NOTE: It will only execute non-aggressive moves
    NOTE: Only selects/sends messages on the last communication round
    """

    def __init__(self, power_name, game) -> None:
        super().__init__(power_name, game)

    def phase_init(self):
        super().phase_init()
        self.cur_msg_round = 0
        self.messages = MessagesData()
        self.orders = OrdersData()

    def gen_messages(self, rcvd_messages):
        return self.messages

    def gen_orders(self):
        return self.orders

    def __call__(self, rcvd_messages):
        self.cur_msg_round += 1
        # only generate messages/orders on final message round
        if self.cur_msg_round == self.total_msg_rounds:
            pass
        else:
            return {"messages": MessagesData(), "orders": OrdersData()}

        proposed_orders = []
        proposed_orders_by_country = {}
        for message in rcvd_messages:
            # parse_arrangement could fail if the message type isnt right
            try:
                parsed = parse_arrangement(message.message)
                proposed_orders += parsed
                proposed_orders_by_country[message.sender] = parsed
            except:
                pass

        # remove aggressive orders
        orders = get_non_aggressive_orders(proposed_orders, self.power_name, self.game)

        # keep ~3/4 of the remaining orders at random
        orders = [order for order in proposed_orders if random.random() > 0.25]

        orders_data = OrdersData()
        orders_data.add_orders(orders)
        messages_data = MessagesData()
        # send messages to other powers if this bot has taken some
        # of their messages
        for other_power in proposed_orders_by_country:
            # construct list of orders which other_power proposed
            # which this bot has taken
            orders_taken = []
            for destination in orders_data:
                order = orders_data.orders[destination]
                if order in proposed_orders_by_country[other_power]:
                    orders_taken.append(order)

            # if none of the country's suggested orders were taken
            if not orders_taken:
                break

            # encode orders taken with daide syntax
            msg = YES(ORR([XDO(order) for order in orders_taken]))

            messages_data.add_message(other_power, str(msg))

        self.messages = messages_data
        self.orders = orders_data

        return {"messages": messages_data, "orders": orders_data}


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
    bot = RandomHonestOrderAccepterBot(bot_power, game)
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
                for msg in messages:
                    msg_obj = Message(
                        sender=bot.power_name,
                        recipient=msg["recipient"],
                        message=msg["message"],
                        phase=game.get_current_phase(),
                    )
                    game.add_message(message=msg_obj)
            if orders is not None:
                game.set_orders(power_name=bot.power_name, orders=orders)

        game.process()

        break

    to_saved_game_format(game, output_path="RandomHonestOrderAccepterBotGame.json")
