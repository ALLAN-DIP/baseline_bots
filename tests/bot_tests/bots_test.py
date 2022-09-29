"""unit tests for bots"""
from gameplay_framework import GamePlay
import diplomacy_research
print(diplomacy_research)
from baseline_bots import BaselineBot
from baseline_bots import RandomProposerBot
from baseline_bots import PushoverBot
from baseline_bots import RandomAllierProposerBot
from baseline_bots import RandomHonestBot
from baseline_bots import RandomHonestOrderAccepterBot
from baseline_bots import LoyalBot
from baseline_bots.bots.dipnet.RealPolitik import RealPolitik

class TestRPBot():
    def test(self):
        game_play = GamePlay(None, [RandomProposerBot, RandomProposerBot], 3, True)
        actions, done = game_play.step()
        print(actions)
        game_play = GamePlay(None, [LoyalBot, RandomProposerBot], 3)
        game_play.play()
        game_play = GamePlay(None, [RealPolitik, RandomProposerBot], 3)
        game_play.play()

# game_play = GamePlay(None, [PushoverBot, RandomProposerBot], 3)
# game_play.play()

# game_play = GamePlay(None, [RandomAllierProposerBot, RandomAllierProposerBot], 3)
# game_play.play()

# game_play = GamePlay(None, [RandomHonestBot, RandomHonestBot], 3)
# game_play.play()

# game_play = GamePlay(None, [RandomProposerBot, RandomHonestOrderAccepterBot], 3)
# game_play.play()
