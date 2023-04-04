#!/usr/bin/env bash

set -euo pipefail

CUR_FILE=$(basename "$(readlink -f "$0")")
IS_ON_TACC=$(
  [[ $(hostname) =~ .*\.tacc\.utexas\.edu ]]
  echo $?
)

if [ "${1:-}" = "--help" ]; then
  echo "usage: bash $CUR_FILE [--runner RUNNER] [--game-id GAME_ID] [--agent AGENT] [bot args]" >&2
  echo >&2
  echo 'Arguments must be provided in this order.' >&2
  echo 'RUNNER must be either "docker" or "singularity".' >&2
  echo 'It defaults to "singularity" on TACC but "docker" everywhere else.' >&2
  echo 'If GAME_ID is not provided, then one will be generated automatically.' >&2
  echo 'If AGENT is not provided, then a default will be chosen depending on the runner and host.' >&2
  echo 'Bot args are passed when running the container.' >&2
  exit 1
fi

if [ -n "${1:-}" ] && [ "--runner" = "$1" ]; then
  RUNNER=$2
  shift 2
elif [[ $IS_ON_TACC -eq 0 ]]; then
  RUNNER=singularity
else
  RUNNER=docker
fi

if [[ $RUNNER == singularity ]]; then
  if ! command -v singularity 1>/dev/null 2>&1; then
    echo -n "Singularity is not installed." >&2
    if [[ $IS_ON_TACC -eq 0 ]]; then
      echo -n " Run \`module load tacc-singularity\`." >&2
    fi
    echo >&2
    exit 2
  fi
  RUN_CMD='singularity run'
elif [[ $RUNNER == docker ]]; then
  if ! command -v docker 1>/dev/null 2>&1; then
    echo "Docker is not installed." >&2
    exit 2
  fi
  RUN_CMD='docker run --rm'
else
  echo "Provided runner not recognized." >&2
  exit 2
fi

if [ -n "${1:-}" ] && [ "--game-id" = "$1" ]; then
  GAME_ID=$2
  shift 2
else
  GAME_ID=
fi

if [ -n "${1:-}" ] && [ "--agent" = "$1" ]; then
  AGENT=$2
  shift 2
else
  if [[ $RUNNER == singularity ]] && [[ $IS_ON_TACC -eq 0 ]]; then
    # Automatically find latest version downloaded on TACC
    AGENT=$(
      find /corral/projects/DARPA-SHADE/Milestone_4/UMD/ \
        -maxdepth 1 -type f -name 'allan_bots_*.sif' |
        sort | tail -1
    )
  else
    AGENT=allan_dip_bot
  fi
fi

HOST=shade-dev.tacc.utexas.edu
OPTS=(--bot_type SmartOrderAccepterBot)

if [[ -z $GAME_ID ]]; then
  # Calculate path based on script's expected location
  CREATE_GAME_SCRIPT="$(dirname "$(readlink --canonicalize "$0")")"/create_game.py
  if [[ ! -f $CREATE_GAME_SCRIPT ]]; then
    echo 'Cannot find "create_game.py" script. The ID of an existing game must be provided.' >&2
    exit 2
  fi

  CUR_ISO_DATE=$(date -u +'%Y_%m_%d_%H_%M_%S')
  GAME_ID=${USER}_$CUR_ISO_DATE

  echo 'Creating game with SHADE account "allanumd" with password "password"'
  python "$CREATE_GAME_SCRIPT" --game_id "$GAME_ID" --deadline 300 --host $HOST

  DOWNLOAD_GAME_SCRIPT="$(dirname "$(readlink --canonicalize "$0")")"/download_game.py
  if [[ -f $DOWNLOAD_GAME_SCRIPT ]]; then
    echo 'Your game can be downloaded with the following command:'
    echo -e "\tpython $DOWNLOAD_GAME_SCRIPT --game_id '$GAME_ID' --host '$HOST'"
  fi
fi

LOG_DIR=logs/"$GAME_ID"
mkdir -p "$LOG_DIR"

POWERS=(AUSTRIA ENGLAND GERMANY FRANCE ITALY RUSSIA TURKEY)
for POWER in "${POWERS[@]}"; do
  $RUN_CMD "$AGENT" --host $HOST --game_id "$GAME_ID" --power "$POWER" "${OPTS[@]}" "$@" \
    &>"$LOG_DIR"/"$POWER".txt &
  sleep 4
done
