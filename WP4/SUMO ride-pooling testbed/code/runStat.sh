codeDir="C:\Users\bochenin\RL project\materials\ridesharing\toy example"
# files will be written to these folders
# and then copied to folder with experiments
rm -f output/* > output/stats/output.txt 2>&1
rm -f output/stats/* >> output/stats/output.txt 2>&1

experimentsDir="$codeDir""\experiments"
cd "$experimentsDir"
rm -r "$experimentsDir"/*
percpass=90
perctaxis='20'
capacities='1 2 3 4 5 6 7'

# run simulation only for private cars (it is made once)
cd "$codeDir"
echo "Starting simulation only with private cars..."
SECONDS=0
sumo.exe -c randgridonlyprivate.sumocfg >> output/stats/output.txt 2>&1
duration=$SECONDS
echo "Simulation with only private cars ended (""$(($duration / 60)) minutes and $(($duration % 60)) seconds elapsed)."

for pc in $perctaxis
do
    for cap in $capacities
    do
        cd "$experimentsDir"
        experDir="pass"$percpass"_taxi"$pc"_cap"$cap
        mkdir $experDir
        cd "$codeDir"

        fullExperDir="$experimentsDir"'\'"$experDir"
        echo "Running experiment with percpass="$percpass", perctaxis="$pc", taxi capacity="$cap
        echo "Copying input files to "$fullExperDir
        # copy input files for the experiment (these are non-changed for the fixed network and demand)
        cp parkingareas.add.xml "$fullExperDir"
        cp randgrid.net.xml "$fullExperDir"
        cp randgrid.sumocfg "$fullExperDir"
        cp randgrid.trips.xml "$fullExperDir"
        cp randgridonlyprivate.sumocfg "$fullExperDir"
        cp sumoview.xml "$fullExperDir"
        mkdir "$fullExperDir"'\output'
        # copy the results for only private cars simulation
        cp "output\emissionsonlyprivate.xml" "$fullExperDir"'\output'
        cp "output\tripinfoonlyprivate.xml" "$fullExperDir"'\output'
        # prepare randgridmixed.rou.xml and write the heading of summary.txt
        python genPassengers.py --tripfile randgrid.trips.xml --percpass $percpass --perctaxi $pc --taxiend 2500 --capacity $cap > output/stats/output.txt 2>&1
        # read -p "Press enter to continue"
        echo "Passengers generated (randgridmixed.rou.xml)"
        # copy generated file to experiment folder
        cp randgridmixed.rou.xml "$fullExperDir"
        echo "Starting simulation with taxis..."
        SECONDS=0
        # for default algorithms launch
        # sumo.exe -c randgrid.sumocfg >> output/stats/output.txt 2>&1
        # for TraCI launch
        python traciLaunch.py 
        duration=$SECONDS
        echo "Simulation with taxis ended (""$(($duration / 60)) minutes and $(($duration % 60)) seconds elapsed)."
        # copy the results for taxi simulation
        echo "Copying simulation results..."
        cp "output\emissions.xml" "$fullExperDir"'\output'
        cp "output\tripinfo.xml" "$fullExperDir"'\output'
        echo "Calculating original time and distance..."
        python getPassOrigTimeDistance.py >> output/stats/output.txt 2>&1
        echo "Calculating passenger stats..."
        python getPassStats.py >> output/stats/output.txt 2>&1
        python passengersDf.py >> output/stats/output.txt 2>&1
        echo "Calculating taxi stats..."
        python getTaxiStats.py >> output/stats/output.txt 2>&1
        python taxiDf.py >> output/stats/output.txt 2>&1
        echo "Calculating emission stats..."
        python getEmissionStats.py >> output/stats/output.txt 2>&1
        python emissionsDf.py >> output/stats/output.txt 2>&1  
        echo "Copying output files..."
        mkdir "$fullExperDir"'\output\stats'
        cp "output\stats\passengers.xml" "$fullExperDir"'\output\stats'
        cp "output\stats\passengerstats.csv" "$fullExperDir"'\output\stats'
        cp "output\stats\taxis.xml" "$fullExperDir"'\output\stats'
        cp "output\stats\taxistats.csv" "$fullExperDir"'\output\stats'
        cp "output\stats\emissions.xml" "$fullExperDir"'\output\stats'
        cp "output\stats\emissionstats.csv" "$fullExperDir"'\output\stats'
        cp "output\stats\summary.txt" "$fullExperDir"'\output\stats'
        cp "output\stats\output.txt" "$fullExperDir"'\output\stats'
    done
done

read -p "Press enter to continue"
# rm -f output/* > output/stats/output.txt 2>&1
# rm -f output/stats/* >> output/stats/output.txt 2>&1
# python genPassengers.py --tripfile randgrid.trips.xml --percpass 80 --perctaxi 20 --taxiend 2500 > output/stats/output.txt 2>&1
# sumo.exe -c randgridonlyprivate.sumocfg >> output/stats/output.txt 2>&1
# sumo.exe -c randgrid.sumocfg >> output/stats/output.txt 2>&1
# python getPassOrigTimeDistance.py >> output/stats/output.txt 2>&1
# python getPassStats.py >> output/stats/output.txt 2>&1
# python passengersDf.py >> output/stats/output.txt 2>&1
# python getTaxiStats.py >> output/stats/output.txt 2>&1
# python taxiDf.py >> output/stats/output.txt 2>&1
# python getEmissionStats.py >> output/stats/output.txt 2>&1
# python emissionsDf.py >> output/stats/output.txt 2>&1  