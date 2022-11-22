from baseline_bots.bots.dipnet.selectively_transparent_bot import (
    SelectivelyTransparentBot,
)
from baseline_bots.gameplay_framework import GamePlay

game_play = GamePlay(None, [SelectivelyTransparentBot, SelectivelyTransparentBot], 3)
