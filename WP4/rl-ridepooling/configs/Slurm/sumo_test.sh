#!/bin/bash
#SBATCH --job-name=sumo_test
#SBATCH --account=project_462000655
#SBATCH --time=5
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --partition=small

export LIBSUMO_AS_TRACI=1
export SUMO_HOME=/user-software/venv/pytorch/bin

cd ~/prj/AIforLEssAuto/WP4/rl-ridepooling
pwd
module --force purge
module load LUMI/23.09 partition/C PyTorch/2.2.0-rocm-5.6.1-python-3.10-singularity-exampleVenv-20240315


srun singularity exec --bind /usr/lib64 $SIF python src/tests/gym_test-rs.py
