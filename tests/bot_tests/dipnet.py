from gameplay_framework import GamePlay
from baseline_bots.bots.dipnet.selectively_transparent_bot import (
    SelectivelyTransparentBot,
)

game_play = GamePlay(None, [SelectivelyTransparentBot, SelectivelyTransparentBot], 3)
