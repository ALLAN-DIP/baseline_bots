"""Bots that carry out random orders and make random order proposals."""

from abc import ABC
import random
from typing import ClassVar, Dict, List, Sequence

from daidepp import AND, PRP, XDO

from chiron_utils.bots.baseline_bot import BaselineBot
from chiron_utils.parsing_utils import dipnet_to_daide_parsing
from chiron_utils.utils import get_other_powers


class RandomProposerBot(BaselineBot, ABC):
    """Bot that carries out random orders and sends random order proposals to other bots.

    Because of the similarity between the advisor and player versions of this bot,
    both of their behaviors are abstracted into this single abstract base class.
    """

    is_first_messaging_round = False

    async def start_phase(self) -> None:
        """Execute actions at the start of the phase."""
        self.is_first_messaging_round = True

    def get_random_proposal_orders(self) -> Dict[str, str]:
        """Generate random order proposals for other powers.

        Returns:
            Mapping from powers to random order proposals.
        """
        # Getting the list of possible orders for all locations
        possible_orders = self.game.get_all_possible_orders()

        proposals = {}

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
                if len(random_orders) > 1:
                    suggested_random_orders = PRP(AND(*random_orders))
                else:
                    suggested_random_orders = PRP(*random_orders)

                proposals[other_power] = str(suggested_random_orders)

        return proposals

    async def do_messaging_round(self, orders: Sequence[str]) -> List[str]:
        """Carry out one round of messaging, along with related tasks.

        Returns:
            List of orders to carry out.
        """
        if not self.is_first_messaging_round:
            return list(orders)

        random_order_proposals = self.get_random_proposal_orders()

        for other_power, suggested_random_orders in random_order_proposals.items():
            if self.bot_type == "advisor":
                await self.suggest_message(other_power, (suggested_random_orders))
            elif self.bot_type == "player":
                await self.send_message(other_power, (suggested_random_orders))

        self.is_first_messaging_round = False

        return list(orders)

    def get_random_orders(self) -> List[str]:
        """Generate random orders to carry out.

        Returns:
            List of random orders.
        """
        possible_orders = self.game.get_all_possible_orders()
        orders = [
            random.choice(list(possible_orders[loc]))
            for loc in self.game.get_orderable_locations(self.power_name)
            if possible_orders[loc]
        ]
        return orders

    async def gen_orders(self) -> List[str]:
        """Generate orders for a turn.

        Returns:
            List of orders to carry out.
        """
        orders = self.get_random_orders()
        if self.bot_type == "advisor":
            await self.suggest_orders(orders)
        return orders


class RandomProposerAdvisor(RandomProposerBot):
    """Advisor form of `RandomProposerBot`."""

    bot_type: ClassVar[str] = "advisor"


class RandomProposerPlayer(RandomProposerBot):
    """Player form of `RandomProposerBot`."""

    bot_type: ClassVar[str] = "player"
