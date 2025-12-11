# install venv
module load pytorch

python3 -m venv --system-site-packages ridepool-venv

# use venv
module load pytorch
source /projappl/project_2016787/...

export SUMO_HOME="/projappl/project_2016787/AIforLEssAuto/WP4/rl-ridepooling/ridepool-venv/bin"