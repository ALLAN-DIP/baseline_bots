import sys
from typing import List, Optional, Tuple, Type, Union

from diplomacy import Game
from diplomacy.utils.export import to_saved_game_format

from baseline_bots.bots.baseline_bot import BaselineBot, BaselineMsgRoundBot

sys.path.append("../../../dipnet_press")


class GamePlay:
    """
    A simple framework to test multiple bots together
    """

    max_turns: int = 20

    def __init__(
        self,
        game: Game,
        bots: List[Union[BaselineBot, Type[BaselineBot]]],
        msg_rounds: int,
        save_json: bool = False,
    ) -> None:
        assert len(bots) <= 7, "too many bots"
        # if no game is passed, assume bots is a list of bot classes to
        # be instantiated.
        if game is None:
            # make game
            game = Game()
            # get list of powers
            power_names = list(game.get_map_power_names())
            inst_bots = []
            # instantiate each bot
            for i, bot_class in enumerate(bots):
                inst_bots.append(bot_class(power_names[i], game))
            self.bots = inst_bots
        else:
            self.bots = bots

        self.game = game
        self.msg_rounds = msg_rounds
        self.save_json = save_json
        self.cur_local_message_round = 0
        self.phase_init_bots()

    async def play(self) -> None:
        """play a game with the bots"""

        turn = 0
        while not self.game.is_game_done and turn < self.max_turns:
            await self.step()
            turn += 1

        if self.save_json:
            to_saved_game_format(self.game, output_path="GamePlayFramework.json")

    def phase_init_bots(self) -> None:
        self.cur_local_message_round = 0
        # reset bot round info
        for bot in self.bots:
            if isinstance(bot, BaselineMsgRoundBot):
                bot.phase_init()

    async def step(self) -> Tuple[Optional[dict], bool]:
        """one step of messaging"""

        if self.game.is_game_done:
            return None, True

        # if message rounds over
        if self.cur_local_message_round == self.msg_rounds:
            self.phase_init_bots()
        while self.game.get_current_phase()[-1] != "M":
            self.game.process()
            if self.game.is_game_done:
                return None, True

        msgs_to_send = {}
        for bot in self.bots:
            if bot is None:
                continue

            # get orders to be sent from bot
            orders = await bot()

        # get/set orders
        for bot in self.bots:
            if bot is None:
                continue
            self.game.set_orders(power_name=bot.power_name, orders=orders)

        self.cur_local_message_round += 1

        if self.cur_local_message_round == self.msg_rounds:
            self.game.process()
        return {"messages": msgs_to_send}, self.game.is_game_done
