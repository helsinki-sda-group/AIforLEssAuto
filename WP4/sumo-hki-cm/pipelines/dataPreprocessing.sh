# check if all the necessary files are present (for those that were not in github repo)
REQUIRED_FILES=(
    "sumo_files/whole_area.net.xml" 
    "data/sijoittelualueet2019.dbf" 
    "data/demand_aht.omx" 
    )

for i in ${REQUIRED_FILES[@]}; do
    if [ ! -f $i ]; then
        echo "File $i does not exist"
        exit 1
    fi
done

echo -e "\nFile check done. Starting the reduced area pipeline:"

echo -e "\nVisum route generation..."
python3 tools/visumRouteGeneration.py

echo -e "\nOD2trips..."
od2trips -c sumo_files/od2trips.config.xml

echo -e "\nDuarouter..."
# If multithreading is enabled
duarouter -c sumo_files/duarcfg_file.trips2routes.duarcfg --routing-threads 4
# Otherwise
# duarouter -c sumo_files/duarcfg_file.trips2routes.duarcfg

echo -e "\nDeparture time sorter..."
python3 tools/randomDepartureTimes.py sumo_files/verified_trips.rou.xml sumo_files/verified_trips.rou.xml 0 3600
python3 tools/departureTimeSorter.py
python3 tools/indexZeroToN.py