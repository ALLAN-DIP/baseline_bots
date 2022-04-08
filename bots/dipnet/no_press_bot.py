__author__ = "Sander Schulhoff"
__email__ = "sanderschulhoff@gmail.com"

import random
import sys

from bots.dipnet.dipnet_bot import DipnetBot

sys.path.append("..")
sys.path.append("../..")

from utils import get_order_tokens

class NoPressDipBot(DipnetBot):
    """just execute orders computed by dipnet"""

    def gen_orders(self):
        """query dipnet for orders"""
        pass

    def gen_messages(self, _):
        if not self.orders:
            self.orders = self.player.get_orders(self.game, self.power_name)
        return self.orders