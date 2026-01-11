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
START_FROM_JOB=""
SEED=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --start-from)
            START_FROM_JOB="$2"
            shift 2
            ;;
        --seed)
            SEED="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--dry-run] [--start-from <job_name>] --seed <seed_value>"
            exit 1
            ;;
    esac
done

# Validate that seed is provided
if [ -z "$SEED" ]; then
    echo "Error: --seed argument is required"
    echo "Usage: $0 [--dry-run] [--start-from <job_name>] --seed <seed_value>"
    exit 1
fi

if [ "$DRY_RUN" == true ]; then
    echo "=== DRY RUN MODE - No jobs will be submitted ==="
    echo ""
fi

if [ -n "$START_FROM_JOB" ]; then
    echo "=== SKIPPING MODE - Will start from job: $START_FROM_JOB ==="
    echo ""
fi

#=============================================================================
# CREATE SLURM OUTPUT DIRECTORY AND EXPERIMENT LOG FILE
#=============================================================================

mkdir -p "${PROJECT_DIR}/slurm_output"
mkdir -p "${PROJECT_DIR}/experiment_logs"

# Create timestamped experiment log file
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
EXPERIMENT_LOG_FILE="${PROJECT_DIR}/experiment_logs/experiment_${TIMESTAMP}_seed${SEED}.txt"

echo "Experiment log file: $EXPERIMENT_LOG_FILE"
echo ""

#=============================================================================
# QUEUE MONITORING CONFIGURATION
#=============================================================================

# Time to wait between queue checks (seconds) - 10 minutes
QUEUE_CHECK_INTERVAL=600

# Counter for successfully submitted jobs
SUBMITTED_COUNT=0

# Arrays to track job submissions
declare -a FAILED_JOBS=()
declare -a FAILED_JOB_CMDS=()
declare -a SUBMITTED_JOB_IDS=()

#=============================================================================
# FUNCTION: Submit a job with retry logic (retries indefinitely on queue limit)
#=============================================================================

submit_job() {
    local job_name="$1"
    local sbatch_cmd="$2"
    
    while true; do
        SUBMIT_OUTPUT=$(eval $sbatch_cmd 2>&1)
        SUBMIT_STATUS=$?
        
        if [ $SUBMIT_STATUS -eq 0 ]; then
            # Extract job ID from output (format: "Submitted batch job XXXXXX")
            JOB_ID=$(echo "$SUBMIT_OUTPUT" | grep -oP 'Submitted batch job \K[0-9]+')
            echo "  ✓ Success: $SUBMIT_OUTPUT"
            SUBMITTED_JOB_IDS+=("$JOB_ID")
            ((SUBMITTED_COUNT++))
            echo "$job_name,$JOB_ID,SUBMITTED" >> "$EXPERIMENT_LOG_FILE"
            return 0
        else
            # Check if it's a queue limit error
            if echo "$SUBMIT_OUTPUT" | grep -qi "limit\|quota\|maximum\|too many\|AssocMaxSubmitJobLimit"; then
                echo "  ⚠ Queue limit hit: $SUBMIT_OUTPUT"
                echo "  Waiting ${QUEUE_CHECK_INTERVAL}s before retry ($(date +%H:%M:%S))..."
                sleep $QUEUE_CHECK_INTERVAL
                # Continue the loop to retry
            else
                # Non-queue-limit error, record and move on
                echo "  ✗ FAILED: $SUBMIT_OUTPUT"
                echo "$job_name,NONE,FAILED:$SUBMIT_OUTPUT" >> "$EXPERIMENT_LOG_FILE"
                FAILED_JOBS+=("$job_name")
                FAILED_JOB_CMDS+=("$sbatch_cmd")
                return 1
            fi
        fi
    done
}

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
                32)  echo "00:45:00" ;;
                64)  echo "01:00:00" ;;
                128) echo "01:45:00" ;;
            esac
        else
            # 1env, 2env, 4env, 8env, 16env all use same times
            case $episodes in
                32)  echo "00:45:00" ;;
                64)  echo "01:15:00" ;;
                128) echo "02:30:00" ;;
            esac
        fi
    else
        # area1: times vary by num_envs and episodes
        case $num_envs in
            1|2|4)
                case $episodes in
                    128)  echo "1-00:00:00" ;;
                    256)  echo "1-00:00:00" ;;
                    1024) echo "2-00:00:00" ;;
                esac
                ;;
            8)
                case $episodes in
                    128)  echo "1-00:00:00" ;;
                    256)  echo "1-00:00:00" ;;
                    1024) echo "2-00:00:00" ;;
                esac
                ;;
            16)
                case $episodes in
                    128)  echo "1-00:00:00" ;;
                    256)  echo "1-00:00:00" ;;
                    1024) echo "2-00:00:00" ;;
                esac
                ;;
            32)
                case $episodes in
                    128)  echo "1-00:00:00" ;;
                    256)  echo "1-00:00:00" ;;
                    1024) echo "2-00:00:00" ;;
                esac
                ;;
        esac
    fi
}

#=============================================================================
# SUBMIT JOBS FOR ALL PARAMETER COMBINATIONS
#=============================================================================

JOB_COUNT=0
SKIPPED_COUNT=0
FOUND_START=false
FIRST_JOB_TO_RUN=""

# If no start-from job specified, we start immediately
if [ -z "$START_FROM_JOB" ]; then
    FOUND_START=true
fi

#=============================================================================
# COUNT TOTAL JOBS FIRST (for confirmation prompt)
#=============================================================================

TOTAL_JOBS_PREVIEW=0

for AREA in "${AREAS[@]}"; do
    if [ "$AREA" == "toy" ]; then
        EPISODES_LIST=("${TOY_EPISODES[@]}")
    else
        EPISODES_LIST=("${AREA1_EPISODES[@]}")
    fi
    
    for BASIC_EPISODES in "${EPISODES_LIST[@]}"; do
        for ENV_CORES in "${ENV_CORES_PAIRS[@]}"; do
            for DELTA_SCALING in "${DELTA_SCALING_PAIRS[@]}"; do
                for GRAD_TF in "${GRAD_TRAINFREQ_PAIRS[@]}"; do
                    ((TOTAL_JOBS_PREVIEW++))
                done
            done
        done
    done
done

#=============================================================================
# CONFIRMATION PROMPT (only in non-dry-run mode)
#=============================================================================

if [ "$DRY_RUN" == false ]; then
    echo "============================================================================="
    echo "EXPERIMENT SUBMISSION SUMMARY"
    echo "============================================================================="
    echo ""
    echo "You are about to submit $TOTAL_JOBS_PREVIEW jobs to the cluster."
    echo ""
    echo "Parameter combinations:"
    echo "  Areas: ${AREAS[*]}"
    echo "  Env-Cores pairs: ${ENV_CORES_PAIRS[*]}"
    echo "  Delta-Scaling pairs: ${#DELTA_SCALING_PAIRS[@]} combinations"
    echo "  Episodes (toy): ${TOY_EPISODES[*]}"
    echo "  Episodes (area1): ${AREA1_EPISODES[*]}"
    echo "  Gradient-TrainFreq pairs: ${GRAD_TRAINFREQ_PAIRS[*]}"
    echo "  Seed: ${SEED}"
    echo ""
    echo "Experiment log will be saved to: $EXPERIMENT_LOG_FILE"
    echo ""
    echo "============================================================================="
    read -p "Do you want to proceed with job submission? (yes/no): " CONFIRM
    echo ""
    
    if [ "$CONFIRM" != "yes" ] && [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
        echo "Job submission cancelled by user."
        exit 0
    fi
    
    echo "Proceeding with job submission..."
    echo ""
fi

# Write header to experiment log file
echo "# Experiment run log - Started at $(date)" > "$EXPERIMENT_LOG_FILE"
echo "# Format: job_name,job_id,status" >> "$EXPERIMENT_LOG_FILE"
echo "" >> "$EXPERIMENT_LOG_FILE"

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

                    # Check if we should skip this job
                    if [ "$FOUND_START" == false ]; then
                        if [ "$JOB_NAME" == "$START_FROM_JOB" ]; then
                            FOUND_START=true
                            echo ">>> Found starting job: $JOB_NAME <<<"
                            echo ""
                        else
                            ((SKIPPED_COUNT++))
                            continue
                        fi
                    fi

                    # Track first job that will be run
                    if [ -z "$FIRST_JOB_TO_RUN" ]; then
                        FIRST_JOB_TO_RUN="$JOB_NAME"
                    fi

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
                        submit_job "$JOB_NAME" "$SBATCH_CMD"
                    fi

                    ((JOB_COUNT++))

                done
            done
        done
    done
done

echo ""
echo "=============================================================================";

# Calculate total and percentages
TOTAL_JOBS=$((JOB_COUNT + SKIPPED_COUNT))
if [ $TOTAL_JOBS -gt 0 ]; then
    SKIP_PERCENTAGE=$(awk "BEGIN {printf \"%.1f\", ($SKIPPED_COUNT / $TOTAL_JOBS) * 100}")
    SUBMIT_PERCENTAGE=$(awk "BEGIN {printf \"%.1f\", ($JOB_COUNT / $TOTAL_JOBS) * 100}")
else
    SKIP_PERCENTAGE="0.0"
    SUBMIT_PERCENTAGE="0.0"
fi

# Count successful and failed submissions
SUCCESSFUL_SUBMISSIONS=$((JOB_COUNT - ${#FAILED_JOBS[@]}))

echo "Summary:"
if [ -n "$FIRST_JOB_TO_RUN" ]; then
    echo "  First job to run: $FIRST_JOB_TO_RUN"
fi
if [ $SKIPPED_COUNT -gt 0 ]; then
    echo "  Jobs skipped: $SKIPPED_COUNT ($SKIP_PERCENTAGE%)"
fi
echo "  Jobs attempted: $JOB_COUNT ($SUBMIT_PERCENTAGE%)"
echo "  Successful submissions: $SUCCESSFUL_SUBMISSIONS"
echo "  Failed submissions: ${#FAILED_JOBS[@]}"
echo "  Total jobs in sequence: $TOTAL_JOBS"
echo ""
echo "  Experiment log saved to: $EXPERIMENT_LOG_FILE"
echo ""
echo "  Parameter combinations:"
echo "    Areas: ${AREAS[*]}"
echo "    Env-Cores pairs: ${ENV_CORES_PAIRS[*]}"
echo "    Delta-Scaling pairs: ${#DELTA_SCALING_PAIRS[@]} combinations"
echo "    Episodes (toy): ${TOY_EPISODES[*]}"
echo "    Episodes (area1): ${AREA1_EPISODES[*]}"
echo "    Gradient-TrainFreq pairs: ${GRAD_TRAINFREQ_PAIRS[*]}"
echo "    Seed: ${SEED}"
echo "=============================================================================";

# Report failed jobs if any
if [ ${#FAILED_JOBS[@]} -gt 0 ]; then
    echo ""
    echo "WARNING: The following jobs failed to submit after all retries:"
    for i in "${!FAILED_JOBS[@]}"; do
        echo "  - ${FAILED_JOBS[$i]}"
    done
    echo ""
    echo "Check $EXPERIMENT_LOG_FILE for details."
fi

if [ "$DRY_RUN" == true ]; then
    echo ""
    echo "This was a dry run. To actually submit jobs, run without --dry-run flag."
fi

if [ "$FOUND_START" == false ] && [ -n "$START_FROM_JOB" ]; then
    echo ""
    echo "WARNING: Start job '$START_FROM_JOB' was not found in the job sequence!"
    echo "All jobs were skipped. Please check the job name."
fi
