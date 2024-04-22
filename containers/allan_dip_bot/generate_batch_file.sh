#!/usr/bin/env bash

set -euo pipefail

{
  printf "max_batch_size { value: %s }\n" "$MAX_BATCH_SIZE"
  printf "batch_timeout_micros { value: %s }\n" "$BATCH_TIMEOUT_MICROS"
  printf "max_enqueued_batches { value: %s }\n" "$MAX_ENQUEUED_BATCHES"
  printf "num_batch_threads { value: %s }\n" "$NUM_BATCH_THREADS"
  printf "pad_variable_length_inputs: %s\n" "$PAD_VARIABLE_LENGTH_INPUTS"
} >"$BATCH_FILE"
