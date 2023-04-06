"""Abstract base classes for baseline bots"""


from abc import ABC, abstractmethod
from typing import List

from diplomacy import Game, Message
from diplomacy_research.players.benchmark_player import DipNetRLPlayer, DipNetSLPlayer
from diplomacy_research.players.model_based_player import ModelBasedPlayer

from baseline_bots.bots.baseline_bot import BaselineMsgRoundBot
from baseline_bots.utils import MessagesData, OrdersData


class DipnetBot(BaselineMsgRoundBot, ABC):
    """Abstract Base Class for dipnet derivative bots"""

    brain: ModelBasedPlayer

    def __init__(
        self,
        power_name: str,
        game: Game,
        total_msg_rounds: int = 3,
        dipnet_type: str = "slp",
    ) -> None:
        super().__init__(power_name, game, total_msg_rounds)
        if dipnet_type == "slp":
            self.brain = DipNetSLPlayer()
        else:
            self.brain = DipNetRLPlayer()

    @abstractmethod
    def gen_messages(self, rcvd_messages: List[Message]) -> MessagesData:
        """sets messages to be sent"""
        raise NotImplementedError()

    def gen_orders(self) -> OrdersData:
        """finalizes moves"""
        self.orders = self.player.get_orders(self.game, self.power_name)
        print(self.orders)
        return self.orders
