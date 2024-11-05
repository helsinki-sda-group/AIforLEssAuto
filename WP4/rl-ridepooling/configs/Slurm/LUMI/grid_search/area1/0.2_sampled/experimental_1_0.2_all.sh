#!/bin/bash
#SBATCH --job-name="1_0.2_all"
#SBATCH --output="output/%j_%x.log"
#SBATCH --account=project_462000655
#SBATCH --time=5
#SBATCH --nodes=1
#SBATCH --mem=16G
#SBATCH --partition=debug
#SBATCH --exclusive

# load modules
module --force purge
module load LUMI/24.03
module load lumi-CPEtools # TODO: REMOVE THIS WHEN ACTUALLY RUNNING SCRIPTS PLEASE
module load partition/C
module load PyTorch/2.2.2-rocm-5.6.1-python-3.10-vllm-0.4.0.post1-singularity-20240617

# list all modules
module list

# declare env variables for SUMO
export LIBSUMO_AS_TRACI=1
export SUMO_HOME=/user-software/venv/pytorch/bin
#export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
#export OMP_PROC_BIND=true
#export OMP_PLACES=cores

# declare env variables for Slurm
#export OMP_DISPLAY_ENV=verbose
#export MPICH_CPUMASK_DISPLAY=1
#export SLURM_CPU_BIND="verbose,ldoms"
#export SLURM_CPU_BIND="mask_cpu:ff,f00"
#,f00,ffff0000,ffffffff00000000,ffffffffffffffff0000000000000000"
#--cpu-bind=verbose,mask_cpu:f00

#cd ~/prj/AIforLEssAuto/WP4/rl-ridepooling
pwd
mkdir "output/${SLURM_JOB_ID}_${SLURM_JOB_NAME}"
#cpu_mask="1,c,f0,ff00,ffff0000,ffffffff00000000,ffffffffffffffff0000000000000000"
cpu_mask="100000000000000000000000000000001"
cpu_mask="${cpu_mask},c0000000000000000000000000000000c"
cpu_mask="${cpu_mask},f0000000000000000000000000000000f0"
cpu_mask="${cpu_mask},ff000000000000000000000000000000ff00"
cpu_mask="${cpu_mask},FFFF0000000000000000000000000000FFFF0000"
cpu_mask="${cpu_mask},FFFFFFFF000000000000000000000000FFFFFFFF00000000"
cpu_mask="${cpu_mask},FFFFFFFFFFFFFFFF0000000000000000FFFFFFFFFFFFFFFF0000000000000000"
cpu_bind="--cpu-bind=verbose,mask_cpu:${cpu_mask}"

export NUM_ENVS_STR="1:2:4:8:16:32:64"

#taskset -cp $$
#--exclusive --output=file1.out
#--exclusive --output=file2.out
srun --ntasks=7 --output="output/%j_%x/%j-%x-%t.log" --hint=multithread ${cpu_bind} bash -c '
    cd ~/prj/AIforLEssAuto/WP4/rl-ridepooling
    pwd
    IFS=":" read -r -a NUM_ENVS <<< "$NUM_ENVS_STR"
    NUM=${NUM_ENVS[$SLURM_PROCID]}
    echo -n "task $SLURM_PROCID num_envs: $NUM "
    taskset -cp $$
    hybrid_check -n -r
    
'
#echo -n "task "${SLURM_PROCID}" num_envs: ${NUM_ENVS_LIST[$SLURM_PROCID]}"; taskset -cp $$; sleep 5'
#srun --ntasks=2 --cpu-bind="verbose,mask_cpu:ff,f00" singularity exec --bind /usr/lib64 $SIF python src/tests/gym_test-rs.py --config configs/policy_training/helsinki_updated_areas/area1_sampled_0.2.yaml --total-iters 128 --num-envs 128 --postfix ${SLURM_JOB_ID}_${SLURM_JOB_NAME}


#srun --exclusive --exact --mem=4G -c8 --cpu-bind=verbose,mask_cpu:ff echo -n "task 1 "; taskset -cp $$; sleep 5 &
#singularity exec --bind /usr/lib64 $SIF python src/tests/gym_test-rs.py --config configs/policy_training/helsinki_updated_areas/area1_sampled_0.2.yaml --total-iters 8 --num-envs 8 --postfix ${SLURM_JOB_ID}_${SLURM_JOB_NAME} &

#srun --exclusive --exact --mem=8G -c4 --cpu-bind=verbose,mask_cpu:f00 echo -n "task 2 "; taskset -cp $$; sleep 5 &
#singularity exec --bind /usr/lib64 $SIF python src/tests/gym_test-rs.py --config configs/policy_training/helsinki_updated_areas/area1_sampled_0.2.yaml --total-iters 4 --num-envs 4 --postfix ${SLURM_JOB_ID}_${SLURM_JOB_NAME} &

#srun --exclusive --hint=compute_bound singularity exec --bind /usr/lib64 $SIF python src/tests/gym_test-rs.py --config configs/policy_training/helsinki_updated_areas/area1_sampled_0.2.yaml --total-iters 16 --num-envs 16 --postfix ${SLURM_JOB_ID}_${SLURM_JOB_NAME} &

#srun --exclusive --hint=compute_bound singularity exec --bind /usr/lib64 $SIF python src/tests/gym_test-rs.py --config configs/policy_training/helsinki_updated_areas/area1_sampled_0.2.yaml --total-iters 32 --num-envs 32 --postfix ${SLURM_JOB_ID}_${SLURM_JOB_NAME} &

#srun --exclusive --hint=compute_bound singularity exec --bind /usr/lib64 $SIF python src/tests/gym_test-rs.py --config configs/policy_training/helsinki_updated_areas/area1_sampled_0.2.yaml --total-iters 64 --num-envs 64 --postfix ${SLURM_JOB_ID}_${SLURM_JOB_NAME} &

wait
