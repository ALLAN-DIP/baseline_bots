"""unit tests for bots"""
from gameplay_framework import GamePlay
import pytest
from tornado.testing import AsyncTestCase, gen_test

from baseline_bots.bots.dipnet.no_press_bot import NoPressDipBot
from baseline_bots.bots.dipnet.pushoverdipnet import PushoverDipnet
from baseline_bots.bots.dipnet.selectively_transparent_bot import (
    SelectivelyTransparentBot,
)
from baseline_bots.bots.dipnet.transparent_bot import TransparentBot
from baseline_bots.bots.random_proposer_bot import RandomProposerBot


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

    @pytest.mark.xfail(
        reason="`DAIDE` library cannot parse a message, even though `daidepp` can",
        strict=True,
    )
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
