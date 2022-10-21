__author__ = "Sander Schulhoff"
__email__ = "sanderschulhoff@gmail.com"

import random

from DAIDE import ORR, XDO, YES
from diplomacy import Message

from baseline_bots.bots.baseline_bot import BaselineBot
from baseline_bots.utils import (
    MessagesData,
    OrdersData,
    get_non_aggressive_orders,
    get_other_powers,
    parse_arrangement,
)


# TODO: Upgrade to new design layout
class RandomStanceBot(BaselineBot):
    """
    This bot reads proposed order messages from other powers.
    It then randomly selects some to take and messages the proposing powers
    with whichever proposed orders of theirs it selected.
    NOTE: It will only execute non-aggressive moves
    """

    def __init__(self, power_name, game) -> None:
        super().__init__(power_name, game)
        self.stance = {
            other_power: 0
            for other_power in get_other_powers([self.power_name], self.game)
        }
        self.orders_obj = None

    def set_stance(self, stance):
        self.stance = stance
        print("Updated stance", self.power_name, self.stance)

    def get_stance(self, stance):
        return self.stance

    def gen_messages(self):
        # Return data initialization
        messages_obj, self.orders_obj = MessagesData(), OrdersData()

        # get proposed orders sent by other countries
        messages = game.filter_messages(
            messages=game.messages, game_role=self.power_name
        )
        # proposed_orders = []
        proposed_orders_by_country = {}
        for key in messages:
            message = messages[key]
            # parse_arrangement could fail if the message type isnt right
            try:
                parsed = parse_arrangement(message.message)
                if self.stance[message.sender] > 0:
                    self.orders_obj.add_orders(parsed)
                    proposed_orders_by_country[message.sender] = parsed
            except:
                pass

        # orders = [random.choice(self.possible_orders[loc]) for loc in
        #           self.game.get_orderable_locations(self.power_name)
        #           if self.possible_orders[loc]]
        # # Add random orders for all other provinces with no orders
        # self.orders_obj.add_orders(orders)

        # set orders
        # print(self.orders_obj.orders)
        self.game.set_orders(self.power_name, self.orders_obj.get_list_of_orders)

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
            messages_obj.add_message(other_power, str(msg))

        possible_orders = game.get_all_possible_orders()

        # for all other powers
        for other_power in get_other_powers([self.power_name], self.game):
            # generate some random moves to suggest to them
            suggested_random_orders = [
                random.choice(possible_orders[loc])
                for loc in self.game.get_orderable_locations(other_power)
                if possible_orders[loc]
            ]
            if suggested_random_orders:
                suggested_random_orders = ORR(XDO(suggested_random_orders))

                # send the other power a message containing the orders
                messages_obj.add_message(other_power, str(suggested_random_orders))

        return messages_obj

    def gen_orders(self):
        return self.orders_obj.get_list_of_orders()


if __name__ == "__main__":
    from diplomacy import Game
    from diplomacy.utils.export import to_saved_game_format
    from random_allier_proposer_bot import RandomAllierProposerBot

    # game instance
    game = Game()
    powers = list(game.get_map_power_names())

    friend_mappings = {
        "ENGLAND": ["FRANCE", "ITALY"],
        "FRANCE": ["ITALY"],
        "GERMANY": ["AUSTRIA"],
        "RUSSIA": ["ENGLAND", "FRANCE", "ITALY", "TURKEY"],
        "TURKEY": ["RUSSIA"],
        "ITALY": ["FRANCE", "ENGLAND"],
        "AUSTRIA": ["GERMANY"],
    }

    bots = []

    for power in powers:
        temp = RandomStanceBot(power, game)
        stance = {other_power: -1 for other_power in get_other_powers([power], game)}
        for val in friend_mappings[power]:
            stance[val] = 1
        temp.set_stance(stance)
        bots.append(temp)

    while not game.is_game_done:

        for bot in bots:
            bot_state = bot.act()
            messages, orders = bot_state.messages, bot_state.orders
            if messages:
                # print(power_name, messages)
                for msg in messages:
                    msg_obj = Message(
                        sender=bot.power_name,
                        recipient=msg["recipient"],
                        message=msg["message"],
                        phase=game.get_current_phase(),
                    )
                    game.add_message(message=msg_obj)
            # print("Submitted orders")
            if orders is not None:
                game.set_orders(power_name=bot.power_name, orders=orders)

        game.process()
        bots = bots[::-1]

    to_saved_game_format(game, output_path="RandomStanceBotGame.json")
