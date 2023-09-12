#!/usr/bin/env bash

set -euxo pipefail

export WORK=$PWD
CICERO=$(realpath cicero/)
export CICERO
REPO=$(realpath diplomacy_cicero/)
export REPO
export GAME_COMMAND="pip install daidepp/ diplomacy/ && python fairdiplomacy_external/mila_api.py --game_id $1 --host $2 --power $3 --game_type 2"
export CUDA_VISIBLE_DEVICES=$4

cd "$REPO"

singularity run --compat --nv \
  --bind "$WORK"/daidepp:/diplomacy_cicero/daidepp \
  --bind "$WORK"/diplomacy:/diplomacy_cicero/diplomacy \
  --bind "$REPO"/fairdiplomacy_external:/diplomacy_cicero/fairdiplomacy_external \
  --bind "$REPO"/parlai_diplomacy:/diplomacy_cicero/parlai_diplomacy \
  --bind "$REPO"/fairdiplomacy/AMR/:/diplomacy_cicero/fairdiplomacy/AMR/ \
  --bind "$CICERO"/agents:/diplomacy_cicero/conf/common/agents \
  --bind "$CICERO"/models:/diplomacy_cicero/models \
  --bind "$CICERO"/gpt2:/usr/local/lib/python3.7/site-packages/data/gpt2 \
  --pwd /diplomacy_cicero ../cicero_latest.sif bash -c "$GAME_COMMAND"
