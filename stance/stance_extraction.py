"""
    Stance vector modules
    
    Tested on the turn-level game logs in
    https://github.com/DenisPeskov/2020_acl_diplomacy/blob/master/utils/ExtraGameData.zip
    
"""

from abc import ABC, abstractmethod

class StanceExtraction(ABC):
    """
        Abstract Base Class for stance vector extraction
    """
    def __init__(self, my_identity, nations) -> None:
        self.identity = my_identity
        self.nations = nations
        self.current_round = 0
        self.territories = {n:[] for n in self.nations}
        self.stance = None
        
    def extract_terr(self, game_rec):
        """
            Extract current terrirories for each nation from 
               game_rec: the turn-level JSON log of a game
        """
        terr = {n:[] for n in self.nations}
        for city in game_rec["territories"].keys():
            terr[game_rec["territories"][city]].append(city)
        return terr
    
    @abstractmethod
    def get_stance(self, log, messages) -> dict:
        """
            Abstract method to extract stance of nation n on nation k,
            for all pairs of nations n, k at the current round, given
            the game history and messages
                log: the turn-level JSON log 
                     or a list of turn-level logs of the game,
                messages: a dict of dialog lists with other nations in a given round
            Returns a bi-level dictionary stance[n][k]
        """
        raise NotImplementedError()
        
        
class ActionBasedStance(StanceExtraction):
    """
        A turn-level action-based objective stance vector baseline
        "Whoever attacks me is my enemy, whoever supports me is my friend."
        Stance on nation k =  
            - α1 * count(k’s hostile moves) 
            - α2 * count(k’s conflict moves)
            - β1 * k’s count(hostile supports/convoys) 
            - β2 * count(k’s conflict supports/convoys)
            + γ1 * count(k’s friendly supports/convoys)
    """
    def __init__(self, my_identity, nations,
                 invasion_coef=1.0, conflict_coef=0.5,
                 invasive_support_coef=1.0, conflict_support_coef=0.5,
                 friendly_coef=1.0) -> None:
        super().__init__(my_identity, nations)
        # hyperparametes weighting different actions
        self.alpha1 = invasion_coef
        self.alpha2 = conflict_coef
        self.beta1 = invasive_support_coef
        self.beta2 = conflict_support_coef
        self.gamma1 = friendly_coef
    
    def extract_hostile_moves(self, nation, game_rec):
        """
            Extract hostile moves toward a nation and evaluate 
            the hostility scores it holds to other nations
                nation: standing point
                game_rec: the turn-level JSON log of a game
            Returns
                hostility: a dict of hostility move scores of the given nation
                hostile_moves: a list of hostile moves against the given nation
                conflict_moves: a list of conflict moves against the given nation
        """
        hostility = {n:0 for n in self.nations}
        hostile_moves = []
        conflit_moves = []
        
        # extract my target cities
        my_targets = []
        if nation in game_rec["orders"].keys():
            for unit in game_rec["orders"][nation].keys():
                if game_rec["orders"][nation][unit]["type"] in ["MOVE"]:
                    target = game_rec["orders"][nation][unit]["to"]
                    if target not in self.territories[nation]:
                        my_targets.append(target)

        # extract other's hostile MOVEs
        for opp in self.nations:
            if opp == nation: continue
            if opp not in game_rec["orders"].keys(): continue
            for unit in game_rec["orders"][opp].keys():
                if game_rec["orders"][opp][unit]["type"] in ["MOVE"]:
                    target = game_rec["orders"][opp][unit]["to"]
                    # invasion or cut support/convoy
                    if target in self.territories[nation]:
                        hostility[opp] += self.alpha1
                        hostile_moves.append(unit+"-"+target)
                    # seize the same city
                    elif target in my_targets:
                        hostility[opp] += self.alpha2
                        conflit_moves.append(unit+"-"+target)
                        
        return hostility, hostile_moves, conflit_moves
                    
    def extract_hostile_supports(self, nation, hostile_mov, conflit_mov, game_rec):
        """
            Extract hostile support toward a nation and evaluate 
            the hostility scores it holds to other nations
                nation: standing point
                hostile_mov: a list of hostile moves against the given nation
                conflit_mov: a list of conflict moves against the given nation
                game_rec: the turn-level JSON log of a game
            Returns
                hostility: dict of hostility support scores of the given nation
                hostile_supports: list of hostile supports against the given nation
                conflit_supports: list of conflict supports against the given nation
        """
        hostility = {n:0 for n in self.nations}
        hostile_supports = []
        conflit_supports = []

        # extract other's hostile MOVEs
        for opp in self.nations:
            if opp == nation: continue
            if opp not in game_rec["orders"].keys(): continue
            for unit in game_rec["orders"][opp].keys():
                if game_rec["orders"][opp][unit]["type"] in ["SUPPORT", "CONVOY"]:
                    source = game_rec["orders"][opp][unit]["from"]
                    # if not supporting a HOLD
                    if "to" in game_rec["orders"][opp][unit].keys():
                        target = game_rec["orders"][opp][unit]["to"]
                        support = source+"-"+target
                        # support invasion or support a cut support/convoy
                        if support in hostile_mov:
                            hostility[opp] += self.beta1
                            hostile_supports.append(unit+":"+source+"-"+target)
                        # support an attack to seize the same city
                        elif target in conflit_mov:
                            hostility[opp] += self.beta2
                            conflit_supports.append(unit+":"+source+"-"+target)

        return hostility, hostile_supports, conflit_supports
    
    def extract_friendly_supports(self, nation, game_rec):
        """
            Extract friendly support toward a nation and evaluate 
            the friend scores it holds to other nations
                nation: standing point
                game_rec: the turn-level JSON log of a game
            Returns
                friendship: dict of friend scores of the given nation
                friendly_supports: list of friendly supports for the given nation
        """
        friendship = {n:0 for n in self.nations}
        friendly_supports = []

        # extract others' friendly SUPPORT
        for opp in self.nations:
            if opp == nation: continue
            if opp not in game_rec["orders"].keys(): continue
            for unit in game_rec["orders"][opp].keys():
                if game_rec["orders"][opp][unit]["type"] in ["SUPPORT", "CONVOY"]:
                    source = game_rec["orders"][opp][unit]["from"]
                    # any kind of support to me
                    if source in self.territories[nation]:
                        friendship[opp] += self.gamma1
                        if "to" in game_rec["orders"][opp][unit].keys():
                            target = game_rec["orders"][opp][unit]["to"] 
                            friendly_supports.append(unit+":"+source+"-"+target)
                        else: 
                            friendly_supports.append(unit+":"+source)

        return friendship, friendly_supports
    
    def get_stance(self, game_rec, message=None):
        """
            Extract turn-level objective stance of nation n on nation k.
                game_rec: the turn-level JSON log of a game,
                messages is not used
            Returns a bi-level dictionary of stance score stance[n][k]
        """
        
        # extract territory info
        self.territories = self.extract_terr(game_rec)

        # extract hostile moves
        hostililty_to, hostile_mov_to, conflit_mov_to = {}, {}, {}
        for n in self.nations:
            hostililty_to[n], hostile_mov_to[n], conflit_mov_to[n] = self.extract_hostile_moves(
                n, game_rec)

        # extract hostile supports
        hostililty_s_to, hostile_sup_to, conflit_sup_to = {}, {}, {}
        for n in self.nations:
            hostililty_s_to[n], hostile_sup_to[n], conflit_sup_to[n] = self.extract_hostile_supports(
                n, hostile_mov_to[n], conflit_mov_to[n], game_rec)

        # extract friendly supports
        friendship_to, friendly_sup_to = {}, {}
        for n in self.nations:
            friendship_to[n], friendly_sup_to[n] = self.extract_friendly_supports(n, game_rec)

        self.stance = {n: {k: -hostililty_to[n][k] -hostililty_s_to[n][k] +friendship_to[n][k]
                         for k in self.nations}
                  for n in self.nations}
    
        return self.stance

import numpy as np

class ScoreBasedStance(StanceExtraction):
    """
        A turn-level score-based subjective stance vector baseline
        "Whoever stronger than me must be evil, whoever weaker than me can be my ally."
        Stance on nation k = 
            sign(my score - k’s score)
    """
    def __init__(self, my_identity, nations) -> None:
        super().__init__(my_identity, nations)
        self.scores = None
        self.stance = None
        
    def extract_scores(self, game_rec):
        """
            Extract scores at the end of each round.
                game_rec: the turn-level JSON log of a game,
            Returns a dict of scores for all nations
        """
        scores = {n:0 for n in self.nations}
        sc_info = game_rec['sc'].split()
        for i, n in enumerate(sc_info):
            if n in self.nations:
                scores[n] = int(sc_info[i+1])
        return scores
    
    def get_stance(self, game_rec, message=None):
        """
            Extract turn-level subjective stance of nation n on nation k.
                game_rec: the turn-level JSON log of a game,
                messages is not used
            Returns a bi-level dictionary of stance score stance[n][k]
        """
        # extract territory info
        self.scores = self.extract_scores(game_rec)

        self.stance = {n: {k: np.sign(self.scores[n]-self.scores[k]) if self.scores[n] > 0 else 0
                         for k in self.nations}
                  for n in self.nations}
        
        return self.stance
    