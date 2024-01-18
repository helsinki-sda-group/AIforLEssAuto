from bs4 import BeautifulSoup

# mixed routes files (with passenger trips)
mixedRoutesFile = "randgridmixed.rou.xml"

with open(mixedRoutesFile, "r") as f:
    data = f.read()

soup = BeautifulSoup(data, "xml")

personEntries = soup.find_all("person")

# create new xml
personSoup = BeautifulSoup(features="xml")
personsInfoTag = soup.new_tag("personsInfo")
personSoup.append(personsInfoTag)

for person in personEntries:
    _id = person["id"]
    _depart = person["depart"]
    _orig = 0
    _dest = 0
    # there should be only one ride per person in mixed routes file
    for ride in person.find_all("ride"):
        _orig = ride["from"]
        _dest = ride["to"]
    personSoup.personsInfo.append(personSoup.new_tag("person", id=_id,  desiredDepart=_depart, orig = _orig, dest = _dest, mode = "taxi"))

# tripinfo file (with only private trips)
tripinfoPrivateFile = "output/tripinfoonlyprivate.xml"
with open(tripinfoPrivateFile, "r") as f:
    data = f.read()

f.close()

soup = BeautifulSoup(data, "xml")

# for each passenger
for person in personSoup.personsInfo.find_all("person"):
    _depart = person["desiredDepart"]
    _orig = person["orig"]
    _dest = person["dest"]
    # find trip for corresponding passenger
    # match by three fields
    # as in trip info we have arrivalLane and deparLane instead of edges, 
    # we append _0 as postfix to convert edge number to lane number
    

    # first we find the entry with the same origin and destination
    results = soup.find_all("tripinfo", {"departLane" : _orig + "_0", "arrivalLane": _dest + "_0"})
    if len(results) == 0:
        print("Passenger with origin = " + _orig + " and destination = " + _dest + " was not found")
    else:
        found = len(results)
        foundDepTimes = []
        match = 0
        match_index = -1
        for i in range(0, found):
            # checking also for departure time
            # as some of the passengers may depart with some delay e.g. if the car cannot be inserted instantly
            # depart in tripinfo is the actual departure time, 
            # departDelay is waiting time from spawning the trip to the actual departure
            # and in the mixed route file we have spawning departure times
            foundDepTime = int(float(results[i]["depart"])) - int(float(results[i]["departDelay"]))
            foundDepTimes.append(foundDepTime)
            if int(float(_depart)) == foundDepTime: 
                match += 1
                match_index = i
        if match == 0:
            print("Passenger with origin = " + _orig + " and destination = " + _dest + " has non-matching departure times, expected = " + _depart + " actual: ")
            print(*foundDepTimes)
        elif match == 1: 
            person["privateDepart"] = results[match_index]["depart"]
            person["privateDepartDelay"] = results[match_index]["departDelay"]
            person["privateDuration"] = results[match_index]["duration"]
            person["privateArrival"] = results[match_index]["arrival"]
            person["privateRouteLength"] = results[match_index]["routeLength"]
        else:
            print("Passenger with origin = " + _orig + " and destination = " + _dest + " has ambiguity, departure times expected = " + _depart + " actual: ")
            print(*foundDepTimes)

# second part - for the trips (non-taxi passengers)
# again we open mixedRoutesFile
with open(mixedRoutesFile, "r") as f:
    data = f.read()

soup = BeautifulSoup(data, "xml")

# we need to skip taxi trips in the beginning, all they have attribute "type"
def custom_selector(tag):
    return tag.name == "trip" and not tag.has_attr("type")

# but now we read all the trip entries
tripEntries = soup.find_all(custom_selector)
print(len(tripEntries))

with open(tripinfoPrivateFile, "r") as f:
    data = f.read()

privateSoup = BeautifulSoup(data, "xml")

f.close()

for trip in tripEntries:
    _id = trip["id"]
    _depart = trip["depart"]
    _orig = trip["from"]
    _dest = trip["to"]
    
    # find trip in private trip file
    privateTrip = privateSoup.find("tripinfo", {"id" : _id}) 
    if privateTrip == None:
        print("Private trip with id " + _id + " was not found in private trip file")
    else:
        personSoup.personsInfo.append(personSoup.new_tag("person", id=_id,  desiredDepart=_depart, orig = _orig, dest = _dest, mode = "private", \
                                                         privateDepart=privateTrip["depart"], privateDepartDelay=privateTrip["departDelay"], \
                                                         privateDuration=privateTrip["duration"], privateArrival=privateTrip["arrival"], \
                                                         privateRouteLength=privateTrip["routeLength"]))
    
                      
# print(personSoup)
f = open("output/stats/passengers.xml", "w")
f.write(personSoup.prettify())
f.close()