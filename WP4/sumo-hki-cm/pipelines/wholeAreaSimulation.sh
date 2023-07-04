python3 tools/visumRouteGeneration.py
od2trips -c sumo_files/od2trips.config.xml
# If multithreading is enabled
duarouter -c sumo_files/duarcfg_file.trips2routes.duarcfg --routing-threads 4 --write-trips true --ignore-errors true
# Otherwise
# duarouter -c sumo_files/duarcfg_file.trips2routes.duarcfg --write-trips true --ignore-errors true
python3 tools/randomDepartureTimes.py sumo_files/verified_trips.rou.xml sumo_files/verified_trips.rou.xml 0 3600
python3 tools/departureTimeSorter.py
python3 tools/indexZeroToN.py
# NOTE: Will generate a 33 GB vehicle trajectory output file if the output is set in the .sumocfg file!
python3 sumo_files/runner.py