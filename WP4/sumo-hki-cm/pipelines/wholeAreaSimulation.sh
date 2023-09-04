# check if all the necessary files are present (for those that were not in github repo)
REQUIRED_FILES=(
    "sumo_files/whole_area.net.xml"
    "sumo_files/verified_trips.rou.xml"
    )

for i in ${REQUIRED_FILES[@]}; do
    if [ ! -f $i ]; then
        echo "File $i does not exist"
        exit 1
    fi
done

# NOTE: Will generate a 33 GB vehicle trajectory output file if the output is set in the .sumocfg file!
python3 sumo_files/runner.py