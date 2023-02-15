# WORK IN PROGRESS

# User guide
This guide will describe all steps in the pipeline that turns an origin-destination (OD) matrix into a simulation in the traffic simulator [SUMO](https://www.eclipse.org/sumo/) (Simulation of Urban MObility) and how to reduce that simulation to a smaller area using the results from the large simulation.

The pipeline can be run with the file `completePipeline.sh` in the root directory.

## Step 1: visumRouteGeneration.py
To run this file the user needs to create a dBase database file (.dbf) in the `data` directory. This file is used for pairing zone indices in the OD matrix with their actual number.

<!-- ## Changes that could improve the project
Rename the output file in `visumRouteGeneration.py` to "SUMO_OD_file.od". -->
