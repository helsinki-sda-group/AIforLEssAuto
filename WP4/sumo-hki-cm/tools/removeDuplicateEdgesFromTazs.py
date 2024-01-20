import xml.etree.ElementTree as ET
import sys

DEFAULT_INPUT = 'sumo_files/data/reduced_cut_districts_2.taz.xml'
DEFAULT_OUTPUT = 'sumo_files/data/reduced_cut_districts_2_removed_duplicates.taz.xml'

try:
    INPUT_FILE = sys.argv[1]
    sys.stdout.write("Route file set to {}.\n".format(INPUT_FILE))
    OUTPUT_FILE = sys.argv[2]
    sys.stdout.write("Output file set to {}.\n".format(OUTPUT_FILE))
except:
    INPUT_FILE = DEFAULT_INPUT
    sys.stdout.write("Input file defaulted to {}, add a file path as argument to change.\n".format(INPUT_FILE))
    OUTPUT_FILE = DEFAULT_OUTPUT
    sys.stdout.write("Output file defaulted to {}, add a file path as argument to change.\n".format(OUTPUT_FILE))

sys.stdout.flush()
def main():
    tree = ET.parse(INPUT_FILE)
    root = tree.getroot()
    
    allEdges = set()
    removedEdges = {}
    for taz in root:
        tazEdges = taz.get('edges').split()

        uniqueTazEdges = []
        for edge in tazEdges:
            if edge in allEdges:
                if edge in removedEdges:
                    removedEdges[edge] += 1
                else:
                    removedEdges[edge] = 1
            else:
                allEdges.add(edge)
                uniqueTazEdges.append(edge)
        
        taz.set('edges', ' '.join(uniqueTazEdges))
                
    print(f"removed {len(removedEdges)} different edges in total")
    tree.write(OUTPUT_FILE)


if __name__ == '__main__':
    sys.exit(main())