__author__ = "Wichayaporn Wongkamjan"

import random
import sys
sys.path.append("..")

from utils import get_order_tokens
from baseline_bot import BaselineMsgRoundBot

class PressDipBot(BaselineMsgRoundBot):

  def gen_messages(stance, msg_list, sender, recipient): # should also take rcvd_messages
    # input: sender, recip, stance, message history, orders from DipNet 
    # output: message_list 
    # decide if want to send message 
    boolean_message_content = [True, False]
    for key in msg_list:
      if random.choice(boolean_message_content):
        # set message for this content type, e.g. pick sender moves 4 out of 10 orders - for now let's do select all - do nothing
        if key =='power_message' or key =='sender_proposal':
  #         #randomly select one power that we want to share power's messages to recipient       
  #         power_message = random.choice(list(msg_list['power_message'].values()))
  #         # we can make sure that we wont set None which is possible from picking message from the received list but for now None is fine
  #         msg_list['power_message'] = power_message  
            msg_list[key] = None # we care only sender_move for now
        else:
          # case when key = sender_move
          if stance[sender][recipient] == 'N':
            msg_list[key] = filter_message(self.game, msg_list['sender_move'], recipient, ['attack','hold','convoy'])
          elif stance[sender][recipient] == 'B':
            msg_list[key] = None
              
      else:
        msg_list[key] = None
    return msg_list

    def get_orders(sender, recipient):
      # propose all units move for recipient
      if self.game.get_orderable_locations(recipient):
          possible_orders = self.game.get_all_possible_orders()
          orders = [random.choice(possible_orders[loc]) for loc in self.game.get_orderable_locations(recipient)
                    if possible_orders[loc]]
          return orders  

  def filter_message(game, msg_list, power_name, type):
    #msg_list = list of string message
    # type - a message type to exclude from message_list e.g. ['attack', 'support', 'proposal', 'to_order', etc.]
    remove_list = []
    for msg in msg_list:
      if get_message_type(game, msg, power_name) in type:
        remove_list.append(msg)
    return [msg for msg in msg_list if msg not in remove_list]
        
  def get_message_type(game, msg, power_name):
    # check if it is support?
    # attack?
    # move? 
    # convoy
    # hold
    order_token = get_order_tokens(msg)
    if order_token[0] =='A' or order_token[0] =='F':
      # this is message about orders
      if order_token[1] == 'S':
        return 'support'
      elif order_token[1] == 'H':
        return 'hold'
      elif order_token[1] == 'C':
        return 'convoy'
      else:
        #move/retreat or attack 
        #get location - add order_token[0] ('A' or 'F') at front to check if it collides with other powers' units
        order_unit = order_token[0]+' '+order_token[2]
        #check if loc has some units of other powers on
        for power in game.powers:
          if power_name != power:
            if order_unit in game.powers[power].units:
              return 'attack'
            else:
              return 'move' 
      


