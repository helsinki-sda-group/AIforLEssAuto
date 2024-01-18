# %%
from bs4 import BeautifulSoup  
import pandas as pd

# %%
file = open("output/stats/emissions.xml",'r')
contents = file.read()
soup = BeautifulSoup(contents,'xml')
vehicles = soup.find_all("emissions")
print("Vehicles found: ", len(vehicles))

# %%
data = []
for vehicle in vehicles:
    id = vehicle["id"]
    simulation = vehicle["simulation"]
    mode = vehicle["mode"]
    routeLength = float(vehicle["routeLength"])
    customers = int(vehicle["customers"])
    CO_abs = float(vehicle["CO_abs"])
    CO2_abs = float(vehicle["CO2_abs"])
    HC_abs = float(vehicle["HC_abs"])
    PMx_abs = float(vehicle["PMx_abs"])
    NOx_abs = float(vehicle["NOx_abs"])
    fuel_abs = float(vehicle["fuel_abs"])
    electricity_abs = float(vehicle["electricity_abs"])
    rows = [id, simulation, mode, routeLength, customers, CO_abs, CO2_abs, HC_abs, PMx_abs, NOx_abs, fuel_abs, electricity_abs]
    data.append(rows)

df = pd.DataFrame(data, columns=["id", "simulation", "mode", "routeLength", "customers", "CO_abs", "CO2_abs", "HC_abs", "PMx_abs", "NOx_abs", "fuel_abs", "electricity_abs"])

# %%
df.to_csv("output/stats/emissionstats.csv", sep=',', index=False, encoding='utf-8')

df_privatesim = df[df["simulation"] == "private"]
df_taxisim = df[df["simulation"] == "taxi"]

CO_private = round(df_privatesim["CO_abs"].sum(),2)
CO2_private = round(df_privatesim["CO2_abs"].sum(),2)
HC_private = round(df_privatesim["HC_abs"].sum(),2)
PMx_private = round(df_privatesim["PMx_abs"].sum(),2)
NOx_private = round(df_privatesim["NOx_abs"].sum(),2)
fuel_private = round(df_privatesim["fuel_abs"].sum(),2)
electricity_private = round(df_privatesim["electricity_abs"].sum(),2)

CO_taxi = round(df_taxisim["CO_abs"].sum(),2)
CO2_taxi = round(df_taxisim["CO2_abs"].sum(),2)
HC_taxi = round(df_taxisim["HC_abs"].sum(),2)
PMx_taxi = round(df_taxisim["PMx_abs"].sum(),2)
NOx_taxi = round(df_taxisim["NOx_abs"].sum(),2)
fuel_taxi = round(df_taxisim["fuel_abs"].sum(),2)
electricity_taxi = round(df_taxisim["electricity_abs"].sum(),2)


# %%
summaryFile = open("output/stats/summary.txt", "a")
summaryFile.write("EMISSIONS MEASURES\n")
summaryFile.write("---------------------------------------------------------------------\n")
summaryFile.write("Simulation with only private cars\n")
summaryFile.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")
summaryFile.write("Sum of CO: " + str(CO_private) + "\n")
summaryFile.write("Sum of CO2: " + str(CO2_private) + "\n")
summaryFile.write("Sum of HC: " + str(HC_private) + "\n")
summaryFile.write("Sum of PMx: " + str(PMx_private) + "\n")
summaryFile.write("Sum of NOx: " + str(NOx_private) + "\n")
summaryFile.write("Sum of fuel: " + str(fuel_private) + "\n")
summaryFile.write("Sum of electricity: " + str(electricity_private) + "\n")
summaryFile.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")
summaryFile.write("Simulation with taxis\n")
summaryFile.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")
summaryFile.write("Sum of CO: " + str(CO_taxi) + "\n")
summaryFile.write("Sum of CO2: " + str(CO2_taxi) + "\n")
summaryFile.write("Sum of HC: " + str(HC_taxi) + "\n")
summaryFile.write("Sum of PMx: " + str(PMx_taxi) + "\n")
summaryFile.write("Sum of NOx: " + str(NOx_taxi) + "\n")
summaryFile.write("Sum of fuel: " + str(fuel_taxi) + "\n")
summaryFile.write("Sum of electricity: " + str(electricity_taxi) + "\n")
summaryFile.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")
summaryFile.write("Advantage of taxis (%)\n")
summaryFile.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")
summaryFile.write("CO: " + str(round((CO_taxi-CO_private)/CO_private * -100.0,2)) + "\n")
summaryFile.write("CO2: " + str(round((CO2_taxi-CO2_private)/CO2_private * -100.0,2)) + "\n")
summaryFile.write("HC: " + str(round((HC_taxi-HC_private)/HC_private * -100.0,2))+ "\n")
summaryFile.write("PMx: " + str(round((PMx_taxi-PMx_private)/PMx_private * -100.0,2)) + "\n")
summaryFile.write("NOx: " + str(round((NOx_taxi-NOx_private)/NOx_private * -100.0,2)) + "\n")
summaryFile.write("fuel: " + str(round((fuel_taxi-fuel_private)/fuel_private * -100.0,2)) + "\n")
# summaryFile.write("electricity: " + str(round((electricity_taxi-electricity_private)/electricity_private * 100.0,2)) + "\n")
summaryFile.write("---------------------------------------------------------------------\n")
summaryFile.close()

# %%


# %%













