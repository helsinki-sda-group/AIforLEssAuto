#!/bin/bash
#SBATCH --job-name="sumo_test_20envs_10cpus_omp_20thr.log"
#SBATCH --output="output/sumo_test_20envs_10cpus_omp_20thr.log"
#SBATCH --account=project_462000655
#SBATCH --time=30:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=10
#SBATCH --mem=15G
#SBATCH --partition=small

export SRUN_CPUS_PER_TASK=10
export OMP_NUM_THREADS=20
export OMP_PROC_BIND=false
export OMP_PLACES=threads

export LIBSUMO_AS_TRACI=1
export SUMO_HOME=/user-software/venv/pytorch/bin

cd ~/prj/AIforLEssAuto/WP4/rl-ridepooling
pwd
module --force purge
module load LUMI/23.09 partition/C PyTorch/2.2.0-rocm-5.6.1-python-3.10-singularity-exampleVenv-20240315

srun singularity exec --bind /usr/lib64 $SIF python src/tests/gym_test-rs.py --config configs/policy_training/helsinki_updated_areas/area1_sampled_0.2.yaml --num-envs 20 --postfix 20envs_10cpus_omp_20thr
