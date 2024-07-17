## AREA 1

### Step 1
(run in `helsinki updated areas/area1`)
`netconvert -s area1_connected.net.xml -p plain`

Then the result should be moved to area1/plain to keep folder structure intact

### Step 2
1. Change the local variables inside the script `plain_scc.py` so that they point to `Helsinki updated areas/area1/plain/...` (The addresses are all prepended with `here` which indicates directory of the script, so you need to use `../../` to refer to the root folder `rl-ridepooling`)

2. Run the script from the root folder with the command `python "src/demand generation/plain_scc.py"`

### Step 3
(run in `helsinki updated areas/area1/plain`)
`netconvert -n area1_gcc_plain.nod.xml -e area1_gcc_plain.edg.xml -x area1_gcc_plain.con.xml -i area1_gcc_plain.tll.xml -t plain.typ.xml -o area1_gcc_plain.net.xml`
The output file would be `area1_gcc_plain.net.xml`

### Step 4
(run in `helsinki updated areas/area1/plain`)
`python $SUMO_HOME/tools/generateParkingAreas.py -n area1_gcc_plain.net.xml -o area1_gcc_parkingareas_plain.add.xml`
The output file would be `area1_gcc_parkingareas_plain.add.xml`

### Step 5
1. Here's the command to run genGCCtrips.py (sampling ratio is set to 1 by default). Run this command inside the root folder `rl-ridepooling`. Keep in mind that in this script everything is related to file location so `../../` refers to root folder `rl-ridepooling`

```
python "src/demand generation/genGCCtrips.py" \
    --connectednet "../../nets/ridepooling/Helsinki updated areas/area1/plain/area1_gcc_plain.net.xml" \
    --disconnectedtrips "../../../sumo-hki-cm/demo/smaller_areas/routes/area1/disconnected/area1_disconnected_trips.rou.xml" \
    --disconnectedroutes "../../../sumo-hki-cm/demo/smaller_areas/routes/area1/disconnected/area1_disconnected_routes.rou.xml" \
    --samplingratio 1 \
    --output "../../nets/ridepooling/Helsinki updated areas/area1/area1_connected_sampled_fixed_1.trips.xml"
```
The output file would be `area1_connected_sampled_fixed_1.trips.xml`


## AREA 2

### Step 1
(run in `helsinki updated areas/area2`)
`netconvert -s area2_connected.net.xml -p plain`

Then the result should be moved to area2/plain to keep folder structure intact