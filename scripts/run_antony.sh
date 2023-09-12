#!/usr/bin/env bash

set -euxo pipefail

GAME_ID=$1
HOST=$2
POWER=$3
OUTDIR=$4
CUDA_NUM=$5
shift 5

export WORK=$PWD
REPO=$(realpath diplomacy_cicero/)
export REPO
CICERO=$(realpath cicero/)
export CICERO
OUTDIR=$(realpath "$OUTDIR")
export OUTDIR
export GAME_COMMAND=(
  python fairdiplomacy_external/mila_api.py
  --game_id "$GAME_ID"
  --host "$HOST"
  --power "$POWER"
  --outdir fairdiplomacy_external/out
)

# Sets `CUDA_VISIBLE_DEVICES` inside the container
# From https://docs.sylabs.io/guides/3.11/user-guide/gpu.html#multiple-gpus
export SINGULARITYENV_CUDA_VISIBLE_DEVICES=$CUDA_NUM

mkdir -p "$OUTDIR"

time singularity run --compat --nv \
  --env OPENBLAS_NUM_THREADS=4 \
  --bind "$REPO"/fairdiplomacy/AMR/:/diplomacy_cicero/fairdiplomacy/AMR/ \
  --bind "$REPO"/fairdiplomacy_external:/diplomacy_cicero/fairdiplomacy_external \
  --bind "$OUTDIR":/diplomacy_cicero/fairdiplomacy_external/out \
  --bind "$CICERO"/agents:/diplomacy_cicero/conf/common/agents \
  --bind "$CICERO"/models:/diplomacy_cicero/models \
  --bind "$CICERO"/gpt2:/usr/local/lib/python3.7/site-packages/data/gpt2 \
  --pwd /diplomacy_cicero \
  antony_5.0.sif "${GAME_COMMAND[@]}" "$@"
