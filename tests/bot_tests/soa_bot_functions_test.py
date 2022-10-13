
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
					["RUSSIA", "HUH (ORR (XDO ((TUR AMY PRU) MTO LVN)) (XDO ((RUS AMY PRU) MTO MOS)))"],
					["RUSSIA", "HUH (XDO ((TUR AMY PRU) MTO LVN))"]
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
					["RUSSIA", "YES (ALY (TUR RUS ENG ITA) VSS (FRA GER AUS))"]
				]
			]
		]

		for tc_ip, tc_op in RESPOND_TO_ALLIANCES_TC:
			msg_data = MessagesData()
			soa_bot.respond_to_alliance_messages(tc_ip, msg_data)
			assert msg_data.messages == tc_op