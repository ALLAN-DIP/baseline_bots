"""unit tests for smart order accepter bot"""
import asyncio
import datetime

from diplomacy import Game
from diplomacy.client.connection import connect
from gameplay_framework import GamePlay  # TODO: Fix sorting
from tornado import testing
from tornado.testing import AsyncTestCase
from typing_extensions import Final

from baseline_bots.bots.random_proposer_bot import RandomProposerBot
from baseline_bots.utils import MessagesData

SOA_TEST_PARAMS: Final = {
    "num_message_rounds": 3,
}


class TestSOABot(AsyncTestCase):
    @testing.gen_test
    def test_play_simple(self):
        game = Game()
        soa_bot = RandomProposerBot("FRANCE", game)
        msg_data = MessagesData()
        yield soa_bot.send_message("FRANCE", "A PAR - BUR", msg_data)

    @testing.gen_test
    def test_play(self):
        game = Game()

        game_play = GamePlay(
            game,
            [
                RandomProposerBot("AUSTRIA", game, **SOA_TEST_PARAMS),
                RandomProposerBot("ENGLAND", game, **SOA_TEST_PARAMS),
                RandomProposerBot("FRANCE", game, **SOA_TEST_PARAMS),
                RandomProposerBot("RUSSIA", game, **SOA_TEST_PARAMS),
                RandomProposerBot("GERMANY", game, **SOA_TEST_PARAMS),
                RandomProposerBot("ITALY", game, **SOA_TEST_PARAMS),
                RandomProposerBot("TURKEY", game, **SOA_TEST_PARAMS),
            ],
            3,
        )

        yield game_play.play()
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
            now = datetime.datetime.now(datetime.timezone.utc)
            game_id = f"usc_soa_test_{now.strftime('%Y_%m_%d_%H_%M_%S_%f')}"
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
            except Exception:
                # game not created because of same game id
                pass

        # Waiting for the game, then joining it
        while not (yield channel.list_games(game_id=game_id)):
            yield asyncio.sleep(1.0)

        channel = yield connection.authenticate("userX", "password")
        game = yield channel.join_game(game_id=game_id, power_name="FRANCE")

        soa_bot1 = RandomProposerBot("FRANCE", game, **SOA_TEST_PARAMS)

        game_play = GamePlay(
            game,
            [
                soa_bot1,
            ],
            3,
        )

        yield game_play.step()

        # Check any other country (randomly chosen RUSSIA here for this purpose)
        # for messages received. SOA bot by design sends ALY message to all other bots
        rcvd_messages = list(
            game_play.game.filter_messages(
                messages=game_play.game.messages, game_role="RUSSIA"
            ).values()
        )
        print([msg.message for msg in rcvd_messages])
        # message count should be non-zero
        assert len(rcvd_messages) != 0

        # Note this is a valid test case since we know ALY is sent by SOA bot to
        # all other powers in the beginning and this is the only bot amongst 7 powers
        assert any(["ALY" in msg.message for msg in rcvd_messages])
        print("finish test_send_message")
