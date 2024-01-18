import os
import sys
from bs4 import BeautifulSoup
if 'SUMO_HOME' in os.environ:
    sys.path.append(os.path.join(os.environ['SUMO_HOME'], 'tools'))
# import traci
import libsumo as traci
sumoBinary = "C:\\Program Files (x86)\\Eclipse\\Sumo\\bin\\sumo.exe"
# sumoBinary = "C:\\Program Files (x86)\\Eclipse\\Sumo\\bin\\sumo-gui.exe"
sumoCmd = [sumoBinary, "-c", "randgrid.sumocfg", "--seed", "42"]
sumoCmd = [sumoBinary, "-c", "MySUMO.sumocfg", "--seed", "42"]

simulationSteps = 3000
all_reservations = []

# get maximum capacity from randgridmixed.rou.xml
with open("randgridmixed.rou.xml", "r") as f:
    data = f.read()
f.close()

soup = BeautifulSoup(data, "xml")
vTypeTag = soup.find("vType")
# personCapacity = vTypeTag.find("param", {"key" : "personCapacity"})
capacity = int(float(vTypeTag["personCapacity"]))

def getTaxi(person, taxis):
    selectedTaxi = -1
    fromEdge = person.fromEdge
    toEdge = person.toEdge
    personId = person.persons[0]
    currentDistance = 10000000
    for taxi in taxis:
        currentCustomers = traci.vehicle.getParameter(taxi, "device.taxi.currentCustomers")
        currList = list(map(lambda x: x[1:], currentCustomers.split(" ")))
        # 4 is the maximum capacity
        if len(currList) == capacity and currentCustomers!='':
            continue

        route = traci.vehicle.getRoute(taxi) 
        taxiDepartEdge = route[0] 
        distance = traci.simulation.getDistanceRoad(taxiDepartEdge, 0, fromEdge, 0, isDriving=True)   
        # check if taxi has free seats!
        if distance < currentDistance:
            selectedTaxi = taxi
            currentDistance = distance
    return selectedTaxi

def getCandPoi(poi, pdList):
    candPoi = []
    # add to candidates all pois that 
    # have not been scheduled before
    for p in poi:
        found = False
        for pd in pdList:
            # ???
            if p == pd:
                found = True
        if not found:
            # but if the poi is drop off
            # we add it only if pickup was
            # already performed or already scheduled
            if p[2] == "dropoff":
                foundPickUp = False
                for pd in poi:
                    if p[0] == pd[0] and pd[2] == "pickup":
                        foundPickUp = True
                # if passenger was already picked up
                if not foundPickUp:
                    candPoi.append(p) 
                else:
                    # if pick up was already scheduled
                    foundPickUpScheduled = False
                    for pd in pdList:
                        if p[0] == pd[0] and pd[2] == "pickup":
                            foundPickUpScheduled = True
                    if foundPickUpScheduled:
                        candPoi.append(p)
            # pick up is always added
            else:
                candPoi.append(p)
    return candPoi

def getNextPoi(currentEdge, candPoi):
    nextPoi = candPoi[0]
    newCurrentEdge = candPoi[0][1]
    currentDistance = 10000000

    for cand in candPoi:
        distance = traci.simulation.getDistanceRoad(currentEdge, 0, cand[1], 0, isDriving=True)   
        if distance < currentDistance:
            nextPoi = cand
            newCurrentEdge = cand[1]
            currentDistance = distance
    return nextPoi, newCurrentEdge


def getPickUpDropOffList(taxi, currentCustomers, newCustomerRes):
    pickupDropoffList = []
    resList = [int(newCustomerRes)]

    currList = list(map(lambda x: x[1:], currentCustomers.split(" ")))
    resList.extend(currList)

    poi = []
    for res in resList:
        person = tuple(filter(lambda x: x.id == str(res), all_reservations))[0]
        fromEdge = person.fromEdge
        toEdge = person.toEdge
        wasPickup = True if int(person.state) == 8 else False
        poi.append((res, toEdge, "dropoff"))
        #if not wasPickup:
        # for some reasons, there is an exception
        # when you try to skip pickup for already picked up person
        # in contrast to documentation
        poi.append((res, fromEdge, "pickup"))
    
    currentEdge = traci.vehicle.getRoute(taxi)[0]

    scheduled = 0
    pdList = []

    while scheduled < len(poi):
        candPoi = getCandPoi(poi, pdList)
        nextPoi, currentEdge = getNextPoi(currentEdge, candPoi)
        pdList.append(nextPoi)
        scheduled += 1

    for p in pdList:
        pickupDropoffList.append(str(p[0]))

    return pickupDropoffList




traci.start(sumoCmd)
step = 0
while step < simulationSteps:
    all_reservations = traci.person.getTaxiReservations(0)
    # get all reservations that have not taxi assigned, and which were not picked up yet
    reservations = tuple(filter(lambda x: x.state!=4 and x.state!=8, all_reservations))
    taxis = traci.vehicle.getTaxiFleet(-1)
    for person in reservations:
        taxi = getTaxi(person, taxis)
        # here we skip some passengers :(
        if (taxi == -1):
            continue
        taxiState = int(traci.vehicle.getParameter(taxi, "device.taxi.state"))
        currentCustomers = traci.vehicle.getParameter(taxi, "device.taxi.currentCustomers")
        # print("Before: customers of taxi " + taxi + " " + currentCustomers)
        # for empty taxi
        if taxiState == 0:
            traci.vehicle.dispatchTaxi(taxi, [person.id])
        else:
            pickupDropoffList = getPickUpDropOffList(taxi, currentCustomers, person.id)
            traci.vehicle.dispatchTaxi(taxi, pickupDropoffList)
        currentCustomers = traci.vehicle.getParameter(taxi, "device.taxi.currentCustomers")
        # print("After: customers of taxi " + taxi + " " + currentCustomers)
        #print("\n")
    traci.simulationStep()
    #if step%10==0: 
        #print("Step = " + str(step))
    step += 1

traci.close()

