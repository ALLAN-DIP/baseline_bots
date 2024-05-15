import random
from typing import List

from daidepp import PRP, XDO
from diplomacy import Game

from baseline_bots.bots.baseline_bot import BaselineBot
from baseline_bots.parsing_utils import dipnet_to_daide_parsing
from baseline_bots.utils import MessagesData, get_other_powers, optional_AND


class RandomProposerBot(BaselineBot):
    """
    Just sends random order proposals to other bots.
    """

    def __init__(self, power_name: str, game: Game) -> None:
        super().__init__(power_name, game)

    async def gen_messages(self) -> MessagesData:
        # Return data initialization
        ret_obj = MessagesData()

        if self.game.get_current_phase()[-1] != "M":
            return ret_obj
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
                orders = [XDO(command) for command in commands]
                suggested_random_orders = PRP(optional_AND(orders))
                # send the other power a message containing the orders
                ret_obj.add_message(other_power, str(suggested_random_orders))

        return ret_obj

    async def gen_orders(self) -> List[str]:
        possible_orders = self.game.get_all_possible_orders()
        orders = [
            random.choice([ord for ord in possible_orders[loc]])
            for loc in self.game.get_orderable_locations(self.power_name)
            if possible_orders[loc]
        ]
        return orders

    async def __call__(self) -> List[str]:
        """
        :return: dict containing messages and orders
        """
        orders = await self.gen_orders()

        # Only communication in the movement phase
        if self.game.get_current_phase().endswith("M"):
            messages = await self.gen_messages()
            await self.send_messages(messages)

        return orders
