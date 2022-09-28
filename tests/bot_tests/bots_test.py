"""unit tests for bots"""
from gameplay_framework import GamePlay

from baseline_bots import BaselineBot
from baseline_bots import RandomProposerBot
from baseline_bots import PushoverBot
from baseline_bots import RandomAllierProposerBot
from baseline_bots import RandomHonestBot
from baseline_bots import RandomHonestOrderAccepterBot
from baseline_bots import LoyalBot
from baseline_bots import SmartOrderAccepterBot

class TestRPBot():
    def test(self):
        game_play = GamePlay(None, [RandomProposerBot, RandomProposerBot], 3, True)
        actions, done = game_play.step()
        print(actions)
        game_play = GamePlay(None, [LoyalBot, RandomProposerBot], 3)
        game_play.play()

# game_play = GamePlay(None, [PushoverBot, RandomProposerBot], 3)
# game_play.play()

# game_play = GamePlay(None, [RandomAllierProposerBot, RandomAllierProposerBot], 3)
# game_play.play()

# game_play = GamePlay(None, [RandomHonestBot, RandomHonestBot], 3)
# game_play.play()

# game_play = GamePlay(None, [RandomProposerBot, RandomHonestOrderAccepterBot], 3)
# game_play.play()

class TestSOABot():
    def test(self):
        from diplomacy import Game

        soa_bot = SmartOrderAccepterBot('AUS', Game())
        assert soa_bot.get_proposals([[0, "PRP (ORR (XDO (F KIE - DEN) XDO (A BER - KIE) (XDO A MUN RUH))"]])