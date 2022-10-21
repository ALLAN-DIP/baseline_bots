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

# create random game id
random_id=$(shuf -i 1-10000000 -n 1)
game_id="ALLAN_game_${random_id}"
echo "creating game: ${game_id}"

# create a game
python diplomacy-playground/scripts/create_game.py --host shade.tacc.utexas.edu --game_id ${game_id} --deadline 30
# launch bot script
python /model/src/model_server/baseline_bots/containers/run_bot.py --host shade.tacc.utexas.edu --game_id ${game_id}
