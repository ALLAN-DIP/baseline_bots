__author__ = "Kartik Shenoy"
__email__ = "kartik.shenoyy@gmail.com"

import random
from collections import defaultdict

from DAIDE import ORR, XDO
from diplomacy import Message

from baseline_bots.bots.baseline_bot import BaselineBot
from baseline_bots.utils import get_order_tokens, OrdersData, MessagesData


class RandomSupportProposerBot(BaselineBot):
    """
    This bot proposes support requests on as many orders as possible.
    For an attack, a support is asked only from 1 power even if it can be asked from multiple powers
    """

    def __init__(self, power_name, game) -> None:
        super().__init__(power_name, game)
        self.orders_obj = None

    def gen_messages(self):

        # Return data initialization
        messages_obj, self.orders_obj = MessagesData(), OrdersData()

        # TODO: Ensure that supporting province and province to be attacked are not owned by the same power
        # TODO: Ensure that attack should not be to a province that the power already owns
        final_messages = defaultdict(list)
        messages = []
        possible_orders = self.game.get_all_possible_orders()

        # TODO: Some scenario is getting missed out | Sanity check: If current phase fetched is not matching with server phase, skip execution
        if self.game.get_current_phase()[0] != "W":
            # TODO: Replace orderable locations with all possible units of a power if needed
            possible_orders = self.game.get_all_possible_orders()
            provs = [
                loc.upper()
                for loc in self.game.get_orderable_locations(self.power_name)
            ]

            n_provs = set()
            for prov in provs:
                n_provs.update(
                    set(
                        [
                            prov2.upper()
                            for prov2 in self.game.map.abut_list(prov)
                            if prov2.upper().split("/")[0] not in provs
                        ]
                    )
                )
            n2n_provs = set()
            for prov in n_provs:
                n2n_provs.update(
                    set(
                        [
                            prov2.upper()
                            for prov2 in self.game.map.abut_list(prov)
                            if prov2.upper().split("/")[0] not in provs
                            and prov2.upper().split("/")[0] not in n_provs
                        ]
                    )
                )

            possible_support_proposals = defaultdict(list)
            for n2n_p in n2n_provs:
                if not (possible_orders[n2n_p]):
                    continue
                possible_orders = possible_orders[n2n_p]

                for order in possible_orders:
                    order_tokens = get_order_tokens(order)
                    if len(order_tokens) <= 1 or order_tokens[1] != "S":
                        continue
                    if (
                        len(order_tokens) != 4
                        or order_tokens[2].split()[1] not in provs
                        or order_tokens[3].split()[1] not in n_provs
                    ):
                        continue
                    possible_support_proposals[
                        (order_tokens[2].split()[1], order_tokens[3].split()[1])
                    ].append((order_tokens[0], order))

            for attack_key in possible_support_proposals:
                selected_order = random.choice(possible_support_proposals[attack_key])
                if self.game._unit_owner(selected_order[0]) is None:
                    raise "Coding Error"
                final_messages[self.game._unit_owner(selected_order[0]).name].append(
                    selected_order[1]
                )

        for recipient in final_messages:
            suggested_proposals = ORR(XDO(final_messages[recipient]))
            messages_obj.add_message(recipient, str(suggested_proposals))
        possible_orders = self.game.get_all_possible_orders()

        orders = [
            random.choice(possible_orders[loc])
            for loc in self.game.get_orderable_locations(self.power_name)
            if possible_orders[loc]
        ]

        self.orders_obj.add_orders(orders)

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
    # select the first name in the list of powers
    bots = [RandomSupportProposerBot(bot_power, game) for bot_power in powers]

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

    to_saved_game_format(game, output_path="RandomSupportProposerBot.json")
