__author__ = "Sander Schulhoff"
__email__ = "sanderschulhoff@gmail.com"

import random
import sys
sys.path.append("..")
sys.path.append("../..")

from utils import get_order_tokens
from baseline_bot import BaselineBot

class SelectivelyTransparent(BaselineBot):
    """
    Execute orders computed by dipnet
    Send out some of them randomly
    """

    def gen_orders(self):
        """query dipnet for orders"""
        pass

    def gen_messages(self, _):
        return None