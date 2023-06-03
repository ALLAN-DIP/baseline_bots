#!/usr/bin/env bash

set -euo pipefail

SCRIPT_FILE=$(readlink --canonicalize "$0")
SCRIPT_NAME=$(basename "$SCRIPT_FILE")
SCRIPT_DIR=$(dirname "$SCRIPT_FILE")
IS_ON_TACC=$(
  [[ $(hostname) =~ .*\.tacc\.utexas\.edu ]]
  echo $?
)

if [ "${1:-}" = "--help" ]; then
  echo "usage: bash $SCRIPT_NAME [--runner RUNNER] [--game-id GAME_ID] [--agent AGENT] [bot args]" >&2
  echo >&2
  echo 'Arguments must be provided in this order.' >&2
  echo 'RUNNER must be either "apptainer" or "docker".' >&2
  echo 'It defaults to "apptainer" on TACC but "docker" everywhere else.' >&2
  echo 'If GAME_ID is not provided, then one will be generated automatically.' >&2
  echo 'If AGENT is not provided, then a default will be chosen depending on the runner and host.' >&2
  echo 'Bot args are passed when running the container.' >&2
  exit 1
fi

if [ -n "${1:-}" ] && [ "--runner" = "$1" ]; then
  RUNNER=$2
  shift 2
elif [[ $IS_ON_TACC -eq 0 ]]; then
  RUNNER=apptainer
else
  RUNNER=docker
fi

if [[ $RUNNER == apptainer ]]; then
  if ! command -v apptainer 1>/dev/null 2>&1; then
    echo -n "Apptainer is not installed." >&2
    if [[ $IS_ON_TACC -eq 0 ]]; then
      echo -n " Run \`module load tacc-apptainer\`." >&2
    fi
    echo >&2
    exit 2
  fi
  # Flags based on following docs:
  # - https://apptainer.org/docs/user/1.1/cli/apptainer_run.html
  # - https://apptainer.org/docs/user/1.1/docker_and_oci.html#docker-like-compat-flag
  RUN_CMD='apptainer run --cleanenv --ipc --no-eval --no-home --no-init --no-umask --pid'
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
  if [[ $RUNNER == apptainer ]] && [[ $IS_ON_TACC -eq 0 ]]; then
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
  # Calculate relative path based on script's expected location
  CANONICAL_PWD=$(readlink --canonicalize "$PWD")
  CREATE_GAME_SCRIPT="$SCRIPT_DIR"/create_game.py
  CREATE_GAME_SCRIPT=${CREATE_GAME_SCRIPT#"$CANONICAL_PWD"/}
  if [[ ! -f $CREATE_GAME_SCRIPT ]]; then
    echo 'Cannot find "create_game.py" script. The ID of an existing game must be provided.' >&2
    exit 2
  fi

  CUR_ISO_DATE=$(date -u +'%Y_%m_%d_%H_%M_%S')
  GAME_ID=${USER}_$CUR_ISO_DATE

  echo 'Creating game with SHADE account "allanumd" with password "password"'
  python "$CREATE_GAME_SCRIPT" --game_id "$GAME_ID" --deadline 300 --host $HOST

  DOWNLOAD_GAME_SCRIPT="$SCRIPT_DIR"/download_game.py
  DOWNLOAD_GAME_SCRIPT=${DOWNLOAD_GAME_SCRIPT#"$CANONICAL_PWD"/}
  if [[ -f $DOWNLOAD_GAME_SCRIPT ]]; then
    echo 'Your game can be downloaded with the following command:'
    echo -e "\tpython $DOWNLOAD_GAME_SCRIPT --game_id '$GAME_ID' --host '$HOST'"
  fi
fi

LOG_DIR=logs/"$GAME_ID"
mkdir -p "$LOG_DIR"

POWERS=(AUSTRIA ENGLAND FRANCE GERMANY ITALY RUSSIA TURKEY)
for POWER in "${POWERS[@]}"; do
  $RUN_CMD "$AGENT" --host $HOST --game_id "$GAME_ID" --power "$POWER" "${OPTS[@]}" "$@" \
    &>"$LOG_DIR"/"$POWER".txt &
  sleep 4
done
