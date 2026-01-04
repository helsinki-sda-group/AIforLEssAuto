#!/bin/bash
#SBATCH --job-name="2env"
#SBATCH --output="slurm_output/%A_%a-%x-stdout.log"
#SBATCH --error="slurm_output/%A_%a-%x-stderr.log"
#SBATCH --account=project_2016787
#SBATCH --time=00:30:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --partition=small
#SBATCH --contiguous

# Mahti: 1 CPU core = 1.875 GiB memory (auto-allocated)
# 4 cores = ~7.5 GiB memory (2 SUMO envs + main process + buffer)

# load modules
module load pytorch

# List all modules
module list

# declare env variables for SUMO
export LIBSUMO_AS_TRACI=1
export SUMO_HOME="/projappl/project_2016787/AIforLEssAuto/WP4/rl-ridepooling/ridepool-venv/bin"

cd /projappl/project_2016787/AIforLEssAuto/WP4/rl-ridepooling
pwd

taskset -cp $$

srun echo $OMP_NUM_THREADS

srun singularity exec \
    -B "/usr/lib64/libnsl.so.1" \
    -B /run/nvme \
    -B /users/volodymy \
    "$SING_IMAGE" \
    bash -c "source ridepool-venv/bin/activate && \
    python src/tests/gym_test-rs.py \
    --config configs/policy_training/old_net/default.yaml \
    --num-envs 2 \
    --postfix ${SLURM_JOB_ID}_${SLURM_JOB_NAME}"
