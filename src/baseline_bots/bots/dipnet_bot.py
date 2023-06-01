"""Abstract base classes for baseline bots"""


from abc import ABC
from typing import List

from diplomacy import Game
from diplomacy_research.players.benchmark_player import DipNetRLPlayer, DipNetSLPlayer
from diplomacy_research.players.model_based_player import ModelBasedPlayer

from baseline_bots.bots.baseline_bot import BaselineMsgRoundBot


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

    async def gen_orders(self) -> List[str]:
        """finalizes moves"""
        return await self.brain.get_orders(self.game, self.power_name)
