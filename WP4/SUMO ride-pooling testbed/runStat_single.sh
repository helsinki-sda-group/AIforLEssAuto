#cd "C:\Users\bochenin\RL project\materials\ridesharing\toy example\experiments"
#rm -f output/* > output/stats/output.txt 2>&1
#rm -f output/stats/* >> output/stats/output.txt 2>&1
python genPassengers.py --tripfile MySUMOFile.trips.xml --percpass 100 --perctaxi 60 --taxiend 3000 --capacity 2 > output/stats/output.txt 2>&1
# sumo.exe -c randgridonlyprivate.sumocfg >> output/stats/output.txt 2>&1
# sumo.exe -c randgrid.#cfg >> output/stats/output.txt 2>&1

# sumo.exe -c MySUMOonlyprivate.sumocfg >> output/stats/output.txt 2>&1
# sumo.exe -c MySUMO.sumocfg >> output/stats/output.txt 2>&1


# sumo.exe -c randgrid.sumocfg >> output/stats/output.txt 2>&1

# python traciLaunch.py 

# python getPassOrigTimeDistance.py >> output/stats/output.txt 2>&1
# python getPassStats.py >> output/stats/output.txt 2>&1
# python passengersDf.py >> output/stats/output.txt 2>&1
# python getTaxiStats.py >> output/stats/output.txt 2>&1
# python taxiDf.py >> output/stats/output.txt 2>&1
# python getEmissionStats.py >> output/stats/output.txt 2>&1
# python emissionsDf.py >> output/stats/output.txt 2>&1

 