export PYTHONPATH="$SUMO_HOME/tools:$PYTHONPATH"
# To run in GUI, add "--gui" to TraCI_demo.py
python3 trafficCreator.py 2400 3600
python3 emissionOutputSwitcher.py emissions_1.xml
python3 TraCI_demo.py 1 3600 
python3 "$SUMO_HOME/tools/xml/xml2csv.py" "simulation_output/emissions_1.xml"
python3 aggregation.py
# For static visuals
# python staticPlots.py
# For interactive visuals in browser
python3 -m jupyter notebook visualization.ipynb