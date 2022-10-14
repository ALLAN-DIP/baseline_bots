#!/bin/bash

# launch model server
/model/src/model_server/run_model_server.sh &

# ASCII art
printf "Running ALLAN bot\n"
printf "    ___    __    __    ___    _   __\n"
printf "   /   |  / /   / /   /   |  / | / /\n"
printf "  / /| | / /   / /   / /| | /  |/ / \n"
printf " / ___ |/ /___/ /___/ ___ |/ /|  /  \n"
printf "/_/  |_/_____/_____/_/  |_/_/ |_/   \n"
printf "\n"

export PYTHONPATH=$PYTHONPATH:/model/src/model_server/research/

# create a game
python diplomacy-playground/scripts/create_game.py --game_id test_game_114514 --deadline 30
# launch bot script
python /model/src/model_server/baseline_bots/run_bot.py --game_id test_game_114514 --power TURKEY --outdir .
