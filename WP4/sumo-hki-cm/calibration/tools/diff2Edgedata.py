import pandas as pd
import xml.etree.ElementTree as ET

EXCEL_FILE = 'calibration/data/real_world_comparison.xlsx'
SHEET_NAME = 'Detectors'
ADD_FILE = 'sumo_files/data/reduced_cut.add.xml'
#ORIG_EDGEDATA_FILE = 'WP4/sumo-hki-cm/sumo_files/data/reduced_edgedata_mid_only.xml'
OUTPUT_EDGEDATA_FILE = 'calibration/data/reduced_edgedata_diff.xml'

statsDF = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME)

addRoot = ET.parse(ADD_FILE).getroot()

# output root
outputRoot = ET.Element("data")

# create interval element that represents all traffic that was in the network right before morning rush hour
intervalElem = ET.SubElement(outputRoot, "interval")
intervalElem.set('id', 'before morning rush')
intervalElem.set('begin', '0.00')
intervalElem.set('end', '3600.00')

# for each station name, find the edge corresponding to it and the counts for this edge 
# and save this info in the dictionary {edge: counts}
edgeCounts = {}
visitedEdges = set()  # set to hold all visited edges to avoid processing the same edge multiple times
for (stationName, realCounts, sumoCounts) in zip(statsDF['Unnamed: 0'][:-1], statsDF['real'][:-1], statsDF['SUMO'][:-1]):
    for loop in addRoot.iter('inductionLoop'):
        if loop.get('id')[:-2] == stationName:
            edge = loop.get('lane')[:-2]
            
            if edge in visitedEdges:  # skip if already saw this edge (the same station)
                 continue

            visitedEdges.add(edge)
            diff = realCounts - sumoCounts
            if diff < 0:  # skip station where sumoCounts bigger than realCounts because routesampler can't handle negative numbers
                print(f"Warning: diff < 0 for station '{stationName}' on edge '{edge}'. The edgedata counts for this edge have been set to '0'")
                edgeCounts[edge] = 0
            else:
                edgeCounts[edge] = diff
            


# create xml 'edge' elements for edgedata file
for edge in edgeCounts:
    edgeElem = ET.SubElement(intervalElem, "edge")
    edgeElem.set("id", edge)
    edgeElem.set("entered", str(edgeCounts[edge]))

# origEdgeDataEdges = {}
# origEdgedataRoot = ET.parse(ORIG_EDGEDATA_FILE).getroot()
# for edge in origEdgedataRoot.iter('edge'):
#      origEdgeDataEdges[edge.get('id')] = None
    
# for edge in edgeCounts:
#     if edge not in origEdgeDataEdges:
#         print(edge)

# write output
outputTree = ET.ElementTree(outputRoot)
with open(OUTPUT_EDGEDATA_FILE, "wb") as f:
        outputTree.write(f)



