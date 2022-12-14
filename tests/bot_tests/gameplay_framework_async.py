__authors__ = ["Sander Schulhoff", "Kartik Shenoy"]
__email__ = "sanderschulhoff@gmail.com"

import sys
from typing import List

from diplomacy import Game, Message, connect
from diplomacy.utils import common
from diplomacy.utils.export import to_saved_game_format
from diplomacy_research.utils.cluster import start_io_loop, stop_io_loop
from tornado import gen

from baseline_bots.bots.baseline_bot import BaselineBot, BaselineMsgRoundBot
from baseline_bots.bots.random_proposer_bot import RandomProposerBot_AsyncBot

sys.path.append("../../../dipnet_press")

from gameplay_framework import GamePlay


class GamePlayAsync(GamePlay):
    @gen.coroutine
    def play(self):
        """play a game with the bots"""

        while not self.game.is_game_done:
            yield self.step()

        if self.save_json:
            to_saved_game_format(self.game, output_path="GamePlayFramework.json")

    @gen.coroutine
    def step(self):
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

        round_msgs = self.game.messages
        msgs_to_send = {}
        for bot in self.bots:
            if bot is None:
                continue
            # retrieve messages sent to bot
            rcvd_messages = self.game.filter_messages(
                messages=round_msgs, game_role=bot.power_name
            )

            # an array of Message objects
            rcvd_messages = list(rcvd_messages.items())

            # get messages to be sent from bot
            ret_dict = yield bot(rcvd_messages)

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
            if hasattr(bot, "orders"):
                orders = ret_dict["orders"]
                if orders is not None:
                    self.game.set_orders(power_name=bot.power_name, orders=orders)

        self.cur_local_message_round += 1

        self.game.process()
        return {"messages": msgs_to_send}, self.game.is_game_done


@gen.coroutine
def game_loop():
    game_play_obj = GamePlayAsync(
        None,
        [
            RandomProposerBot_AsyncBot,
            RandomProposerBot_AsyncBot,
            RandomProposerBot_AsyncBot,
        ],
        3,
        True,
    )
    yield game_play_obj.play()
    stop_io_loop()


if __name__ == "__main__":
    # from utils import OrdersData, MessagesData, get_order_tokens

    start_io_loop(game_loop)
