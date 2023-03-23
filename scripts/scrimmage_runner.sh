#!/usr/bin/env bash

set -euo pipefail

GAME_ID=$1
agent=/corral/projects/DARPA-SHADE/Milestone_4/UMD/allan_v2.1.sif
host=shade.tacc.utexas.edu
opts="--bot_type SmartOrderAccepterBot --sleep_delay False --discount_factor 0.5"

singularity run "$agent" --host "$host" --game_id "$GAME_ID" --power AUSTRIA "$opts" &
sleep 5
singularity run "$agent" --host "$host" --game_id "$GAME_ID" --power ENGLAND "$opts" &
sleep 5
singularity run "$agent" --host "$host" --game_id "$GAME_ID" --power GERMANY "$opts" &
sleep 5
singularity run "$agent" --host "$host" --game_id "$GAME_ID" --power FRANCE "$opts" &
sleep 5
singularity run "$agent" --host "$host" --game_id "$GAME_ID" --power ITALY "$opts" &
sleep 5
singularity run "$agent" --host "$host" --game_id "$GAME_ID" --power RUSSIA "$opts" &
sleep 5
singularity run "$agent" --host "$host" --game_id "$GAME_ID" --power TURKEY "$opts" &
