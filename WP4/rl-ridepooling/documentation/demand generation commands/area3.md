# AREA 3

### Step 1
This step converts the weakly connected area into its "plain" components
Run the following command in `helsinki updated areas/area3`:
`netconvert -s area3_connected.net.xml -p plain`

Then the result should be moved to area3/plain to keep folder structure intact

### Step 2
This step creates the plain files that only contain the largest strongly connected component from the network
1. Change the local variables inside the script `plain_scc.py` so that they point to `Helsinki updated areas/area3/plain/...` (The addresses are all prepended with `here` which indicates directory of the script, so you need to use `../../` to refer to the root folder `rl-ridepooling`)

2. Run the script from the root folder with the command `python "src/demand generation/plain_scc.py"`
3. The output files would be `area3_gcc_plain.xxx.xml`

### Step 3
This step creates the network file from the plain files obtained in the last step
Run the following command in `helsinki updated areas/area3/plain`:
`netconvert -n area3_gcc_plain.nod.xml -e area3_gcc_plain.edg.xml -x area3_gcc_plain.con.xml -i area3_gcc_plain.tll.xml -t plain.typ.xml -o area3_gcc_plain.net.xml`
The output file would be `area3_gcc_plain.net.xml`

### Step 4
This step generates parking areas for the strongly connected network
Run the following command in `helsinki updated areas/area3/plain`:
`python $SUMO_HOME/tools/generateParkingAreas.py -n area3_gcc_plain.net.xml -o area3_gcc_parkingareas_plain.add.xml`
The output file would be `area3_gcc_parkingareas_plain.add.xml`

### Step 5
This step extracts the parts of the existing routes that are valid within the strongly connected network
1. Here's the command to run genGCCtrips.py (sampling ratio is set to 1 by default). Run this command inside the root folder `rl-ridepooling`. Keep in mind that in this script everything is related to file location so `../../` refers to root folder `rl-ridepooling`

```
python "src/demand generation/genGCCtrips.py" \
    --connectednet "../../nets/ridepooling/Helsinki updated areas/area3/plain/area3_gcc_plain.net.xml" \
    --disconnectedtrips "../../../sumo-hki-cm/demo/smaller_areas/routes/area3/disconnected/area3_disconnected_trips.rou.xml" \
    --disconnectedroutes "../../../sumo-hki-cm/demo/smaller_areas/routes/area3/disconnected/area3_disconnected_routes.rou.xml" \
    --samplingratio 1 \
    --output "../../nets/ridepooling/Helsinki updated areas/area3/area3_connected_sampled_fixed_1.trips.xml"
```
The output file would be `area3_connected_sampled_fixed_1.trips.xml`