from typing import List

from diplomacy import Game

from baseline_bots.bots.baseline_bot import BaselineBot


class GamePlay:
    """
    A simple framework to test multiple bots together
    """

    max_turns: int = 20

    def __init__(
        self,
        game: Game,
        bots: List[BaselineBot],
        msg_rounds: int,
    ) -> None:
        assert len(bots) <= 7, "too many bots"
        self.bots = bots
        self.game = game
        self.msg_rounds = msg_rounds
        self.cur_local_message_round = 0

    async def play(self) -> None:
        """play a game with the bots"""

        turn = 0
        while not self.game.is_game_done and turn < self.max_turns:
            await self.step()
            turn += 1

    async def step(self) -> None:
        """one step of messaging"""

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

        self.cur_local_message_round += 1

        if self.cur_local_message_round == self.msg_rounds:
            self.game.process()
