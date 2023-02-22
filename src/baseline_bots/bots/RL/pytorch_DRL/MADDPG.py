from copy import deepcopy

from common.Memory import ReplayMemory
from common.Model import ActorNetwork, CriticNetwork
from common.utils import to_tensor_var
import numpy as np
import torch as th
import torch.nn as nn
from torch.optim import Adam, RMSprop


class MADDPG(object):
    """
    An multi-agent learned with Deep Deterministic Policy Gradient using Actor-Critic framework
    - Actor takes state as input
    - Critic takes both state and action as input
    """

    def __init__(self):
        """
        TODO
        """
        pass
