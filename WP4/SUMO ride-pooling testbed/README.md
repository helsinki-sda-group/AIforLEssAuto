# SUMO ride-pooling testbed

![Status](https://img.shields.io/badge/Status-Completed-green)

## General description

This repository contains scripts for calculating the metrics for SUMO ride-pooling algorithms, performing batched experiments for the range of parameters, aggregating and visualizing the results. 

Two scenarios are considered: (i) baseline – all trips are served by private cars, (ii) ride-pooling – a given percentage of trips is served by ride-pooling service, other trips represent background traffic.

To study different combinations of supply and demand, we vary the following parameters of a ride-pooling scenario: (i) *percPass* – a percentage of trips which are served with the ride-pooling service, (ii) *percTaxi* – percentage of taxis related to the number of passengers (e.g. if *percTaxi*=20%, and the number of passengers is equal to 100, 20 taxis will be available for ride-pooling), (iii) *capacity* – the maximum occupancy of a taxi (the same as the maximum number of passengers sharing the ride).

Three groups of metrics are supported:
1. Passenger satisfaction measures
   * passenger waiting time;
   * detour time/distance (compared to baseline scenario);
   * detour time/distance percentage (compared to baseline scenario);
   * taxi travel time (waiting time + travel time);
   * taxi-private coefficient. Calculated as (t_taxi - t_private)/t_private * 100.
2. Taxi fleet usage measures
    * % of used taxis;
    * average number of customers;
    * occupied/idle time/distance of a taxi;
    * idle time/distance ratio - fraction of idle time/distance from total time/distance of a taxi;
    * occupancy rate - average number of passengers for occupied legs of a trip.
5. Emission measures - total emissions of CO_2, CO, HC, NO_x, PM_x, fuel, % of advantage compared to baseline scenario.

## Content
1. SUMO simulation input files:
   * randgrid.net.xml - road network file.
   * parkingareas.add.xml - file with parking areas. It is necessary for single lane roads, otherwise taxi will block the road while waiting for passengers or during pick-up and drop-off.
   * randgridonlyprivate.sumocfg, randgrid.sumocfg - SUMO configuration files for baseline and ride-pooling scenarios, respectively.
   * randgrid.trips.xml - trip file generated by randomTrips tool (demand)
   * sumoview.xml - visualization settings for SUMO GUI.
   * randgridonlyprivate.rou.xml, randgridmixed.rou.xml - route files. For ride-pooling scenarios, contain also random trips for taxis (which will be replaced by dispatching algorithm during simulation).
2. Testbed scripts:
   * traciLaunch.py - external ride-pooling algorithm which is launched via TraCI interface. Here contains the implementation of maxOccupancy algorithm (selects the taxi with minimum pick-up distance which still has free seats).
   * genPassengers.py - generates ride-pooling route file randgridmixed.rou.xml. As an input, uses the values of parameters percPass, percTaxi, capacity.
   * runStat_single.sh - a shell script for a single launch of simulation and calculation of metrics.
   * runStat.sh - a shell script for batch experiments with a range of parameters.
   * getPassOrigTimeDistance.py - calculates trip metrics for baseline scenario (private cars). This input is output/tripinfoonlyprivate.xml (SUMO output file for baseline scenario). The output is output/stats/passengers.xml file.
   * getPassStats.py - calculates passengers satisfaction metrics. The input is output/tripinfo.xml file. The output is output/stats/passengers.xml file.
   * getTaxiStats.py - calculates taxi fleet usage metrics. The output is output/stats/taxi.xml file.
   * getEmissionStats.py - calcuate emission metrics. The input is output/emissionsonlyprivate.xml (for baseline scenario), output/emissions.xml. The output is output/stats/emissions.xml.
   * passengerDf.py, taxiDf.py, emissionsDf.py - creates dataframes with metrics and saves it to *.csv files in output/stats folder.
   * passengerStats.ipynb, taxiStats.ipynb, emissionStats.ipynb - Python notebooks for plotting the values of metrics from xml files.

## Usage
1. Prepare the input files for the simulation. In the example, road network file was prepared with netgenerate SUMO tool, demand was prepared with randomTrips SUMO tool.
2. Generate the ride-pooling scenario with genPassengers.py for the desired parameters of percPass, percTaxi and capacity.
3. Perform SUMO simulation for baseline scenario (using sumo.exe), for ride-pooling scenario (using traciLaunch.py).
4. Calculate the metrics from SUMO output files (tripinfo and emissions xml files in output folder).
5. Visualize the results with *.ipynb files.

For steps 2-6 shell scripts are provided (runStat_single.sh for a single experiment, runStat.sh - for batch experiment with varying parameters).
