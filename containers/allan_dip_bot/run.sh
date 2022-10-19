#!/bin/bash

printf "Sleeping for 4s"
sleep 4
printf "Slept for 4s"

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

# launch bot script
python /model/src/model_server/baseline_bots/run_bot.py $@
