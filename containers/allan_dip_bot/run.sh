#!/bin/bash

#launch model server
/model/src/model_server/run_model_server.sh &

printf "Running ALLAN bot\n"
printf "    ___    __    __    ___    _   __\n"
printf "   /   |  / /   / /   /   |  / | / /\n"
printf "  / /| | / /   / /   / /| | /  |/ / \n"
printf " / ___ |/ /___/ /___/ ___ |/ /|  /  \n"
printf "/_/  |_/_____/_____/_/  |_/_/ |_/   \n"

export PYTHONPATH=$PYTHONPATH:/model/src/model_server/research/

#launch dipnet script
python /model/src/model_server/baseline_bots/run_dipnet.py $@
