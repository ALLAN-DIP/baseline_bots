"""unit tests for bots"""
from gameplay_framework import GamePlay
from tornado.testing import AsyncTestCase, gen_test

from baseline_bots.bots.no_press_bot import NoPressDipBot
from baseline_bots.bots.pushover_bot import PushoverDipnet
from baseline_bots.bots.random_proposer_bot import RandomProposerBot
from baseline_bots.bots.selectively_transparent_bot import SelectivelyTransparentBot
from baseline_bots.bots.transparent_bot import TransparentBot


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
