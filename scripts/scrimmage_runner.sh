#!/bin/bash
GAME_ID=$1
bot1=/corral/projects/DARPA-SHADE/Milestone_4/Jataware/borgia_0.2.sif
bot2=/corral/projects/DARPA-SHADE/Milestone_4/Jataware/borgia_0.2.sif
bot3=/corral/projects/DARPA-SHADE/Milestone_4/Northwestern/nu_shade_bot.sif
bot4=/corral/projects/DARPA-SHADE/Milestone_4/LM_Adv_Tech_Lab/sifs/mse.sif
agent=/corral/projects/DARPA-SHADE/Milestone_4/UMD/allan_v2.1.sif
host=shade.tacc.utexas.edu
opts="--bot_type SmartOrderAccepterBot --sleep_delay False --discount_factor 0.5"
singularity run $agent --host $host --game_id $GAME_ID --power AUSTRIA $opts &
sleep 5
singularity run $agent --host $host --game_id $GAME_ID --power ENGLAND $opts &
sleep 5
singularity run $agent --host $host --game_id $GAME_ID --power GERMANY $opts &
sleep 5
singularity run $agent --host $host --game_id $GAME_ID --power FRANCE $opts &
sleep 5
singularity run $agent --host $host --game_id $GAME_ID --power ITALY $opts &
sleep 5
singularity run $agent --host $host --game_id $GAME_ID --power RUSSIA $opts &
sleep 5
singularity run $agent --host $host --game_id $GAME_ID --power TURKEY $opts &