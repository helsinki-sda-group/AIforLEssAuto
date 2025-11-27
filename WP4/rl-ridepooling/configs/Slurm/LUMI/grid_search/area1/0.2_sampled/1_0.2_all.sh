#!/bin/bash
#SBATCH --job-name="1_0.2_all"
#SBATCH --output="output/%A_%a-%x-stdout.log"
#SBATCH --error="output/%A_%a-%x-stderr.log"
#SBATCH --account=project_462000655
#SBATCH --time=2:00:00
#SBATCH --nodes=1
#SBATCH --mem=0
#SBATCH --partition=standard

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

# declare env variables for Slurm
#export OMP_DISPLAY_ENV=verbose
export MPICH_CPUMASK_DISPLAY=1
export SLURM_CPU_BIND="verbose,mask_cpu:ff,f00,ffff0000,ffffffff00000000,ffffffffffffffff0000000000000000"

cd ~/prj/AIforLEssAuto/WP4/rl-ridepooling
pwd

taskset -cp $$

srun --exclusive --cpu-freq=Performance bash -c 'echo "SLURM_CPU_FREQ_REQ: $SLURM_CPU_FREQ_REQ"'; singularity exec --bind /usr/lib64 $SIF python src/tests/gym_test-rs.py --config configs/policy_training/helsinki_updated_areas/area1_sampled_0.2.yaml --total-iters 8 --num-envs 8 --postfix ${SLURM_JOB_ID}_${SLURM_JOB_NAME} &


srun --exclusive --cpu-freq=Performance bash -c 'echo "SLURM_CPU_FREQ_REQ: $SLURM_CPU_FREQ_REQ"'; singularity exec --bind /usr/lib64 $SIF python src/tests/gym_test-rs.py --config configs/policy_training/helsinki_updated_areas/area1_sampled_0.2.yaml --total-iters 4 --num-envs 4 --postfix ${SLURM_JOB_ID}_${SLURM_JOB_NAME} &

srun --exclusive --hint=compute_bound singularity exec --bind /usr/lib64 $SIF python src/tests/gym_test-rs.py --config configs/policy_training/helsinki_updated_areas/area1_sampled_0.2.yaml --total-iters 16 --num-envs 16 --postfix ${SLURM_JOB_ID}_${SLURM_JOB_NAME} &

srun --exclusive --hint=compute_bound singularity exec --bind /usr/lib64 $SIF python src/tests/gym_test-rs.py --config configs/policy_training/helsinki_updated_areas/area1_sampled_0.2.yaml --total-iters 32 --num-envs 32 --postfix ${SLURM_JOB_ID}_${SLURM_JOB_NAME} &

srun --exclusive --hint=compute_bound singularity exec --bind /usr/lib64 $SIF python src/tests/gym_test-rs.py --config configs/policy_training/helsinki_updated_areas/area1_sampled_0.2.yaml --total-iters 64 --num-envs 64 --postfix ${SLURM_JOB_ID}_${SLURM_JOB_NAME} &



