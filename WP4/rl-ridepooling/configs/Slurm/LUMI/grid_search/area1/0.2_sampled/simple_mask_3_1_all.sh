#!/bin/bash
#SBATCH --job-name="3_1_all_dynamic"
#SBATCH --output="output/%j_%x.log"
#SBATCH --account=project_462000655
#SBATCH --time=12:00:00
#SBATCH --nodes=1
#SBATCH --mem=256G
#SBATCH --partition=small
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

export OMP_DYNAMIC=TRUE

mkdir "output/${SLURM_JOB_ID}_${SLURM_JOB_NAME}"
cpu_mask="1"
cpu_mask="${cpu_mask},c"
cpu_mask="${cpu_mask},f0"
cpu_mask="${cpu_mask},ff00"
cpu_mask="${cpu_mask},FFFF0000"
cpu_mask="${cpu_mask},FFFFFFFF00000000"
cpu_mask="${cpu_mask},FFFFFFFFFFFFFFFF0000000000000000"
#cpu_mask="${cpu_mask},FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000000000000000000000000000"
cpu_bind="--cpu-bind=verbose,mask_cpu:${cpu_mask}"

export NUM_ENVS_STR="1:2:4:8:16:32:64"

srun --ntasks=7 --kill-on-bad-exit=0 --output="output/%j_%x/%j-%x-%t.log" --error="output/%j_%x/%j-%x-%t.err" ${cpu_bind} bash -c '
    cd ~/prj/AIforLEssAuto/WP4/rl-ridepooling
    pwd
    IFS=":" read -r -a NUM_ENVS <<< "$NUM_ENVS_STR"
    NUM=${NUM_ENVS[$SLURM_PROCID]}
    echo -n "task $SLURM_PROCID num_envs: $NUM "
    taskset -cp $$
    hybrid_check -n -r
    singularity exec --bind /usr/lib64 $SIF python src/tests/gym_test-rs.py --config configs/policy_training/helsinki_updated_areas/area3_sampled_1.yaml --total-iters $NUM --num-envs $NUM --prefix ${SLURM_JOB_ID}_${SLURM_JOB_NAME}_${SLURM_PROCID}_${NUM}e

'

wait
