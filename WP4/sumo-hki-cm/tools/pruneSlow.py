import xml.etree.ElementTree as ET
import pandas as pd
from collections import defaultdict
from typing import DefaultDict, Tuple, Dict

BASE_DIR = 'WP4/sumo-hki-cm/'
SUMO_FILES_DIR = 'sumo_files'

def get_base_files_path(rel_path:str):
    return f'{BASE_DIR}{rel_path}'

SUMO_CONFIG = get_base_files_path(f'{SUMO_FILES_DIR}/reduced_area_geo_runner.sumocfg')
REAL_WORLD_CMP_FILE = get_base_files_path('calibration/data/real_world_comparison.xlsx')  # doesn't matter if contains valid data. Only used for retrieving the station names and real counts
SHEET_NAME = 'Detectors'

DELETE_ROUTESAMPLER_ONLY = False

root = ET.parse(SUMO_CONFIG).getroot()
INPUT_ROUTES = list(map(get_base_files_path, list(map(lambda x: f'{SUMO_FILES_DIR}/{x}', root.find(".//input/route-files").get("value").split(',')))))
SUMO_EXIT_TIMES_ROUTES = get_base_files_path(f'{SUMO_FILES_DIR}/{root.find(".//output/vehroute-output").get("value")}')
DETECTORS_FILE = get_base_files_path(f'{SUMO_FILES_DIR}/{root.find(".//input/additional-files").get("value")}')
OUTPUT_ROUTES = list(map(lambda x: x[:-8]+'_no_slow.rou.xml', INPUT_ROUTES))
OUTPUT_THEORETICAL_PERFECT_COUNTS_AFTER_PRUNING = get_base_files_path('calibration/data/theoretical_perfect_counts_after_pruning.xml')


def keep_fast_that_visit_everything_in_time(routes_file, output_file, detector_edges):
    # keep fast routes
    vehs_tree = ET.parse(routes_file)
    vehs_root = vehs_tree.getroot()
    total_vehs = len(vehs_root)
    
    fast = set()
    total_slow_pruned_detections = 0
    total_inactive_pruned_vehicles = 0

    for vehicle in vehs_root:
        depart = float(vehicle.get('depart'))
        visited_detectors = 0
        visited_detectors_in_time = 0
        arrival = depart
        is_fast = True

        route = vehicle[0]
        edges = route.get('edges').split()

        exit_times = [float(t) for t in route.get('exitTimes').split()]
        for edge_id, exit_time in zip(edges, exit_times):
            if edge_id in detector_edges:
                visited_detectors += 1

                # if at least one detector edge was not visited completely until the end of the simulation, route is slow
                if exit_time > 3600:
                    is_fast = False

        if is_fast and visited_detectors != 0:  # if at least one detector is visited and the vehicle is fast (visits all detectors in time)
            fast.add((vehicle.get('id')))
        elif visited_detectors == 0:
            total_inactive_pruned_vehicles += 1
        else:
            total_slow_pruned_detections += visited_detectors
            

    fast_elems = [veh for veh in vehs_root if veh.get('id') in fast]
    vehs_root[:] = fast_elems
    #vehs_tree.write(output_file)
    print('Pruned', total_vehs - len(fast) - total_inactive_pruned_vehicles, 'slow vehicles, which made up', total_slow_pruned_detections, 'detections. Also pruned', total_inactive_pruned_vehicles, 'inactive vehicles.')
         

def find_routes_without_special_roads_or_slow(special_roads:list[str], xml_file=SUMO_EXIT_TIMES_ROUTES) -> list[str]:
    routes_without_special_roads = []

    tree = ET.parse(xml_file)
    root = tree.getroot()

    # purely for some stats
    routesampler_route_lens = []

    for vehicle in root.findall("./vehicle"):
        vehicle_id = vehicle.get("id")

        # check if vehID is from routesampler
        if DELETE_ROUTESAMPLER_ONLY and not vehicle_id.startswith('rs'):
            continue

        exit_times = [float(t) for t in vehicle.find("./route").get("exitTimes").split()]
        edges = vehicle.find("./route").get("edges").split()

        has_special_road = False

        routesampler_route_lens.append(len(edges))
        for road_id, exit_time in zip(edges, exit_times):
            if road_id in special_roads and exit_time < 3600.0:
                has_special_road = True

                break

        if not has_special_road:
            routes_without_special_roads.append(vehicle_id)

    avg_routesampler_route_len = sum(routesampler_route_lens) / len(routesampler_route_lens)
    print('average route length:', avg_routesampler_route_len)
    
    return routes_without_special_roads


def get_station_edges(input_file=REAL_WORLD_CMP_FILE, sheet_name = SHEET_NAME) -> Tuple[list[str], Dict[str, Tuple[int, str]]]:
    '''
    we want to get only those stations that are actually present in the final comparison file
    some stations might be ommited from the stats file because the data was missing
    or for some other reasons
    '''
    
    stats_df = pd.read_excel(input_file, sheet_name=sheet_name)
    station_names = []
    station_values = []
    for station_name, station_value in zip(stats_df['Unnamed: 0'][:-1], stats_df['real'][:-1]):
        station_names.append(station_name)
        station_values.append(station_value)
  
    # read xml, find edge for each station
    tree = ET.parse(DETECTORS_FILE)
    root = tree.getroot()

    station_edges = {}
    for station in station_names:
        station_induction_loop = root.find(f'./inductionLoop[@id="{station + "_0"}"]')
        station_edges[station] = station_induction_loop.get('lane')[:-2]

    station_values_dict = {}
    for station, value in zip(station_names, station_values):
        station_edge = station_edges[station]
        station_values_dict[station_edge] = (value, station)

    return list(station_edges.values()), station_values_dict


def deleteVehicles(input_file: str, output_file: str, veh_ids_to_delete: list[str], theoretical_perfect_diff_after_pruning, real_counts:Dict[str,Tuple[int,str]], special_roads:list[str]):
    '''creates a copy of a file and prints output there'''
    tree = ET.parse(input_file)
    root = tree.getroot()
    
    veh_elems_to_keep = [veh for veh in root if veh.get('id') not in veh_ids_to_delete]
    update_theoretical_perfect_counts(theoretical_perfect_diff_after_pruning, real_counts, veh_elems_to_keep, special_roads)
    root[:] = veh_elems_to_keep
    
    # with open(output_file, "wb") as f:
    #     tree.write(f)


def update_theoretical_perfect_counts(theoretical_perfect_diff_after_pruning:DefaultDict[str,int], real_counts:Dict[str,Tuple[int,str]], veh_elems:list[ET.Element], special_roads:list[str]):
    '''diff = real - SUMO'''
    
    for veh_elem in veh_elems:
        edges = veh_elem.find("./route").get("edges").split()
        for edge in edges:
            if edge in special_roads:
                theoretical_perfect_diff_after_pruning[edge] += 1

    for edge in theoretical_perfect_diff_after_pruning:
        theoretical_perfect_diff_after_pruning[edge] = real_counts[edge][0] - theoretical_perfect_diff_after_pruning[edge]


def counts_to_xml(counts_dict:DefaultDict[str,int]):
    # Create the root element
    root = ET.Element('data')

     # Create a dictionary to contain root element attributes
    interval_attributes = {
        'id': 'undefined',
        'begin': '0.00',
        'end': '3600.00'
    }

    # Create interval element and set its attributes
    interval = ET.SubElement(root, 'interval', interval_attributes)

    # Loop through the dictionary and create child elements for each entry
    for edge_id, entered in counts_dict.items():
        edge_elem = ET.SubElement(interval, 'edge')
        edge_elem.set('id', str(edge_id))
        edge_elem.set('entered', str(entered))

    # Return ElementTree object
    return ET.ElementTree(root)


if __name__ == "__main__":
    special_roads, real_counts = get_station_edges()
    routes_without_special_roads = find_routes_without_special_roads_or_slow(special_roads)

    for i, o in zip(INPUT_ROUTES, OUTPUT_ROUTES):
        keep_fast_that_visit_everything_in_time(i, o, special_roads)

    # print(f'Deleting {len(routes_without_special_roads)} vehicles...')

    # theoretical_perfect_diff_after_pruning = defaultdict(lambda: 0)
    # for i, o in zip(INPUT_ROUTES, OUTPUT_ROUTES):
    #     deleteVehicles(i, o, routes_without_special_roads, theoretical_perfect_diff_after_pruning, real_counts, special_roads)

    #counts_to_xml(theoretical_perfect_diff_after_pruning).write(OUTPUT_THEORETICAL_PERFECT_COUNTS_AFTER_PRUNING)