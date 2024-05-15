import random
from typing import List, Sequence

from daidepp import PRP, XDO
from diplomacy import Game

from baseline_bots.bots.baseline_bot import BaselineBot
from baseline_bots.parsing_utils import dipnet_to_daide_parsing
from baseline_bots.utils import MessagesData, get_other_powers, optional_AND


class RandomProposerBot(BaselineBot):
    """
    Just sends random order proposals to other bots.
    """

    async def do_messaging_round(
        self,
        orders: Sequence[str],
        msgs_data: MessagesData,
    ) -> List[str]:
        """
        :return: dict containing messages and orders
        """
        # Getting the list of possible orders for all locations
        possible_orders = self.game.get_all_possible_orders()

        # For each power, randomly sample a valid order
        for other_power in get_other_powers([self.power_name], self.game):
            suggested_random_orders = [
                random.choice(possible_orders[loc])
                for loc in self.game.get_orderable_locations(other_power)
                if possible_orders[loc]
            ]
            suggested_random_orders = list(
                filter(
                    lambda x: x != "WAIVE" and not x.endswith("VIA"),
                    suggested_random_orders,
                )
            )
            if len(suggested_random_orders) > 0:
                commands = dipnet_to_daide_parsing(suggested_random_orders, self.game)
                random_orders = [XDO(command) for command in commands]
                suggested_random_orders = PRP(optional_AND(random_orders))
                # send the other power a message containing the orders
                await self.send_message(
                    other_power, str(suggested_random_orders), msgs_data
                )

        return list(orders)

    async def gen_orders(self) -> List[str]:
        possible_orders = self.game.get_all_possible_orders()
        orders = [
            random.choice([ord for ord in possible_orders[loc]])
            for loc in self.game.get_orderable_locations(self.power_name)
            if possible_orders[loc]
        ]
        return orders
