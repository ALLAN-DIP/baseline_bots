import json
from subprocess import PIPE, run
import time

from tqdm import tqdm

no_of_games = 100

# prefix = 'np'

# for i in range (no_of_games):
#     run(f"python3 botgame_launcher_dipnet.py -t np,np,np,np,np,np,np -f Analysis/{prefix}_{i}.json &", shell=True)
#     time.sleep(60)
# time.sleep(600)

prefix = "LSP_RUSTUR_v02"

for i in range(no_of_games):
    run(
        f"python3 botgame_launcher_dipnet.py -t np,np,np,np,np,rlspm,rlsp -f Analysis/{prefix}_{i}.json &",
        shell=True,
    )
    time.sleep(60)
time.sleep(600)
