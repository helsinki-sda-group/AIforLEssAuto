# Demand generation pipeline
> [!NOTE]  
> Running this pipeline is not mandatory, as the premade demand generation routes can be found in `nets/ridepooling/Helsinki updated areas/areaX/demand_gen_routes`. However, the scripts can be used to alter the demand routes by changing the parameters. The configs used to create the routees are located in the `demand_gen_routes/demand_configs_used`. Before running these scripts, make sure you have installed and activated the conda environment specified in `conda_env.yaml` or have installed the neccessary requirements mentioned in `requirements.txt`. The term `areaX` which you will see in this script can refer to either `area1`, `area2` or `area3`. To repeat these commands for any of these three areas, just replace `areaX` with any of those terms.

### Step 1
This step converts the weakly connected area into its "plain" components
Run the following command in `helsinki updated areas/areaX`:
`netconvert -s areaX_connected.net.xml -p plain`

Then the result should be moved to `areaX/plain` to keep folder structure intact

### Step 2
This step creates the plain files that only contain the largest strongly connected component from the network
1. Change the local variables inside the script `plain_scc.py` so that they point to `Helsinki updated areas/areaX/plain/...` (The addresses are all prepended with `here` which indicates directory of the script, so you need to use `../../` to refer to the root folder `rl-ridepooling`)

2. Run the script from the root folder with the command `python "src/demand generation/plain_scc.py"`
3. The output files would be `areaX_gcc_plain.xxx.xml`

### Step 3
This step creates the network file from the plain files obtained in the last step
Run the following command in `helsinki updated areas/areaX/plain`:
`netconvert -n areaX_gcc_plain.nod.xml -e areaX_gcc_plain.edg.xml -x areaX_gcc_plain.con.xml -i areaX_gcc_plain.tll.xml -t plain.typ.xml -o areaX_gcc_plain.net.xml`
The output file would be `areaX_gcc_plain.net.xml`

### Step 4
This step generates parking areas for the strongly connected network
Run the following command in `helsinki updated areas/areaX/plain`:
`python $SUMO_HOME/tools/generateParkingAreas.py -n areaX_gcc_plain.net.xml -o areaX_gcc_parkingareas_plain.add.xml`
The output file would be `areaX_gcc_parkingareas_plain.add.xml`

### Step 5
This step extracts the parts of the existing routes that are valid within the strongly connected network
1. Here's the command to run genGCCtrips.py (sampling ratio is set to 1 by default). Run this command inside the root folder `rl-ridepooling`. Keep in mind that in this script every path that starts with `../../` refers to the root folder `rl-ridepooling`. Adding `../../` is needed because by default the script interprets every path relative to the folder where the script is located. (i.e. `src/demand generation`)

```
python "src/demand generation/genGCCtrips.py" \
    --connectednet "../../nets/ridepooling/Helsinki updated areas/areaX/plain/areaX_gcc_plain.net.xml" \
    --disconnectedtrips "../../../sumo-hki-cm/demo/smaller_areas/routes/areaX/disconnected/areaX_disconnected_trips.rou.xml" \
    --disconnectedroutes "../../../sumo-hki-cm/demo/smaller_areas/routes/areaX/disconnected/areaX_disconnected_routes.rou.xml" \
    --samplingratio 1 \
    --output "../../nets/ridepooling/Helsinki updated areas/areaX/areaX_connected_sampled_fixed_1.trips.xml"
```
The output file would be `areaX_connected_sampled_fixed_1.trips.xml`

### Step 6
Next step will split the sampled trips obtained in the previous step into taxis and passengers using `genPassengers.py` script. The split will be determined based on the ratio provided as an argument. You can read the details about every argument by typing `python "src/demand generation/genPassengers.py" --help`. The config files with predetermined arguments are located in `configs/gen_passengers/areaX/areaX_sampled_X.yaml`. To launch the script with the premade config file, execute `python "src/demand generation/genPassengers.py" -c configs/gen_passengers/areaX/areaX_sampled_X.yaml` from the project root folder (`rl-ridepooling`)
The output will be stored in `src/demand generation/output`. The folder containing the results will start with the datetime when the script was launched, followed by the name of the config file used (if the script was launched without the config file, then it will consist of only the datetime).
The output folder will contain the following:
* copy of the config used to launch the script (if any)
* summary information about the output
* `.rou.xml` file containing the resulting routes (splitted between passengers, taxis, and regular routes)
* `simulation` folder containing everything necessary to run the trips with SUMO. This folder will include the copied network file, sumoview for GUI, and three `.sumocfg.xml` files, out of which you will most likely only need the first one:
    * `sumo_launch_rl_...`: this file can be used to start the policy training if you specify the path to this file in the `sumocfg` of the config. (See `configs/policy_training/helsinki_updated_areas/area1_sampled_0.2.yaml` as an example)
    * `sumo_launch_...`: this file is used internally by `genPassengers.py` if you specify the `run_cli_sim` option. This option lets  You will most likely not need this file.
    * `sumo_launch_gui_...`: this config is also used internally by `genPassengers.py` if you specify the `run_gui_sim` option.
