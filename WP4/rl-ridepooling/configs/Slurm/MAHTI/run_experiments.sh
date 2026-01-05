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

# Network areas: "toy" (old network) or "area3" (Helsinki area 3)
AREAS=("toy" "area3")

# Demand levels: percentage of trips as taxi passengers
# Note: "toy" network only supports 1.0, combinations with 0.2 will be skipped
DEMANDS=("0.2" "1.0")

# Delta: RL step duration in SUMO simulation steps
DELTAS=(1 30)

# Number of parallel SUMO environments (affects CPU allocation)
# 1 env -> 3 CPUs, small partition
# 126 envs -> 128 CPUs, medium partition
NUM_ENVS_LIST=(1 126)

# DQN train frequency: update model every N steps
TRAIN_FREQS=(4 100)

# Gradient steps per update: -1 means use num_envs, 1 means single step
GRADIENT_STEPS_LIST=(-1 1)

# Episode scaling coefficient: 0 = no scaling, 1 = full scaling for delta
SCALING_COEFS=(0 1)

#=============================================================================
# SLURM CONFIGURATION
#=============================================================================

ACCOUNT="project_2016787"
MAIL_USER="volodymyr.beimuk@helsinki.fi"

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
SKIPPED_COUNT=0

echo "Submitting experiment jobs..."
echo ""

for AREA in "${AREAS[@]}"; do
    for DEMAND in "${DEMANDS[@]}"; do
        # Skip invalid combination: toy network doesn't have 0.2 demand
        if [ "$AREA" == "toy" ] && [ "$DEMAND" == "0.2" ]; then
            ((SKIPPED_COUNT++))
            continue
        fi

        for DELTA in "${DELTAS[@]}"; do
            for NUM_ENVS in "${NUM_ENVS_LIST[@]}"; do
                for TRAIN_FREQ in "${TRAIN_FREQS[@]}"; do
                    for GRADIENT_STEPS in "${GRADIENT_STEPS_LIST[@]}"; do
                        for SCALING_COEF in "${SCALING_COEFS[@]}"; do

                            # Build job name
                            JOB_NAME="${AREA}_d${DEMAND}_delta${DELTA}_env${NUM_ENVS}_tf${TRAIN_FREQ}_gs${GRADIENT_STEPS}_sc${SCALING_COEF}"

                            # Determine resources based on NUM_ENVS
                            if [ "$NUM_ENVS" -eq 1 ]; then
                                CPUS=3
                                PARTITION="small"
                            else
                                CPUS=128
                                PARTITION="medium"
                            fi

                            # Determine time limit based on area and num_envs
                            if [ "$AREA" == "toy" ]; then
                                if [ "$NUM_ENVS" -eq 1 ]; then
                                    TIME_LIMIT="00:30:00"
                                else
                                    TIME_LIMIT="02:00:00"
                                fi
                            else
                                # area3 gets 10 hours
                                TIME_LIMIT="10:00:00"
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
                                --export=ALL,AREA=${AREA},DEMAND=${DEMAND},DELTA=${DELTA},NUM_ENVS=${NUM_ENVS},TRAIN_FREQ=${TRAIN_FREQ},GRADIENT_STEPS=${GRADIENT_STEPS},SCALING_COEF=${SCALING_COEF} \
                                ${TEMPLATE_SCRIPT}"

                            if [ "$DRY_RUN" == true ]; then
                                echo "[DRY RUN] Would submit: $JOB_NAME"
                                echo "  Command: $SBATCH_CMD"
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
done

echo ""
echo "=============================================================================";
echo "Summary:"
echo "  Jobs submitted: $JOB_COUNT"
echo "  Combinations skipped: $SKIPPED_COUNT (toy + 0.2 demand)"
echo "=============================================================================";

if [ "$DRY_RUN" == true ]; then
    echo ""
    echo "This was a dry run. To actually submit jobs, run without --dry-run flag."
fi
