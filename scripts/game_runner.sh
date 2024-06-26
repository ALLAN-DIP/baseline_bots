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

for COMMAND_FILE in "$@"; do
  time python -m chiron_utils.scripts.run_game "$COMMAND_FILE"
done
