# get taxi fleet usage measures

from bs4 import BeautifulSoup
from collections import defaultdict

# get taxi ids from route file

# routes file (mixed one)
rouFile = "randgridmixed.rou.xml"
with open(rouFile, "r") as f:
    data = f.read()

f.close()

rouSoup = BeautifulSoup(data, "xml")


# find finishing time of all taxis
taxiVType = rouSoup.find("vType", {"vClass": "taxi"})
paramTag = taxiVType.find("param", {"key": "device.taxi.end"})
# taxiFinishingTime = int(float(paramTag["value"]))

taxis = rouSoup.find_all("trip", {"type": "taxi"})
print(str(len(taxis)) + " taxis found in " + rouFile)

taxiIds = []

for taxi in taxis:
    taxiIds.append(taxi["id"])

# tripinfo file (mixed one)
tripinfoFile = "output/tripinfo.xml"
with open(tripinfoFile, "r") as f:
    data = f.read()

f.close()

tripSoup = BeautifulSoup(data, "xml")

# print(tripSoup)

# create new xml
taxiSoup = BeautifulSoup(features="xml")
taxiInfoTag = taxiSoup.new_tag("taxisInfo")
taxiSoup.append(taxiInfoTag)

# add information which may be extracted from tripInfo
for taxi in taxiIds:
    try:
        tripInfo = tripSoup.find("tripinfo", {"id": taxi})
    except:
        print("No taxi trip was found in trip info file for id " + taxi)

    _fullDistance = float(tripInfo["routeLength"])
    try:
        taxiTrip = tripInfo.find("taxi")
    except:
        print("No taxi trip was found for id " + taxi)
    _customers = int(float(taxiTrip["customers"]))
    _occupiedDistance = float(taxiTrip["occupiedDistance"])
    _occupiedTime = int(float(taxiTrip["occupiedTime"]))
    _idleDistance = round(_fullDistance-_occupiedDistance, 2)
    _idleDistanceRatio = round(_idleDistance / _fullDistance, 2)

    taxiSoup.taxisInfo.append(taxiSoup.new_tag("taxi", id=taxi,  customers=_customers, fullDistance=_fullDistance, \
                                               occupiedDistance=_occupiedDistance, idleDistance=_idleDistance, \
                                                idleDistanceRatio = _idleDistanceRatio, occupiedTime=_occupiedTime))
taxiRides = defaultdict(list)

# to calculate idle time, we need to know the time of latest passenger arrival
# after that, we treat all customers as served, so time till despawning of the taxis will not be added
persons = tripSoup.find_all("personinfo")
latestArrival = 0
for person in persons:
    ride = person.find("ride")
    arrival = int(float(ride["arrival"]))
    taxi = ride["vehicle"]
    taxiRides[taxi].append(ride)
    if arrival > latestArrival:
        latestArrival = arrival

print("Latest passenger arrival: " + str(latestArrival))
# print("Taxi finishing time: " + str(taxiFinishingTime))
endTaxiFleet = latestArrival # if latestArrival < taxiFinishingTime else taxiFinishingTime

# picking up all the passenger data for taxis
for taxi in taxis:
    tSoup = taxiSoup.find("taxi", {"id": taxi["id"]})
    _occupiedTime = int(float(tSoup["occupiedTime"]))

    pickupDropoffList = []
    for ride in taxiRides[taxi["id"]]:
        pickup = (int(float(ride["depart"])), "pickup")
        dropoff = (int(float(ride["arrival"])), "dropoff")
        # if arrival == -1, it means incomplete trip, and
        # we put arrival equal to end taxi fleet
        if dropoff[0] == -1:
            dropoff = (endTaxiFleet, "dropoff")
        pickupDropoffList.append(pickup)
        pickupDropoffList.append(dropoff)

    pickupDropoffList = sorted(pickupDropoffList)
    if len(pickupDropoffList) == 0:
        _occupancyRate = 0
        # we assume that taxi fleet starts operating from 0 iteration
        _idleTime = endTaxiFleet
        _fullTime = _idleTime
        _idleTimeRatio = 1
    else:
        pdCount = len(pickupDropoffList)
        firstIdleLegTime = pickupDropoffList[0][0]
        if pickupDropoffList[pdCount-1][1] == "dropoff":
            lastIdleLegTime = endTaxiFleet - pickupDropoffList[pdCount-1][0]
        else:
            lastIdleLegTime = 0
        currCustomerCount = 0
        intermIdleTime = 0
        aggCustomerCount = 0
        occupLegs = 0
        for i, event in enumerate(pickupDropoffList):
            if i != 0:
                aggCustomerCount += currCustomerCount
                if currCustomerCount == 0:
                    intermIdleTime += event[0]-pickupDropoffList[i-1][0]
                else:
                    occupLegs += 1
            if event[1] == "pickup":
                currCustomerCount += 1
            else:
                currCustomerCount -= 1
        _idleTime = firstIdleLegTime + intermIdleTime + lastIdleLegTime
        _fullTime = _occupiedTime + _idleTime
        _idleTimeRatio = round(_idleTime / _fullTime, 2)
        _occupancyRate = round(aggCustomerCount / occupLegs,2)
    tSoup["fullTime"] = _fullTime
    tSoup["idleTime"] = _idleTime
    tSoup["idleTimeRatio"] = _idleTimeRatio
    tSoup["occupancyRate"] = _occupancyRate

# print(taxiSoup)
f = open("output/stats/taxis.xml", "w")
f.write(taxiSoup.prettify())
f.close()

        





    


