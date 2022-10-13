
from diplomacy import Game, Message

from baseline_bots.bots.smart_order_accepter_bot import SmartOrderAccepterBot
from baseline_bots.utils import MessagesData

class TestUtils:
	def test(self):
		soa_bot = SmartOrderAccepterBot()
		RESPOND_TO_INV_ORDERS_TC = [
			[
				{
					"RUSSIA": [("A PRU - LVN", "TUR"), (("A PRU - MOS", "RUS"))],
					"AUSTRIA": [("A PRU - LVN", "ENG")]
				},
				[
					{"recipient": "RUSSIA", "message": "HUH (PRP (ORR (XDO ((TUR AMY PRU) MTO LVN)) (XDO ((RUS AMY PRU) MTO MOS))))"},
					{"recipient": "AUSTRIA", "message": "HUH (PRP (XDO ((ENG AMY PRU) MTO LVN)))"}
				]
			]
		]

		for tc_ip, tc_op in RESPOND_TO_INV_ORDERS_TC:
			msg_data = MessagesData()
			soa_bot.respond_to_invalid_orders(tc_ip, msg_data)
			assert msg_data.messages == tc_op

		RESPOND_TO_ALLIANCES_TC = [
			[
				{
					"RUSSIA": [("RUSSIA", "ALY (TUR RUS ENG ITA) VSS (FRA GER AUS)")],
					"ENGLAND": [("RUSSIA", "ALY (TUR RUS ENG ITA) VSS (FRA GER AUS)")],
					"ITALY": [("RUSSIA", "ALY (TUR RUS ENG ITA) VSS (FRA GER AUS)")],
				},
				[
					{"recipient": "RUSSIA", "message": "YES (ALY (TUR RUS ENG ITA) VSS (FRA GER AUS))"}
				]
			]
		]

		for tc_ip, tc_op in RESPOND_TO_ALLIANCES_TC:
			msg_data = MessagesData()
			soa_bot.alliances = tc_ip
			soa_bot.respond_to_alliance_messages(msg_data)
			assert msg_data.messages == tc_op