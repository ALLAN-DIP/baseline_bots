"""Unit tests for `RandomProposerPlayer`."""
import asyncio
import datetime
import os

from diplomacy import Game
from diplomacy.client.connection import connect
from gameplay_framework import GamePlay
import pytest
from tornado import testing
from tornado.testing import AsyncTestCase
from typing_extensions import Final

from chiron_utils.bots import RandomProposerPlayer
from chiron_utils.game_utils import DEFAULT_PORT

SOA_TEST_PARAMS: Final = {
    "num_message_rounds": 3,
}


class TestBots(AsyncTestCase):
    """Tests for `RandomProposerPlayer` bot."""

    @testing.gen_test
    def test_play_simple(self):  # type: ignore[no-untyped-def]
        """Test sending a single message in a local game."""
        game = Game()
        soa_bot = RandomProposerPlayer("FRANCE", game)
        yield soa_bot.send_message("FRANCE", "A PAR - BUR")

    @testing.gen_test
    def test_play(self):  # type: ignore[no-untyped-def]
        """Test playing a local 3-phase game with all `RandomProposerPlayer` bots."""
        game = Game()

        game_play = GamePlay(
            game,
            [
                RandomProposerPlayer("AUSTRIA", game, **SOA_TEST_PARAMS),
                RandomProposerPlayer("ENGLAND", game, **SOA_TEST_PARAMS),
                RandomProposerPlayer("FRANCE", game, **SOA_TEST_PARAMS),
                RandomProposerPlayer("RUSSIA", game, **SOA_TEST_PARAMS),
                RandomProposerPlayer("GERMANY", game, **SOA_TEST_PARAMS),
                RandomProposerPlayer("ITALY", game, **SOA_TEST_PARAMS),
                RandomProposerPlayer("TURKEY", game, **SOA_TEST_PARAMS),
            ],
            3,
        )

        yield game_play.play()
        print("finish test_play")

    @pytest.mark.skipif(
        "CI" in os.environ,  # Do not run in CI because it does not have access to server
        reason="Requires running Diplomacy server",  # type: ignore[no-untyped-def]
        # Not clear why `mypy` requires the ignore to be on the above line
        # instead of on the function declaration itself
    )
    @testing.gen_test
    def test_send_message(self):
        """Test playing a network 3-phase game with a single `RandomProposerPlayer` bot."""
        hostname = "localhost"
        port = DEFAULT_PORT

        connection = yield connect(hostname, port, use_ssl=False)
        channel = yield connection.authenticate("userX", "password")

        now = datetime.datetime.now(datetime.timezone.utc)
        game_id = f"usc_soa_test_{now.strftime('%Y_%m_%d_%H_%M_%S_%f')}"
        yield channel.create_game(
            game_id=game_id,
            n_controls=1,
            deadline=30,
            rules={"REAL_TIME", "NO_DEADLINE", "POWER_CHOICE"},
        )

        # Waiting for the game, then joining it
        while not (yield channel.list_games(game_id=game_id)):
            yield asyncio.sleep(1.0)

        channel = yield connection.authenticate("userX", "password")
        game = yield channel.join_game(game_id=game_id, power_name="FRANCE")

        soa_bot1 = RandomProposerPlayer("FRANCE", game, **SOA_TEST_PARAMS)

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
        assert any("PRP" in msg.message for msg in rcvd_messages)
        print("finish test_send_message")
