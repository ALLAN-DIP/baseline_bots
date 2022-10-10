#!/bin/bash

#launch model server
/model/src/model_server/run_model_server.sh &

export PYTHONPATH=$PYTHONPATH:/model/src/model_server/research/

#launch dipnet script
python /model/src/model_server/baseline_bots/run_dipnet.py $@
