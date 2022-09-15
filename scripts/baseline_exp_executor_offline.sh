#!/bin/bash
#SBATCH -J np_leader_follower           # Job name
#SBATCH -o out/np_leader_follower.o%j       # Name of stdout output file
#SBATCH -e out/np_leader_follower.e%j       # Name of stderr error file
#SBATCH -p normal           # Queue (partition) name
#SBATCH -N 1              # Total # of nodes (must be 1 for serial)
#SBATCH -n 1
#SBATCH -t 48:00:00        # Run time (hh:mm:ss)
#SBATCH --mail-type=all    # Send email at begin and end of job
#SBATCH --mail-user=wwongkam@umd.edu

module add python3/3.7.13
module load tacc-singularity
export WORKING_DIR=$WORK/dipnet_press/WORKING_DIR/
export PYTHONPATH=$PYTHONPATH:$WORK/dipnet_press/
python3 baseline_exp_executor_offline.py