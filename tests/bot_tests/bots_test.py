"""unit tests for bots"""
from gameplay_framework import GamePlay
from tornado.testing import AsyncTestCase, gen_test

from baseline_bots.bots import RandomProposerBot


class TestOtherBots(AsyncTestCase):
    @gen_test
    def test_random_proposer_vs_random_proposer(self):
        game_play = GamePlay(None, [RandomProposerBot, RandomProposerBot], 3, True)
        yield game_play.play()
