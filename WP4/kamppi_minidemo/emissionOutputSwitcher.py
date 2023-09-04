import sys
import xml.etree.ElementTree as ET

SUMOCFG_FILE = "TraCI_demo.sumocfg"

try:
    EMISSION_FILE_NAME = sys.argv[1]
except:
    sys.exit("Please provide the emission output file name as an argument.")

def main():
    configXml = ET.parse(SUMOCFG_FILE)
    tree = configXml.getroot()
    output = tree.find("output")
    emissionOutput = output.find("emission-output")
    emissionOutput.set("value", "simulation_output/" + EMISSION_FILE_NAME)
    configXml.write(SUMOCFG_FILE)

if __name__ == "__main__":
    sys.exit(main())