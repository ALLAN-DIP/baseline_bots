"""unit tests for smart order accepter bot"""
from diplomacy import Game
from tornado import testing
from tornado.testing import AsyncTestCase

from baseline_bots.bots import RandomProposerBot
from baseline_bots.utils import MessagesData


class TestSimpleSOABot(AsyncTestCase):
    @testing.gen_test
    def test_play(self):
        game = Game()
        soa_bot = RandomProposerBot("FRANCE", game)
        msg_data = MessagesData()
        yield soa_bot.send_message("FRANCE", "A PAR - BUR", msg_data)
