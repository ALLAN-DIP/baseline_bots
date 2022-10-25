"""
Some quickly built utils mostly for DAIDE stuff
"""

__author__ = "Kartik Shenoy"
__email__ = "kartik.shenoyy@gmail.com"
import re
from collections import defaultdict
from typing import Dict, List, Tuple, Union

from DAIDE.utils.exceptions import ParseError
from diplomacy import Game, Message

from baseline_bots.utils import *


