# check if all the necessary files are present
REQUIRED_FILES=(
    "calibration/data/collection_days_2018.txt" 
    )

for i in ${REQUIRED_FILES[@]}; do
    if [ ! -f $i ]; then
        echo "File $i does not exist"
        exit 1
    fi
done

python3 calibration/tools/traffic_counts_retrieval_2018/gatherDigitrafficDetectors2018.py
python3 calibration/tools/traffic_counts_retrieval_2018/historyTrafficDataCollection.py
python3 calibration/tools/traffic_counts_retrieval_2018/digitrafficPeakHourTraffic.py