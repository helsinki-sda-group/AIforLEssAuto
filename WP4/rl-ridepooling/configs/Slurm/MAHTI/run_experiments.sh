#!/bin/bash
#=============================================================================
# MAHTI Master Experiment Launcher
#=============================================================================
# This script submits batch jobs for all parameter combinations.
# Edit the arrays below to customize which experiments to run.
#
# Usage:
#   ./run_experiments.sh           # Submit all jobs
#   ./run_experiments.sh --dry-run # Preview commands without submitting
#=============================================================================

#=============================================================================
# PARAMETER CONFIGURATION - Edit these arrays to customize experiments
#=============================================================================

# Network areas: "toy" (old network) or "area1" (Helsinki area 1)
AREAS=("toy" "area1")

# Number of parallel SUMO environments and corresponding CPU allocation
# Format: "num_envs:cpus"
ENV_CORES_PAIRS=("1:3" "2:4" "4:6" "8:10" "16:18" "32:34")

# Delta and Scaling coefficient combinations (specific pairs, not all combinations)
# Format: "delta:scaling_coef"
# Delta 1: scaling 0
# Delta 3: scaling 0, 0.25, 0.5, 0.75, 1
# Delta 9: scaling 0, 0.1, 0.2, 0.3
# Delta 30: scaling 0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.1
DELTA_SCALING_PAIRS=(
    "1:0"
    "3:0" "3:0.25" "3:0.5" "3:0.75" "3:1"
    "9:0" "9:0.0625" "9:0.125" "9:0.1875" "9:0.25"
    "30:0" "30:0.017" "30:0.034" "30:0.051" "30:0.068"
)

# Number of episodes (area-specific)
# toy: 32, 64, 128
# area1: 128, 256, 512
TOY_EPISODES=(32 64 128)
AREA1_EPISODES=(256 512 1024)

# Gradient steps and train frequency combinations
# Format: "gradient_steps:train_freq"
# Note: "n" means use num_envs value, represented as -1
GRAD_TRAINFREQ_PAIRS=("1:1" "1:4" "-1:1" "-1:4")

# Random seeds for reproducibility (5 different seeds)
SEEDS=(42 123 456 789 1024)

#=============================================================================
# SLURM CONFIGURATION
#=============================================================================

ACCOUNT="project_2016787"
MAIL_USER="volodymyr.beimuk@helsinki.fi"
PARTITION="small"

# Base directory (should match where this script is run from on MAHTI)
PROJECT_DIR="/projappl/project_2016787/AIforLEssAuto/WP4/rl-ridepooling"
TEMPLATE_SCRIPT="${PROJECT_DIR}/configs/Slurm/MAHTI/job_template.sh"

#=============================================================================
# PARSE ARGUMENTS
#=============================================================================

DRY_RUN=false
if [ "$1" == "--dry-run" ]; then
    DRY_RUN=true
    echo "=== DRY RUN MODE - No jobs will be submitted ==="
    echo ""
fi

#=============================================================================
# CREATE SLURM OUTPUT DIRECTORY
#=============================================================================

mkdir -p "${PROJECT_DIR}/slurm_output"

#=============================================================================
# SUBMIT JOBS FOR ALL PARAMETER COMBINATIONS
#=============================================================================

JOB_COUNT=0

echo "Submitting experiment jobs..."
echo ""

for AREA in "${AREAS[@]}"; do
    # Select episodes based on area
    if [ "$AREA" == "toy" ]; then
        EPISODES_LIST=("${TOY_EPISODES[@]}")
    else
        EPISODES_LIST=("${AREA1_EPISODES[@]}")
    fi

    for BASIC_EPISODES in "${EPISODES_LIST[@]}"; do
        for SEED in "${SEEDS[@]}"; do
            for ENV_CORES in "${ENV_CORES_PAIRS[@]}"; do
                # Parse num_envs and cpus from pair
                NUM_ENVS="${ENV_CORES%%:*}"
                CPUS="${ENV_CORES##*:}"

                for DELTA_SCALING in "${DELTA_SCALING_PAIRS[@]}"; do
                    # Parse delta and scaling_coef from pair
                    DELTA="${DELTA_SCALING%%:*}"
                    SCALING_COEF="${DELTA_SCALING##*:}"

                    for GRAD_TF in "${GRAD_TRAINFREQ_PAIRS[@]}"; do
                        # Parse gradient_steps and train_freq from pair
                        GRADIENT_STEPS="${GRAD_TF%%:*}"
                        TRAIN_FREQ="${GRAD_TF##*:}"

                        # Build job name
                        JOB_NAME="${AREA}_ep${BASIC_EPISODES}_env${NUM_ENVS}_delta${DELTA}_sc${SCALING_COEF}_gs${GRADIENT_STEPS}_tf${TRAIN_FREQ}_seed${SEED}"

                        # Determine time limit based on area
                        if [ "$AREA" == "toy" ]; then
                            TIME_LIMIT="3-00:00:00"
                        else
                            # area1
                            TIME_LIMIT="3-00:00:00"
                        fi

                        # Build sbatch command
                        SBATCH_CMD="sbatch \
                            --job-name=\"${JOB_NAME}\" \
                            --output=\"slurm_output/%A-%x-stdout.log\" \
                            --error=\"slurm_output/%A-%x-stderr.log\" \
                            --account=${ACCOUNT} \
                            --time=${TIME_LIMIT} \
                            --nodes=1 \
                            --ntasks=1 \
                            --cpus-per-task=${CPUS} \
                            --partition=${PARTITION} \
                            --contiguous \
                            --mail-user=${MAIL_USER} \
                            --mail-type=FAIL,TIME_LIMIT \
                            --export=ALL,AREA=${AREA},BASIC_EPISODES=${BASIC_EPISODES},SEED=${SEED},DELTA=${DELTA},NUM_ENVS=${NUM_ENVS},TRAIN_FREQ=${TRAIN_FREQ},GRADIENT_STEPS=${GRADIENT_STEPS},SCALING_COEF=${SCALING_COEF},JOB_NAME=${JOB_NAME} \
                            ${TEMPLATE_SCRIPT}"

                        if [ "$DRY_RUN" == true ]; then
                            echo "[DRY RUN] Would submit: $JOB_NAME"
                            echo "  CPUs: $CPUS, Time: $TIME_LIMIT"
                            echo ""
                        else
                            echo "Submitting: $JOB_NAME"
                            eval $SBATCH_CMD
                        fi

                        ((JOB_COUNT++))

                    done
                done
            done
        done
    done
done

echo ""
echo "=============================================================================";
echo "Summary:"
echo "  Total jobs submitted: $JOB_COUNT"
echo "  Parameter combinations:"
echo "    Areas: ${AREAS[*]}"
echo "    Env-Cores pairs: ${ENV_CORES_PAIRS[*]}"
echo "    Delta-Scaling pairs: ${#DELTA_SCALING_PAIRS[@]} combinations"
echo "    Episodes (toy): ${TOY_EPISODES[*]}"
echo "    Episodes (area1): ${AREA1_EPISODES[*]}"
echo "    Gradient-TrainFreq pairs: ${GRAD_TRAINFREQ_PAIRS[*]}"
echo "    Seeds: ${SEEDS[*]}"
echo "=============================================================================";

if [ "$DRY_RUN" == true ]; then
    echo ""
    echo "This was a dry run. To actually submit jobs, run without --dry-run flag."
fi
