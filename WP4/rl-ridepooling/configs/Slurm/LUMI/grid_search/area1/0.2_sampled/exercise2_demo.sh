#!/bin/bash -l
#SBATCH --partition=debug           # Partition (queue) name
#SBATCH --nodes=1                   # Total number of nodes
#SBATCH --ntasks-per-node=8         # 8 MPI ranks per node
#SBATCH --cpus-per-task=16          # 16 threads per task
#SBATCH --time=5                    # Run time (minutes)
#SBATCH --account=project_462000655      # Project for billing

export SRUN_CPUS_PER_TASK=16
export OMP_NUM_THREADS=${SRUN_CPUS_PER_TASK}
export OMP_PROC_BIND=close
export OMP_PLACES=cores
export MPICH_CPUMASK_DISPLAY=1

module load LUMI/22.12
module load lumi-CPEtools

srun hybrid_check -n -r
