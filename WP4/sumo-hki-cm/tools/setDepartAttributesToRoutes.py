import xml.etree.ElementTree as ET
import sys


try:
    ROUTES_INPUT_FILE = sys.argv[1]
    sys.stdout.write("Route file set to {}.\n".format(ROUTES_INPUT_FILE))
    OUTPUT_FILE = sys.argv[2]
    sys.stdout.write("Output file set to {}.\n".format(OUTPUT_FILE))
except:
    ROUTES_INPUT_FILE = 'sumo_files/reduced_routesampler_routes.rou.xml'
    sys.stdout.write("Input file defaulted to {}, add a file path as argument to change.\n".format(ROUTES_INPUT_FILE))
    OUTPUT_FILE = ROUTES_INPUT_FILE
    sys.stdout.write("Output file defaulted to {}, add a file path as argument to change.\n".format(OUTPUT_FILE))

sys.stdout.flush()
def main():
    tree = ET.parse(ROUTES_INPUT_FILE)
    root = tree.getroot()
    
    for vehicle in root:
        vehicle.set('departLane', 'free')
        vehicle.set('departSpeed', 'max')

    tree.write(OUTPUT_FILE)


if __name__ == '__main__':
    sys.exit(main())


