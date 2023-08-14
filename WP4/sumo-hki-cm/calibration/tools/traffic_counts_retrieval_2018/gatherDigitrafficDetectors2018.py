import sys
import requests
import json

# columns = ["name", "tmsNumber", "systemId", "lat", "lon", "coord3", "lat lon", "lat lon dms\n"]
OUTPUT_FILE = "calibration/data/digitraffic_detectors.csv"

def main():
    r = requests.get("https://tie.digitraffic.fi/api/tms/v1/stations")

    data = json.loads(r.text)



    f = open(OUTPUT_FILE, "w")
    # f.write(",".join(columns))
    f.write("st170_Kulosaari,155,101,23155,60.185804,24.994641,0.0,60.185804 24.994641,60°11'08\"N 24°59'40.7\"E\n")  # an old station that was not in the "stations" list because it was replaced by a new one

    for i in range(len(data["features"])):
        station = data["features"][i]

        stationId = station["id"]
        stationInfo = getStationInfo(stationId)
        if stationInfo["properties"]["municipality"] == "Helsinki" and stationInfo["properties"]["name"] != "vt4_Oulu_Intiö_LML":
            f.write(",".join([
                str(stationInfo["properties"]["name"]),
                str(stationInfo["properties"]["tmsNumber"]),
                str(i),
                str(stationInfo["geometry"]["coordinates"][1]),
                str(stationInfo["geometry"]["coordinates"][0]),
                str(stationInfo["geometry"]["coordinates"][2]),
                " ".join([str(stationInfo["geometry"]["coordinates"][1]), str(stationInfo["geometry"]["coordinates"][0])]),
                " ".join([dmsStringNorth(stationInfo["geometry"]["coordinates"][1]), dmsStringEast(stationInfo["geometry"]["coordinates"][0]) + "\n"]),
            ]))

    f.close()


def getStationInfo(station_id: str) -> str:
    print(f'getting info for station "{station_id}"')
    r = requests.get(f"https://tie.digitraffic.fi/api/tms/v1/stations/{station_id}")
    return json.loads(r.text)

def dmsStringNorth(coor):
    dms = decdeg2dms(coor)
    value = "".join([
        dms[0],
        "°",
        dms[1],
        "\'",
        dms[2],
        "\"N"
    ])
    return value

def dmsStringEast(coor):
    dms = decdeg2dms(coor)
    value = "".join([
        dms[0],
        "°",
        dms[1],
        "\'",
        dms[2],
        "\"E"
    ])
    return value


def decdeg2dms(dd):
    mult = -1 if dd < 0 else 1
    mnt,sec = divmod(abs(dd)*3600, 60)
    deg,mnt = divmod(mnt, 60)
    return twoNumbers(mult*deg, mult*mnt, mult*sec)

def twoNumbers(d, m, s):
    return (stringConversion(d), stringConversion(m), stringConversionWithDecimal(s))

def stringConversion(f):
    if str(f)[1] == ".":
        return "".join(["0", str(f)[0]])
    return str(f)[0:2]

def stringConversionWithDecimal(f):
    if str(f)[1] == ".":
        return "".join(["0", str(f)[0]])
    return str(f)[0:4]


if __name__ == '__main__':
    sys.exit(main())