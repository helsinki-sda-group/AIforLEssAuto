#!/bin/bash
#=============================================================================
# MAHTI Job Template - Parameterized via environment variables
#=============================================================================
# Required environment variables (passed via sbatch --export):
#   AREA          - Network area: "toy" or "area3"
#   DEMAND        - Demand level: "0.2" or "1.0" (ignored for toy)
#   DELTA         - RL step duration: 1, 30, etc.
#   NUM_ENVS      - Number of parallel SUMO environments: 1, 126
#   TRAIN_FREQ    - DQN train frequency: 4, 100, etc.
#   GRADIENT_STEPS - Gradient steps per update: -1, 1, etc.
#   SCALING_COEF  - Episode scaling coefficient: 0, 1
#=============================================================================

# Build job name from parameters
JOB_NAME="${AREA}_d${DEMAND}_delta${DELTA}_env${NUM_ENVS}_tf${TRAIN_FREQ}_gs${GRADIENT_STEPS}_sc${SCALING_COEF}"

#SBATCH --job-name="${JOB_NAME}"
#SBATCH --output="slurm_output/%A-%x-stdout.log"
#SBATCH --error="slurm_output/%A-%x-stderr.log"
#SBATCH --account=project_2016787
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --contiguous
#SBATCH --mail-user=volodymyr.beimuk@helsinki.fi
#SBATCH --mail-type=FAIL,TIME_LIMIT

# Note: --time, --cpus-per-task, --partition are set dynamically
# via sbatch command line in run_experiments.sh

#=============================================================================
# Construct SUMOCFG path based on area and demand
#=============================================================================

if [ "$AREA" == "toy" ]; then
    SUMOCFG="nets/ridepooling/older_net.sumocfg"
else
    # area3 path pattern
    SUMOCFG="nets/ridepooling/Helsinki updated areas/${AREA}/${AREA}_sampled_${DEMAND}_3000.sumocfg.xml"
fi

#=============================================================================
# Environment setup
#=============================================================================

# Load modules
module load pytorch

# List all modules
module list

# SUMO environment variables
export LIBSUMO_AS_TRACI=1
export SUMO_HOME="/projappl/project_2016787/AIforLEssAuto/WP4/rl-ridepooling/ridepool-venv/bin"

# Navigate to project directory
cd /projappl/project_2016787/AIforLEssAuto/WP4/rl-ridepooling
pwd

# Debug info
echo "=== Job Parameters ==="
echo "AREA: $AREA"
echo "DEMAND: $DEMAND"
echo "DELTA: $DELTA"
echo "NUM_ENVS: $NUM_ENVS"
echo "TRAIN_FREQ: $TRAIN_FREQ"
echo "GRADIENT_STEPS: $GRADIENT_STEPS"
echo "SCALING_COEF: $SCALING_COEF"
echo "SUMOCFG: $SUMOCFG"
echo "JOB_NAME: $JOB_NAME"
echo "======================"

taskset -cp $$
srun echo "OMP_NUM_THREADS: $OMP_NUM_THREADS"

#=============================================================================
# Run training
#=============================================================================

srun singularity exec \
    -B "/usr/lib64/libnsl.so.1" \
    -B /users/volodymy \
    "$SING_IMAGE" \
    bash -c "source ridepool-venv/bin/activate && \
    python src/tests/gym_test-rs.py \
    --config configs/policy_training/base.yaml \
    --num-envs ${NUM_ENVS} \
    --delta ${DELTA} \
    --train-freq ${TRAIN_FREQ} \
    --gradient-steps ${GRADIENT_STEPS} \
    --scaling-coef ${SCALING_COEF} \
    --sumocfg '${SUMOCFG}' \
    --postfix ${SLURM_JOB_ID}_${JOB_NAME}"
