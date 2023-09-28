#!/usr/bin/env bash

#SBATCH --partition=isi
#SBATCH --ntasks=1
#SBATCH --mem-per-gpu=62G  # A little less than 1/8 of node's memory
#SBATCH --cpus-per-gpu=8  # Exactly 1/8 of node's CPUs
#SBATCH --gres='gpu:a40:7'
#SBATCH --time=24:00:00
#SBATCH --job-name=RUN_ANTONYS
#SBATCH --mail-type=all

set -euxo pipefail

# Determine directory script is stored in
# `sbatch` makes a temporary copy when the job is queued,
# so some complex logic is needed
# Currently does not support paths with spaces,
# but that is difficult to do without a Bash parser
# Based on https://stackoverflow.com/a/56991068/2445901
if [[ -n ${SLURM_JOB_ID:-} ]]; then
  SCRIPT_FILE=$(scontrol show job "$SLURM_JOB_ID" | grep -E '^   Command' | cut -f 2- -d '=' | cut -f 1 -d ' ')
else
  SCRIPT_FILE=$0
fi
SCRIPT_DIR=$(dirname "$(realpath "$SCRIPT_FILE")")

for COMMAND_FILE in "$@"; do
  time python "$SCRIPT_DIR"/run_game.py "$COMMAND_FILE"
done
