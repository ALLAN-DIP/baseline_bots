import sys
from typing import List, Optional, Tuple, Type, Union

from diplomacy import Game, Message
from diplomacy.utils import common
from diplomacy.utils.export import to_saved_game_format
from tornado import gen

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

    @gen.coroutine
    def play(self) -> None:
        """play a game with the bots"""

        turn = 0
        while not self.game.is_game_done and turn < self.max_turns:
            yield self.step()
            turn += 1

        if self.save_json:
            to_saved_game_format(self.game, output_path="GamePlayFramework.json")

    def phase_init_bots(self) -> None:
        self.cur_local_message_round = 0
        # reset bot round info
        for bot in self.bots:
            if isinstance(bot, BaselineMsgRoundBot):
                bot.phase_init()

    @gen.coroutine
    def step(self) -> Tuple[Optional[dict], bool]:
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

            # get messages to be sent from bot
            ret_dict = yield bot()

            if "messages" in ret_dict:
                bot_messages = ret_dict["messages"]  # bot.gen_messages(rcvd_messages)

                msgs_to_send[bot.power_name] = bot_messages

        # Send all messages after all bots decide
        for power_name in msgs_to_send:
            msgs = msgs_to_send[power_name]
            for msg in msgs:
                msg_obj = Message(
                    sender=power_name,
                    recipient=msg["recipient"],
                    message=msg["message"],
                    phase=self.game.get_current_phase(),
                    time_sent=common.timestamp_microseconds(),
                )
                self.game.add_message(message=msg_obj)

        # get/set orders
        for bot in self.bots:
            if bot is None:
                continue
            if hasattr(bot, "orders") and ret_dict["orders"] is not None:
                orders = ret_dict["orders"]
                if hasattr(orders, "get_list_of_orders"):
                    orders = orders.get_list_of_orders()
                self.game.set_orders(power_name=bot.power_name, orders=orders)

        self.cur_local_message_round += 1

        self.game.process()
        return {"messages": msgs_to_send}, self.game.is_game_done
