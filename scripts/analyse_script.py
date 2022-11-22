import argparse
import json
import os
from collections import defaultdict
from datetime import datetime
from time import time

import pandas as pd
from tqdm import tqdm

today = datetime.today()
suffix = today.strftime("%Y_%m_%d-%H:%M:%S")
# suffix = '2022_04_13-22:34:01'

parent_analysis = []


def parse_args():
    parser = argparse.ArgumentParser(description="Bot Analyzer")
    parser.add_argument("--comb", "-c", type=int, default=1, help="combination no.")

    args = parser.parse_args()
    print(args)
    return args


args = parse_args()


def execute_scenario(
    pows,
    types,
    file,
    runname,
    parent_analysis,
    bypass_exec=False,
    game_play_count=100,
    del_file=True,
):
    file = "GameAnalysisFiles/" + file
    times = []

    # If the previous executions results need to be used for compilation of analyses,
    # bypass_exec needs to be set to True
    if not bypass_exec:
        if del_file:
            os.system(f"rm {file}")
        for _ in tqdm(range(game_play_count)):
            start = time()
            cmd = f"python botgame_launcher_dipnet.py -p {pows} -t {types} -f {file}"
            print(os.system(cmd))
            end = time()
            times.append(end - start)

    power_total_wins = defaultdict(int)
    power_solo_wins = defaultdict(int)
    power_shared_wins = defaultdict(int)
    power_solo_durations = defaultdict(int)
    power_shared_durations = defaultdict(int)

    no_of_games = 0
    with open(file) as f:
        for line in f:
            game = json.loads(line)
            winners = [
                pow1.strip()
                for pow1 in game["phases"][-1]["state"]["note"]
                .split(":")[-1]
                .split(",")
            ]
            for pow1 in winners:
                power_total_wins[pow1] += 1
            if len(winners) == 1:
                power_solo_wins[winners[0]] += 1
                power_solo_durations[winners[0]] += (
                    int(game["phases"][-2]["name"][1:-1]) - 1900
                )
            else:
                for pow1 in winners:
                    power_shared_wins[pow1] += 1
                    power_shared_durations[pow1] += (
                        int(game["phases"][-2]["name"][1:-1]) - 1900
                    )
    for pow1 in power_solo_durations:
        power_solo_durations[pow1] /= power_solo_wins[pow1]
    for pow1 in power_shared_durations:
        power_shared_durations[pow1] /= power_shared_wins[pow1]
    print(pd.Series(times).describe())
    parent_analysis.append(
        (
            runname,
            power_total_wins,
            power_solo_wins,
            power_shared_wins,
            power_solo_durations,
            power_shared_durations,
        )
    )


# if args.comb == 0:
# All Dipnets
pows = "ENGLAND,AUSTRIA,ITALY,FRANCE,GERMANY,RUSSIA,TURKEY"
types = "re_np,re_np,re_np,re_np,re_np,re_np,re_np"
runname = "All_dip_np"
file = runname + "_" + suffix + ".json"
execute_scenario(pows, types, file, runname, parent_analysis)

# elif args.comb == 1:
# Germ Leader, Italy Follower All Dipnets
pows = "ENGLAND,AUSTRIA,ITALY,FRANCE,GERMANY,RUSSIA,TURKEY"
types = "re_np,re_np,rlsp,re_np,rlspm,re_np,re_np"
runname = "All_dip_Ger_Ita"
file = runname + "_" + suffix + ".json"
execute_scenario(pows, types, file, runname, parent_analysis)

# elif args.comb == 2:
# Aus Leader, Italy Follower All Dipnets
pows = "ENGLAND,AUSTRIA,ITALY,FRANCE,GERMANY,RUSSIA,TURKEY"
types = "re_np,rlspm,rlsp,re_np,re_np,re_np,re_np"
runname = "All_dip_Aus_Ita"
file = runname + "_" + suffix + ".json"
execute_scenario(pows, types, file, runname, parent_analysis)

# elif args.comb == 3:
# Eng Leader, France Follower All Dipnets
pows = "ENGLAND,AUSTRIA,ITALY,FRANCE,GERMANY,RUSSIA,TURKEY"
types = "rlspm,re_np,re_np,rlsp,re_np,re_np,re_np"
runname = "All_dip_Eng_Fra"
file = runname + "_" + suffix + ".json"
execute_scenario(pows, types, file, runname, parent_analysis)

# elif args.comb == 4:
# France Leader, Eng Follower All Dipnets
pows = "ENGLAND,AUSTRIA,ITALY,FRANCE,GERMANY,RUSSIA,TURKEY"
types = "rlsp,re_np,re_np,rlspm,re_np,re_np,re_np"
runname = "All_dip_Fra_Eng"
file = runname + "_" + suffix + ".json"
execute_scenario(pows, types, file, runname, parent_analysis)

# elif args.comb == 5:
# Aus Dipnet, All others random
pows = "ENGLAND,AUSTRIA,ITALY,FRANCE,GERMANY,RUSSIA,TURKEY"
types = "rnp,re_np,rnp,rnp,rnp,rnp,rnp"
runname = "All_rand_Aus_dip"
file = runname + "_" + suffix + ".json"
execute_scenario(pows, types, file, runname, parent_analysis)

# elif args.comb == 6:
# Eng Dipnet, All others random
pows = "ENGLAND,AUSTRIA,ITALY,FRANCE,GERMANY,RUSSIA,TURKEY"
types = "re_np,rnp,rnp,rnp,rnp,rnp,rnp"
runname = "All_rand_Eng_dip"
file = runname + "_" + suffix + ".json"
execute_scenario(pows, types, file, runname, parent_analysis)

# elif args.comb == 7:
# Eng Leader, Tur Follower All Dipnets
pows = "ENGLAND,AUSTRIA,ITALY,FRANCE,GERMANY,RUSSIA,TURKEY"
types = "rlspm,re_np,re_np,re_np,re_np,re_np,rlsp"
runname = "All_dip_Eng_Tur"
file = runname + "_" + suffix + ".json"
execute_scenario(pows, types, file, runname, parent_analysis)

# elif args.comb == 8:
# Tur Leader, Eng Follower All Dipnets
pows = "ENGLAND,AUSTRIA,ITALY,FRANCE,GERMANY,RUSSIA,TURKEY"
types = "rlsp,re_np,re_np,re_np,re_np,re_np,rlspm"
runname = "All_dip_Tur_Eng"
file = runname + "_" + suffix + ".json"
execute_scenario(pows, types, file, runname, parent_analysis)

# elif args.comb == 9:
# Fra Leader, Rus Follower All Dipnets
pows = "ENGLAND,AUSTRIA,ITALY,FRANCE,GERMANY,RUSSIA,TURKEY"
types = "re_np,re_np,re_np,rlspm,re_np,rlsp,re_np"
runname = "All_dip_Fra_Rus"
file = runname + "_" + suffix + ".json"
execute_scenario(pows, types, file, runname, parent_analysis)

# elif args.comb == 10:
# Eng Leader, Rus Follower All Dipnets
pows = "ENGLAND,AUSTRIA,ITALY,FRANCE,GERMANY,RUSSIA,TURKEY"
types = "rlspm,re_np,re_np,re_np,re_np,rlsp,re_np"
runname = "All_dip_Eng_Rus"
file = runname + "_" + suffix + ".json"
execute_scenario(pows, types, file, runname, parent_analysis)

rows = []
pows = "ENG,AUS,ITA,FRA,GER,RUS,TUR".split(",")
for col in parent_analysis:
    for i in range(1, len(col)):
        for pow1 in pows:
            rows.append([pow1, col[0], i, col[i][pow1]])

pd.DataFrame(rows, columns=["power", "scenario", "key", "val"]).to_csv(
    "GameAnalysisFiles/n_comms_game_analysis_" + suffix + ".csv"
)
