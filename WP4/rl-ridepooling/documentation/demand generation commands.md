## AREA 1

### Step 1
(run in helsinki updated areas/area1)
netconvert -s area1_connected.net.xml -p plain

Then the result is moved to area1/plain to keep folder structure intact

### Step 2
1. Change the local variables inside the script `plain_scc.py` so that they point to `Helsinki updated areas/area1/plain/...` (The addresses are all prepended with `here` which indicates directory of the script, so you need to use `../../` to refer to the root folder `rl-ridepooling`)

2. Run the script