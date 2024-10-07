#!/bin/bash
#SBATCH --job-name="0.4_16e_16c_spawn"
#SBATCH --output="output/%A_%a-%x-stdout.log"
#SBATCH --error="output/%A_%a-%x-stderr.log"
#SBATCH --clusters=ukko
#SBATCH --time=4:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --extra-node-info=1-1:16:1
#SBATCH --mem=16G
#SBATCH --partition=short

# exit when any command fails

# load modules
module purge
module load GDAL
module load X11
module load Mesa
module load libGLU
module load Anaconda3
module load cuDNN/8.6.0.163-CUDA-11.8.0

# activate environment
source /wrk-vakka/appl/easybuild/opt/Anaconda3/2023.09-0/etc/profile.d/conda.sh
conda activate rl-ridepooling

# declare env variables for SUMO
export LIBSUMO_AS_TRACI=1
export SUMO_HOME=/home/beimukvo/.conda/envs/rl-ridepooling/bin
export LD_LIBRARY_PATH=/home/beimukvo/local/lib:$LD_LIBRARY_PATH

# declare env variables for OMP
export OMP_DISPLAY_ENV=verbose

cd ~/prj/AIforLEssAuto/WP4/rl-ridepooling
pwd
python -c 'import torch;print(torch.cuda.device_count())'

taskset -cp $$

srun python src/tests/gym_test-rs_multiproc.py --config configs/policy_training/helsinki_updated_areas/area1_sampled_0.4.yaml --num-envs 16 --postfix ${SLURM_JOB_ID}_${SLURM_JOB_NAME}
