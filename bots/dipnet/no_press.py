__author__ = "Wichayaporn Wongkamjan"

import random
import sys
sys.path.append("..")
sys.path.append("../..")

from utils import get_order_tokens
from baseline_bot import BaselineBot

class PressDipBot(BaselineBot):
    """just execute orders computed by dipnet"""

    