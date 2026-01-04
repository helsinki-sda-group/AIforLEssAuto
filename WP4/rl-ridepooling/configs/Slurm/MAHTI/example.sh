# install venv
module load pytorch

python3 -m venv --system-site-packages ridepool-venv

# use venv
module load pytorch
source /projappl/project_2016787/...


export SUMO_HOME="/projappl/project_2016787/AIforLEssAuto/WP4/rl-ridepooling/ridepool-venv/bin"

# don't use srun when on interactive partition, run singularity directly
srun singularity exec \
    -B "/usr/lib64/libnsl.so.1" \
    -B /run/nvme \
    -B /users/volodymy \
    "$SING_IMAGE" \
    bash -c "source ridepool-venv/bin/activate && \
    python src/tests/gym_test-rs.py \
    --config configs/policy_training/old_net/default.yaml \
    --postfix ${SLURM_JOB_ID}_${SLURM_JOB_NAME}"

srun singularity exec \
    -B "/usr/lib64/libnsl.so.1" \
    -B /run/nvme \
    -B /users/volodymy \
    "$SING_IMAGE" \
    bash -c "source ridepool-venv/bin/activate && \
    python src/tests/plot_results.py \
    2025-12-12T12-53-20_5612096_16env* 1"

# install new package to venv
module load pytorch
singularity exec -B "/usr/lib64/libnsl.so.1" -B /run/nvme -B /users/volodymy "$SING_IMAGE" bash
source ridepool-venv/bin/activate
python --version
python -m pip install <package>