#!/bin/bash
#SBATCH --job-name="1_0.8_128e_64c"
#SBATCH --output="output/%A_%a-%x-stdout.log"
#SBATCH --error="output/%A_%a-%x-stderr.log"
#SBATCH --account=project_462000655
#SBATCH --time=2:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=64
#SBATCH --mem=128G
#SBATCH --partition=small

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
#export OMP_DISPLAY_ENV=verbose

cd ~/prj/AIforLEssAuto/WP4/rl-ridepooling
pwd

taskset -cp $$
srun hybrid_check -n -r

srun --hint=compute_bound singularity exec --bind /usr/lib64 $SIF python src/tests/gym_test-rs.py --config configs/policy_training/helsinki_updated_areas/area1_sampled_0.8.yaml --total-iters 128 --num-envs 128 --postfix ${SLURM_JOB_ID}_${SLURM_JOB_NAME}


