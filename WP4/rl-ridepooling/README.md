# RL for ride-pooling (SUMO, Gym)

This repository contains the implementation of SUMO Gym environment for ride-pooling and tests for it. The implementation is based on https://github.com/LucasAlegre/sumo-rl.

# Usage
- To train and test the model, launch `tests\gym_test-rs.py -c configs/default.yaml` with the conda environment from `conda_env.yaml`
- Output will be shown in `nets/ridepooling/output` in the folder with the same timestamp when the script was launched
- Implementation of environment is contaned in <i>sumo_rl_rs</i> folder (<i>env.py</i> - environment class, <i>observations.py</i> - observations class, <i>ridepool_controller</i> - SUMO ridepooling logic e.g. dispatching algorithm, observations and reward calculation).
- `libsumo` library is used for access to the running SUMO simulation (Python TraCI has worser performance).
- Input files for simulation are in <i>nets\ridepooling</i>. Main files are configuration file <i>MySUMO.sumocfg</i> (contains e.g. number of simulation steps), road network <i>\*.net.xml</i>, route file <i>\*.rou.xml</i>, trip file <i>\*.trips.xml</i>, file with parking areas.
- The default occupancy of the taxis is read during environment initialization from the route file <code>vType</code> section.