#!/usr/bin/env bash

set -euo pipefail

tensorflow_model_server \
  --port=9501 \
  --model_name="player" \
  --enable_batching=true \
  --batching_parameters_file="$BATCH_FILE" \
  --model_base_path=/model/src/model_server/bot_neurips2019-sl_model/ \
  --tensorflow_session_parallelism=8 \
  --file_system_poll_wait_seconds=3
