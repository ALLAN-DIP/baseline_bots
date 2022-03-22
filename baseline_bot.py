__author__ = "Sander Schulhoff"
__email__ = "sanderschulhoff@gmail.com"

from abc import ABC, abstractmethod

class BaselineBot(ABC):
    """Abstract Base Class for baselines bots"""
    def __init__(self, power_name, game) -> None:
        self.power_name = power_name
        self.game = game
        self.possible_orders = game.get_all_possible_orders()

    @abstractmethod
    def act(self) -> None:
        """set moves and send messages"""
        raise NotImplementedError()