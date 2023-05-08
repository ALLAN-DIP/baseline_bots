import random
from typing import List

from DAIDE import ORR, PRP, XDO
from diplomacy import Game, Message
from diplomacy.client.network_game import NetworkGame

from baseline_bots.bots.baseline_bot import BaselineBot
from baseline_bots.parsing_utils import dipnet_to_daide_parsing
from baseline_bots.utils import (
    MessagesAndOrders,
    MessagesData,
    OrdersData,
    get_other_powers,
)


class RandomProposerBot(BaselineBot):
    """
    Just sends random order proposals to other bots.
    """

    def __init__(self, power_name: str, game: Game) -> None:
        super().__init__(power_name, game)

    async def gen_messages(self, _) -> MessagesData:
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
                filter(lambda x: x != "WAIVE", suggested_random_orders)
            )
            if len(suggested_random_orders) > 0:
                suggested_random_orders = PRP(
                    ORR(
                        [
                            XDO(order)
                            for order in dipnet_to_daide_parsing(
                                suggested_random_orders, self.game
                            )
                        ]
                    )
                )
                # send the other power a message containing the orders
                ret_obj.add_message(other_power, str(suggested_random_orders))

        return ret_obj

    async def gen_orders(self) -> List[str]:
        self.orders = OrdersData()
        possible_orders = self.game.get_all_possible_orders()

        orders = [
            random.choice([ord for ord in possible_orders[loc]])
            for loc in self.game.get_orderable_locations(self.power_name)
            if possible_orders[loc]
        ]

        self.orders.add_orders(orders)

        return self.orders.get_list_of_orders()

    async def __call__(self, rcvd_messages: List[Message]) -> MessagesAndOrders:
        """
        :return: dict containing messages and orders
        """
        messages = await self.gen_messages(rcvd_messages)

        if messages and messages.messages:
            for msg in messages.messages:
                msg_obj = Message(
                    sender=self.power_name,
                    recipient=msg["recipient"],
                    message=msg["message"],
                    phase=self.game.get_current_phase(),
                )
                if isinstance(self.game, NetworkGame):
                    await self.game.send_game_message(message=msg_obj)
        orders = await self.gen_orders()
        # maintain current orders
        self.orders = orders
        return {"messages": messages, "orders": orders}
