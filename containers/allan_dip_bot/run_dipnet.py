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

from diplomacy_research.utils.cluster import is_port_opened

POWERS = ['AUSTRIA', 'ENGLAND', 'FRANCE', 'GERMANY', 'ITALY', 'RUSSIA', 'TURKEY']


#@gen.coroutine

async def test(hostname='localhost', port=8432):
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

async def launch(hostname, port, game_id, power_name, outdir):
	print("Waiting for tensorflow server to come online")
	serving_flag = False
	while not serving_flag:
		serving_flag = is_port_opened(9501)
		print("+")
		await asyncio.sleep(1)
	print("tensorflow server online")

	await play(hostname, port, game_id, power_name, outdir)

async def play(hostname, port, game_id,power_name, outdir):

	print("DipNetSL joining game: " + game_id + " as " + power_name)
	connection = await connect(hostname, port)
	channel = await connection.authenticate('dipnet_' + power_name, 'password')
	game = await channel.join_game(game_id=game_id, power_name=power_name)


	bot = NoPressDipBot(power_name, game)

	# Wait while game is still being formed
	while game.is_game_forming:
		await asyncio.sleep(0.5)

	t1 = time.perf_counter()
	i = 0

	# Playing game
	print("Started playing")
	while not game.is_game_done:

		current_phase = game.get_current_phase()

		rcvd_messages = game.filter_messages(messages=game.messages, game_role=bot.power_name)
		rcvd_messages = list(rcvd_messages.items())
		rcvd_messages.sort()

		round_msgs = game.messages
		to_send_msgs = {}
	
		if not game.powers[bot.power_name].is_eliminated():
			# Retrieve messages
			rcvd_messages = game.filter_messages(messages=round_msgs, game_role=bot.power_name)
			rcvd_messages = list(rcvd_messages.items())
			rcvd_messages.sort()

			# Send messages to bots and fetch messages from bot
			bot_messages = await bot.gen_messages(rcvd_messages)

			# If messages are to be sent, send them
			if bot_messages and bot_messages.messages:
				to_send_msgs[bot.power_name] = bot_messages.messages

		# Send all messages
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
			
		if not game.powers[bot.power_name].is_eliminated():
			# Orders round
			orders = await bot.gen_orders()

			if orders is not None:
				await game.set_orders(power_name=power_name, orders=orders, wait=False)
			print("Phase: " + current_phase)
			print("Orders: ")
			print(orders)

		while current_phase == game.get_current_phase():
			await asyncio.sleep(2)

	t2 = time.perf_counter()
	print(f"TIMING: {t2-t1}:0.4")
	print('-'*30 + 'GAME COMPLETE' + '-'*30)


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('--host', type=str)
	parser.add_argument('--port', type=int)
	parser.add_argument('--game_id', type=str)
	parser.add_argument("--power", type=str)
	parser.add_argument('--outdir', type=str)
	args = parser.parse_args()
	host = args.host
	port = args.port
	game_id = args.game_id
	outdir = args.outdir
	power = args.power

	#default
	if host == None:
		host = 'localhost'
	if port == None:
		port = 8432
	if game_id == None:
		print("Game ID required")
		sys.exit(1)

	asyncio.run(launch(hostname=host, port=port, game_id=game_id,power_name=power, outdir=outdir))
