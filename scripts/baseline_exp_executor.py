import json
import time
from subprocess import PIPE, run

from tqdm import tqdm

daide_ports = []

no_of_games = 100

prefix = "FINAL_06_19_FINAL"

# for i in tqdm(range(no_of_games)):
# 	result = run(f"python ../diplomacy-playground/scripts/create_game.py \
# 		--host shade.tacc.utexas.edu --game_id kshenoy-{prefix}_test_{i} --deadline 30",
# 		shell=True,
# 		stdout=PIPE, stderr=PIPE, universal_newlines=True)
# 	port1 = json.loads(result.stdout)['daide_port']
# 	daide_ports.append(port1)
# 	# print(result['daide_port']) # Works

# for i in tqdm(range(no_of_games)):
# 	run(f"singularity run docker://tacc/albert-ai:v1 --host shade.tacc.utexas.edu --port {daide_ports[i]} &", shell=True)
# 	time.sleep(3)
# 	run(f"singularity run docker://tacc/albert-ai:v1 --host shade.tacc.utexas.edu --port {daide_ports[i]} &", shell=True)
# 	time.sleep(3)
# 	run(f"singularity run docker://tacc/albert-ai:v1 --host shade.tacc.utexas.edu --port {daide_ports[i]} &", shell=True)
# 	time.sleep(3)
# 	run(f"singularity run docker://tacc/albert-ai:v1 --host shade.tacc.utexas.edu --port {daide_ports[i]} &", shell=True)
# 	time.sleep(3)
# 	run(f"singularity run docker://tacc/albert-ai:v1 --host shade.tacc.utexas.edu --port {daide_ports[i]} &", shell=True)


for i in range(no_of_games):
    run(
        f"python dip_ui_bot_launcher.py -H shade.tacc.utexas.edu \
		-p RUSSIA -B rlspm -g kshenoy-{prefix}_test_{i} &",
        shell=True,
    )
    time.sleep(10)
    run(
        f"python dip_ui_bot_launcher.py -H shade.tacc.utexas.edu \
		-p TURKEY -B rlsp -g kshenoy-{prefix}_test_{i} &",
        shell=True,
    )
    time.sleep(20)

time.sleep(172800)
