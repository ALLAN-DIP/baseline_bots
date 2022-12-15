"""unit tests for smart order accepter bot"""
import asyncio
import random

import tornado
from diplomacy import Game, Message
from diplomacy.client.connection import connect
from diplomacy_research.utils.cluster import start_io_loop, stop_io_loop
from gameplay_framework_async import GamePlayAsync
from tornado import gen, testing
from tornado.testing import AsyncTestCase

from baseline_bots.bots.baseline_bot import BaselineBot, BaselineMsgRoundBot
from baseline_bots.bots.random_proposer_bot import RandomProposerBot_AsyncBot
from baseline_bots.bots.smart_order_accepter_bot import SmartOrderAccepterBot
from baseline_bots.parsing_utils import (
    daide_to_dipnet_parsing,
    dipnet_to_daide_parsing,
    parse_proposal_messages,
)
from baseline_bots.utils import (
    MessagesData,
    OrdersData,
    get_best_orders,
    get_order_tokens,
    get_other_powers,
    get_state_value,
    parse_alliance_proposal,
    parse_arrangement,
    parse_PRP,
)


class TestSOABot(AsyncTestCase):
    @testing.gen_test
    def test_play(self):
        game = Game()
        soa_bot1 = SmartOrderAccepterBot("FRANCE", game, test_mode=True)

        soa_bot2 = SmartOrderAccepterBot("RUSSIA", game, test_mode=True)
        game_play = GamePlayAsync(
            game,
            [
                RandomProposerBot_AsyncBot("AUSTRIA", game, test_mode=True),
                RandomProposerBot_AsyncBot("ENGLAND", game, test_mode=True),
                soa_bot1,
                soa_bot2,
                RandomProposerBot_AsyncBot("GERMANY", game, test_mode=True),
                RandomProposerBot_AsyncBot("ITALY", game, test_mode=True),
                RandomProposerBot_AsyncBot("TURKEY", game, test_mode=True),
            ],
            3,
            True,
        )

        # test 1 round
        test_rounds_count = 1
        while test_rounds_count:
            msgs, done = yield game_play.step()
            test_rounds_count -= 1
        print("finish test_play")

    @testing.gen_test
    def test_send_message(self):
        hostname = "shade.tacc.utexas.edu"
        port = 8432
        game_id = None

        connection = yield connect(hostname, port)
        channel = yield connection.authenticate("userX", "password")

        game_created = False
        while not (game_created):
            game_id = "usc_soa_test_" + str(random.randint(0, 10000))
            try:
                game = yield channel.create_game(
                    game_id=game_id,
                    rules={"REAL_TIME", "NO_DEADLINE", "POWER_CHOICE"},
                    deadline=30,
                    n_controls=1,
                    registration_password="",
                    daide_port=None,
                )
                game_created = True
            except:
                # game not created because of same game id
                pass

        # Waiting for the game, then joining it
        while not (yield channel.list_games(game_id=game_id)):
            yield asyncio.sleep(1.0)

        channel = yield connection.authenticate("userX", "password")
        game = yield channel.join_game(game_id=game_id, power_name="FRANCE")

        soa_bot1 = SmartOrderAccepterBot("FRANCE", game, test_mode=False)

        game_play = GamePlayAsync(
            game,
            [
                soa_bot1,
                None,
                None,
                None,
                None,
                None,
                None,
            ],
            3,
            True,
        )

        # test 1 round
        test_rounds_count = 1
        while test_rounds_count:
            msgs, done = yield game_play.step()
            test_rounds_count -= 1

            # Check any other country (randomly chosen RUSSIA here for this purpose) for messages received. SOA bot by design sends ALY message to all other bots
            rcvd_messages = list(
                game_play.game.filter_messages(
                    messages=game_play.game.messages, game_role="RUSSIA"
                ).values()
            )
            print([msg.message for msg in rcvd_messages])
            # message count should be non-zero
            assert len(rcvd_messages) != 0

            # Note this is a valid test case since we know ALY is sent by SOA bot to all other powers in the beginning and this is the only bot amongst 7 powers
            assert any(["ALY" in msg.message for msg in rcvd_messages])
        print("finish test_send_message")

    @testing.gen_test
    def test_respond_to_invalid_orders(self):
        game = Game()
        soa_bot = SmartOrderAccepterBot("FRANCE", game, test_mode=True)
        RESPOND_TO_INV_ORDERS_TC = [
            [
                {
                    "RUSSIA": [("A PRU - LVN", "TUR"), (("A PRU - MOS", "RUS"))],
                    "AUSTRIA": [("A PRU - LVN", "ENG")],
                },
                [
                    {
                        "recipient": "RUSSIA",
                        "message": "HUH (PRP (ORR (XDO ((TUR AMY PRU) MTO LVN)) (XDO ((RUS AMY PRU) MTO MOS))))",
                    },
                    {
                        "recipient": "AUSTRIA",
                        "message": "HUH (PRP (XDO ((ENG AMY PRU) MTO LVN)))",
                    },
                ],
            ]
        ]

        for tc_ip, tc_op in RESPOND_TO_INV_ORDERS_TC:
            msg_data = MessagesData()
            yield soa_bot.respond_to_invalid_orders(tc_ip, msg_data)
            assert msg_data.messages == tc_op, (msg_data.messages, tc_op)

    @testing.gen_test
    def test_respond_to_alliance_messages(self):
        game = Game()
        soa_bot = SmartOrderAccepterBot("FRANCE", game, test_mode=True)
        RESPOND_TO_ALLIANCES_TC = [
            [
                {
                    "RUSSIA": [("RUSSIA", "ALY (TUR RUS ENG ITA) VSS (FRA GER AUS)")],
                    "ENGLAND": [("RUSSIA", "ALY (TUR RUS ENG ITA) VSS (FRA GER AUS)")],
                    "ITALY": [("RUSSIA", "ALY (TUR RUS ENG ITA) VSS (FRA GER AUS)")],
                },
                [
                    {
                        "recipient": "RUSSIA",
                        "message": "YES (ALY (TUR RUS ENG ITA) VSS (FRA GER AUS))",
                    }
                ],
            ]
        ]

        for tc_ip, tc_op in RESPOND_TO_ALLIANCES_TC:
            msg_data = MessagesData()
            soa_bot.alliances = tc_ip
            yield soa_bot.respond_to_alliance_messages(msg_data)
            assert msg_data.messages == tc_op, (msg_data.messages, tc_op)

        stop_io_loop()

    @testing.gen_test
    def test_score_stance(self):
        # score-based
        game = Game()
        soa_bot = SmartOrderAccepterBot("FRANCE", game, test_mode=True, stance_type="S")
        bot_instances = [
            RandomProposerBot_AsyncBot("AUSTRIA", game, test_mode=True),
            RandomProposerBot_AsyncBot("ENGLAND", game, test_mode=True),
            RandomProposerBot_AsyncBot("GERMANY", game, test_mode=True),
            soa_bot,
        ]
        game_play = GamePlayAsync(game, bot_instances, 3, True)
        game_play.game.set_centers("AUSTRIA", ["VIE", "TRI", "BUD"], reset=True)
        game_play.game.set_centers("ENGLAND", ["LON"], reset=True)
        game_play.game.set_centers("GERMANY", ["MUN", "KIE", "BER", "BEL"])
        game_play.game.set_centers(soa_bot.power_name, ["PAR", "BRE", "MAR"])
        msgs, done = yield game_play.step()
        soa_bot_stance = soa_bot.stance.get_stance()[soa_bot.power_name]
        print(game_play.game.get_centers())
        print("expected stance ENGLAND: 1, GERMANY: -1, AUTRIA:0")
        print("soa stance", soa_bot_stance)
        assert soa_bot_stance["ENGLAND"] == 1, "Positive stance error"
        assert soa_bot_stance["GERMANY"] == -1, "Negative stance error"
        assert soa_bot_stance["AUSTRIA"] == 0, "Neutral stance error"

        print("finish test_stance")
        stop_io_loop()

    @testing.gen_test
    def test_action_stance(self):
        # score-based
        game = Game()
        soa_bot = SmartOrderAccepterBot("FRANCE", game, test_mode=True)
        bot_instances = [
            RandomProposerBot_AsyncBot("ENGLAND", game, test_mode=True),
            RandomProposerBot_AsyncBot("GERMANY", game, test_mode=True),
            soa_bot,
        ]
        game_play = GamePlayAsync(game, bot_instances, 3, True)
        game_play.game.set_orders("FRANCE", ["A MAR H", "A PAR H", "F BRE - PIC"])
        game_play.game.set_orders(
            "ENGLAND", ["A LVP - WAL", "F EDI - NTH", "F LON - ENG"]
        )
        game_play.game.set_orders(
            "GERMANY", ["A BER - MUN", "A MUN - BUR", "F KIE - HOL"]
        )
        game_play.game.process()
        game_play.game.set_orders("FRANCE", ["A MAR - BUR", "A PAR - BRE", "F PIC H"])
        game_play.game.set_orders(
            "ENGLAND", ["A WAL - BEL VIA", "F ENG C A WAL - BEL", "F NTH - HEL"]
        )
        game_play.game.set_orders("GERMANY", ["A BUR - MAR", "A MUN - RUH", "F HOL H"])
        game_play.game.process()
        game_play.game.set_orders("ENGLAND", ["A LON B"])
        game_play.game.set_orders("GERMANY", ["A MUN B"])
        game_play.game.process()
        game_play.game.set_orders("FRANCE", ["A BRE H", "A MAR - GAS", "F PIC H"])
        game_play.game.set_orders(
            "ENGLAND", ["A BEL S F PIC", "F ENG S A BRE", "F HEL - HOL"]
        )
        game_play.game.set_orders("GERMANY", ["A BUR - PAR", "A RUH - BUR", "F HOL H"])
        game_play.game.process()
        game_play.game.set_orders(
            "FRANCE", ["A BRE - PAR", "A GAS - BUR", "F PIC - BEL"]
        )
        game_play.game.set_orders(
            "ENGLAND", ["A BEL - HOL", "F ENG S F PIC - BEL", "F HEL S A BEL - HOL"]
        )
        game_play.game.set_orders(
            "GERMANY", ["A BUR S A PAR - PIC", "A PAR - PIC", "F HOL H"]
        )
        game_play.game.process()
        soa_bot_stance = soa_bot.stance.get_stance(game_play.game)[soa_bot.power_name]
        print(soa_bot_stance)

        print("expected stance ENGLAND >0, GERMANY<0")
        print("soa stance", soa_bot_stance)
        assert soa_bot_stance["ENGLAND"] > 0.0, "Positive stance error"
        assert soa_bot_stance["GERMANY"] < 0.0, "Negative stance error"

        print("finish test_stance")
        stop_io_loop()

    @testing.gen_test
    def test_ally_move_filter(self):
        # assume that stance is correct using score-based
        game = Game()
        soa_bot = SmartOrderAccepterBot("FRANCE", game, test_mode=True)
        soa_bot.ally_threshold = 1.0
        bot_instances = [
            RandomProposerBot_AsyncBot("ENGLAND", game, test_mode=True),
            RandomProposerBot_AsyncBot("GERMANY", game, test_mode=True),
            soa_bot,
        ]
        game_play = GamePlayAsync(game, bot_instances, 3, True)
        game_play.game.set_centers("ENGLAND", ["LON"], reset=True)
        game_play.game.set_centers("GERMANY", ["MUN", "KIE", "BER", "BEL"])
        game_play.game.set_centers(soa_bot.power_name, ["PAR", "BRE", "MAR"])
        game_play.game.set_orders("FRANCE", ["A MAR - BUR", "A PAR - PIC", "F BRE H"])
        game_play.game.set_orders(
            "ENGLAND", ["A LVP - WAL", "F EDI - NTH", "F LON - ENG"]
        )
        game_play.game.process()
        orders = ["F BRE - ENG", "A PIC - BEL", "A BUR - PIC"]
        orders_data = OrdersData()
        orders_data.add_orders(orders)
        soa_bot.orders = orders_data

        print("aggressive order: ", orders)
        soa_bot_stance = soa_bot.stance.get_stance(game_play.game)[soa_bot.power_name]
        print(
            "soa stance",
            {k: v for k, v in soa_bot_stance.items() if v >= soa_bot.ally_threshold},
        )
        yield soa_bot.replace_aggressive_order_to_allies()
        print("remove non-aggressive", soa_bot.orders.get_list_of_orders())

        print("finish test ally move filter")
        stop_io_loop()

    @testing.gen_test
    def test_parse_proposals(self):
        # proposal messages -> proposal dict {power_name: a list of proposal orders}
        # valid moves and power units must belong to SOA
        game = Game()
        soa_bot = SmartOrderAccepterBot("FRANCE", game, test_mode=True)
        baseline1 = RandomProposerBot_AsyncBot("AUSTRIA", game, test_mode=True)
        baseline2 = RandomProposerBot_AsyncBot("ENGLAND", game, test_mode=True)
        bot_instances = [baseline1, baseline2, soa_bot]
        game_play = GamePlayAsync(game, bot_instances, 3, True)
        rcvd_messages = game_play.game.filter_messages(
            messages=game_play.game.messages, game_role="AUSTRIA"
        )
        bl1_msg = yield baseline1.gen_messages(rcvd_messages)
        rcvd_messages = game_play.game.filter_messages(
            messages=game_play.game.messages, game_role="ENGLAND"
        )
        bl2_msg = yield baseline2.gen_messages(rcvd_messages)

        for msg in bl1_msg:
            msg_obj1 = Message(
                sender=baseline1.power_name,
                recipient=msg["recipient"],
                message=msg["message"],
                phase=game_play.game.get_current_phase(),
            )
            game_play.game.add_message(message=msg_obj1)

        for msg in bl2_msg:
            msg_obj2 = Message(
                sender=baseline2.power_name,
                recipient=msg["recipient"],
                message=msg["message"],
                phase=game_play.game.get_current_phase(),
            )
            game_play.game.add_message(message=msg_obj2)

        rcvd_messages = game.filter_messages(
            messages=game_play.game.messages, game_role=soa_bot.power_name
        )
        rcvd_messages = list(rcvd_messages.items())
        rcvd_messages.sort()
        parsed_messages_dict = parse_proposal_messages(
            rcvd_messages, game_play.game, soa_bot.power_name
        )
        valid_proposal_orders = parsed_messages_dict["valid_proposals"]

        # print('parsed_messages_dict ', parsed_messages_dict)
        possible_orders = game_play.game.get_all_possible_orders()

        soa_power_units = game_play.game.powers[soa_bot.power_name].units[:]

        for power, orders in valid_proposal_orders.items():
            for order in orders:
                order_token = get_order_tokens(order)
                unit_order = order_token[0]
                unit_loc = unit_order.split()[1]
                assert unit_order in soa_power_units, (
                    "unit in "
                    + order
                    + " does not belong to SOA's power ("
                    + soa_bot.power_name
                    + ")"
                )
                assert order in possible_orders[unit_loc], (
                    order
                    + " is not possible in this current phase of a game for SOA's power ("
                    + soa_bot.power_name
                    + ")"
                )
        print("finish test_parse_proposal")
        stop_io_loop()

    @testing.gen_test
    def test_gen_pos_stance_messages(self):
        # gen for only allies
        game = Game()
        soa_bot = SmartOrderAccepterBot("FRANCE", game, test_mode=True, stance_type="S")
        soa_bot.ally_threshold = 0.5
        bot_instances = [
            RandomProposerBot_AsyncBot("AUSTRIA", game, test_mode=True),
            RandomProposerBot_AsyncBot("ENGLAND", game, test_mode=True),
            RandomProposerBot_AsyncBot("GERMANY", game, test_mode=True),
            RandomProposerBot_AsyncBot("RUSSIA", game, test_mode=True),
            soa_bot,
        ]
        game_play = GamePlayAsync(game, bot_instances, 3, True)

        # skip 1 game phase for the test to work correctly
        game_play.game.process()
        game_play.game.set_centers("AUSTRIA", ["VIE", "TRI", "BUD"], reset=True)
        game_play.game.set_centers("ENGLAND", ["LON"], reset=True)
        game_play.game.set_centers("RUSSIA", ["MOS"], reset=True)
        game_play.game.set_centers("GERMANY", ["MUN", "KIE", "BER", "BEL"])
        game_play.game.set_centers(soa_bot.power_name, ["PAR", "BRE", "MAR"])
        rcvd_messages = game.filter_messages(
            messages=game_play.game.messages, game_role=soa_bot.power_name
        )
        rcvd_messages = list(rcvd_messages.items())
        rcvd_messages.sort()
        ret_data = yield soa_bot(rcvd_messages)
        soa_bot_stance = soa_bot.stance.get_stance()[soa_bot.power_name]
        print(game_play.game.get_centers())
        print("expected stance ENGLAND: 1, RUSSIA: 1, GERMANY: -1, AUTRIA:0")
        print("soa stance", soa_bot_stance)
        print(
            "recipients of messages:",
            [msg["recipient"] for msg in ret_data["messages"]],
        )

        assert (
            "ENGLAND" in soa_bot.allies and "RUSSIA" in soa_bot.allies
        ), f"SOA bot is sending FCT orders to these powers: {soa_bot.allies}"
        print("test pos_stance_msg")
        stop_io_loop()
