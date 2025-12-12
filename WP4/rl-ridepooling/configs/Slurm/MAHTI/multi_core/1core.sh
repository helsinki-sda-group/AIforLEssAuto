#!/bin/bash
#SBATCH --job-name="1_0.2_16e_8c"
#SBATCH --output="output/%A_%a-%x-stdout.log"
#SBATCH --error="output/%A_%a-%x-stderr.log"
#SBATCH --account=project_462000655
#SBATCH --time=5
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --partition=debug
#SBATCH --extra-node-info=1-1:8:1

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
    --num-envs 1 \
    --postfix ${SLURM_JOB_ID}_${SLURM_JOB_NAME}"



