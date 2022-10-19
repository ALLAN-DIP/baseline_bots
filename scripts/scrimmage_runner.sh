#!/bin/bash
GAME_ID=$1
dumbbot=/scratch/01262/jadrake/shade_experiments/containers/dumbbot_v1.sif
agent=/corral/projects/DARPA-SHADE/Milestone_4/UMD/allan_v1.2.sif
host=shade.tacc.utexas.edu
opts="--bot_type SmartOrderAccepterBot"
singularity run $agent --host $host --game_id $GAME_ID --power AUSTRIA $opts &
singularity run $agent --host $host --game_id $GAME_ID --power ENGLAND $opts &
singularity run $agent --host $host --game_id $GAME_ID --power GERMANY $opts &
singularity run $agent --host $host --game_id $GAME_ID --power FRANCE $opts &
singularity run $agent --host $host --game_id $GAME_ID --power ITALY $opts &
singularity run $agent --host $host --game_id $GAME_ID --power RUSSIA $opts &
singularity run $agent --host $host --game_id $GAME_ID --power TURKEY $opts &