__authors__ = ["Sander Schulhoff"]
__email__ = "sanderschulhoff@gmail.com"

import random
import sys
sys.path.append("..")
sys.path.append("../..")

from baseline_bots.utils import MessagesData, parse_orr_xdo, parse_FCT, ORR, XDO, FCT, get_other_powers
from baseline_bots.bots.dipnet.transparent_bot import TransparentBot
from collections import defaultdict
from tornado import gen

class SelectivelyTransparentBot(TransparentBot):
    """
    Execute orders computed by dipnet
    Sends out non-aggressive actions 
    """

    @gen.coroutine
    def gen_messages(self, rcvd_messages):
        messages = super().gen_messages(rcvd_messages)

if __name__ == "__main__":
    import sys
