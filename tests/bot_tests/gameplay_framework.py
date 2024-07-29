"""A framework to test bots."""

from typing import List

from diplomacy import Game

from chiron_utils.bots.baseline_bot import BaselineBot


class GamePlay:
    """A simple framework to test multiple bots together."""

    def __init__(
        self,
        game: Game,
        bots: List[BaselineBot],
        msg_rounds: int,
    ) -> None:
        """Construct a `GamePlay` object.

        Args:
            game: Game to orchestrate.
            bots: Instantiated bots playing in the game.
            msg_rounds: Maximum number of phases to play.
        """
        assert len(bots) <= 7, "too many bots"
        self.bots = bots
        self.game = game
        self.max_turns = msg_rounds

    async def play(self) -> None:
        """Play a game with the bots."""
        turn = 0
        while not self.game.is_game_done and turn < self.max_turns:
            await self.step()
            turn += 1

    async def step(self) -> None:
        """Carry out one game phase."""
        if self.game.is_game_done:
            return

        while not self.game.get_current_phase().endswith("M"):
            self.game.process()
            if self.game.is_game_done:
                return

        for bot in self.bots:
            # get and send orders to be sent from bot
            orders = await bot()
            await bot.send_orders(orders)

        self.game.process()
