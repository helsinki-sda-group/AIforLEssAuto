
# AREA 2

### Step 1
This step converts the weakly connected area into its "plain" components
Run the following command in `helsinki updated areas/area2`:
`netconvert -s area2_connected.net.xml -p plain`

Then the result should be moved to area2/plain to keep folder structure intact

### Step 2
This step creates the plain files that only contain the largest strongly connected component from the network
1. Change the local variables inside the script `plain_scc.py` so that they point to `Helsinki updated areas/area2/plain/...` (The addresses are all prepended with `here` which indicates directory of the script, so you need to use `../../` to refer to the root folder `rl-ridepooling`)

2. Run the script from the root folder with the command `python "src/demand generation/plain_scc.py"`
3. The output files would be `area2_gcc_plain.xxx.xml`

### Step 3
This step creates the network file from the plain files obtained in the last step
Run the following command in `helsinki updated areas/area2/plain`:
`netconvert -n area2_gcc_plain.nod.xml -e area2_gcc_plain.edg.xml -x area2_gcc_plain.con.xml -i area2_gcc_plain.tll.xml -t plain.typ.xml -o area2_gcc_plain.net.xml`
The output file would be `area2_gcc_plain.net.xml`

### Step 4
his step generates parking areas for the strongly connected network
Run the following command in `helsinki updated areas/area2/plain`:
`python $SUMO_HOME/tools/generateParkingAreas.py -n area2_gcc_plain.net.xml -o area2_gcc_parkingareas_plain.add.xml`
The output file would be `area2_gcc_parkingareas_plain.add.xml`