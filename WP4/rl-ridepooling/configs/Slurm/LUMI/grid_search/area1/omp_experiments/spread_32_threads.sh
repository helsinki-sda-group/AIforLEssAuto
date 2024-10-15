#!/bin/bash
#SBATCH --job-name="spread_32_numth_threads"
#SBATCH --output="output/%A_%a-%x-stdout.log"
#SBATCH --error="output/%A_%a-%x-stderr.log"
#SBATCH --account=project_462000655
#SBATCH --time=2:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=20G
#SBATCH --partition=small

# load modules
module --force purge
module load LUMI/23.09
module load lumi-CPEtools
module load partition/C
module load PyTorch/2.2.0-rocm-5.6.1-python-3.10-singularity-exampleVenv-20240315

# declare env variables for SUMO
export LIBSUMO_AS_TRACI=1
export SUMO_HOME=/user-software/venv/pytorch/bin

# declare env variables for OMP
export OMP_DISPLAY_ENV=verbose

export OMP_NUM_THREADS=${SRUN_CPUS_PER_TASK}
echo ${OMP_NUM_THREADS}
export OMP_PROC_BIND=spread
export OMP_PLACES=threads

cd ~/prj/AIforLEssAuto/WP4/rl-ridepooling
pwd

taskset -cp $$
srun hybrid_check -n -r

srun singularity exec --bind /usr/lib64 $SIF python src/tests/gym_test-rs.py --config configs/policy_training/helsinki_updated_areas/area1_sampled_0.2.yaml --num-envs 32 --postfix ${SLURM_JOB_ID}_${SLURM_JOB_NAME}


