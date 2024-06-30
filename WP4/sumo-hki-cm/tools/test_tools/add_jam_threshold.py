
import xml.etree.ElementTree as ET

def indent(elem, level=0):
    """In-place indentation for pretty-printing an XML element tree."""
    i = "\n" + "    " * level  # Each level adds 4 spaces
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "    "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for child in elem:
            indent(child, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if not elem.tail or not elem.tail.strip():
            elem.tail = i


# Example XML data, replace with the actual file or string
net = 'WP4/sumo-hki-cm/sumo_files/data/reduced_cut_area_2_tl_fixed.net.xml'

# Parse the XML data
root = ET.parse(net)

# Find all tlLogic elements with type="actuated"
#actuated_elements = root.findall(".//tlLogic[@type='actuated']")

# Find all edges
edges = root.findall(".//edge")

print(len(edges))

# Display the attributes of the actuated elements

# print(len(actuated_elements))
# for element in actuated_elements:
#     param = ET.Element("param", {"key": "jam-threshold", "value": "30"})
#     element.append(param)

# for element in actuated_elements:
#     indent(element)
#     print(ET.tostring(element, encoding='unicode').strip())



# root.write(net, encoding='utf-8', xml_declaration=True)