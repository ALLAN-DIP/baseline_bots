"""Abstract base classes for baseline bots"""


from abc import ABC
from typing import List, Optional, Tuple

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

    async def get_brain_orders(
        self, game: Optional[Game] = None, power_name: Optional[str] = None
    ) -> List[str]:
        if game is None:
            game = self.game
        if power_name is None:
            power_name = self.power_name
        return await self.brain.get_orders(game, power_name)

    async def get_brain_beam_orders(
        self, game: Optional[Game] = None, power_name: Optional[str] = None
    ) -> Tuple[List[str], List[float]]:
        if game is None:
            game = self.game
        if power_name is None:
            power_name = self.power_name
        return await self.brain.get_beam_orders(game, power_name)

    async def gen_orders(self) -> List[str]:
        """finalizes moves"""
        return await self.get_brain_orders()
