import sys
sys.path.append("..")

from gameplay_framework import GamePlay
from bots.baseline_bot import BaselineBot

from bots.random_proposer_bot import RandomProposerBot

from bots.loyal_bot import LoyalBot

game_play = GamePlay(None, [RandomProposerBot, RandomProposerBot], 3)
game_play.play()

game_play = GamePlay(None, [LoyalBot, RandomProposerBot], 3)
game_play.play()
