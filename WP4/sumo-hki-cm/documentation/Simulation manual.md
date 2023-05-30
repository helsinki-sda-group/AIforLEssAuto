# The directory structure
This directory is split into 4 main categories:
- tools
- SUMO files
- data
- calibration

The tools directory contains Python files used for different processes in creating a traffic simulation. sumo_files contains mostly XML files that are used as input for SUMO. These can be data from traffic simulations, configuration files or files containing traffic networks and additionals for use during simulations. The data directory contains the original OD matrix from the Helmet model, a table with the zones and some other files. The calibration directory contains a data directory with traffic counting station comparisons and a tools directory containing tools used for analysis and calibration. The three most important calibration tools are digitrafficPeakHourTraffic.py, hkiPeakHourTraffic.py and statistics.py. The first two ones are used for getting the peak hour traffic for the traffic counting stations from the two data sources: Digitraffic and the city of Helsinki.

# The simulation process

## The large simulation

### Short instructions
Run the section "Whole area simulation" in completePipeline.sh.

### Needed directories
|Directory|
|----|
| data |
| sumo_files |
| sumo_files/simulation_output |
| sumo_files/simulation_output/detector_outputs |
| tools |

### Needed files
|File|Explanation|
|----|-----|
| tools/visumRouteGeneration.py | a tool for creating an OD file in SUMO's format |
| data/sijoittelualueet2019.dbf | table over Helmet zones |
| data/demand_aht.omx | Helmet OD matrix (morning rush hour)
| sumo_files/od2trips.config.xml | od2trips config file
| sumo_files/whole_area_districts.taz.xml | a file containing the SUMO TAZs corresponding to the Helmet zones
| sumo_files/duarcfg_file.trips2routes.duarcfg | a duarouter config file (for checking that paths exist between origins and destinations)
| sumo_files/whole_area.net.xml | the network for the whole Helmet area
| tools/randomDepartureTimes.py | for giving vehicles random departure times within the chosen time window (in this case 0 to 3600)
| tools/departureTimeSorter.py | for sorting the vehicles according to their departure time, they need to be sorted when the simulation is started
| tools/indexZeroToN.py | for giving indexes from 0 to n to make things tidier after sorting the vehicles by departure time
| sumo_files/runner.py | a Python file which runs the large simulation through TraCI and stops it after 1 hour simulation time has passed
| sumo_files/1_hour_whole_area.sumocfg | the SUMO simulation configuration file |
| sumo_files/1_hour.add.xml | a file containing additional simulation elements for the large simulation, in this case mainly vehicle detectors (induction loops) |
| sumo_files/whole_area_zones.poly.xml | a file containing the Helmet zones in SUMO's polygon format (not actually used during the simulation, but used for creating TAZ files) |

### Commands
```
python3 tools/visumRouteGeneration.py
od2trips -c sumo_files/od2trips.config.xml
# If multithreading is enabled
duarouter -c sumo_files/duarcfg_file.trips2routes.duarcfg --routing-threads 4 --write-trips true --ignore-errors true
# Otherwise
# duarouter -c sumo_files/duarcfg_file.trips2routes.duarcfg --write-trips true --ignore-errors true
python3 tools/randomDepartureTimes.py sumo_files/verified_trips.rou.xml sumo_files/verified_trips.rou.xml 0 3600
python3 tools/departureTimeSorter.py
python3 tools/indexZeroToN.py
python3 sumo_files/runner.py
```

### Explanation
The traffic simulation process is run in 2 parts: the large area (whole_area) and the reduced area (reduced_cut_area). The "cut" in the name reduced_cut_area comes from that the network is a subnetwork from the large network that was cut using the SUMO tool netconvert. Originally this was only done by downloading a smaller network using OSMWebWizard, so when the change was made, "cut" was added to the file name to emphasize that it was a subset of the large network. The pipleine of this process can be found in the executable shell script file completePipeline.sh. First the file visumRouteGeneration.py creates an origin-destination (OD) file in SUMO's O-format (VISUM/VISSIM). The input is the Helmet OD matrix file (demand_aht.omx) and the output is a file called OD_file.od. This file is given to the SUMO tool od2trips and picks a random edge from the origin and destination zone (or TAZ, as they are called in SUMO). The TAZs and their edges are stored in the file whole_area_zones.taz.xml. Then duarouter is used to check if there actually are paths between the OD pairs. Then the trips get random departure times, get sorted by departure time, get indexes from 0 to n and then the large simulation is run. On a modern Lenovo ThinkPad laptop (2022) this simulation takes around 6.5 hours. The configuration file (1_hour_whole_area.sumocfg) is set to output vehicle trajectories (fcd output) to sumo_files/simulation_output/fcdresults.xml. This file will be around 33 GB in size. It is used for reducing the simulation to a smaller area, in this case Helsinki.

### Creating a TAZ file
In this step the file whole_area_zones.taz.xml was used to distinguish between different zones. This file is obtained by running the SUMO tool edgesInDistricts.py with a polygon (.poly.xml) file. To convert the polygon files (.shp) the polygon file was first converted to OpenStreetMap (.osm) format using [Java OpenStreetMap Editor](https://josm.openstreetmap.de/) and then converted from OpenStreetMap format to SUMO's polygon format using the tool `osmToPolyConverterV3.py` (can be found in the `tools` directory). If one wishes to create a TAZ file with a subset of zones, then of the ways to do it is to copy the file containing all the zones and then remove all zones that should not be included.

## The reduction

### Short instructions
Run the section "Whole area simulation" in completePipeline.sh.

### Modifying the reduced area
If the user wants to change the reduced area, the following things need to be done:
- Change the variables `REDUCED_AREA_MIN_LAT`, `REDUCED_AREA_MAX_LAT`,  `REDUCED_AREA_MIN_LON` and `REDUCED_AREA_MAX_LON`, which make up the square that is the reduced area so that they make up a square that covers the wanted area.
- Define the set of zones in the reduced area in a file called helsinkiTazs.py.
- To make the reduced simulation more computationally efficient the user should also cut a new subnetwork from the original network that corresponds to the reduced area. The borders for this network should be increased a bit from what the parameters `REDUCED_AREA_MIN_LAT`, `REDUCED_AREA_MAX_LAT`,  `REDUCED_AREA_MIN_LON` and `REDUCED_AREA_MAX_LON` are so that edges are actually found for the the vehicles that had their origins and destinations at the borders saved as coordinates. If the network borders are too narrow this could cause the streets at the borders not to be included, which could cause vehicles to be lost in the reduced simulation. The network cutting can be done with SUMO's tool Netconvert.
- For the traffic generation part in the next section where coordinateODToTripsV2.py is used, a TAZ file with only the Helmet zones that are included in the wanted reduced area are included. More on the needed parameter changes in the file in the next section. 

### Needed directories
|Directory|
|----|
| data/fcd_analysis |

### Needed files
|File|Explanation|
|----|-----|
| tools/fcdDataExtractionV8.py | a tool that analyzes where vehicles enter and exit a reduced area |
| tools/helsinkiTazs.py | a file containing the reduced area TAZs |
| tools/coordinateODToTripsV2.py | a tool that makes a SUMO trip file from the table produced by fcdDataExtractionV8.py (and the original OD matrix for the zones within the reduced area) |

### Commands
```
# Version 8 is more efficient
# python3 tools/fcdDataExtractionV5.py
python3 tools/fcdDataExtractionV8.py
```

### Explanation
Once the large simulation is done the tool fcdDataExtractionV5.py or fcdDataExtractionV8.py (more on their differences further down) is used to extract information from the large simulation to allow recreating the same traffic in a smaller area. The reduction is done by going through the vehcile trajectory file and checking where different vehicles enter and exit the reduced area. The reason the large simulation is run in the first place is because of our goal: to create traffic for a reduced area from an OD matrix for a larger area. What we could do is to only instantiate the vehicles that start and go to the reduced area, but this would not be a very realistic scenario since most vehicles that should be in the simulation will be lost. What needs to be done instead is to run a large simulation and check where different vehicles enter and exit the reduced area. We can divide the vehicles into four categories: in-in, in-out, out-in and out-out vehicles. The word ”in” refers to an origin or destination in the reduced area and ”out” refers to an origin or destination outside the reduced area. This means that the categories can be described as origin and destination in Helsinki, origin in Helsinki and destination outside Helsinki, origin outside Helsinki and origin in Helsinki and origin and destination outside Helsinki. Since we can already use the OD matrix for the in-in vehicles we can simply ignore them during the trajectory analysis. For the rest of the vehicles the procedure is the following (fcdDataExtractionV8): 

- in-out vehicles: If the vehicle has exited the reduced area, then add a departure with the origin zone as origin and the current coordinates as destination
- out-in vehicles: If the vehicle has entered the reduced area, then add a departure with the current coordinates as origin and the destination zone as destination
- out-out vehicles: Save the coordinates when the vehicle enters the reduced area and when the vehicle exits the reduced area, add a departure with those coordinates as origin and the coordinates when the vehicle exits as destination

For vehicles that start within the reduced area, the departure time is picked directly form the original SUMO traffic file (.rou.xml) and for the rest the departure time will be the time step at which they entered the reduced area.

NOTE: In version 8 it is assumed that the reduced area is a square. Originally in version 5 (the first working version) the area was assumed to be a random shape. SUMO's polygon format and its tool edgesInDistrict.py was used to define a set of edges that made up the reduced area. To avoid having the program check if every vehicle was in the area by checking if its edge was in this set up edges, versions 6, 7 and 8 were developed. Version 8 was the goal of version 6 and 7, but the changes were implemented in smaller steps.

## Reduced simulation

### Short instructions
Run the section "Reduced area simulation" in completePipeline.sh.

### Needed directories
|Directory|
|----|
| data |
| sumo_files |
| sumo_files/simulation_output |
| sumo_files/simulation_output/reduced_geo_detector_outputs |
| tools |

### Needed files
|File|Explanation|
|----|-----|
| sumo_files/reduced_cut_area.net.xml | the network for the reduced area |
| sumo_files/reduced_cut_districts.taz.xml | a file containing the SUMO TAZs corresponding to the Helmet zones within the reduced area |
| tools/departureTimeSorter.py | for sorting the vehicles according to their departure time, they need to be sorted when the simulation is started
| tools/indexZeroToN.py | for giving indexes from 0 to n to make things tidier after sorting the vehicles by departure time |
| sumo_files/geoRunnerV2.py | a Python file which runs the reduced simulation through TraCI and stops it after 1 hour simulation time has passed |
| sumo_files/1_hour_reduced_area_geo_V2.sumocfg | the SUMO simulation configuration file for the reduced simulation |
| sumo_files/1_hour_reduced.add.xml | a file containing additional simulation elements for the reduced simulation, in this case mainly vehicle detectors (induction loops) |

### Modifying the reduced area continued
**NOTE:** If the wanted reduced area is another than Helsinki and the needed changes in the reduction process in the previous section have already been made, then proceed with the following changes in coordinateODToTripsV2.py before running it:

- The parameter `NET_FILE` should be changed to whatever network is used for the reduced area. In the program it is used for finding the nearest edges to the coordinates in the Excel file.
- Change `REDUCED_AREA_TAZ_FILE` to a new TAZ file containing only TAZs corresponding to the wanted Helmet zones.
- Change the parameter `REDUCED_AREA_INDICES` to a Python list containing the **indices** of the wanted zones found in the file "sijoittelualueet2019.dbf" (the column "FID_1"). The indices should be given as integers (normal numbers without anything special to them). Per default the parameter is set to be all the indices in the Helsinki interval.

### Commands
```
python3 tools/coordinateODToTripsV2.py
# If multithreading is enabled
duarouter -c sumo_files/geo_duarcfg_file.trips2routes_V2.duarcfg --routing-threads 4 --write-trips true --ignore-errors true
# Otherwise
# duarouter -c sumo_files/geo_duarcfg_file.trips2routes_V2.duarcfg --write-trips true --ignore-errors true
python3 tools/departureTimeSorter.py sumo_files/verified_reduced_geo_trips_V2.rou.xml sumo_files/verified_reduced_geo_trips_V2.rou.xml
python3 tools/indexZeroToN.py sumo_files/verified_reduced_geo_trips_V2.rou.xml
python3 sumo_files/geoRunnerV2.py
python3 calibration/tools/statistics.py 1 sumo_files/simulation_output/reduced_detector_outputs
```

### Explanation
The output of the extraction process is a table file in Excel format (.xlsx) containing departures for external traffic (the traffic which cannot be generated directly from the original OD matrix: in-out, out-in and out-out). This file is then used by the tool coordinateODToTripsV2.py to generate a traffic file in SUMO's .rou.xml format. The in-in trips are first generated the same way as in the large simulation, but then each row in the external traffic table is turned into an XML row. If the origin or destination are coordinates the closest edge in the network to that coordinate is picked and if the origin or destination is a zone, then an random edge from that zone is picked from a TAZ file containing the zones in the reduced network and their edges.

After `coordinateODToTripsV2.py` has been run the process is pretty similar to running the large simulation. Duarouter is used to check that paths actually exist between the origins and destinations in the generated traffic file, the trips are sorted by their departure time, the trips get indices from 0 to n and finally, the simulation is run through TraCI. After the simulation a file containing comparisons between real traffic counting stations and stations in the corresponding places in the simulation. The file is generated with a command that gives it the path `calibration/data/real_world_comparison_sc_1_2021.xlsx`.

# Important notes
- All commands should be run from the root folder (not the root directory of the entire GitHub repository, but the one called sumo-hki-cm). If you are in the right directory you should see the subdirectories `calibration`, `data`, `sumo_files` and `tools`.
- If you get the error message `ModuleNotFoundError: No module named 'sumolib'` when starting Python programs that use sumolib (e.g. for reading SUMO networks), then run the command `export PYTHONPATH="$SUMO_HOME/tools:$PYTHONPATH"` to set the needed environment variable.

# Notes and more detailed descriptions of some of the files

## demand_aht.omx
The file extension .omx stands for Open Matrix. The origin-destination matrices that were used in this project were provided in this format. For more info on the format, visit https://github.com/osPlanning/omx. The file contains 9 matrices. Out of these the 3 that contains cars and vans are used to generate traffic.

## sijoittelualueet2019.dbf
This file contains a table with descriptions of the Helmet zones (not the shapes though). The table has the following columns:

|FID_1|WSP_SIJ|WSP_ENN|KELA|SIJ2016|SIJ_MAARA|SIJ_ID|ENN2016|SIJ2019|
|----|-----|-----|-----|-----|-----|-----|-----|-----|

The most important ones are `FID_1`, which is the index, `KUNTANIMI`, which is the name of the municipality and `SIJ2019`, which is the zone number.

# The differences between fcdDataExtractionV5.py and fcdDataExtractionV8.py
After the first working version of the external traffic extracter (version 5) was completed improvements were made in 3 new versions. The changes are listed below.

## Version 6
- Iterative parsing of the XML file instead of reading the whole file at once to improve memory efficiency. If the file is too big to be read into a computer's memory, then version 5 won't run properly. NOTE: XML parsing removed completely in version 8.

## Version 7
- It is assumed that the reduced area is a square. This is to improve resource efficiency by not having to store out-out vehicles until the end of the program's execution.
- The sets used in the class fcdInformationExtracter have been replaced by NumPy arrays to improve performance.

## Version 8
- The XML parsing was replaced by reading the file line by line (with Python's `open()` and `readline()` methods) and searching for the wanted fields with regular expressions (regex) using (Python's `re` module). One may ask why this was done. Wouldn't the best thing to do be to read the XML file with and XML parser? The answer in this case was strangely no. During a race between the XML parsing module (`xml.etree.ElementTree`) and the regular expression module (`re`) where both were tasked with going through the XML file and printing the time steps on the time step rows without doing anything else the regex module was almost twice as fast in this case. It also seemed to perform better in the context of extracting the external traffic from the XML file.

### Comment from the author
The point of the changes in version 8 is not to imply that it is better to use regex reading instead of XML parsers, but that it worked better in this context. The results may be different in other computing environments. If the user wishes to experiment with the different versions, then version 7 is also available to try out. It may be worth checking that that the output is as expected since version 7 was never tested thoroughly because it was only an intermediate step towards version 8.

# Leftovers from side projects
Not all files are used for the main simulation process. In the sumo_files directory there are many files that have been used for side projects. These have been experiments such as comparing SUMO’s cutRoutes tool with the geo based simulation reduction. Another experiment was to create a 2 hour instance of the simulation to see if the traffic counts at the traffic counting stations were any better, since the total number of vehicle detections in the simulation seemed to be smaller than the number of detections in the real world.