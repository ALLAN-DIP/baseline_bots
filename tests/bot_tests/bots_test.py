"""unit tests for bots"""
from gameplay_framework import GamePlay
from gameplay_framework_async import GamePlayAsync
import pytest
from tornado.testing import AsyncTestCase, gen_test

from baseline_bots.bots.dipnet.no_press_bot import NoPressDipBot
from baseline_bots.bots.dipnet.pushoverdipnet import PushoverDipnet
from baseline_bots.bots.dipnet.selectively_transparent_bot import (
    SelectivelyTransparentBot,
)
from baseline_bots.bots.dipnet.transparent_bot import TransparentBot
from baseline_bots.bots.loyal_bot import LoyalBot
from baseline_bots.bots.pushover_bot import PushoverBot
from baseline_bots.bots.random_allier_proposer_bot import RandomAllierProposerBot
from baseline_bots.bots.random_honest_bot import RandomHonestBot
from baseline_bots.bots.random_honest_order_accepter_bot import (
    RandomHonestOrderAccepterBot,
)
from baseline_bots.bots.random_no_press import RandomNoPressBot
from baseline_bots.bots.random_proposer_bot import (
    RandomProposerBot,
    RandomProposerBot_AsyncBot,
)


class TestOtherBots(AsyncTestCase):
    def test_no_press_vs_no_press(self):
        game_play = GamePlay(None, [RandomNoPressBot, RandomNoPressBot], 3, True)
        game_play.play()

    @gen_test
    def test_no_press_dip_vs_no_press_dip(self):
        game_play = GamePlayAsync(None, [NoPressDipBot, NoPressDipBot], 3, True)
        yield game_play.play()

    @gen_test
    def test_pushover_dip_vs_random_proposer(self):
        game_play = GamePlayAsync(
            None, [PushoverDipnet, RandomProposerBot_AsyncBot], 3, True
        )
        yield game_play.play()

    @gen_test
    def test_transparent_vs_random_proposer(self):
        game_play = GamePlayAsync(
            None, [TransparentBot, RandomProposerBot_AsyncBot], 3, True
        )
        yield game_play.play()

    @pytest.mark.xfail(
        reason="`DAIDE` library cannot parse a message, even though `daidepp` can",
        strict=True,
    )
    @gen_test
    def test_selectively_transparent_vs_random_proposer(self):
        game_play = GamePlayAsync(
            None, [SelectivelyTransparentBot, RandomProposerBot_AsyncBot], 3, True
        )
        yield game_play.play()

    def test_random_proposer_vs_random_proposer(self):
        game_play = GamePlay(None, [RandomProposerBot, RandomProposerBot], 3, True)
        game_play.play()

    def test_loyal_vs_random_proposer(self):
        game_play = GamePlay(None, [LoyalBot, RandomProposerBot], 3)
        game_play.play()

    def test_pushover_vs_random_proposer(self):
        game_play = GamePlay(None, [PushoverBot, RandomProposerBot], 3)
        game_play.play()

    def test_random_allier_proposer_vs_random_allier_proposer(self):
        game_play = GamePlay(
            None, [RandomAllierProposerBot, RandomAllierProposerBot], 3
        )
        game_play.play()

    def test_random_honest_vs_random_honest(self):
        game_play = GamePlay(None, [RandomHonestBot, RandomHonestBot], 3)
        game_play.play()

    def test_random_proposer_vs_random_honest_order_accepter(self):
        game_play = GamePlay(None, [RandomProposerBot, RandomHonestOrderAccepterBot], 3)
        game_play.play()
