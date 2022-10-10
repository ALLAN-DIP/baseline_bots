__author__ = "Kartik Shenoy"
__email__ = "kartik.shenoyy@gmail.com"

import sys, os

sys.path.append("..") # Adds higher directory to python modules path.

# inside container
os.environ['WORKING_DIR'] = "/model/src/model_server/research/WORKING_DIR"
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'cpp'

import argparse
import time
import asyncio
import ujson as json
from tornado import gen
from diplomacy import Game, connect, Message

# import required bots
from baseline_bots.bots.dipnet.no_press_bot import NoPressDipBot
from baseline_bots.bots.dipnet.transparent_bot import TransparentBot
from baseline_bots.bots.smart_order_accepter_bot import SmartOrderAccepterBot

from diplomacy_research.utils.cluster import is_port_opened

POWERS = ['AUSTRIA', 'ENGLAND', 'FRANCE', 'GERMANY', 'ITALY', 'RUSSIA', 'TURKEY']

async def test(hostname:str='localhost', port:int=8432) -> None:
	"""
	Tests the game connection

	:param hostname: name of host on which games are hosted
	:param port: port to which the bot should connect on the host
	"""
	connection = await connect(hostname, port)
	channel = await connection.authenticate('random_user', 'password')
	games = await channel.list_games()
	for game in games:
		game_info = {
			"game_id":game.game_id,
			"phase":game.phase,
			"timestamp":game.timestamp,
			"timestamp_created":game.timestamp_created,
			"map_name":game.map_name,
			"observer_level":game.observer_level,
			"controlled_powers":game.controlled_powers,
			"rules":game.rules,
			"status":game.status,
			"n_players":game.n_players,
			"n_controls":game.n_controls,
			"deadline":game.deadline,
			"registration_password":game.registration_password
		}
		print(game_info)
	print(games)


async def launch(hostname:str, port:int, game_id:str, power_name:str, bot_type:str, outdir:str) -> None:
	"""
	Waits for dipnet model to load and then starts the bot execution

	:param hostname: name of host on which games are hosted
	:param port: port to which the bot should connect on the host
	:param game_id: game id to connect to on host
	:param power_name: power name of the bot to be launched
	:param bot_type: the type of bot to be launched - NoPressDipBot/TransparentBot/SmartOrderAccepterBot/..
	:param outdir: the output directory where game json files should be stored
	"""
	print("Waiting for tensorflow server to come online", end=' ')
	serving_flag = False
	while not serving_flag:
		serving_flag = is_port_opened(9501)
		print("", end='.')
		await asyncio.sleep(1)
	print()
	print("Tensorflow server online")

	await play(hostname, port, game_id, power_name, bot_type, outdir)


async def play(hostname:str, port:int, game_id:str, power_name:str, bot_type:str, outdir:str) -> None:
	"""
	Launches the bot for game play

	:param hostname: name of host on which games are hosted
	:param port: port to which the bot should connect on the host
	:param game_id: game id to connect to on host
	:param power_name: power name of the bot to be launched
	:param bot_type: the type of bot to be launched - NoPressDipBot/TransparentBot/SmartOrderAccepterBot/..
	:param outdir: the output directory where game json files should be stored
	"""
	# Connect to the game
	print("DipNetSL joining game: " + game_id + " as " + power_name)
	connection = await connect(hostname, port)
	channel = await connection.authenticate('dipnet_' + power_name, 'password')
	game = await channel.join_game(game_id=game_id, power_name=power_name)


	bot = None

	if bot_type == "NoPressDipBot":
		bot = NoPressDipBot(power_name, game)
	elif bot_type == "TransparentBot":
		bot = TransparentBot(power_name, game)
	elif bot_type == "SmartOrderAccepterBot":
		bot = SmartOrderAccepterBot(power_name, game)
		
	# Wait while game is still being formed
	print("Waiting for game to start", end=' ')
	while game.is_game_forming:
		await asyncio.sleep(2)
		print("", end='.')
	print()


	t1 = time.perf_counter()
	i = 0

	# Playing game
	print("Started playing")
	while not game.is_game_done:

		current_phase = game.get_current_phase()

		# Retrieve messages
		rcvd_messages = game.filter_messages(messages=game.messages, game_role=bot.power_name)
		rcvd_messages = list(rcvd_messages.items())
		rcvd_messages.sort()

		to_send_msgs = {}
	
		if not game.powers[bot.power_name].is_eliminated():
			# Send messages to bots and fetch messages from bot
			messages_data = await bot.gen_messages(rcvd_messages)

			# Fetch orders from bot
			orders_data = await bot.gen_orders()

			# If messages are to be sent, send them
			if messages_data and messages_data.messages:
				to_send_msgs[bot.power_name] = messages_data.messages

			for sender in to_send_msgs:
				for msg in to_send_msgs[sender]:
					msg_obj = Message(
						sender=sender,
						recipient=msg['recipient'],
						message=msg['message'],
						phase=game.get_current_phase(),
					)
					await game.send_game_message(message=msg_obj)

			if len(to_send_msgs):
				print(f"Messages sent: {len(to_send_msgs)}")

			# If orders are present, send them
			if orders_data is not None:
				await game.set_orders(power_name=power_name, orders=orders_data, wait=False)

			print("Phase: " + current_phase)
			print("Orders: ")
			print(orders_data)

		while current_phase == game.get_current_phase():
			await asyncio.sleep(2)

	t2 = time.perf_counter()
	print(f"TIMING: {t2-t1}:0.4")
	print('-'*30 + 'GAME COMPLETE' + '-'*30)


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='ALLAN-DIP: Team ALLAN\'s Diplomacy Agent')
	parser.add_argument('--host', type=str, default='localhost', help='host IP address (defaults to localhost)')
	parser.add_argument('--port', type=int, default=8432, help='port to connect to the game')
	parser.add_argument('--game_id', type=str, help='game id of game created in DATC diplomacy game')
	parser.add_argument("--power", type=str, help='power name (AUSTRIA, ENGLAND, FRANCE, GERMANY, ITALY, RUSSIA, TURKEY)')
	parser.add_argument("--bot_type", type=str, default="TransparentBot", help='type of bot to be launched (NoPressDipBot, TransparentBot, SmartOrderAccepterBot)')
	parser.add_argument('--outdir', type=str, help='output directory for game json to be stored')
	args = parser.parse_args()
	host = args.host
	port = args.port
	game_id = args.game_id
	bot_type = args.bot_type
	outdir = args.outdir
	power = args.power

	if game_id == None:
		print("Game ID required")
		sys.exit(1)

	asyncio.run(launch(hostname=host, port=port, game_id=game_id,power_name=power, bot_type=bot_type, outdir=outdir))
