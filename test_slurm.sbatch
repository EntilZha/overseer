#!/bin/sh

#SBATCH --job-name=overseer
#SBATCH --cpus-per-task 1
#SBATCH --ntasks-per-node=1
#SBATCH --partition=devlab
#SBATCH --mem=1GB
#SBATCH --nodes=2

srun python main.py record /checkpoint/par/overseer &
srun sleep 1h
wait