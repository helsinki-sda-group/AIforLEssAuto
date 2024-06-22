from bs4 import BeautifulSoup

# tripinfo file (mixed one)
tripinfoFile = "output/tripinfo.xml"
with open(tripinfoFile, "r") as f:
    data = f.read()

f.close()

soup = BeautifulSoup(data, "xml")

# append entry of passengers.xml with corresponding id
# file containing original duration and distance
passengersFile = "output/stats/passengers.xml"
with open(passengersFile, "r") as f:
    data = f.read()

newPassengerSoup = BeautifulSoup(data, "xml")

f.close()

# for all person in mixed trip info file
for person in soup.find_all("personinfo"):
    _id = person["id"]
    _desiredDepart = person["depart"]
    rides = person.find_all("ride")
    # from SUMO documentation:
    # waitingTime -- the time in which the vehicle speed was below or 
    # equal 0.1 m/s (scheduled stops do not count)
    _taxiWaitingTime = rides[0]["waitingTime"]
    _taxiVehicle = rides[0]["vehicle"]
    _taxiDepart = int(float(rides[0]["depart"]))
    _taxiDepartDelay = int(float(_taxiDepart)) - int(float(_desiredDepart))    
    _taxiArrival = int(float(rides[0]["arrival"]))
    _taxiDuration = rides[0]["duration"]
    _taxiRouteLength = rides[0]["routeLength"]
    _unfinishedTrip = False if _taxiArrival != -1 else True
    _unstartedTrip = False if _taxiDepart != -1 else True
    _taxiDetourTime = 0
    _taxiDetourDistance = 0
    _taxiDetourTimePerc = 0
    _taxiDetourDistancePerc = 0
    _sharedRide = False

    sharedRide = False
    # check if it was shared rides for that person
    # find all the rides of the same taxi
    for person2 in soup.find_all("personinfo"):
        if _id != person2["id"]:
            rides = person2.find_all("ride")
            p2vehicle = rides[0]["vehicle"]
            if p2vehicle == _taxiVehicle:
                # actual depart and arrival of person 2
                p2depart = int(float(rides[0]["depart"]))
                p2arrival = int(float(rides[0]["arrival"]))
                # checking intersection of rides
                if _taxiDepart < p2depart:
                    if _taxiArrival > p2depart:
                        sharedRide = True
                if _taxiDepart > p2depart:
                    if p2arrival > _taxiDepart:
                        sharedRide = True
        if sharedRide:
            _sharedRide = True
            # print("Passengers with id " + _id + " and " + person2["id"] + " have shared ride")

    # file containing original duration and distance
    passengersFile = "output/stats/passengers.xml"
    with open(passengersFile, "r") as f:
        data = f.read()

    passengerSoup = BeautifulSoup(data, "xml")
    # to check that all is read correstly
    # tags = len(passengerSoup.personsInfo.find_all("person"))
    # print("Person tags count: ", tags)
    results = passengerSoup.find_all("person", {"id" : _id})
    if len(results) == 0:
        print("Original trip was not found for passenger with id " + _id)
    elif len(results) > 1:
        print("Ambiguation in finding original trip for passenger with id " + _id)
    else:
        privateDuration = int(float(results[0]["privateDuration"]))
        privateRouteLength = float(results[0]["privateRouteLength"])
        _taxiDetourTime = int(float(_taxiDuration)) - privateDuration
        _taxiDetourDistance = round(float(_taxiRouteLength) - privateRouteLength, 2)
        _taxiDetourTimePerc = round(_taxiDetourTime / float(privateDuration) * 100, 2)
        _taxiDetourDistancePerc = round(_taxiDetourDistance / privateRouteLength * 100, 2)
        if _unfinishedTrip:
            _taxiDetourTime = -1
            _taxiDetourDistance = -1
            _taxiDetourTimePerc = -1
            _taxiDetourDistancePerc = -1
            _taxiDepartDelay = -1
    f.close()

    for person in newPassengerSoup.find_all("person", {"id" : _id}):
        person["sharedRide"] = _sharedRide
        person["unfinishedTrip"] = _unfinishedTrip
        person["unstartedTrip"] = _unstartedTrip
        person["taxiWaitingTime"] = _taxiWaitingTime
        person["taxiVehicle"] = _taxiVehicle 
        person["taxiDepart"] = _taxiDepart 
        person["taxiDepartDelay"] = _taxiDepartDelay 
        person["taxiArrival"] = _taxiArrival 
        person["taxiDuration"] = _taxiDuration 
        person["taxiRouteLength"] = _taxiRouteLength 
        person["detourTime"] = _taxiDetourTime 
        person["detourDistance"] = _taxiDetourDistance 
        person["detourTimePerc"] = _taxiDetourTimePerc 
        person["detourDistancePerc"] = _taxiDetourDistancePerc 

# part 2 (private trips)

privateTrips = newPassengerSoup.find_all("person", {"mode": "private"})
print("Private trips found: ", len(privateTrips))

for person in privateTrips:
    _id = person["id"]
    mixedTrip = soup.find("tripinfo", {"id" : _id})
    person["sharedRide"] = "False"
    person["unfinishedTrip"] = "False"
    person["unstartedTrip"] = "False"
    person["taxiWaitingTime"] = 0
    person["taxiVehicle"] = _id 
    person["taxiDepart"] = mixedTrip["depart"] 
    person["taxiDepartDelay"] = mixedTrip["departDelay"] 
    person["taxiArrival"] = mixedTrip["arrival"] 
    person["taxiDuration"] = mixedTrip["duration"] 
    person["taxiRouteLength"] = mixedTrip["routeLength"] 
    person["detourTime"] = int(float(mixedTrip["duration"]))-int(float(person["privateDuration"])) 
    person["detourDistance"] = round(float(mixedTrip["routeLength"])-float(person["privateRouteLength"]),2)
    person["detourTimePerc"] = round(float(person["detourTime"]) / int(float(person["privateDuration"])) * 100,2)
    person["detourDistancePerc"] = round(float(person["detourDistance"]) / float(person["privateRouteLength"]) * 100,2)
    
# print(passengerSoup)
f = open("output/stats/passengers.xml", "w")
f.write(newPassengerSoup.prettify())
f.close()


    

    