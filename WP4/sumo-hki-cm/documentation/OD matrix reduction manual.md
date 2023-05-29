# OD matrix reduction using SUMO
This manual will describe how to reduce an origin-destination (OD) matrix to a subset of zones by using the traffic simulator SUMO (Simulation of Urban MObility).

# Problem explanation
When working with OD matrices that describe the quantity of traffic between a set of zones the user may want to work with a subset of these zones. Let's say that the OD matrix describes a larger area consisting multiple cities, but we are only interested in working with a reduced area consisting of one of these cities. If we want to run traffic simulations and generate traffic from this OD matrix we still have to work with the whole area, since some of the traffic may be lost otherwise. As an example, let's describe the 4 types of vehicles we will be dealing with:

- in-in: vehicles with origin and destination within the reduced area
- in-out: vehicles with origin inside the reduced area and destination outside the reduced area
- out-in: vehicles with origin outside the reduced area and destination inside the reduced area
- out-out: vehicles with origin outside the reduced area and destination outside the reduced area

When working with a reduced road network, the in-in vehicles could be generated from the original OD matrix, since their origins and destinations are still present in the reduced network, but when generating the 3 other types we run into problems. Since the origins and destinations that are outside the reduced network can't be used because they don't exist, we need to remap these origins and destinations to zones that are still present in the reduced network. We can do this by simulating the traffic generated from the original OD matrix, recording the vehicle trajectories and adding traffic to the zones in the original matrix that are included in the reduced area. In short, the input is an OD matrix for a larger area and the output is a matrix, which contains a subset of the zones from the original OD matrix with added traffic to include the external traffic (in-out, out-in and out-out vehicles).

# The process in short
The OD matrix reduction can be described in the following steps:

- Run a simulation of the whole area where the traffic is generated from the original OD matrix and record the trajectories (fcd output).
- Run the tool odReductionV2.py. This tool creates a reduced OD matrix with the same dimensions as the original matrix, but only containing the traffic for the reduced area.

# Changing the reduced area
There are 3 main things that would need to be changed to use the OD matrix reduction tool for any arbitrary area:

- The TAZ file containing the zones included in the reduced area. This file is used to create a unified set of all edges to determine when a vehicles is in the reduced area without ever reading the network itself. The TAZs area also used to create maps from edge to TAZ. These maps are used when traffic is added to the reduced OD matrix. The pairing from edge to a cell in the matrix is edge - taz - index. The file path is stored in the variable `REDUCED_AREA_TAZS_FILE`. TAZ files can be generated using SUMO's tool edgesInDistricts.py.
- The file containing information about the zones and which is used to create data structures needed in the edge - taz - index mapping. The path to the file is stored in the variable `DBF_FILE`. If a subset of zones from the Helmet model is used nothing has to be changed about this file.
- The dimensions of the new matrix. The variable `reducedOdMatrix` in the `odMatrixReducer` class is created with the dimensions 2035 x 2035, since these were the dimensions in the original OD matrix used in HSL's Helmet model, which was used as base for creating a traffic model of Helsinki in AIforLEssAuto.

