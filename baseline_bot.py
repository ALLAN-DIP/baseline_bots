__author__ = "Sander Schulhoff"
__email__ = "sanderschulhoff@gmail.com"

from abc import ABC, abstractmethod

from daide_utils import OrdersData


class BaselineBot(ABC):
    """Abstract Base Class for baselines bots"""
    def __init__(self, power_name, game) -> None:
        self.power_name = power_name
        self.game = game
        self.possible_orders = game.get_all_possible_orders()
        self.total_comms_rounds = 0
        self.curr_comms_round = 1
        self.current_phase = ""
        self.selected_orders = OrdersData()
        self.my_influence = set()

    def phase_init(self):
        self.curr_comms_round = 1
        self.possible_orders = self.game.get_all_possible_orders()
        self.current_phase = self.game.get_current_phase()
        self.selected_orders = OrdersData()
        self.my_influence = set(self.game.get_power(self.power_name).influence)

    def config(self, config):
        self.total_comms_rounds = config['comms_rounds']

    def comms_rounds_completed(self):
        return self.curr_comms_round == self.total_comms_rounds

    @abstractmethod
    def comms(self, rcvd_messages):
        """sets messages to be sent"""
        raise NotImplementedError()

    @abstractmethod
    def act(self) -> None:
        """finalizes moves"""
        raise NotImplementedError()