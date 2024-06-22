# ----------------------------------------------------------------------
# Copyright (c) 2023 University of Helsinki SDA group
# @file    statistics.py
# @author  Anton Taleiko
# @date    Wed Feb 15 2023
# ----------------------------------------------------------------------

# launch command for reduced simulation stats: (run with sumo-hki-cm as working directory)
# python3 calibration/tools/statistics.py

import sys
import os
import json
import glob
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import math

def getRealRoadStationData():
    with open(REAL_ROAD_STATION_DETECTIONS_FILE, "r") as f:
        roadStationData = json.load(f)
    return roadStationData

REAL_ROAD_STATION_DETECTIONS_FILE = "calibration/data/road_station_detections.json"
try:
    OUTPUT_FILE = "calibration/data/real_world_comparison_sc_{}_2021.xlsx".format(sys.argv[1])
except:
    OUTPUT_FILE = "calibration/data/real_world_comparison.xlsx"
try:
    SUMO_DETECTOR_OUTPUT_DIR = sys.argv[2]
    print("SUMO detector count directory set to {}.".format(SUMO_DETECTOR_OUTPUT_DIR))
except:
    SUMO_DETECTOR_OUTPUT_DIR = "sumo_files/output/simulation/reduced_detector_outputs"
    print("SUMO detector output directory defaulted to {}.".format(SUMO_DETECTOR_OUTPUT_DIR))
detectionData = getRealRoadStationData()
DETECTORS_STATS_COLUMNS = ["real", "SUMO", "MAPE", "GEH"]
OD_STATS_COLUMNS = ["FromTaz", "ToTaz", "Real", "SUMO", "diff"]
TIME_OF_DAY = "morning"
SUBTIME_OF_DAY = "mid"
DIR_1 = "dir1"
DIR_2 = "dir2"
BEGIN_SUMO_COUNT_TIME = 0
END_SUMO_COUNT_TIME = 111607984


def main():
    df = pd.DataFrame(columns=DETECTORS_STATS_COLUMNS)
    for stationName in detectionData.keys():
        if detectionsInBothDirections(detectionData, stationName):
            df = statisticsProcedure(df, stationName, "_1_output.xml", DIR_1, "_1")
            df = statisticsProcedure(df, stationName, "_2_output.xml", DIR_2, "_2")
    df["RMSE"] = np.append(np.array(calculateRMSE(df)), np.full((len(df["MAPE"])-1), np.nan))
    df = addSumRow(df)

    # OD_df = createODStats()

    with pd.ExcelWriter(OUTPUT_FILE) as writer:
        df.to_excel(writer, sheet_name="Detectors")
        #OD_df.to_excel(writer, sheet_name="OD") 


def calculateGEH(m, c):
    if m + c == 0:
        return 0
    else:
        return math.sqrt(2 * (m - c) * (m - c) / (m + c))


def detectionsInBothDirections(detectionData, stationName):
    detectionsInDir1 = detectionData[stationName][TIME_OF_DAY][SUBTIME_OF_DAY][DIR_1] != 0
    detectionsInDir2 = detectionData[stationName][TIME_OF_DAY][SUBTIME_OF_DAY][DIR_2] != 0
    return detectionsInDir1 & detectionsInDir2


def statisticsProcedure(df, stationName, fileTail, direction, dirTail):
    stationFile1Search = stationFileSearch(stationName, fileTail)
    if len(stationFile1Search) != 0:
        dfRow = createStationStatistics(stationName, stationFile1Search[0], direction, dirTail)
        return pd.concat([df, dfRow])
    return df


def stationFileSearch(stationName, tail):
    return glob.glob(os.path.join(SUMO_DETECTOR_OUTPUT_DIR, stationName + tail))


def createStationStatistics(stationName, stationFile, direction, dirTail):
    realCounts = 0
    realCounts += detectionData[stationName][TIME_OF_DAY][SUBTIME_OF_DAY][direction]
    sumoCounts = getSumoCounts(stationFile)
    absPercError = abs(realCounts - sumoCounts) / realCounts
    geh = calculateGEH(realCounts, sumoCounts)
    
    dfRow = pd.DataFrame(np.array([[realCounts, sumoCounts, absPercError, geh]]), index=[stationName + dirTail], columns=DETECTORS_STATS_COLUMNS)
    return dfRow


def getSumoCounts(stationFile):
    sumoStationsCounts = countVehicles(stationFile)
    return sumoStationsCounts


def countVehicles(file):
    tree = ET.parse(file) 
    root = tree.getroot()
    vehicles = 0
    for interval in root:
        if shouldBeCounted(interval):  # count only certain intervals
            vehicles += int(interval.attrib["nVehContrib"])  # append vehicles
    return vehicles


def calculateRMSE(df):
    rmse = math.sqrt(sum(df["MAPE"]**2) / len(df["MAPE"]))
    return rmse


def addSumRow(df):
    totalRealCounts = np.sum(df[DETECTORS_STATS_COLUMNS[0]])
    totalSumoCounts = np.sum(df[DETECTORS_STATS_COLUMNS[1]])
    dfRow = pd.DataFrame(np.array([[totalRealCounts, totalSumoCounts, np.nan, np.nan]]), index=["sum"], columns=DETECTORS_STATS_COLUMNS)
    df = pd.concat([df, dfRow])
    return df


# check if the interval should be counted or not based on its begin and end time
def shouldBeCounted(interval: ET.Element):
    # get the begin and end time of sumo interval and
    begin = float(interval.attrib["begin"])
    end = float(interval.attrib["end"])

    # check if it's within the counting time
    return begin >= BEGIN_SUMO_COUNT_TIME and end <= END_SUMO_COUNT_TIME

    
# def createODStats():
#     # Parse the XML data
#     realCounts = getODCounts(REAL_TAZRELATIONS_FILE)
#     sumoCounts = getODCounts(SUMO_TAZRELATIONS_FILE)

#     # Create sets of OD pairs for both original and generated counts
#     realODs = set(realCounts.keys())
#     sumoODs = set(sumoCounts.keys())

#     # Create common dictionary with all OD pairs present either in original or generated counts
#     # Format: (from, to): {'real': 321, 'sumo': 213}
#     allODCounts = dict.fromkeys(realODs.union(sumoODs))
#     for ODPair in allODCounts.keys():
#         original = 0 if ODPair not in realCounts else realCounts[ODPair]
#         generated = 0 if ODPair not in sumoCounts else sumoCounts[ODPair]

#         allODCounts[ODPair] = {'real': original, 'sumo': generated}

#     # generate columns of the resulting dataframe
#     originsList = []
#     destinationsList = []
#     realCountsList = []
#     sumoCountsList = []
#     diffList = []

#     for (fromTaz, toTaz), counts in allODCounts.items():
#         originsList.append(fromTaz)
#         destinationsList.append(toTaz)
#         realCountsList.append(counts['real'])
#         sumoCountsList.append(counts['sumo'])
#         diffList.append(abs(counts['real'] - counts['sumo']))

#     # create and return the dataframe
#     df = pd.DataFrame({
#         OD_STATS_COLUMNS[0]: originsList,
#         OD_STATS_COLUMNS[1]: destinationsList,
#         OD_STATS_COLUMNS[2]: realCountsList,
#         OD_STATS_COLUMNS[3]: sumoCountsList,
#         OD_STATS_COLUMNS[4]: diffList
#     })

#     # add sum row to the bottom
#     df.loc[len(df.index)] = ['sum', None, np.sum(df[OD_STATS_COLUMNS[2]]), np.sum(df[OD_STATS_COLUMNS[3]]), np.sum(df[OD_STATS_COLUMNS[4]])] 
#     return df


# def getODCounts(tazRelationsFile: str):
#     root = ET.parse(tazRelationsFile).getroot()

#     uniquePairs = {}

#     for interval in root.iter("interval"):
#         for tazRelation in interval.iter("tazRelation"):
            
#             fromTaz = tazRelation.get("from")
#             toTaz = tazRelation.get("to")
#             count = int(tazRelation.get("count"))

#             if (fromTaz, toTaz) in uniquePairs.keys():  # one interval contains duplicate od pairs (should not happen)
#                 uniquePairs[((fromTaz, toTaz))] += count
#             else:
#                 uniquePairs[(fromTaz, toTaz)] = count

#     return uniquePairs


if __name__ == '__main__':
    sys.exit(main())