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
DELTA_SCALING_PAIRS=(
    "1:0"
    "3:0" "3:0.25" "3:0.5" "3:0.75" "3:1"
    "9:0" "9:0.0625" "9:0.125" "9:0.1875" "9:0.25"
    "30:0" "30:0.017" "30:0.034" "30:0.051" "30:0.068"
)

# Number of episodes (area-specific)
TOY_EPISODES=(32 64 128)
AREA1_EPISODES=(128 256 1024)

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
# FUNCTION: Calculate time limit based on area, num_envs, and episodes
#=============================================================================

get_time_limit() {
    local area=$1
    local num_envs=$2
    local episodes=$3
    
    if [ "$area" == "toy" ]; then
        # Toy network: 32env has different times, others share same times
        if [ "$num_envs" -eq 32 ]; then
            case $episodes in
                32)  echo "00:30:00" ;;
                64)  echo "00:45:00" ;;
                128) echo "01:30:00" ;;
            esac
        else
            # 1env, 2env, 4env, 8env, 16env all use same times
            case $episodes in
                32)  echo "00:30:00" ;;
                64)  echo "01:00:00" ;;
                128) echo "02:00:00" ;;
            esac
        fi
    else
        # area1: times vary by num_envs and episodes
        case $num_envs in
            1|2|4)
                case $episodes in
                    128)  echo "02:00:00" ;;
                    256)  echo "04:00:00" ;;
                    1024) echo "16:00:00" ;;
                esac
                ;;
            8)
                case $episodes in
                    128)  echo "02:00:00" ;;
                    256)  echo "03:30:00" ;;
                    1024) echo "14:00:00" ;;
                esac
                ;;
            16)
                case $episodes in
                    128)  echo "01:30:00" ;;
                    256)  echo "03:00:00" ;;
                    1024) echo "10:00:00" ;;
                esac
                ;;
            32)
                case $episodes in
                    128)  echo "00:45:00" ;;
                    256)  echo "01:30:00" ;;
                    1024) echo "06:00:00" ;;
                esac
                ;;
        esac
    fi
}

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

                        # Calculate time limit
                        TIME_LIMIT=$(get_time_limit "$AREA" "$NUM_ENVS" "$BASIC_EPISODES")

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
