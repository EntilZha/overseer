# Overseer Cluster Monitoring

Overseer is a barebones, cluster/job monitoring package. It has two components:

1. Command to be run on workers/hosts that will log `psutil` stats to a file based on hostname/Slurm IDs/command line args. The program runs an infinite `while` loop and by default logs data every 15 seconds.
2. Streamlit app that given the stats directory from (1), will visualize the data.

## Adding Overseer to a bash script

If you have a bash script that runs a command, then only minimal changes are needed. Assuming a command like `python do_stuff.py

```bash
#!/usr/bin/env bash

python main.py record /checkpoint/par/stats_output &
python do_stuff.py
wait
```

## Adding Overseer to a slurm job

Adding overseer to a slurm job is similarly easy. Overseer will automatically detect Slurm environment variables and separate data by host/Job ID/Proc ID/etc. Below is one example:

```bash
#!/bin/sh

#SBATCH --job-name=overseer
#SBATCH --cpus-per-task 1
#SBATCH --ntasks-per-node=1
#SBATCH --partition=devlab
#SBATCH --mem=1GB
#SBATCH --nodes=2

srun python main.py record /checkpoint/par/stats_output &
srun sleep 1h
wait
```

## Running Visualization UI

To visualize cluster stats, simply run

```
streamlit run overseer/monitor.py
```

## Installation

1. (Optional) Create an anaconda/minconda environment and activate it.
2. Install python poetry
3. Run `poetry install` (this will create a virtual env unless a conda environment is active)
