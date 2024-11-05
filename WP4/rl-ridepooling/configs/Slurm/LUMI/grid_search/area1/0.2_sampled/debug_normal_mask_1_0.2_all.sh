#!/bin/bash
#SBATCH --job-name="1_0.2_all_twice_envs"
#SBATCH --output="output/%j_%x.log"
#SBATCH --account=project_462000655
#SBATCH --time=5
#SBATCH --nodes=1
#SBATCH --mem=8G
#SBATCH --partition=debug
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

#export OMP_PLACES=cores
#export OMP_PROC_BIND=close

mkdir "output/${SLURM_JOB_ID}_${SLURM_JOB_NAME}"
cpu_mask="100000000000000000000000000000001"
cpu_mask="${cpu_mask},c0000000000000000000000000000000c"
cpu_mask="${cpu_mask},f0000000000000000000000000000000f0"
cpu_mask="${cpu_mask},ff000000000000000000000000000000ff00"
cpu_mask="${cpu_mask},FFFF0000000000000000000000000000FFFF0000"
cpu_mask="${cpu_mask},FFFFFFFF000000000000000000000000FFFFFFFF00000000"
cpu_mask="${cpu_mask},FFFFFFFFFFFFFFFF0000000000000000FFFFFFFFFFFFFFFF0000000000000000"
cpu_bind="--cpu-bind=verbose,mask_cpu:${cpu_mask}"

export NUM_ENVS_STR="2:4:8:16:32:64:128"

srun --ntasks=7 --output="output/%j_%x/%j-%x-%t.log" ${cpu_bind} bash -c '
    cd ~/prj/AIforLEssAuto/WP4/rl-ridepooling
    pwd
    IFS=":" read -r -a NUM_ENVS <<< "$NUM_ENVS_STR"
    NUM=${NUM_ENVS[$SLURM_PROCID]}
    echo -n "task $SLURM_PROCID num_envs: $NUM "
    taskset -cp $$
    hybrid_check -n -r
    #singularity exec --bind /usr/lib64 $SIF python src/tests/gym_test-rs.py --config configs/policy_training/helsinki_updated_areas/area1_sampled_0.2.yaml --total-iters $NUM --num-envs $NUM --prefix ${SLURM_JOB_ID}_${SLURM_PROCID}_${NUM}e_${SLURM_JOB_NAME}

'

wait
