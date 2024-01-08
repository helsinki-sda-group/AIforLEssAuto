# RL for ride-pooling (SUMO, Gym)

This repository contains the implementation of SUMO Gym environment for ride-pooling. The implementation is based on https://github.com/LucasAlegre/sumo-rl.

# Usage
- To train and test the model, launch <i>tests\gym_test-rs.py</i>.
- Basic logging is performed using standard output to <i>stdout.txt</i>.
- Implementation of environment is contaned in <i>sumo_rl_rs</i> folder (<i>env.py</i> - environment class, <i>observations.py</i> - observations class, <i>ridepool_controller</i> - SUMO ridepooling logic e.g. dispatching algorithm, observations and reward calculation).
- <i>libsumo</i> library is used for access to the running SUMO simulation (Python TraCI has worser performance).
- Input files for simulation are at <i>nets\ridepooling</i>. Main files are configuration file <i>MySUMO.sumocfg</i> (contains e.g. number of simulation steps), road network <i>\*.net.xml</i>, route file <i>\*.rou.xml</i>, trip file <i>\*.trips.xml</i>, file with parking areas.
- The default occupancy of the taxis is read during environment initialization from the route file <code>vType</code> section. The number of simulation iterations is read from the configuration file.
