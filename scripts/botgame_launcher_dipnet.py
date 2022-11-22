import argparse
import sys
from time import time

import ujson as json
from diplomacy import Game, Message
from diplomacy.utils.export import to_saved_game_format

sys.path.append("..")
sys.path.append("../dipnet_press")
sys.path.append("./bots/RL/")
sys.path.append("./bots/RL/models")

import asyncio
import os

from bots.baseline_bot import BaselineMsgRoundBot
from bots.dipnet.dipnet_proposer_bot import ProposerDipBot
from bots.dipnet.loyal_support_proposal import LSP_DipBot
from bots.dipnet.no_press_bot import NoPressDipBot
from bots.dipnet.RealPolitik import RealPolitik
from bots.dipnet.selectively_transparent_bot import SelectivelyTransparentBot
from bots.dipnet.transparent_bot import TransparentBot
from bots.dipnet.transparent_proposer_bot import TransparentProposerDipBot
from bots.pushover_bot import PushoverBot_AsyncBot
from bots.random_loyal_support_proposal import RandomLSPBot
from bots.random_no_press import RandomNoPress_AsyncBot
from bots.random_proposer_bot import RandomProposerBot_AsyncBot
from diplomacy_research.utils.cluster import start_io_loop, stop_io_loop

# from bots.RL.RLProposerBot import RLProposerBot
# from bots.RL.DiplomacyEnv import DiplomacyEnv
from stance.stance_extraction import ScoreBasedStance, StanceExtraction
from tornado import gen
from utils import is_cross_support


def parse_args():
    parser = argparse.ArgumentParser(description="Analysis-Dip")
    parser.add_argument(
        "--powers",
        "-p",
        type=str,
        default="AUSTRIA,ITALY,ENGLAND,FRANCE,GERMANY,RUSSIA,TURKEY",
        help="comma-seperated country names (AUSTRIA,ITALY,ENGLAND,FRANCE,GERMANY,RUSSIA,TURKEY)",
    )
    parser.add_argument(
        "--filename", "-f", type=str, default="DipNetBotGame.json", help="json filename"
    )
    parser.add_argument(
        "--types",
        "-t",
        type=str,
        default="lspm,lsp,np,np,np,np,np",
        help="comma-seperated bottypes (lspm,lsp,np,np,np,np,np)",
    )

    args = parser.parse_args()
    print(args)
    return args


def is_in_instance_list(obj, instance_list):
    boo_v = False
    for instance in instance_list:
        boo_v = isinstance(obj, instance)
        if boo_v:
            break
    return boo_v


@gen.coroutine
def bot_loop():
    bots = []
    agent_id = 0
    for bot_power, bot_type in zip(args.powers.split(","), args.types.split(",")):
        if bot_type == "np":
            bot = NoPressDipBot(bot_power, game)
        elif bot_type == "re_np":
            bot = NoPressDipBot(bot_power, game, dipnet_type="rlp")
        elif bot_type == "rpbt":
            bot = RandomProposerBot_AsyncBot(bot_power, game)
        elif bot_type == "rnp":
            bot = RandomNoPress_AsyncBot(bot_power, game)
        elif bot_type == "push":
            bot = PushoverBot_AsyncBot(bot_power, game)
        elif bot_type.startswith("lsp"):
            bot = LSP_DipBot(bot_power, game, 3, alliance_all_in)
            if bot_type.endswith("m"):
                bot.set_leader()
        elif bot_type.startswith("rlsp"):
            bot = LSP_DipBot(bot_power, game, 3, alliance_all_in, dipnet_type="rlp")
            if bot_type.endswith("m"):
                bot.set_leader()
        elif bot_type == "tbt":
            bot = TransparentBot(bot_power, game, 3)
        elif bot_type == "stbt":
            bot = SelectivelyTransparentBot(bot_power, game, 3)
        elif bot_type == "tpbt":
            bot = TransparentProposerDipBot(bot_power, game, 3)
        elif bot_type == "pbt":
            bot = ProposerDipBot(bot_power, game, 3)
        elif bot_type == "rplt":
            bot = RealPolitik(bot_power, game, 3)
        # elif bot_type == "rlprop":
        #     env = DiplomacyEnv()
        #     env.game = game
        #     env.n_agents = 7
        #     #keep track of RL agents
        #     env.power_mapping[bot_power] = agent_id
        #     bot = RLProposerBot(bot_power, game, env, 3)
        # agent_id += 1
        bots.append(bot)
    start = time()
    stance = ScoreBasedStance("", powers)
    dict_support_count = {power: 0 for power in game.powers}
    dict_support_count["total"] = 0
    while not game.is_game_done:

        print(game.get_current_phase())
        for bot in bots:
            # if not game.powers[bot.power_name].is_eliminated():
            #     if isinstance(bot, BaselineMsgRoundBot):
            #         bot.phase_init()
            dip_instance_list = [
                NoPressDipBot,
                LSP_DipBot,
                TransparentBot,
                SelectivelyTransparentBot,
                TransparentProposerDipBot,
                ProposerDipBot,
                RealPolitik,
            ]  # , RLProposerBot]
            if is_in_instance_list(bot, dip_instance_list):
                bot.phase_init()

            # stance vector
            sc = {bot_power: len(game.get_centers(bot_power)) for bot_power in powers}
            stance_vec = stance.get_stance(game_rec=sc, game_rec_type="game")

            proposer_instance_list = [TransparentBot, ProposerDipBot, RealPolitik]
            if is_in_instance_list(bot, proposer_instance_list):
                bot.stance = stance_vec[bot.power_name]
        # print(game.get_current_phase())
        if game.get_current_phase()[-1] == "M":
            # Iterate through multiple rounds of comms during movement phases
            for _ in range(comms_rounds):
                round_msgs = game.messages
                to_send_msgs = {}
                for bot in bots:
                    if not game.powers[bot.power_name].is_eliminated():
                        # Retrieve messages
                        rcvd_messages = game.filter_messages(
                            messages=round_msgs, game_role=bot.power_name
                        )
                        rcvd_messages = list(rcvd_messages.items())
                        rcvd_messages.sort()

                        # Send messages to bots and fetch messages from bot
                        bot_messages = yield bot.gen_messages(rcvd_messages)

                        # If messages are to be sent, send them
                        if bot_messages and bot_messages.messages:
                            to_send_msgs[bot.power_name] = bot_messages.messages

                # Send all messages after all bots decide on comms
                for sender in to_send_msgs:
                    for msg in to_send_msgs[sender]:
                        msg_obj = Message(
                            sender=sender,
                            recipient=msg["recipient"],
                            message=msg["message"],
                            phase=game.get_current_phase(),
                        )
                        game.add_message(message=msg_obj)
            dict_support_count["total"] += 1
        for bot in bots:
            # if not game.powers[bot.power_name].is_eliminated():
            #     # Orders round
            #     orders = yield bot.gen_orders()
            #     # messages, orders = bot_state.messages, bot_state.orders

            #     if orders is not None:
            #         game.set_orders(power_name=bot.power_name, orders=orders)

            # __call__ for pushover bot to retrieve last order
            if isinstance(bot, PushoverBot_AsyncBot):
                rcvd_messages = game.filter_messages(
                    messages=game.messages, game_role=bot.power_name
                )
                rcvd_messages = list(rcvd_messages.items())
                rcvd_messages.sort()
                rcvd_messages = [msg for _, msg in rcvd_messages]

                return_obj = yield bot(rcvd_messages)
                for msg in return_obj["messages"]:
                    msg_obj = Message(
                        sender=sender,
                        recipient=msg["recipient"],
                        message=msg["message"],
                        phase=game.get_current_phase(),
                    )
                    game.add_message(message=msg_obj)

            # Orders round
            orders = yield bot.gen_orders()
            for order in orders:
                if is_cross_support(order, bot.power_name, game):
                    dict_support_count[bot.power_name] += 1
                    print(order)

            # messages, orders = bot_state.messages, bot_state.orders
            if orders is not None:
                game.set_orders(power_name=bot.power_name, orders=orders)

        game.process()
    print(dict_support_count)

    print(time() - start)
    # to_saved_game_format(game, output_path=args.filename)
    with open(args.filename, "w") as file:
        file.write(json.dumps(to_saved_game_format(game)))

    stop_io_loop()


if __name__ == "__main__":
    args = parse_args()
    comms_rounds = 3

    # game instance
    game = Game()
    powers = list(game.get_map_power_names())
    # powers = ['ENGLAND', 'FRANCE', 'GERMANY', 'ITALY', 'AUSTRIA', 'RUSSIA', 'TURKEY']

    assert len(args.powers.split(",")) == 7, "Powers specified are not 7"

    alliance_all_in = sum(typ.startswith("lsp") for typ in args.types.split(",")) == 7
    if alliance_all_in:
        print("Alliances are all in")

    config = {"comms_rounds": comms_rounds, "alliance_all_in": alliance_all_in}
    start_io_loop(bot_loop)
