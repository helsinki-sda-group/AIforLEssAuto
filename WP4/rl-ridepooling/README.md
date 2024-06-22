# RL for ride-pooling (SUMO, Gym)

This repository contains the implementation of SUMO Gym environment for ride-pooling and tests for it. The implementation is based on https://github.com/LucasAlegre/sumo-rl.

# Usage
- To train and test the model, launch `tests/gym_test-rs.py -c configs/timesteps_3000/default.yaml` with the conda environment from `conda_env.yaml`. You can select any other config file available or create your own. More about different configs in the later section.
- Output will be shown in `nets/ridepooling/output` in the folder with the same timestamp when the script was launched and the same config name that was used to launch the script.

## Configs
Three folders for different config files are present:
* `timesteps_3000` contains config files that use 3000 seconds of SUMO simulation time for a small Helsinki area. This is the default option, and the one that was used to obtain the results above.
* `timesteps_3600` contains config files that use 3600 seconds (1 hour) of SUMO simulation time for the same Helisnki area. This is an alternative simulation.
* `old_net` contains config files for a small test network.

Note that by default, the `sumo_seed` variable is the same for every configs.

## Demand data

* The script was tested using a small Helsinki area (around keskuspuisto). The demand traffic was modeled based on traffic counting stations using another one of our repositories you can find [here](https://github.com/helsinki-sda-group/AIforLEssAuto/tree/ridepool-linux/WP4/sumo-hki-cm). The network and the demand data are located in `nets/helsinki_area3`. The demand data includes road network <i>\*.net.xml</i>, route file <i>\*.rou.xml</i>, trip file <i>\*.trips.xml</i>, file with parking areas. The name `area3` is because the network uses the same area as one of the network from [this repo](https://github.com/helsinki-sda-group/AIforLEssAuto/tree/ridepool-linux/WP4/sumo-hki-cm).
* There are also small networks developed initially for testing that you can find in `nets/older_networks`.

# Implementation

## Environment
- Implementation of environment is contaned in <i>sumo_rl_rs</i> folder (<i>env.py</i> - environment class, <i>observations.py</i> - observations class, <i>ridepool_controller</i> - SUMO ridepooling logic e.g. dispatching algorithm, observations and reward calculation).
- The default occupancy of the taxis is read during environment initialization from the route file `vType` section.

### Interaction with SUMO
- `libsumo` library is used for access to the running SUMO simulation (Python TraCI has worser performance).

# Results

The results of the experiments can be seen on the image below. The policies B1-B7 represent the baseline policies. 

![Annotation 2024-06-07 105316](https://github.com/helsinki-sda-group/AIforLEssAuto/assets/53058806/a8d2dd69-7e94-478b-b9d3-766880fab696)

