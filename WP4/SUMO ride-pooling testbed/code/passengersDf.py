# %%
from bs4 import BeautifulSoup  
import pandas as pd

# %%
file = open("output/stats/passengers.xml",'r')
contents = file.read()


# %%
soup = BeautifulSoup(contents,'xml')
file.close()

# %%
persons = soup.find_all("person")
print("Passengers found: ", len(persons))

# %%


# %%


# %%
data = []
for person in persons:
    id = person["id"]
    privateDuration = float(person["privateDuration"])
    taxiDuration = float(person["taxiDuration"])
    detourTime = float(person["detourTime"])
    detourTimePerc = float(person["detourTimePerc"])
    privateRouteLength = float(person["privateRouteLength"])
    taxiRouteLength = float(person["taxiRouteLength"])
    detourDistance = float(person["detourDistance"])
    detourDistancePerc = float(person["detourDistancePerc"])
    sharedRide = person["sharedRide"]
    taxiDepartDelay = int(float(person["taxiDepartDelay"]))
    mode = person["mode"]
    unfinishedTrip = person["unfinishedTrip"]
    unstartedTrip = person["unstartedTrip"]
    rows = [id, privateDuration, taxiDuration, detourTime, detourTimePerc, privateRouteLength, taxiRouteLength, detourDistance, detourDistancePerc,  sharedRide, unfinishedTrip, unstartedTrip, taxiDepartDelay, mode]
    data.append(rows)

df = pd.DataFrame(data, columns=['id', 'privateDuration', 'taxiDuration', 'detourTime', 'detourTimePerc', 'privateDistance', 'taxiDistance', 'detourDistance', 'detourDistancePerc',  'sharedRide', 'unfinishedTrip', 'unstartedTrip', 'taxiDepartDelay', 'mode'])

# %%
df["taxiTripTime"] = df["taxiDuration"] + df["taxiDepartDelay"]
df["taxiPrivateCoeff"] = round((df["taxiTripTime"] - df["privateDuration"]) / df["privateDuration"] * 100, 2)

# %%


# %%
df_shared = df[(df["sharedRide"] == "True") & (df["mode"]=="taxi") & (df["unfinishedTrip"]=="False")]
df_nonshared = df[(df["sharedRide"] == "False") & (df["mode"]=="taxi") & (df["unfinishedTrip"]=="False")]
df_private = df[df["mode"] == "private"]
df_alltaxi = df[df["mode"]=="taxi"]
df_taxi = df[(df["mode"]=="taxi") & (df["unfinishedTrip"]=="False")]
df_taxi_unfinished = df[(df["mode"]=="taxi") & (df["unfinishedTrip"]=="True")]
df_taxi_unstarted = df[(df["mode"]=="taxi") & (df["unstartedTrip"]=="True")]


df.to_csv("output/stats/passengerstats.csv", sep=',', index=False, encoding='utf-8')

# %%
summaryFile = open("output/stats/summary.txt", "a")
summaryFile.write("PASSENGER SATISFACTION MEASURES\n")
summaryFile.write("---------------------------------------------------------------------\n")
summaryFile.write("All taxi passengers: " + str(len(df_alltaxi)) + "\n")
summaryFile.write("Passengers with finished trips: " + str(len(df_taxi))+ "\n")
summaryFile.write("Including ride-shared trips: " + str(len(df_shared))+ "\n")
summaryFile.write("Including trips without ride-sharing: " + str(len(df_nonshared))+ "\n")
summaryFile.write("Passengers with unfinished trips: " + str(len(df_taxi_unfinished))+ "\n")
summaryFile.write("Passengers with unstarted trips: " + str(len(df_taxi_unstarted))+ "\n")
summaryFile.write("---------------------------------------------------------------------\n")
summaryFile.write("Taxi passengers\n")
summaryFile.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")
summaryFile.write("Average waiting time: " + str(round(df_taxi["taxiDepartDelay"].mean(),2)) + "\n")
summaryFile.write("Average detour time: " + str(round(df_taxi["detourTime"].mean(),2)) + "\n")
summaryFile.write("Average detour time (%): " + str(round(df_taxi["detourTimePerc"].mean(),2)) + "\n")
summaryFile.write("Average detour distance: " + str(round(df_taxi["detourDistance"].mean(),2)) + "\n")
summaryFile.write("Average detour distance (%): " + str(round(df_taxi["detourDistancePerc"].mean(),2)) + "\n")
summaryFile.write("Excessive taxi trip time (%): " + str(round(df_taxi["taxiPrivateCoeff"].mean(),2)) + "\n")
summaryFile.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")
summaryFile.write("Shared taxi passengers\n")
summaryFile.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")
summaryFile.write("Average waiting time: " + str(round(df_shared["taxiDepartDelay"].mean(),2)) + "\n")
summaryFile.write("Average detour time: " + str(round(df_shared["detourTime"].mean(),2)) + "\n")
summaryFile.write("Average detour time (%): " + str(round(df_shared["detourTimePerc"].mean(),2)) + "\n")
summaryFile.write("Average detour distance: " + str(round(df_shared["detourDistance"].mean(),2)) + "\n")
summaryFile.write("Average detour distance (%): " + str(round(df_shared["detourDistancePerc"].mean(),2)) + "\n")
summaryFile.write("Excessive taxi trip time (%): " + str(round(df_shared["taxiPrivateCoeff"].mean(),2)) + "\n")
summaryFile.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")
summaryFile.write("Non-shared taxi passengers\n")
summaryFile.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")
summaryFile.write("Average waiting time: " + str(round(df_nonshared["taxiDepartDelay"].mean(),2)) + "\n")
summaryFile.write("Average detour time: " + str(round(df_nonshared["detourTime"].mean(),2)) + "\n")
summaryFile.write("Average detour time (%): " + str(round(df_nonshared["detourTimePerc"].mean(),2)) + "\n")
summaryFile.write("Average detour distance: " + str(round(df_nonshared["detourDistance"].mean(),2)) + "\n")
summaryFile.write("Average detour distance (%): " + str(round(df_nonshared["detourDistancePerc"].mean(),2)) + "\n")
summaryFile.write("Excessive taxi trip time (%): " + str(round(df_nonshared["taxiPrivateCoeff"].mean(),2)) + "\n")
summaryFile.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")
summaryFile.write("Private car passengers\n")
summaryFile.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")
summaryFile.write("Average waiting time: " + str(round(df_private["taxiDepartDelay"].mean(),2)) + "\n")
summaryFile.write("Average detour time: " + str(round(df_private["detourTime"].mean(),2)) + "\n")
summaryFile.write("Average detour time (%): " + str(round(df_private["detourTimePerc"].mean(),2)) + "\n")
summaryFile.write("Average detour distance: " + str(round(df_private["detourDistance"].mean(),2)) + "\n")
summaryFile.write("Average detour distance (%): " + str(round(df_private["detourDistancePerc"].mean(),2)) + "\n")
summaryFile.write("Excessive taxi trip time (%): " + str(round(df_private["taxiPrivateCoeff"].mean(),2)) + "\n")
summaryFile.write("---------------------------------------------------------------------\n")
summaryFile.close()

# %%


# %%



# %%


# %%


# %%

# %%


# %%


# %%



