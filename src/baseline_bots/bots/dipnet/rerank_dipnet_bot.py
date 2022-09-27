__authors__ = ["Kartik Shenoy"]
__email__ = "kartik.shenoyy@gmail.com"

import random
import sys

from bots.dipnet.dipnet_bot import DipnetBot
from diplomacy import Game, Message
from diplomacy.utils.order_results import OK, NO_CONVOY, BOUNCE, VOID, CUT, DISLODGED, DISRUPTED, DISBAND, MAYBE
from utils import OrdersData, MessagesData, get_order_tokens, get_other_powers
from typing import List
from tornado import gen
import time
import numpy as np

sys.path.append("..")
sys.path.append("../..")

from utils import get_order_tokens

class ReRankDipnetBot(DipnetBot):
	"""just execute orders computed by dipnet"""
	def __init__(self, power_name:str, game:Game, total_msg_rounds=3, dipnet_type='slp', bounce_multiplier=0.5):
		super().__init__(power_name, game, total_msg_rounds)
		self.bounce_multiplier = bounce_multiplier
		self.old_orders_dict = {}
		self.updated_orders_count_dict = {}
		self.old_orders_count_dict = {}
		self.new_orders_count_dict = {}
		print(f"Bounce multiplier of rerank bot set to {self.bounce_multiplier}")

	@gen.coroutine
	def gen_messages(self, rcvd_messages:List[Message]) -> MessagesData:
		"""query dipnet for orders"""
		return None
		
	def rerank_score(self, orders, prob, other_pow_orders):

		sim_game = self.game.__deepcopy__(None)
		# sim_game.process()
		sim_game.process()
		for other_power in get_other_powers([self.power_name], self.game):
			sim_game.set_orders(power_name=other_power, orders=other_pow_orders[other_power])
		sim_game.set_orders(power_name=self.power_name, orders=orders)
		# print()
		# print("Orders")
		# for other_power in get_other_powers([], self.game):
		# 	print(f"Orders of {other_power}")
		# 	print(sim_game.get_orders(power_name=other_power))
		# print(orders)
		sim_game.process()
		# print(self.game.phase)
		# print(sim_game.phase)

		curr_units = self.game.get_units(self.power_name)
		# curr_units = self.game.get_centers(self.power_name)
		future_units = sim_game.get_units(self.power_name)
		future_centres = sim_game.get_centers(self.power_name)
		order_statuses = sim_game.get_order_status(self.power_name)

		# print("Curr Units")
		# print(curr_units)
		# print("Fut Units")
		# print(future_units)
		# print("Fut Centres")
		# print(future_centres)
		# print("Order statuses")
		# print(order_statuses)

		for order in orders:
			order_tokens = get_order_tokens(order)
			# print(order_tokens)

			# TODO
			if order_tokens[1] == 'H': #hold move
				continue
			if order_tokens[1] == 'S': #support move
				continue
			if order_tokens[-1] == 'VIA': #convoy move
				continue
			assert len(order_tokens[-2].split()) == 2, order_tokens
			src_province = order_tokens[-2].split()[-1]
			src_unit = order_tokens[-2]
			assert len(order_tokens[-1].split()) == 2, order_tokens
			target_province = order_tokens[-1].split()[-1]
			target_unit = order_tokens[-2].split()[0] + ' ' + order_tokens[-1].split()[1]

			curr_owner = self.game._unit_owner(target_unit)
			future_owner = sim_game._unit_owner(target_unit)
			# print("Curr Owner of target:",curr_owner.name if curr_owner is not None else "None")
			# print("Future Owner of target:",future_owner.name if future_owner is not None else "None")
			# self.game.get_power(self.power_name).influence

			# Check if move was successful
			if src_unit in order_statuses:
				successful_move = order_statuses[src_unit] == []
			else:
				successful_move = False
				print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>", order_tokens)
			# Check if some unit was present before at destination
			displaced_unit = curr_owner is not None and \
							curr_owner.name != self.power_name and \
							future_owner is not None and \
							future_owner.name == self.power_name
			# Check if province has SC
			sc_province = target_province in self.game.map.scs

			# print(f"Success move: {successful_move}, displaced_unit: {displaced_unit}, sc_province: {sc_province}")
			# print("Prob was: ",prob)
			if not(successful_move): # Order resulted in a bounce
				prob *= self.bounce_multiplier
			# else:
			# 	if displaced_unit:
			# 		prob = prob * 1.8 if sc_province else 1.3
			# 	else:
			# 		prob *= prob * 1.35 if sc_province else 1
			# print("Prob is: ",prob)
		return prob


	@gen.coroutine
	def gen_orders(self):
		self.orders = OrdersData()
		# orders = yield self.brain.get_orders(self.game, self.power_name)
		# print("Get orders")
		# print(orders)
		# self.orders.add_orders(orders, overwrite=True)
		if self.game.get_current_phase()[-1] == 'M':
			orders, probabilities = yield self.brain.get_beam_orders(self.game, self.power_name)
			if len(orders) == 0 or len(probabilities) == 0:
				return self.orders.get_list_of_orders()
			oth_orders = {}
			for other_power in get_other_powers([self.power_name], self.game):
				oth_orders[other_power] = yield self.brain.get_orders(self.game, other_power)
			# print("Beam orders")
			# print(orders)
			final_probs = []
			for order_set, prob in zip(orders, probabilities):
				# prob = self.rerank_score(order_set) * prob
				final_probs.append(self.rerank_score(order_set, prob, oth_orders))
			# print("OG Orders and probs:")
			# print(orders)
			# print(probabilities)
			# print("New probabilities")
			# print(final_probs)
			# assert len(probabilities) != 0, orders
			phase_name = self.game.get_current_phase()
			if np.argmax(final_probs) != np.argmax(probabilities):
				print("Updated orders choice")
				self.old_orders_dict[phase_name] = orders[np.argmax(probabilities)]
				self.old_orders_count_dict[phase_name] = len(orders[np.argmax(probabilities)])
				self.new_orders_count_dict[phase_name] = len(orders[np.argmax(final_probs)])
				self.updated_orders_count_dict[phase_name] = len(set(orders[np.argmax(probabilities)]) - set(orders[np.argmax(final_probs)]))
			self.orders.add_orders(orders[np.argmax(final_probs)], overwrite=True)
			
		else:
			orders = yield self.brain.get_orders(self.game, self.power_name)
			# print("Get orders")
			# print(orders)
			self.orders.add_orders(orders, overwrite=True)

		return self.orders.get_list_of_orders()