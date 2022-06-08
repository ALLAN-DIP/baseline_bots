import gym
import numpy as np
from tornado import gen
from diplomacy import Game
from diplomacy.engine.message import Message
from diplomacy.utils.export import to_saved_game_format
from diplomacy_research.players.benchmark_player import DipNetSLPlayer, DipNetRLPlayer
from diplomacy_research.utils.cluster import start_io_loop, stop_io_loop
from diplomacy_research.models.state_space import get_order_tokens
from bot_communication import Diplomacy_Press, Diplomacy_Press_Player
from pytorch_DRL.MAA2C import MAA2C
from pytorch_DRL.common.utils import ma_agg_double_list
import sys
import copy

# MAA2C: https://github.com/ChenglongChen/pytorch-DRL/

class DiplomacyEnv(gym.Env):
  def __init__(self):
    self.n_agents = 7
    self.sender_power = None
    self.state = 'no_sender' # env state no sender -> (with sender assigned but )no_order -> censoring if censored -> no_order - > no_sender
                   #                                          if not -> share_order ->  no_order  -> no_sender
    self.stance = 0.0
    self.agent_id = [id for id in range(self.n_agents)]
    self.order_type_id = [id for id in range(5)]
    self.power_mapping = {}
    self.order_type_mapping = {'move': 0, 'hold': 1, 'support':2, 'attack':3, 'convoy':4}
    self.power_type_mapping = {'self':0, 'neutral':1, 'ally':2, 'enemy':3 }
    """
    stance vector of [power1][power2],  
    send? 0/1
    orders:
            ['self', 'ally', 'neutral', 'enemy'] of unit's power, one hot 
            type of order, one hot 5 [move, hold, support, attack, convoy]
            ['self', 'ally', 'neutral', 'enemy'] of unit's power = attack whom/move to whose territory one hot 
    cur_obs for each agent and action for each agent
    """
    self.observation_space = gym.spaces.Box(low=np.array([-10.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]), 
                                            high=np.array([10.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]), 
                                            dtype=np.float32)
    self.action_space = gym.spaces.Discrete(2) # 
    self.cur_obs = None
    self.episode_len = 0
    self.dip_net = None
    self.dip_game = None
    self.ep_states = []
    self.ep_actions = []
    self.ep_rewards = []
    self.ep_info = []
    self.ep_n_states = []
    self.ep_dones = []

  
  def reset(self): 
    # return to initial state - Diplomacy game and DipNet reset
    # get stance vector, orders from framework
    self.ep_states = []
    self.ep_actions = []
    self.ep_rewards = []
    self.ep_info = []
    self.ep_n_states = []
    self.ep_dones = []
    self.dip_player =  Diplomacy_Press_Player(bot_type=['RL','RL','RL','RL','RL','RL','RL'], Player=DipNetRLPlayer())
    self.dip_game =  Diplomacy_Press(Game=Game(), Player=self.dip_player)
    self.dip_player.init_communication(self.dip_game.powers)
    # self.power_mapping = {power: id for power,id in zip(self.dip_game.powers,self.agent_id)}
    self.episode_len = 0
    # initial state = neutral for any power and no order OR having not assigned sender, recipient yet
    self.cur_obs = self.reset_cur_obs() 
    return self.cur_obs

  def set_power_state(self, power_a, stance_of_power_b):
    done = {agent_id: False for agent_id in self.agent_id}
    self.ep_dones.append(done) 
    action = {agent_id: 0 for agent_id in self.agent_id}
    self.ep_actions.append(action)
    self.ep_states.append(copy.deepcopy(self.cur_obs))
    self.ep_info.append(('no_sender', power_a, None, None))
    self.cur_obs[self.power_mapping[power_a]][0] = stance_of_power_b
    self.ep_n_states.append(self.cur_obs)
    self.state = 'no_order'
    
  def reset_cur_obs(self):
    return {agent_id: np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]) for agent_id in self.agent_id}
    
  def reset_power_state(self, power_a, power_b):
    if self.dip_game.game.is_game_done:
      done = {agent_id: True for agent_id in self.agent_id}
    else:  
      done = {agent_id: False for agent_id in self.agent_id}
      
    self.ep_dones.append(done) 
    action = {agent_id: 0 for agent_id in self.agent_id}
    self.ep_actions.append(action)
    self.ep_states.append(copy.deepcopy(self.cur_obs))
    self.ep_info.append(('no_more_order', power_a, power_b, None))
    self.cur_obs = self.reset_cur_obs() 
    self.ep_n_states.append(self.cur_obs)
    self.state = 'no_sender'
    
  def get_power_type(self, power_a, power_b):
    if power_a == power_b:
      return 'self'
    if self.dip_player.stance[power_a][power_b] < -1:
      return 'enemy'
    if self.dip_player.stance[power_a][power_b] > 1:
      return 'ally'
    return 'neutral'

  def index_order(self, one_hot_order,r_type='int'):
    #4,5,4
    index = []
    for i in range (len(one_hot_order)):
      if one_hot_order[i] ==1.:
        index.append(i)
    index[1] -=4
    for key, ind in self.order_type_mapping.items():
      if ind ==index[1]:
        index[1] = key
    if index[1] != 'hold' and index[1] != 'move':
      index[2] -=9
    if r_type=='int':
      return index
    else:
      for key, ind in self.power_type_mapping.items():
        if ind ==index[0]:
          index[0] = key
        if index[1] != 'hold' and index[1] != 'move' and ind ==index[2]:
          index[2] = key
      return index
      

  def one_hot_order(self, order, sender):
    order_token = get_order_tokens(order)
    # print('token: ', order_token)
    if order_token[0][0] =='A' or order_token[0][0] =='F':
      # this is message about orders
      power1 = self.get_unit_power(order_token[0])
      if order_token[1] == 'S':
        order_type = 'support'
        order_unit = order_token[2]
        power2 =self.get_unit_power(order_unit)
        return self.one_hot(self.power_type_mapping[self.get_power_type(sender, power1)], 4) + self.one_hot(self.order_type_mapping[order_type],5) + self.one_hot(self.power_type_mapping[self.get_power_type(sender, power2)], 4)
        
      elif order_token[1] == 'H':
        order_type = 'hold'
        return self.one_hot(self.power_type_mapping[self.get_power_type(sender, power1)], 4) + self.one_hot(self.order_type_mapping[order_type],5) + [0.0]*4
        
      elif order_token[1] == 'C':
        order_type = 'convoy'
        order_unit = order_token[2]
        power2 =self.get_unit_power(order_unit)
        return self.one_hot(self.power_type_mapping[self.get_power_type(sender, power1)], 4) + self.one_hot(self.order_type_mapping[order_type],5) + self.one_hot(self.power_type_mapping[self.get_power_type(sender, power2)], 4)
        
      else:
        #move/retreat or attack 
        #get location - add order_token[0] ('A' or 'F') at front to check if it collides with other powers' units
        order_unit = order_token[0][0] + order_token[1][1:]
        # print(order_unit)
        power2 =self.get_unit_power(order_unit)
        if power2 and power1!=power2:
          order_type= 'attack'
          return self.one_hot(self.power_type_mapping[self.get_power_type(sender, power1)], 4) + self.one_hot(self.order_type_mapping[order_type],5) + self.one_hot(self.power_type_mapping[self.get_power_type(sender, power2)], 4)
        else:
          order_type = 'move'
          return self.one_hot(self.power_type_mapping[self.get_power_type(sender, power1)], 4) + self.one_hot(self.order_type_mapping[order_type],5) + [0.0]*4

  def translate_order(self, order):
    order_info= []
    order_token = get_order_tokens(order)
    # print('token: ', order_token)
    if order_token[0][0] =='A' or order_token[0][0] =='F':
      # this is message about orders
      power1 = self.get_unit_power(order_token[0])
      order_info.append(power1)
      if order_token[1] == 'S':
        order_type = 'support'
        order_info.append(order_type)
        order_unit = order_token[2]
        power2 =self.get_unit_power(order_unit)
        order_info.append(power2)
        
      elif order_token[1] == 'H':
        order_type = 'hold'
        order_info.append(order_type)

        
      elif order_token[1] == 'C':
        order_type = 'convoy'
        order_info.append(order_type)
        order_unit = order_token[2]
        power2 =self.get_unit_power(order_unit)
        order_info.append(power2)
        
      else:
        #move/retreat or attack 
        #get location - add order_token[0] ('A' or 'F') at front to check if it collides with other powers' units
        order_unit = order_token[0][0] + order_token[1][1:]
        # print(order_unit)
        power2 =self.get_unit_power(order_unit)
        if power2 and power1!=power2:
          order_type= 'attack'
          order_info.append(order_type)
          order_info.append(power2)
        else:
          order_type = 'move'
          order_info.append(order_type)
    return order_info
        
  def get_unit_power(self, unit):
    for power in self.dip_game.powers:
      if unit in self.dip_game.powers[power].units:
        return power
      
  def one_hot(self, id, n):
    one_hot_list = [0.0 for i in range(n)]
    one_hot_list[id] = 1.
    return one_hot_list
    
  def step(self, action, power_a, power_b, order): 
    """
    input:  action=dictionary of agent action where action = Discrete(2) or 0 or 1, 
            power_a = sender, 
            power_b = receiver, 
            order = order we're considering 
    """

    
    if self.dip_game.game.is_game_done:
      done = {agent_id: True for agent_id in self.agent_id}
    else:  
      done = {agent_id: False for agent_id in self.agent_id}
      
    one_hot_order = self.one_hot_order(order, power_a)  
    self.ep_dones.append(done) 
    self.ep_actions.append(action)
    self.ep_states.append(copy.deepcopy(self.cur_obs))
    self.ep_info.append((self.state, power_a, power_b, one_hot_order))
    # print('state:', self.state)
    # print('check second last inserted obs: ', self.ep_states[-2])
    # print('last inserted obs: ', self.ep_states[-1])
    # print('action', action)
    agent_id = self.power_mapping[power_a]
    if self.state =='no_order': 
      self.state = 'censoring'
      self.cur_obs[agent_id][-13:] = one_hot_order 
      self.ep_n_states.append(self.cur_obs)
      # print('new obs: ', self.cur_obs)
      # self.step(action, power_a, power_b, order)
      
    elif self.state == 'censoring':
      if action[agent_id] ==0:
        self.state ='no_order'
        self.cur_obs[agent_id][2:] = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        # print('new obs: ', self.cur_obs)
        self.ep_n_states.append(self.cur_obs)
      else:
        self.state = 'share_order'
        self.cur_obs[agent_id][1] = 1.0
        self.ep_n_states.append(self.cur_obs)
        # self.step(action, power_a, power_b, order)
    else:
      # if state==no sender
      self.state = 'no_order'
      self.cur_obs[agent_id][1:] = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
      self.ep_n_states.append(self.cur_obs)
    
  def get_transactions(self):
    #when the dip phase is done
    return  self.ep_states, self.ep_actions, self.ep_rewards, self.ep_n_states, self.ep_dones
