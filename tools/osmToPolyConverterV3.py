import sys
import os
from bs4 import BeautifulSoup
sys.path.append(os.path.join(os.environ["SUMO_HOME"], 'tools'))
import sumolib

OSM_FILE = os.path.join(os.getcwd(), "data/shape_files/sijoittelualueet2019.osm")
OUTPUT_FILE = os.path.join(os.getcwd(), "sumo_files/helmet_zones.poly.xml")
NETFILE = "sumo_files/helmet_area.net.xml"
NET = sumolib.net.readNet(NETFILE)

def main():
    with open(OSM_FILE, 'r') as fIn:
        data = fIn.read()
    bs = BeautifulSoup(data, "xml")
    nodes = getNodes(bs)
    polys = getPolygons(bs)

    writePolyFile(nodes, polys)


def getNodes(bs):
    nodeResults = bs.find_all("node")
    nodes = {}
    for result in nodeResults:
        node = {}
        lon = result.get("lon")
        lat = result.get("lat")
        xy_pos = NET.convertLonLat2XY(lon, lat)
        node["lon"] = xy_pos[0]
        node["lat"] = xy_pos[1]
        nodes[result.get("id")] = node
    return nodes

def getPolygons(bs):
    polys = {}
    polys = findNormalPolygons(bs, polys)
    polys = findRelationPolygons(bs, polys)
    return polys

def findRelationPolygons(bs, polys):
    for result in bs.find_all("relation"):
        nodeIds = []
        for tag in result.find_all("tag"):
            if tag["k"] == "SIJ2019":
                # Note!!! STORED AS INTEGER
                polyId = int(float(tag["v"]))
        for member in result.find_all("member"):
            if member["role"] == "outer":
                # Could be optimized by creating a separate dictionary for the relation
                # polygons and finding the referenced polygons in the poly dictionary?
                referencedPolygon = bs.find("way", {"id": member["ref"]})
                for node in referencedPolygon.find_all("nd"):
                    nodeIds.append(node["ref"])
        polys[polyId] = nodeIds
    return polys

def findNormalPolygons(bs, polys):
    for result in bs.find_all("way"):
        # Find the zone number
        for tag in result.find_all("tag"):
            if tag["k"] == "SIJ2019":
                # Note!!! STORED AS INTEGER
                polyId = int(float(tag["v"]))
        # Add all node ids to the polygon
        nodeIds = []
        for node in result.find_all("nd"):
            nodeIds.append(node["ref"])
        polys[polyId] = nodeIds
    return polys

def writePolyFile(nodes, polys):
    with open(OUTPUT_FILE, 'w') as fOut:
        fOut.write("""<?xml version="1.0" encoding="UTF-8"?>
<additional xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/additional_file.xsd">
    <!-- Shapes -->\n""")
        for polygonId in polys.keys():
            fOut.write(createPolyRow(polygonId, nodes, polys))
        fOut.write("""</additional>""")

def createPolyRow(polygonId, nodes, polys):
    row = ["    <poly id=\"po_"]
    row.append(str(polygonId))
    row.append("\" color=\"red\" fill=\"0\" layer=\"0.00\" shape=\"")
    for node in polys[polygonId]:
        row.extend([str(nodes[node]["lon"]), ",", str(nodes[node]["lat"]), " "])
    row.pop()
    row.append("\"/>\n")
    return "".join(row)


if __name__ == '__main__':
    sys.exit(main())