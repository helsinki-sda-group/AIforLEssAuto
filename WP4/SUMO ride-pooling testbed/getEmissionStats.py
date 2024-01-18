from bs4 import BeautifulSoup

tripInfoFiles = [("private", "output/tripinfoonlyprivate.xml"), ("taxi", "output/tripinfo.xml")]

# create new xml
emissionsSoup = BeautifulSoup(features="xml")
emissionsInfoTag = emissionsSoup.new_tag("emissionsInfo")
emissionsSoup.append(emissionsInfoTag)


for file in tripInfoFiles:
    fileName = file[1]
    fileType = file[0]

    with open(fileName, "r") as f:
        data = f.read()

    f.close()

    tripSoup = BeautifulSoup(data, "xml")

    trips = tripSoup.find_all("tripinfo")
    
    
    for trip in trips:
        _id = trip["id"]
        vType = trip["vType"]
        _routeLength = round(float(trip["routeLength"]),2)
        emissions = trip.find("emissions")

        _CO_abs = round(float(emissions["CO_abs"]),2) 
        _CO2_abs = round(float(emissions["CO2_abs"]),2)
        _HC_abs = round(float(emissions["HC_abs"]),2)
        _PMx_abs = round(float(emissions["PMx_abs"]),2)
        _NOx_abs = round(float(emissions["NOx_abs"]),2)
        _fuel_abs = round(float(emissions["fuel_abs"]),2)
        _electricity_abs = round(float(emissions["electricity_abs"]),2)
        _simulation = fileType
        _mode = "taxi" if vType == "taxi" else "private"
        _customers = 0 if _mode == "taxi" else 1
        if _mode == "taxi":
            taxiInfo = trip.find("taxi")
            _customers = taxiInfo["customers"]


        emissionsSoup.emissionsInfo.append(emissionsSoup.new_tag("emissions", id=_id,  simulation = _simulation, mode = _mode, routeLength = _routeLength, customers=_customers, CO_abs=_CO_abs, \
                                               CO2_abs=_CO2_abs, HC_abs=_HC_abs, PMx_abs = _PMx_abs, NOx_abs = _NOx_abs, \
                                                fuel_abs = _fuel_abs, electricity_abs=_electricity_abs))
# print(emissionSoup)
f = open("output/stats/emissions.xml", "w")
f.write(emissionsSoup.prettify())
f.close()


