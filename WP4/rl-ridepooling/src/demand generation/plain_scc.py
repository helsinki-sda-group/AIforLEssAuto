import networkx as nx
import xml.etree.ElementTree as ET
import os

here = os.path.dirname(os.path.abspath(__file__))

G = nx.DiGraph()

connFile = "../../nets/ridepooling/Helsinki updated areas/area2/plain/plain.con.xml"
edgeFile = "../../nets/ridepooling/Helsinki updated areas/area2/plain/plain.edg.xml"
nodeFile = "../../nets/ridepooling/Helsinki updated areas/area2/plain/plain.nod.xml"
tllFile = "../../nets/ridepooling/Helsinki updated areas/area2/plain/plain.tll.xml"
newConnFile = "../../nets/ridepooling/Helsinki updated areas/area2/plain/area2_gcc_plain.con.xml"
newEdgeFile = "../../nets/ridepooling/Helsinki updated areas/area2/plain/area2_gcc_plain.edg.xml"
newNodeFile = "../../nets/ridepooling/Helsinki updated areas/area2/plain/area2_gcc_plain.nod.xml"
newTllFile = "../../nets/ridepooling/Helsinki updated areas/area2/plain/area2_gcc_plain.tll.xml"

tree = ET.parse(os.path.join(here, connFile))
root = tree.getroot()

# creation of the directed graph when nodes are tuples (edge, lane), and edge is the connection

for conn in root.findall('connection'):
    fromEdge = conn.get("from")
    fromLane = conn.get("fromLane")
    toEdge = conn.get("to")
    toLane = conn.get("toLane")
    if fromEdge == None or fromLane == None or toEdge == None or toLane == None:
        continue
    fromName = fromEdge + "_" + fromLane
    toName = toEdge + "_" + toLane
    G.add_nodes_from([fromName, toName])
    G.add_edge(fromName, toName)

print("Number of nodes: ", G.number_of_nodes())
print("Number of edges: ", G.number_of_edges())

# get giant strongly connected component
largest = max(nx.strongly_connected_components(G),key=len)
sc = G.subgraph(largest)
print("Number of nodes in the lcc: ", sc.number_of_nodes())
print("Number of edges in the lcc: ", sc.number_of_edges())

tree = ET.parse(os.path.join(here, connFile))
root = tree.getroot()

connRemoved = 0
edgeLaneSet = set()
edgeSet = set()

# creation of the new connections file which contains only connections which are in GCC
# memoryzing which edges should be present in a new network (edgeSet)
# and which lanes (edgeLaneSet)

for conn in root.findall('connection'):
    fromEdge = conn.get("from")
    fromLane = conn.get("fromLane")
    toEdge = conn.get("to")
    toLane = conn.get("toLane")
    if fromEdge == None or fromLane == None or toEdge == None or toLane == None:
        root.remove(conn)
        continue
    fromName = fromEdge + "_" + fromLane
    toName = toEdge + "_" + toLane
    # if connection is not in strongly gcc
    if not sc.has_edge(fromName, toName):
        root.remove(conn)
        connRemoved += 1
    else:
        edgeLaneSet.add((fromEdge,fromLane))
        edgeLaneSet.add((toEdge,toLane))
        edgeSet.add(toEdge)
        edgeSet.add(fromEdge)

print("Connections removed: ", connRemoved)
tree.write(os.path.join(here, newConnFile))

# creation of the new traffic light file which contains only connections which are in GCC;
connRemoved = 0

tree = ET.parse(os.path.join(here, tllFile))
root = tree.getroot()

for conn in root.findall('connection'):
    fromEdge = conn.get("from")
    fromLane = conn.get("fromLane")
    toEdge = conn.get("to")
    toLane = conn.get("toLane")
    if fromEdge == None or fromLane == None or toEdge == None or toLane == None:
        root.remove(conn)
        continue
    fromName = fromEdge + "_" + fromLane
    toName = toEdge + "_" + toLane
    # if connection is not in strongly gcc
    if not sc.has_edge(fromName, toName):
        root.remove(conn)
        connRemoved += 1

print("Connections removed for tll: ", connRemoved)
tree.write(os.path.join(here, newTllFile))

# creation of the new edge file which contains only edges and lanes which are in GCC;
tree = ET.parse(os.path.join(here, edgeFile))
root = tree.getroot()

edgesRemoved = 0
lanesRemoved = 0

print("Number of edges in the original graph: ", len(root.findall('edge')))

for edge in root.findall('edge'):
    edgeId = edge.get("id")
    if not edgeId in edgeSet:
        root.remove(edge)
        edgesRemoved += 1
    else:
        for lane in edge.findall("lane"):
            laneIndex = lane.get("index")
            if not (edgeId, laneIndex) in edgeLaneSet:
                edge.remove(lane)
                lanesRemoved += 1

print("Edges removed: ", edgesRemoved)
print("Lanes removed: ", lanesRemoved)
tree.write(os.path.join(here, newEdgeFile))

# creation of the nodeSet with nodes only in GCC
nodeSet = set()

tree = ET.parse(os.path.join(here, newEdgeFile))
root = tree.getroot()

for edge in root.findall('edge'):
    fromNode = edge.get("from")
    toNode = edge.get("to")
    nodeSet.add(fromNode)
    nodeSet.add(toNode)

# creation of new node file with nodes only in GCC
# memorizing traffic lights for the removed nodes
nodesRemoved = 0

tree = ET.parse(os.path.join(here, nodeFile))
root = tree.getroot()

print("Number of nodes in the original graph: ", len(root.findall('node')))

tlSet = set()

for node in root.findall('node'):
    nodeId = node.get("id")
    if nodeId not in nodeSet:
        if node.get("tl") is not None:
            tlSet.add(node.get("tl"))
        root.remove(node)
        nodesRemoved += 1

print("Nodes removed: ", nodesRemoved)
tree.write(os.path.join(here, newNodeFile))

# remove from tllset traffic light that participate in connections in the GCC
tree = ET.parse(os.path.join(here, newTllFile))
root = tree.getroot()
for conn in root.findall("connection"):
    tllId = conn.get("tl")
    if tllId in tlSet:
        tlSet.remove(tllId)

# print(tlSet)
# modifying traffic lights file to remove lights from the removed nodes

tree = ET.parse(os.path.join(here, newTllFile))
root = tree.getroot()

tllRemoved = 0

for tll in root.findall("tlLogic"):
    tllId = tll.get("id")
    if tllId  in tlSet:
        tllRemoved += 1
        root.remove(tll)

print("Tll removed: ", tllRemoved)
tree.write(os.path.join(here, newTllFile))