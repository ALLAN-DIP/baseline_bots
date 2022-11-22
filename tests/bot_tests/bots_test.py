"""unit tests for bots"""
from gameplay_framework import GamePlay

from baseline_bots.bots.baseline_bot import BaselineBot
from baseline_bots.bots.loyal_bot import LoyalBot
from baseline_bots.bots.pushover_bot import PushoverBot
from baseline_bots.bots.random_allier_proposer_bot import RandomAllierProposerBot
from baseline_bots.bots.random_honest_bot import RandomHonestBot
from baseline_bots.bots.random_honest_order_accepter_bot import (
    RandomHonestOrderAccepterBot,
)
from baseline_bots.bots.random_proposer_bot import RandomProposerBot


class TestRPBot:
    def test(self):
        game_play = GamePlay(None, [RandomProposerBot, RandomProposerBot], 3, True)
        actions, done = game_play.step()
        game_play = GamePlay(None, [LoyalBot, RandomProposerBot], 3)
        game_play.play()
        # game_play = GamePlay(None, [RealPolitik, RandomProposerBot], 3)
        # game_play.play()


# game_play = GamePlay(None, [PushoverBot, RandomProposerBot], 3)
# game_play.play()

# game_play = GamePlay(None, [RandomAllierProposerBot, RandomAllierProposerBot], 3)
# game_play.play()

# game_play = GamePlay(None, [RandomHonestBot, RandomHonestBot], 3)
# game_play.play()

# game_play = GamePlay(None, [RandomProposerBot, RandomHonestOrderAccepterBot], 3)
# game_play.play()
