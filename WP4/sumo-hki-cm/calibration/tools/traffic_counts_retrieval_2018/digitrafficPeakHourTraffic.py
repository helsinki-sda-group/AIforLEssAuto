import sys
import os
import math
import pandas as pd
import numpy as np
import json
import csv
import concurrent.futures
import dataclasses
from dataclasses import dataclass

def calculateTimeNumber(hour, min, sec, milli):
    return hour * 216000 + min * 3600 + sec * 60 + milli

MORNING_BEG = calculateTimeNumber(7, 20, 0, 0)
MORNING_END = calculateTimeNumber(8, 19, 0, 0)

DAY_BEG = calculateTimeNumber(9, 0, 0, 0)
DAY_END = calculateTimeNumber(15, 0, 0, 0)

EVENING_BEG = calculateTimeNumber(15, 30, 0, 0)
EVENING_END = calculateTimeNumber(16, 30, 0, 0)

DIGITRAFFIC_DATA_DIR = "WP4/sumo-hki-cm/calibration/data/digitraffic_2018"
DATE_DIRECTORIES = os.listdir(DIGITRAFFIC_DATA_DIR)
STATIONS_FILE = "WP4/sumo-hki-cm/calibration/data/digitraffic_detectors.csv"
OUTPUT_ALL_DAYS_FILE = "WP4/sumo-hki-cm/calibration/data/road_station_detections_daily.json"
OUTPUT_AVG_FILE = "WP4/sumo-hki-cm/calibration/data/road_station_detections_2.json"

REPLACEMENTS = {"ä": "a", "Ä": "A", "ö": "o", "Ö": "O"}
HOUR_COL = 3
MINUTE_COL = 4
DIRECTION_COL = 9
VEH_CLASS_COL = 10
ACCEPTED_VEHICLES = set([1, 6, 7])
COLUMNS = range(16)

HOUR_COL = 3
MIN_COL = 4
SEC_COL = 5
MILLI_COL = 6


@dataclass
class TimeIntervalCounts:
    dir1: int = 0
    dir2: int = 0

    def __add__(a, b):
        return TimeIntervalCounts(
            a.dir1 + b.dir1, 
            a.dir2 + b.dir2
        )
    
    def avg(self, days: int):
        return TimeIntervalCounts(
            dir1=math.floor(self.dir1 / days),
            dir2=math.floor(self.dir2 / days)
        )


@dataclass
class Counts:
    morning: TimeIntervalCounts = TimeIntervalCounts()
    day: TimeIntervalCounts = TimeIntervalCounts()
    evening: TimeIntervalCounts = TimeIntervalCounts()

    def __add__(a, b):
        return Counts(
            a.morning + b.morning, 
            a.day + b.day, 
            a.evening + b.evening
        )
    
    def avg(self, days: int):
        return Counts(
            morning=self.morning.avg(days),
            day=self.day.avg(days),
            evening=self.evening.avg(days)
        )
        

def main():
    avgResults = {}
    detectors = getDetectors()
    dailyResults = {}

    for detector in detectors:
        print("Gathering averages for station", detector["tmsId"])
        totalCounts, dailyCounts, nDays = countVehiclesInFiles(detector["tmsId"])
        averages = getAverages(totalCounts, nDays)
        transformDailyCounts(dailyCounts)
        safeName = createSafeName(detector["name"])
        detectorResults = dataclasses.asdict(averages)
        print("Adding results to dict for", detector["tmsId"])
        avgResults[safeName] = detectorResults
        dailyResults[safeName] = dailyCounts
    writeResults(avgResults, OUTPUT_AVG_FILE)
    writeResults(dailyResults, OUTPUT_ALL_DAYS_FILE)


def transformDailyCounts(dailyCounts):
    for key in dailyCounts:
        dailyCounts[key] = dataclasses.asdict(dailyCounts[key])

# calculate average daily traffic counts for a specific TMS station
def getAverages(totalCounts: Counts, nDays: int) -> Counts:
    # print("Gathering averages for station", tmsId)
    if nDays == 0:  # avoid division by 0 error
        return Counts()
    print("Calculating averages")
    return totalCounts.avg(nDays)


# return traffic counts for a specific digitraffic TMS station for all days
def countVehiclesInFiles(tmsId):

    totalCounts = Counts()
    dailyCounts = {}
    days = 0
    root_dir = os.listdir(DIGITRAFFIC_DATA_DIR)
    root_dir.sort()  # sort so that folders are sorted by name for a more understandable console output
    for directory in root_dir:
        filePath = createDataFilePath(tmsId, directory)
        detectionDf = readDetections(filePath)
        
        # check if file is not accessible for some reason
        if detectionDf is None:
            continue

        print(filePath)
        counts = Counts()
        # print("Counting morning cars")
        counts.morning = countAllCars(detectionDf, MORNING_BEG, MORNING_END)

        # print("Counting day cars")
        counts.day = countAllCars(detectionDf, DAY_BEG, DAY_END)

        # print("Counting evening cars")
        counts.evening = countAllCars(detectionDf, EVENING_BEG, EVENING_END)

        dailyCounts[directory] = counts
        
        totalCounts += counts
        days += 1
    return totalCounts, dailyCounts, days



# count all cars in both directions from pandas dataframe in interval [begTime; endTime]
# returns TimeIntervalCounts
def countAllCars(df, begTime, endTime):
    cars = df[createTimeFilter(df, begTime, endTime)]
    carsDir1 = len(cars[cars.iloc[:,DIRECTION_COL] == 1])
    carsDir2 = len(cars) - carsDir1
    return TimeIntervalCounts(carsDir1, carsDir2)


def countDayCars(df):
    cars = df[createTimeFilter(df, DAY_BEG, DAY_END)]
    carsDir1 = len(cars[cars.iloc[:,DIRECTION_COL] == 1])
    carsDir2 = len(cars) - carsDir1
    return np.array([math.floor(carsDir1 / 6), math.floor(carsDir2 / 6)])


def countEveningCars(df):
    cars = df[createTimeFilter(df, EVENING_BEG, EVENING_END)]
    carsDir1 = len(cars[cars.iloc[:,DIRECTION_COL] == 1])
    carsDir2 = len(cars) - carsDir1
    return np.array([carsDir1, carsDir2])


def createTimeFilter(df, beg, end):
    df_time = calculateTimeNumber(df[HOUR_COL], df[MIN_COL], df[SEC_COL], df[MILLI_COL])

    return (df_time >= beg) & (df_time <= end) & (df.iloc[:,VEH_CLASS_COL].isin(ACCEPTED_VEHICLES))


def readDetections(filePath):
    df = pd.read_csv(filePath, names=COLUMNS, sep=";")

    # when the file on the digitraffic server was not found 
    # the file contains xml error message code instead of csv
    if (df.iloc[0][0] == '<?xml version="1.0" encoding="UTF-8"?>'):
        print(f"Warning: File '{filePath}' was not found on the digitraffic servers")
        return None
    
    # with open(filePath, "r") as f:
    #     fileRows = np.array([row.split(";") for row in f])
    #     df = pd.DataFrame(columns=["time", "type"])
    #     df["time"] = [calculateTimeNumber(int(fileRows[i,HOUR_COL]), int(fileRows[i,MINUTE_COL])) for i in range(len(fileRows))]
    #     df["type"] = np.array(fileRows[:,VEH_CLASS_COL])
    return df

def createDataFilePath(tmsId, directory):
    filename = "roadData_{}_{}.csv".format(tmsId, directory)
    return os.path.join(DIGITRAFFIC_DATA_DIR, "".join([directory, "/", filename]))

def getDetectors():
    with open(STATIONS_FILE, "r") as f:
        csvreader = csv.reader(f)
        stations = []
        for row in csvreader:
            stations.append({"name": row[0], "tmsId": row[1]})
    return stations

def createSafeName(name):
    return ''.join([ch if ch not in REPLACEMENTS.keys() else REPLACEMENTS[ch] for ch in name])

def outputResults(results, outputFile=OUTPUT_AVG_FILE):
    print(results)
    existingDetections = lookForExistingDetections(outputFile)
    print(existingDetections)
    updatedDetections = updateDetections(results, existingDetections)
    print(updatedDetections)
    writeResults(updatedDetections)

def writeResults(detectionStruct, outputFile=OUTPUT_AVG_FILE):
    with open(outputFile, "w") as f:
        f.write(json.dumps(detectionStruct, indent=2))

def lookForExistingDetections(outputFile=OUTPUT_AVG_FILE):
    try:
        with open(outputFile, "r") as f:
            existingDetections = json.load(f)
        return existingDetections
    except:
        return {}

def updateDetections(results, existingDetections):
    for detector in results.keys():
        existingDetections[detector] = results[detector]
    return existingDetections

if __name__ == '__main__':
    sys.exit(main())