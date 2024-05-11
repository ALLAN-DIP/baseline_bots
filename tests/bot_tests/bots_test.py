"""unit tests for bots"""
from gameplay_framework import GamePlay
from tornado.testing import AsyncTestCase, gen_test

from baseline_bots.bots import RandomProposerBot


class TestOtherBots(AsyncTestCase):
    @gen_test
    def test_no_press_dip_vs_no_press_dip(self):
        game_play = GamePlay(None, [NoPressDipBot, NoPressDipBot], 3, True)
        yield game_play.play()

    @gen_test
    def test_pushover_dip_vs_random_proposer(self):
        game_play = GamePlay(None, [PushoverDipnet, RandomProposerBot], 3, True)
        yield game_play.play()

    @gen_test
    def test_transparent_vs_random_proposer(self):
        game_play = GamePlay(None, [TransparentBot, RandomProposerBot], 3, True)
        yield game_play.play()

    @gen_test
    def test_selectively_transparent_vs_random_proposer(self):
        game_play = GamePlay(
            None, [SelectivelyTransparentBot, RandomProposerBot], 3, True
        )
        yield game_play.play()

    @gen_test
    def test_random_proposer_vs_random_proposer(self):
        game_play = GamePlay(None, [RandomProposerBot, RandomProposerBot], 3, True)
        yield game_play.play()
