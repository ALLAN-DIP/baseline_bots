import sys
sys.path.append("..")
sys.path.append("../..")

from baseline_bots.gameplay_framework import GamePlay
from baseline_bots.bots.dipnet.selectively_transparent_bot import SelectivelyTransparentBot

game_play = GamePlay(None, [SelectivelyTransparentBot, SelectivelyTransparentBot], 3)
