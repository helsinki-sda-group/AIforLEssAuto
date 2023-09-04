import pandas as pd
import xml.etree.ElementTree as ET

EDGERELATIONS_1_XML = 'sumo_files/reduced_OD_undivided.xml'
EDGERELATIONS_2_XML = 'sumo_files/'
OUTPUT_EXCEL_FILE = 'sumo_files/origin_destination_matrix.xlsx'

# Parse the XML data
tree = ET.parse(EDGERELATIONS_1_XML)
root = tree.getroot()

# Create lists to store the data
origins = []
destinations = []
counts = []

uniquePairs = {}

# Extract the data from XML
for interval in root.iter("interval"):
    for tazRelation in interval.iter("tazRelation"):
        
        fromTaz = tazRelation.get("from")
        toTaz = tazRelation.get("to")
        count = int(tazRelation.get("count"))

        if (fromTaz, toTaz) in uniquePairs.keys():
            print("AAAAAAAAAAAAAAAAAAAa")

        origins.append(fromTaz)
        destinations.append(toTaz)
        counts.append(count)

        uniquePairs[(fromTaz, toTaz)] = count

# Create a pandas DataFrame
data = {
    "From": origins,
    "To": destinations,
    "Count": counts
}
df = pd.DataFrame(data)

# Save the DataFrame to Excel
df.to_excel(OUTPUT_EXCEL_FILE, index=False)