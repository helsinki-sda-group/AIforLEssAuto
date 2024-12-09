#!/bin/bash
#SBATCH --array=0-5
#SBATCH --job-name="job_array_area2_128"
#SBATCH --output="output/%A_%a_%x/main.log"
#SBATCH --account=project_462000655
#SBATCH --time=1:30:00
#SBATCH --nodes=1
#SBATCH --mem=0
#SBATCH --partition=standard
#SBATCH --exclusive

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

#export OMP_DYNAMIC=TRUE

#cpu_mask="1"
#cpu_mask="${cpu_mask},c"
#cpu_mask="${cpu_mask},f0"
#cpu_mask="${cpu_mask},ff00"
#cpu_mask="${cpu_mask},FFFF0000"
#cpu_mask="${cpu_mask},FFFFFFFF00000000"
#cpu_mask="${cpu_mask},FFFFFFFFFFFFFFFF0000000000000000"
cpu_mask="FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"
cpu_bind="--cpu-bind=verbose,mask_cpu:${cpu_mask}"

#export NUM_ENVS_STR="1:2:4:8:16:32:64"
export SRUN_CPUS_PER_TASK=128
export OMP_NUM_THREADS=${SRUN_CPUS_PER_TASK}

export AREAS_STR="area2"
export PERCENTAGE_SAMPLED_STR="0.2"
export TRAIN_FREQS_STR="1"
export DELTAS_STR="1:60:300:600:900:1800"

# Read arrays
IFS=":" read -r -a AREAS <<< "$AREAS_STR"
IFS=":" read -r -a PERCENTAGES <<< "$PERCENTAGE_SAMPLED_STR"
IFS=":" read -r -a TRAIN_FREQS <<< "$TRAIN_FREQS_STR"
IFS=":" read -r -a DELTAS <<< "$DELTAS_STR"

# Generate all combinations
declare -a COMBINATIONS
index=0
for area in "${AREAS[@]}"; do
    for percent in "${PERCENTAGES[@]}"; do
        for train_freq in "${TRAIN_FREQS[@]}"; do
            for delta in "${DELTAS[@]}"; do
                COMBINATIONS[$index]="$area:$percent:$train_freq:$delta"
                ((index++))
            done
        done
    done
done

# Get the combination for this task
combo=${COMBINATIONS[$SLURM_ARRAY_TASK_ID]}
IFS=":" read -r AREA PERCENTAGE_SAMPLED TRAIN_FREQ DELTA <<< "$combo"

# Export variables
export AREA
export PERCENTAGE_SAMPLED
export TRAIN_FREQ
export DELTA

echo "Selected AREA: $AREA"
echo "Selected PERCENTAGE_SAMPLED: $PERCENTAGE_SAMPLED"
echo "Selected TRAIN_FREQ: $TRAIN_FREQ"
echo "Selected DELTA: $DELTA"

output_file_dir="output/${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}_${SLURM_JOB_NAME}_${AREA}_sampled${PERCENTAGE_SAMPLED}_trainfreq${TRAIN_FREQ}_delta${DELTA}"

srun --ntasks=1 ${cpu_bind} bash -c '
    cd ~/prj/AIforLEssAuto/WP4/rl-ridepooling
    pwd
    IFS=":" read -r -a NUM_ENVS <<< "$NUM_ENVS_STR"
    NUM=128
    echo -n "task $SLURM_PROCID num_envs: $NUM "
    taskset -cp $$
    hybrid_check -n -r
    singularity exec --bind /usr/lib64 $SIF python src/tests/gym_test-rs.py --config configs/policy_training/helsinki_updated_areas/${AREA}_sampled_${PERCENTAGE_SAMPLED}.yaml --total-iters $NUM --num-envs $NUM --train-freq $TRAIN_FREQ --delta $DELTA --prefix ${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}_${SLURM_PROCID}_e${NUM}_${AREA}_${PERCENTAGE_SAMPLED}_tf${TRAIN_FREQ}_dlt${DELTA}_${SLURM_JOB_NAME}

'

wait
