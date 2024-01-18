# %%
from bs4 import BeautifulSoup  
import pandas as pd

# %%
file = open("output/stats/taxis.xml",'r')
contents = file.read()
soup = BeautifulSoup(contents,'xml')
file.close()
taxis = soup.find_all("taxi")
print("Taxis found: ", len(taxis))

# %%
data = []
for taxi in taxis:
    id = taxi["id"]
    customers = int(taxi["customers"])
    fullDistance = float(taxi["fullDistance"])
    fullTime = int(taxi["fullTime"])
    idleDistance = float(taxi["idleDistance"])
    idleDistanceRatio = float(taxi["idleDistanceRatio"])
    idleTime = int(taxi["idleTime"])
    idleTimeRatio = float(taxi["idleTimeRatio"])
    occupancyRate = float(taxi["occupancyRate"])
    occupiedDistance = float(taxi["occupiedDistance"])
    occupiedTime = int(taxi["occupiedTime"])
    rows = [id, customers, occupancyRate, fullDistance, occupiedDistance, idleDistance, idleDistanceRatio, fullTime, occupiedTime, idleTime, idleTimeRatio]
    data.append(rows)

df = pd.DataFrame(data, columns=["id", "customers", "occupancyRate", "fullDistance", "occupiedDistance", "idleDistance", "idleDistanceRatio", "fullTime", "occupiedTime", "idleTime", "idleTimeRatio"])

# %%
df.to_csv("output/stats/taxistats.csv", sep=',', index=False, encoding='utf-8')

df_shared = df[df["occupancyRate"] > 1]
df_nonshared = df[df["occupancyRate"] == 1]

# %%
summaryFile = open("output/stats/summary.txt", "a")
summaryFile.write("TAXI FLEET USAGE MEASURES\n")
summaryFile.write("---------------------------------------------------------------------\n")
summaryFile.write("Total number of taxis: " + str(len(taxis)) + "\n")
summaryFile.write("Number of taxis with ride-sharing: " + str(len(df_shared)) + "\n")
summaryFile.write("Number of taxis without ride-sharing: " + str(len(df_nonshared)) + "\n")
summaryFile.write("---------------------------------------------------------------------\n")
summaryFile.write("All taxis\n")
summaryFile.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")
summaryFile.write("Average number of customers: " + str(round(df["customers"].mean(),2)) + "\n")
summaryFile.write("Average occupancy rate: " + str(round(df["occupancyRate"].mean(),2)) + "\n")
summaryFile.write("Average idle distance ratio: " + str(round(df["idleDistanceRatio"].mean(),2)) + "\n")
summaryFile.write("Average idle time ratio: " + str(round(df["idleTimeRatio"].mean(),2)) + "\n")
summaryFile.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")
summaryFile.write("Taxi with ride-sharing\n")
summaryFile.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")
summaryFile.write("Average number of customers: " + str(round(df_shared["customers"].mean(),2)) + "\n")
summaryFile.write("Average occupancy rate: " + str(round(df_shared["occupancyRate"].mean(),2)) + "\n")
summaryFile.write("Average idle distance ratio: " + str(round(df_shared["idleDistanceRatio"].mean(),2)) + "\n")
summaryFile.write("Average idle time ratio: " + str(round(df_shared["idleTimeRatio"].mean(),2)) + "\n")
summaryFile.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")
summaryFile.write("Taxi without ride-sharing\n")
summaryFile.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")
summaryFile.write("Average number of customers: " + str(round(df_nonshared["customers"].mean(),2)) + "\n")
summaryFile.write("Average occupancy rate: " + str(round(df_nonshared["occupancyRate"].mean(),2)) + "\n")
summaryFile.write("Average idle distance ratio: " + str(round(df_nonshared["idleDistanceRatio"].mean(),2)) + "\n")
summaryFile.write("Average idle time ratio: " + str(round(df_nonshared["idleTimeRatio"].mean(),2)) + "\n")
summaryFile.write("---------------------------------------------------------------------\n")
summaryFile.close()

# %%



