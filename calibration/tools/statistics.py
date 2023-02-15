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
    SUMO_DETECTOR_OUTPUT_DIR = "sumo_files/simulation_output/detector_outputs"
    print("SUMO detector output directory defaulted to {}.".format(SUMO_DETECTOR_OUTPUT_DIR))
detectionData = getRealRoadStationData()
COLUMNS = ["real", "SUMO", "MAPE"]
TIME_OF_DAY = "morning"
DIR_1 = "dir1"
DIR_2 = "dir2"


def main():
    df = pd.DataFrame(columns=COLUMNS)
    for stationName in detectionData.keys():
        if detectionsInBothDirections(detectionData, stationName):
            df = statisticsProcedure(df, stationName, "_1_output.xml", DIR_1, "_1")
            df = statisticsProcedure(df, stationName, "_2_output.xml", DIR_2, "_2")
    df["RMSE"] = np.append(np.array(calculateRMSE(df)), np.full((len(df["MAPE"])-1), np.nan))
    df.to_excel(OUTPUT_FILE)


def detectionsInBothDirections(detectionData, stationName):
    detectionsInDir1 = detectionData[stationName][TIME_OF_DAY][DIR_1] != 0
    detectionsInDir2 = detectionData[stationName][TIME_OF_DAY][DIR_2] != 0
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
    realCounts = detectionData[stationName][TIME_OF_DAY][direction]
    sumoCounts = getSumoCounts(stationFile)
    absPercError = abs(realCounts - sumoCounts) / realCounts
    
    dfRow = pd.DataFrame(np.array([[realCounts, sumoCounts, absPercError]]), index=[stationName + dirTail], columns=COLUMNS)
    return dfRow

def getSumoCounts(stationFile):
    sumoStationsCounts = countVehicles(stationFile)
    return sumoStationsCounts

def countVehicles(file):
    tree = ET.parse(file) 
    root = tree.getroot()
    vehicles = 0
    for interval in root:
        vehicles += int(interval.attrib["nVehContrib"])
    return vehicles

def calculateRMSE(df):
    rmse = math.sqrt(sum(df["MAPE"]**2) / len(df["MAPE"]))
    return rmse

    
if __name__ == '__main__':
    sys.exit(main())