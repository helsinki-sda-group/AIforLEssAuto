## AREA 1

### Step 1
(run in `helsinki updated areas/area1`)
`netconvert -s area1_connected.net.xml -p plain`

Then the result is moved to area1/plain to keep folder structure intact

### Step 2
1. Change the local variables inside the script `plain_scc.py` so that they point to `Helsinki updated areas/area1/plain/...` (The addresses are all prepended with `here` which indicates directory of the script, so you need to use `../../` to refer to the root folder `rl-ridepooling`)

2. Run the script from the root folder with the command `python "src/demand generation/plain_scc.py"`

### Step 3
(run in `helsinki updated areas/area1/plain`)
`netconvert -n area1_gcc_plain.nod.xml -e area1_gcc_plain.edg.xml -x area1_gcc_plain.con.xml -i area1_gcc_plain.tll.xml -t plain.typ.xml -o area1_gcc_plain.net.xml`
The output file would be `area1_gcc_plain.net.xml`