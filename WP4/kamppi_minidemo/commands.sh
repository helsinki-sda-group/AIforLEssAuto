export PYTHONPATH="$SUMO_HOME/tools:$PYTHONPATH"
# To run in GUI, add "--gui" to TraCI_demo.py
# 1st scenario
# Baseline
python3 trafficCreator.py 300
python3 emissionOutputSwitcher.py emissions_1.xml
python3 TraCI_demo.py --gui 1
# 2nd scenario
# More vehicles
python3 trafficCreator.py 400
python3 emissionOutputSwitcher.py emissions_2.xml
python3 TraCI_demo.py 2
# 3rd scenario
# Change vehicle parameters
python3 confirmContinue.py
python3 emissionOutputSwitcher.py emissions_3.xml
python3 TraCI_demo.py 3
# 4th scenario
# Change vehicle parameters
python3 confirmContinue.py
python3 emissionOutputSwitcher.py emissions_4.xml
python3 TraCI_demo.py 4
# The results
python3 outputPlots.py