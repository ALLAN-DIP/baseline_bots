"""Abstract base classes for baseline bots"""


from abc import ABC

from diplomacy import Game
from diplomacy_research.players.benchmark_player import DipNetRLPlayer, DipNetSLPlayer
from diplomacy_research.players.model_based_player import ModelBasedPlayer

from baseline_bots.bots.baseline_bot import BaselineMsgRoundBot
from baseline_bots.utils import OrdersData


class DipnetBot(BaselineMsgRoundBot, ABC):
    """Abstract Base Class for dipnet derivative bots
    """



    brain: ModelBasedPlayer

    # allaince_bots = ['rus_tuk','rus_frc','rus_ger','rus_aust','rus_eng','rus_itl']


    def __init__(
        self,
        power_name: str,
        game: Game,
        total_msg_rounds: int = 3,
        dipnet_type: str = "slp",
        alliance_bots: list = ['RUSSIA_TURKEY','RUSSIA_FRANCE'],
    ) -> None:
        super().__init__(power_name, game, total_msg_rounds)
    
        if dipnet_type == "slp":
            self.brain = DipNetSLPlayer(tf_model_name='player',name='main_bot')
                      
            # self.alliance_brains = {'al1':DipNetSLPlayer(model_name='alliance_player1',name='al1'),
            #                         'al2':DipNetSLPlayer(model_name='alliance_player1',name='al2'),
            #                         'al3':DipNetSLPlayer(model_name='alliance_player1',name='al3'),
            #                         'al4':DipNetSLPlayer(model_name='alliance_player1',name='al4'),
            #                         'al5':DipNetSLPlayer(model_name='alliance_player1',name='al5'),
            #                         'al6':DipNetSLPlayer(model_name='alliance_player1',name='al6')
            #        
            #                  }
            # print(alliance_bots)
            if alliance_bots:
                self.alliance_brains = {alliance_bots[i]:DipNetSLPlayer(tf_model_name=alliance_bots[i],name=alliance_bots[i]) for i in range(len(alliance_bots))}
            else:
                self.alliance_brains = {}
            # print(self.alliance_brains)
        else:
            self.brain = DipNetRLPlayer()

    def gen_orders(self) -> OrdersData:
        """finalizes moves"""
        self.orders = self.brain.get_orders(self.game, self.power_name)
        print(self.orders)
        return self.orders
