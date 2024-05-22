import random
from typing import List, Sequence

from baseline_bots.bots.baseline_bot import BaselineBot
from baseline_bots.utils import MessagesData


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
        await self.send_message(
            "GLOBAL", f"Current game round: {self.game.get_current_phase()}", msgs_data
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
