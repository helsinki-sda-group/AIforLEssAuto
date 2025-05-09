#!/bin/bash
#SBATCH --job-name="3_0.6_32e_16c"
#SBATCH --output="output/%A_%a-%x-stdout.log"
#SBATCH --error="output/%A_%a-%x-stderr.log"
#SBATCH --account=project_462000655
#SBATCH --time=8:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=32G
#SBATCH --partition=small
#SBATCH --extra-node-info=1-1:16:1

# load modules
module --force purge
module load LUMI/24.03
module load lumi-CPEtools
module load partition/C
module load PyTorch/2.2.2-rocm-5.6.1-python-3.10-vllm-0.4.0.post1-singularity-20240617

# list all modules
module list

# declare env variables for SUMO
export LIBSUMO_AS_TRACI=1
export SUMO_HOME=/user-software/venv/pytorch/bin

# declare env variables for OMP
export OMP_DISPLAY_ENV=verbose

cd ~/prj/AIforLEssAuto/WP4/rl-ridepooling
pwd

taskset -cp $$
srun hybrid_check -n -r

srun --hint=compute_bound singularity exec --bind /usr/lib64 $SIF python src/tests/gym_test-rs.py --config configs/policy_training/helsinki_updated_areas/area3_sampled_0.6.yaml --total-iters 32 --num-envs 32 --postfix ${SLURM_JOB_ID}_${SLURM_JOB_NAME}


