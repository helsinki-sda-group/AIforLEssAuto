#!/bin/bash
#SBATCH --job-name="8env"
#SBATCH --output="output/%A_%a-%x-stdout.log"
#SBATCH --error="output/%A_%a-%x-stderr.log"
#SBATCH --account=project_2016787
#SBATCH --time=5
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=10
#SBATCH --partition=debug
#SBATCH --gres=nvme:5

# Mahti: 1 CPU core = 1.875 GiB memory (auto-allocated)
# 10 cores = ~18.75 GiB memory (8 SUMO envs + main process + buffer)

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
srun hybrid_check -n -r

srun echo $OMP_NUM_THREADS

srun singularity exec \
    -B "/usr/lib64/libnsl.so.1" \
    -B /run/nvme \
    -B /users/volodymy \
    "$SING_IMAGE" \
    bash -c "source ridepool-venv/bin/activate && \
    python src/tests/gym_test-rs.py \
    --config configs/policy_training/old_net/default.yaml \
    --num-envs 8 \
    --postfix ${SLURM_JOB_ID}_${SLURM_JOB_NAME}"
