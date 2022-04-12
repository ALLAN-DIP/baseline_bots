import json
import os
from collections import defaultdict
import pandas as pd
from tqdm import tqdm
from datetime import datetime

today = datetime.today()
suffix = today.strftime("%Y_%m_%d-%H:%M:%S")
# suffix = '2022_04_08-20:34:01'

parent_analysis = []

def execute_scenario(pows, types, file, runname, parent_analysis, bypass_exec=False, game_play_count = 30, del_file=True):
    file = "GameAnalysisFiles/" + file
    if not bypass_exec:
        if del_file:
            os.system(f"rm {file}")

        for _ in tqdm(range(game_play_count)):
            cmd = f"python analyze_dipbots.py -p {pows} -t {types} -f {file}"
            print(os.system(cmd))

    power_total_wins = defaultdict(int)
    power_solo_wins = defaultdict(int)
    power_shared_wins = defaultdict(int)
    power_solo_durations = defaultdict(int)
    power_shared_durations = defaultdict(int)

    no_of_games = 0
    with open(file) as f:
        for line in f:
            game = json.loads(line)
            winners = [pow1.strip() for pow1 in game['phases'][-1]['state']['note'].split(":")[-1].split(",")]
            for pow1 in winners:
                power_total_wins[pow1] += 1
            if len(winners) == 1:
                power_solo_wins[winners[0]] += 1
                power_solo_durations[winners[0]] += int(game['phases'][-2]['name'][1:-1]) - 1900
            else:
                for pow1 in winners:
                    power_shared_wins[pow1] += 1
                    power_shared_durations[pow1] += int(game['phases'][-2]['name'][1:-1]) - 1900
    for pow1 in power_solo_durations:
        power_solo_durations[pow1] /= power_solo_wins[pow1]
    for pow1 in power_shared_durations:
        power_shared_durations[pow1] /= power_shared_wins[pow1]
        
    parent_analysis.append((runname, power_total_wins, power_solo_wins, power_shared_wins, power_solo_durations, power_shared_durations))

# All Dipnets
pows = 'ENGLAND,AUSTRIA,ITALY,FRANCE,GERMANY,RUSSIA,TURKEY'
types = 'np,np,np,np,np,np,np'
runname = 'All_dip_np'
file = runname + "_" + suffix + ".json"
execute_scenario(pows, types, file, runname, parent_analysis, True)

# Germ Leader, Italy Follower All Dipnets
pows = 'ENGLAND,AUSTRIA,ITALY,FRANCE,GERMANY,RUSSIA,TURKEY'
types = 'np,np,lsp,np,lspm,np,np'
runname = 'All_dip_Ger_Ita'
file = runname + "_" + suffix + ".json"
execute_scenario(pows, types, file, runname, parent_analysis, True)

# Aus Leader, Italy Follower All Dipnets
pows = 'ENGLAND,AUSTRIA,ITALY,FRANCE,GERMANY,RUSSIA,TURKEY'
types = 'np,lspm,lsp,np,np,np,np'
runname = 'All_dip_Aus_Ita'
file = runname + "_" + suffix + ".json"
execute_scenario(pows, types, file, runname, parent_analysis, True)

# # Eng Leader, France Follower All Dipnets
pows = 'ENGLAND,AUSTRIA,ITALY,FRANCE,GERMANY,RUSSIA,TURKEY'
types = 'lspm,np,np,lsp,np,np,np'
runname = 'All_dip_Eng_Fra'
file = runname + "_" + suffix + ".json"
execute_scenario(pows, types, file, runname, parent_analysis, True)

# # France Leader, Eng Follower All Dipnets
pows = 'ENGLAND,AUSTRIA,ITALY,FRANCE,GERMANY,RUSSIA,TURKEY'
types = 'lsp,np,np,lspm,np,np,np'
runname = 'All_dip_Fra_Eng'
file = runname + "_" + suffix + ".json"
execute_scenario(pows, types, file, runname, parent_analysis, True)

# Aus Dipnet, All others random
pows = 'ENGLAND,AUSTRIA,ITALY,FRANCE,GERMANY,RUSSIA,TURKEY'
types = 'rnp,np,rnp,rnp,rnp,rnp,rnp'
runname = 'All_rand_Aus_dip'
file = runname + "_" + suffix + ".json"
execute_scenario(pows, types, file, runname, parent_analysis)

# Eng Dipnet, All others random
pows = 'ENGLAND,AUSTRIA,ITALY,FRANCE,GERMANY,RUSSIA,TURKEY'
types = 'np,rnp,rnp,rnp,rnp,rnp,rnp'
runname = 'All_rand_Eng_dip'
file = runname + "_" + suffix + ".json"
execute_scenario(pows, types, file, runname, parent_analysis)


rows = []
pows = 'ENG,AUS,ITA,FRA,GER,RUS,TUR'.split(",")
for col in parent_analysis:
    for i in range(1, len(col)):
        for pow1 in pows:
            rows.append([pow1, col[0], i, col[i][pow1]])

pd.DataFrame(rows, columns=['power', 'scenario', 'key', 'val']).to_csv('GameAnalysisFiles/n_comms_game_analysis_' + suffix + '.csv')
