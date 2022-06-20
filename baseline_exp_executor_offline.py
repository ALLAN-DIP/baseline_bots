from subprocess import PIPE, run
import json
from tqdm import tqdm
import time
no_of_games = 100

prefix = 'LSP_RUSTUR'

for i in range (no_of_games):
    run(f"python3 botgame_launcher_dipnet.py -t np,np,np,np,np,rlspm,rlsp -f Analysis/{prefix}_{i}.json &", shell=True)
    time.sleep(60)