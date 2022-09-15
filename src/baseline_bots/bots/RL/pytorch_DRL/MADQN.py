import numpy as np
import torch as th
from common.Memory import ReplayMemory
from common.Model import ActorNetwork
from common.utils import to_tensor_var
from torch import nn
from torch.optim import Adam, RMSprop


class MADQN(object):
    """
    An multi-agent learned with DQN using replay memory and temporal difference
    - use a value network to estimate the state-action value
    """

    def __init__(self):
        """
        TODO
        """
        pass
