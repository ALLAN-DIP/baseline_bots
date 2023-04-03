#!/usr/bin/env bash

set -euo pipefail

batch_file="batch.txt"
{
  printf "max_batch_size { value: %s }\n" "$MAX_BATCH_SIZE"
  printf "batch_timeout_micros { value: %s }\n" "$BATCH_TIMEOUT_MICROS"
  printf "max_enqueued_batches { value: %s }\n" "$MAX_ENQUEUED_BATCHES"
  printf "num_batch_threads { value: %s }\n" "$NUM_BATCH_THREADS"
  printf "pad_variable_length_inputs: %s\n" "$PAD_VARIABLE_LENGTH_INPUTS"
} >$batch_file

tensorflow_model_server --port=9501 --model_name="player" --enable_batching=true --batching_parameters_file=batch.txt --model_base_path=/model/src/model_server/bot_neurips2019-sl_model/ --tensorflow_session_parallelism=8 --file_system_poll_wait_seconds=3

~
