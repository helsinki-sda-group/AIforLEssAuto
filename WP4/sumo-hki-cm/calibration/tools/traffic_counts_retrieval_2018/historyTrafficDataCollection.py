from codecs import readbuffer_encode
import sys
import requests
import csv
from datetime import date, datetime
import os.path
import os
import numpy as np
import asyncio
import aiofile
import aiohttp
import re
import time
from datetime import datetime
import math

DATES_FILE = "calibration/data/collection_days_2018.txt"
DIGITRAFFIC_DETECTOR_FILE = "calibration/data/digitraffic_detectors.csv"
DETECTOR_DATA_DIR = "calibration/data/digitraffic_2018"
URL = "https://tie.digitraffic.fi/api/tms/v1/history/raw/lamraw_{}_18_{}.csv"
BATCH_SIZE = 950
WAIT_TIME = 300
URL_OUTPUT_FILE = "calibration/data/digitraffic_urls.txt"

def main():
    getDetectorData()


def getDetectorData():
    days, months, years = getCollectionDates()
    createDirectories(days, months, years)

    # urls = np.full(5, "https://tie-test.digitraffic.fi/api/tms/history/raw/lamraw_11_21_4.csv")
    urls = []
    filePaths = {}

    with open(DIGITRAFFIC_DETECTOR_FILE, "r") as f:
        detectorReader = csv.reader(f)
        urlIndex = 0
        for row in detectorReader:
            tmsId = row[1]
            for i in range(len(days)):
                numberOfDay = (date(int(years[i]), int(months[i]), int(days[i])) - date(int(years[i]) - 1, 12, 31)).days
                filePaths["".join([tmsId, "_", str(numberOfDay)])] = createFilePath(tmsId, days[i], months[i], years[i])
                detectorLink = URL.format(tmsId, numberOfDay)
                # urls[urlIndex] = detectorLink
                urls.append(detectorLink)
                urlIndex += 1

    writeUrlsToFile(urls)

    sema = asyncio.BoundedSemaphore(10)

    async def fetchFile(url):
        tmsId, numberOfDay = re.findall(r"_([-]*[0-9]*)_[0-9]*_([0-9]*)", url)[0]
        filePath = filePaths["".join([tmsId, "_", numberOfDay])]
        async with sema, aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                # assert resp.status == 200
                data = await resp.read()

        async with aiofile.async_open(
            filePath, "wb"
        ) as outfile:
            await outfile.write(data)

    print("Gathering traffic information...")
    loop = asyncio.get_event_loop()
    tasks = [loop.create_task(fetchFile(url)) for url in urls]
    loop.run_until_complete(asyncio.wait(tasks))
    loop.close()


def writeUrlsToFile(urls):
    with open(URL_OUTPUT_FILE, "w") as f:
        for url in urls:
            f.write(url + "\n")

def createFilePathKey(tmsIdAndDay):
    return "".join([tmsIdAndDay[0], "_", tmsIdAndDay[1]])


def createFilePath(tmsId, day, month, year):
    datestr = "_".join([str(year), str(month), str(day)])
    directoryPath = os.path.join(os.getcwd(), DETECTOR_DATA_DIR, "{}_{}_{}".format(year, month, day))
    return os.path.join(directoryPath, "roadData_{}_{}.csv".format(tmsId, datestr))

def createDirectories(days, months, years):
    currDir = os.getcwd()
    dataDir = os.path.join(currDir, DETECTOR_DATA_DIR)
    createDirectory(dataDir)
    for i in range(len(days)):
        datestr = "_".join([str(years[i]), str(months[i]), str(days[i])])
        dateDirectory = os.path.join(dataDir, "{}/".format(datestr))
        createDirectory(dateDirectory)

def createDirectory(directoryPath):
    if not os.path.isdir(directoryPath):
        os.mkdir(directoryPath)

def getCollectionDates():
    days, months, years = initializeDateArrays()

    with open(DATES_FILE, "r") as f:
        line = f.readline()
        for n in range(len(days)):
            dateParts = line.split(".")
            days[n] = dateParts[0]
            months[n] = dateParts[1]
            years[n] = dateParts[2]
            line = f.readline()

    return days, months, years

def initializeDateArrays():
    with open(DATES_FILE, "r") as f:
        ndays = f.read().count("\n")
        days = np.full(ndays, "00")
        months = np.full(ndays, "00")
        years = np.full(ndays, "0000")
    return days, months, years


if __name__ == '__main__':
    sys.exit(main())