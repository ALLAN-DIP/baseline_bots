"""unit tests for bots"""

import sys
sys.path.append("..")
sys.path.append("../..")
sys.path.append("../../..")
import unittest

from gameplay_framework import GamePlay

from bots.baseline_bot import BaselineBot
from bots.random_proposer_bot import RandomProposerBot
from bots.pushover_bot import PushoverBot
from bots.random_allier_proposer_bot import RandomAllierProposerBot
from bots.random_honest_bot import RandomHonestBot
from bots.random_honest_order_accepter_bot import RandomHonestOrderAccepterBot
from bots.loyal_bot import LoyalBot

class TestRPBot(unittest.TestCase):
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


if __name__ == '__main__':
    unittest.main()