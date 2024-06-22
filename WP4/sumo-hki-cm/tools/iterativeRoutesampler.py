import os
import sys
import xml.etree.ElementTree as ET
import random
import pandas as pd
from collections import defaultdict
import shutil
if 'SUMO_HOME' in os.environ:
        tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
        sys.path.append(tools)
else:   
        sys.exit("please declare environment variable 'SUMO_HOME'")
    
import sumolib

# main script parameters
CYCLES = -1 # 5 cycles is mostly enough to converge. set to -1, if you want the script to run indefinitely (you will stop it when it converges well enough for you. NOTE: it won't create a final SUMO config automatically for you if you set it to -1)
RS_ITERATIONS = 3  # how many times to sample routes using routesampler. If RUN_KEEP_FAST_ON_RS is set to False, 1 routesampler iteration is enough
DUA_STEPS = 50  # if 0, doesn't run duaiterate. if steps are less than 2, will not work because the route files won't appear in the 000 folder (because we skip the first routing)
SUMO_ITERATIONS = 2  # how many times to run sumo iterations to remove slow or inactive routes
RUN_KEEP_FAST_ON_RS = True  # if set to True, from each iteration of routesampler removes route that are too slow (don't visit all detectors) based on the provided network edges lengths and maximum speed (the arrival times will be interpolated from network)

BASE_DIR = ''
WORK_DIR = BASE_DIR + 'sumo_files/output/tools/reduced_area_routesampler_iterative_no_lanes/'

ROUTESAMPLER_DIR_NAME = 'routesampler'
DUAITERATE_DIR_NAME = 'duaiterate'
SUMO_DIR_NAME = 'sumo'
FINAL_SUMO_DIR_NAME = 'final'

# paths to input files
EDGEDATA_DIFF_FILE = BASE_DIR + 'calibration/data/reduced_edgedata_real.xml'
SHEET_NAME = 'Detectors'
ADD_FILE = BASE_DIR + 'sumo_files/data/reduced_cut.add.xml'
DUAITERATED_OD_ROUTES = BASE_DIR + 'sumo_files/output/tools/reduced_area_duaiterate_past_iterations/reduced_area_duaiterate_again_default_cut_trips_to_create_a_better_edgedata_diff_file/047/verified_cut_trips_047.rou.xml'
RANDOM_ROUTES = BASE_DIR + 'sumo_files/output/tools/reduced_area_random_trips/routes/random_routes_no_lanes.rou.xml'
NET_FILE = BASE_DIR + 'sumo_files/data/reduced_cut_area_2_tl_fixed.net.xml'


# functions that take a config file path as a parameter and return a command (probably change this if you're on windows)
get_rs_launch_command = lambda config_path: f'python3 $SUMO_HOME/tools/routeSampler.py -c {config_path}'
get_dua_launch_command = lambda config_path: f'python3 $SUMO_HOME/tools/assign/duaIterate.py -c {config_path} --skip-first-routing sumo--time-to-teleport.highways.min-speed 0 sumo--ignore-junction-blocker 1 duarouter--routing-threads 8 1>/dev/null'
get_sumo_launch_command = lambda config_path: f'sumo -c {config_path} 2>/dev/null'



# DO NOT MODIFY ANYTHING BELOW THIS COMMENT UNLESS SOMETHING DOESN'T WORK AND YOU'RE SURE THE COMMANDS ARE OK

get_rs_config_def_filename = lambda c, i: f'routesampler_c{format_number(c)}_{format_number(i)}.config.xml'
get_rs_routes_output_def_filename = lambda c, i: f'routesampler_c{format_number(c)}_{format_number(i)}_routes.rou.xml'
get_rs_fast_routes_output_def_filename = lambda c, i: f'routesampler_c{format_number(c)}_{format_number(i)}_routes_fast.rou.xml'
get_rs_mismatch_output_def_filename = lambda c, i: f'routesampler_c{format_number(c)}_{format_number(i)}_mismatch.rou.xml'

DUA_CONFIG_DEF_FILENAME = 'dua.config.xml'
DUA_NET_DEF_FILENAME = 'dua.net.xml'

get_sumo_config_def_filename = lambda c, i: f'sumo_c{format_number(c)}_{format_number(i)}.sumocfg.xml'
get_sumo_vehroute_output_def_filename = lambda c, i: f'sumo_c{format_number(c)}_{format_number(i)}_vehroute_output.rou.xml'
get_sumo_fast_routes_output_def_filename = lambda c, i: f'sumo_c{format_number(c)}_{format_number(i)}_routes_fast.rou.xml'
get_sumo_stats_output_def_filename = lambda c, i: f'sumo_c{format_number(c)}_{format_number(i)}_stats.xml'
get_sumo_errors_log_def_filename = lambda c, i: f'sumo_c{format_number(c)}_{format_number(i)}_errors.log'
SUMO_NET_DEF_FILENAME = 'sumo.net.xml'


def main():
    print(f'Using {RANDOM_ROUTES} as random routes')
    # name local input files
    local_edgedata_diff_filename = 'edgedata_real.xml'
    # local_add_file = 'detectors.add.xml'
    #local_duaiterated_od_routes_filename = 'duaiterated_od.rou.xml'
    local_random_routes_filename = 'random.rou.xml'
    local_net_filename = 'local.net.xml'
    local_add_filename = 'local.add.xml'
    output_filename = 'output.rou.xml'

    # remove output folder if it already exists
    if (os.path.isdir(WORK_DIR)):
        print(f"Directory {WORK_DIR} already exists. Aborting")
        return

    # copy input files
    create_dir_safe(WORK_DIR)
    copy_file_safe(EDGEDATA_DIFF_FILE, WORK_DIR + local_edgedata_diff_filename)
    # copy_file_safe(ADD_FILE, WORK_DIR + local_add_file)
    #copy_file_safe(DUAITERATED_OD_ROUTES, WORK_DIR + local_duaiterated_od_routes_filename)
    copy_file_safe(RANDOM_ROUTES, WORK_DIR + local_random_routes_filename)
    copy_file_safe(NET_FILE, WORK_DIR + local_net_filename)
    copy_file_safe(ADD_FILE, WORK_DIR + local_add_filename)

    # create diff file    
    stations_info = get_stations_info(WORK_DIR + local_edgedata_diff_filename)
    edges_net_info = get_edges_info(NET_FILE)
    stations_edges = set(stations_info.keys())

    # cycles loop
    cycles = sys.maxsize if (CYCLES == -1) else CYCLES 
    prev_sumo_fast_route_file = ''  # routes with fast SUMO routes from each previous cycle
    for cycle in range(cycles):
        print(f'\nCYCLE {cycle}')
        create_dir_safe(get_cycle_dir(cycle))

        # routesampler
        create_dir_safe(get_rs_dir(cycle))
        rs_iterations = RS_ITERATIONS  # how many times routesampler should run within the cycle (note that random trips will be used from 2 iteration)
        all_rs_route_files = []  # routes with fast routesampler routes from each previous iteration within current cycle
        for i in range(0, rs_iterations):
            print(f'\nRS ITERATION {i}')

            # any cycle, first iteration
            if (i == 0):
                # first cycle, first iteration:
                if (cycle == 0):
                    # use random trips as input to routeseampler
                    input_routes = WORK_DIR + local_random_routes_filename
                    # use real edgedata file as the first diff
                    prev_diff_file = WORK_DIR + local_edgedata_diff_filename
                # non-first cycle, first iteration:
                else:
                    # use diff from the previous sumo iteration
                    prev_diff_file = get_sumo_iter_dir(cycle-1, SUMO_ITERATIONS-1) + 'diff.xml'
                    # use random routes as input for the first iteration
                    input_routes = WORK_DIR + local_random_routes_filename
            # any cycle, non-first iteration
            else:
                # get diff from the previous iteration
                prev_diff_file = get_rs_iter_dir(cycle, i-1) + 'diff.xml'

                # non-first iteration, first cycle
                if (cycle == 0):
                    # get random routes for routesampler
                    input_routes = WORK_DIR + local_random_routes_filename
                # non-first iteration, non-frst cycle
                else:
                    # get random input routes for routesampler
                    input_routes = WORK_DIR + local_random_routes_filename

            rs_output_file = get_rs_iter_dir(cycle, i) + get_rs_routes_output_def_filename(cycle, i)

            # run routesampler
            run_routesampler(cycle, i, prev_diff_file, input_routes)

            # keep fast
            if RUN_KEEP_FAST_ON_RS:            
                output_routes_file = get_rs_iter_dir(cycle, i) + get_rs_fast_routes_output_def_filename(cycle, i)
                keep_fast(rs_output_file, output_routes_file, stations_edges, edges_net_info)
            else:
                output_routes_file = rs_output_file
            
            # update diff
            new_diff_file = get_rs_iter_dir(cycle, i) + 'diff.xml'
            update_diff(prev_diff_file, output_routes_file, new_diff_file)
            
            # append fast routes to the total rs route files list for the current 
            all_rs_route_files.append(output_routes_file)

        all_routes = all_rs_route_files
        if cycle != 0:  # already have sumo fast routes
            all_routes.append(prev_sumo_fast_route_file)

        # duaiterate
        if DUA_STEPS > 1:  # if 1, won't work
            print(f"\nRUNNING {DUA_STEPS} ITERATIONS OF DUAITERATE...")
            print(f"(see {get_dua_dir(cycle)}stdout.log for more details)")
            run_duaiterate(cycle, all_routes, DUA_STEPS)

            # retrieve duaiterate routes
            last_step_dua_dir = get_dua_step_dir(cycle, DUA_STEPS-1)
            duaiterate_last_step_route_files = [f'{last_step_dua_dir}{os.path.basename(f)[:-8]}_{format_number(DUA_STEPS-1)}.rou.xml' for f in all_routes]
            all_routes = [f'{last_step_dua_dir}{os.path.basename(f)[:-8]}_{format_number(DUA_STEPS-1)}_fast.rou.xml' for f in all_routes]
            duaiterate_last_step_diff_file = f'{last_step_dua_dir}_{format_number(DUA_STEPS-1)}_diff.xml'
            
            # create diff files after duaiterate (just for debugging)
            prev_diff_file = WORK_DIR + local_edgedata_diff_filename
            for r, f_r in zip(duaiterate_last_step_route_files, all_routes): 
                keep_fast(r, f_r, stations_edges, edges_net_info)
                update_diff(prev_diff_file, f_r, duaiterate_last_step_diff_file, allow_negative=True)
                
                # set prev_diff_file to the diff file if not already
                if prev_diff_file == WORK_DIR + local_edgedata_diff_filename:
                    prev_diff_file = duaiterate_last_step_diff_file

        # SUMO
        for i in range(SUMO_ITERATIONS):
            # create sumo dir
            sumo_dir = get_sumo_dir(cycle)
            create_dir_safe(sumo_dir)
            
            print(f'\nSUMO ITERATION {i}')
            if i == 0:
                sumo_input_routes = all_routes
            else:
                sumo_input_routes = [prev_sumo_fast_route_file]
            
            # prepare for sumo launch
            create_sumo_dir(
                dir_path = get_sumo_iter_dir(cycle, i),
                net_file = WORK_DIR + local_net_filename, 
                route_files = sumo_input_routes,  # change to duaiterate_last_step_route_files
                output_config_filename = get_sumo_config_def_filename(cycle, i),
                vehroute_output_filename = get_sumo_vehroute_output_def_filename(cycle, i),
                stats_output_filename = get_sumo_stats_output_def_filename(cycle, i),
                errors_log_filename = get_sumo_errors_log_def_filename(cycle, i)
                )

            # launch sumo simulation
            run_sumo(get_sumo_iter_dir(cycle, i) + get_sumo_config_def_filename(cycle, i))
        
            # prune SUMO routes
            sumo_vehroute_output_file = get_sumo_iter_dir(cycle, i) + get_sumo_vehroute_output_def_filename(cycle, i)
            
            keep_fast_output_file = get_sumo_iter_dir(cycle, i) + get_sumo_fast_routes_output_def_filename(cycle, i)
            keep_fast(sumo_vehroute_output_file, keep_fast_output_file, stations_edges)

            # keep only important attributes
            remove_bs_attrs(keep_fast_output_file, keep_fast_output_file)

            prev_sumo_fast_route_file = keep_fast_output_file


            # update SUMO diff (since in sumo we combine routes from all iterations and cycles, we create diff file from real edgedata)
            # the diff file for the last sumo iteration will be used by routesampler in the next cycle
            # the dif is calculated 
            update_diff(WORK_DIR + local_edgedata_diff_filename, keep_fast_output_file, get_sumo_iter_dir(cycle, i) + 'diff.xml')
        
    # when done, create a config file that can be used to launch the simulation and place it in the work dir
    final_routes = [get_sumo_iter_dir(CYCLES-1, SUMO_ITERATIONS-1) + get_sumo_fast_routes_output_def_filename(CYCLES-1, SUMO_ITERATIONS-1)]
    final_config_filename = 'final.sumocfg.xml'
    create_sumo_dir(
        dir_path = get_final_sumo_dir(),
        net_file = WORK_DIR + local_net_filename,
        route_files = final_routes,
        output_config_filename = final_config_filename,
        vehroute_output_filename = 'vehroute.xml',
        stats_output_filename = 'stats.xml',
        errors_log_filename = 'stderr.log',
        add_files = [WORK_DIR + local_add_filename],
        add_files_dir_name = 'reduced_detector_outputs',  # has to match the directories inside the 'file' properties of the add file you're copying
        begin=0,
        end=3600
    )
    #run_sumo(WORK_DIR + final_config_filename)

    # when done, copy the last sumo output routes to the base output folder
    # copy_file_overridable(prev_sumo_fast_route_file, WORK_DIR + output_filename)
     


def remove_bs_attrs(input_file, output_file):
    tree = ET.parse(input_file)
    root = tree.getroot()
    
    for vehicle in root:
        vehicle.attrib.pop('departLane', None)
        vehicle.attrib.pop('departSpeed', None)
        vehicle.attrib.pop('speedFactor', None)
        vehicle.attrib.pop('arrival', None)
        vehicle.set('departSpeed', 'max')
        vehicle.set('departLane', 'best')

        route = vehicle[0]
        route.attrib.pop('exitTimes', None)

    tree.write(output_file)

     
def run_routesampler(cycle, iter_number, edgedata_file, route_files:list[str]):
    # create dir for current iteration
    rs_iter_dir = get_rs_iter_dir(cycle, iter_number)
    create_dir_safe(rs_iter_dir)
    
    prefix = f'rs_c{format_number(cycle)}_i{format_number(iter_number)}_'
    seed = random.randint(0, 10**5)
    output_routes_file = rs_iter_dir + get_rs_routes_output_def_filename(cycle, iter_number)
    output_mismatch_file = rs_iter_dir + get_rs_mismatch_output_def_filename(cycle, iter_number)
    
    # create config
    config_path = rs_iter_dir + get_rs_config_def_filename(cycle, iter_number)
    config_xml_tree = create_routesampler_config(
        edgedata_file=edgedata_file, 
        route_files=[route_files],
        prefix=prefix, 
        seed=seed, 
        output_file=output_routes_file,
        mismatch_output=output_mismatch_file)
    config_xml_tree.write(config_path)
    
    # run routesampler
    os.system(get_rs_launch_command(config_path))


def run_duaiterate(cycle, route_files:list[str], steps):
    dua_dir = get_dua_dir(cycle)
    
    create_dir_safe(dua_dir)
    
    # create config
    # copy the net to avoid all the '../../../../../../' in the config
    local_net_file = dua_dir + DUA_NET_DEF_FILENAME
    copy_file_safe(NET_FILE, local_net_file)

    # copy route files to avoid the same issue and easier see all the routes used
    local_route_filenames = []  # a list of filenames will be used in dua.config.xml since dua will read files relative to its current folder
    for route_file in route_files:
        local_route_filename = os.path.basename(route_file)
        local_route_file = dua_dir + local_route_filename
        copy_file_safe(route_file, local_route_file)
        local_route_filenames.append(local_route_filename)

    config_tree = create_duaiterate_config(DUA_NET_DEF_FILENAME, local_route_filenames, 0, steps)
    config_tree.write(dua_dir + DUA_CONFIG_DEF_FILENAME)
    
    base_dir = os.getcwd()  # save curr dir
    os.chdir(dua_dir)  # switch dir
    os.system(get_dua_launch_command(DUA_CONFIG_DEF_FILENAME))  # run command
    os.chdir(base_dir)  # switch back


def create_sumo_dir(dir_path, net_file, route_files:list[str], output_config_filename, vehroute_output_filename, stats_output_filename, errors_log_filename, 
                    add_files:list[str]=None, add_files_dir_name=None, begin:float=None, end:float=None):
    # create dir for this iteration
    create_dir_safe(dir_path)
    # copy input files because same as duarouter, sumo uses path to files in its config relative to where the config is located
    # copy net
    local_net_file = dir_path + SUMO_NET_DEF_FILENAME
    copy_file_safe(net_file, local_net_file)

    # copy add files (if any)
    local_add_filenames = []
    if add_files != None:
        for add_file in add_files:
            local_add_filename = os.path.basename(add_file)
            local_add_file = dir_path + local_add_filename
            copy_file_safe(add_file, local_add_file)
            local_add_filenames.append(local_add_filename)

        # create a folder for the detector outputs
        create_dir_safe(dir_path + add_files_dir_name)

    # copy routes
    local_route_filenames = []  # a list of filenames will be used in sumo.sumocfg.xml since dua will read files relative to its current folder
    for route_file in route_files:
        local_route_filename = os.path.basename(route_file)
        local_route_file = dir_path + local_route_filename
        copy_file_safe(route_file, local_route_file)
        local_route_filenames.append(local_route_filename)


    # create sumo config (include exit times, all the fast routes from the most recent duaiterate step)
    config_tree = create_sumo_config(
        net_file = SUMO_NET_DEF_FILENAME, 
        route_files = local_route_filenames, 
        vehroute_output_file = vehroute_output_filename, 
        stats_output_file = stats_output_filename, 
        errors_log_file = errors_log_filename, 
        add_files = local_add_filenames,
        begin_f = begin, 
        end_f = end)
    config_path = dir_path + output_config_filename
    config_tree.write(config_path)
    

def run_sumo(config_path):
    os.system(get_sumo_launch_command(config_path))


def create_real_counts_xml(stations_info, output_file):
    edges_real_counts = {}
    for station_info in stations_info.values():
        edge = station_info['edge']
        real = station_info['real']
        edges_real_counts[edge] = real

    tree = counts_to_xml(edges_real_counts)
    tree.write(output_file)


def get_stations_info(edgedata_real):
    '''
    we want to get only those stations that are actually present in the final comparison file
    some stations might be ommited from the stats file because the data was missing
    or for some other reasons
    '''
    
    ed_tree = ET.parse(edgedata_real)
    ed_root = ed_tree.getroot()

    stations_info = {}
    for ed in ed_root[0]:
        stations_info[ed.get('id')] = ed.get('entered')

    # read xml, find edge for each station
    # tree = ET.parse(add_file)
    # root = tree.getroot()

    # for station_name in stations_info:
    #     station_induction_loop = root.find(f'./inductionLoop[@id="{station_name + "_0"}"]')
    #     stations_info[station_name]['edge'] = station_induction_loop.get('lane')[:-2]

    return stations_info


def keep_fast(routes_file, output_file, detector_edges, edges_info=None):
    '''
    if no edges_info dictionary provided, will assume the routes have exit times specified at the end 
    (as in SUMO simulation output)
    '''
    use_exit_times = edges_info == None

    # keep fast routes
    vehs_tree = ET.parse(routes_file)
    vehs_root = vehs_tree.getroot()
    total_vehs = len(vehs_root)
    
    fast = set()
    total_inactive_pruned_vehicles = 0

    for vehicle in vehs_root:
        depart = float(vehicle.get('depart'))
        visited_detectors = 0
        not_visited_detectors = 0
        arrival = depart
        route = vehicle[0]
        edges = route.get('edges').split()

        saved_edges = []

        if use_exit_times:
            exit_times = [float(t) for t in route.get('exitTimes').split()]
            for edge_id, exit_time in zip(edges, exit_times):
                if exit_time >= 3600:
                    if edge_id in detector_edges:  # save the detectors that were not visited in time
                        not_visited_detectors += 1
                else:  # exit_time < 3600
                    saved_edges.append(edge_id)
                    if edge_id in detector_edges:
                        visited_detectors += 1

        else:  # extrapolate exit times (the routes come from routesampler)
            for edge in edges:
                edge_info = edges_info[edge]
                
                # detector edge should be visited completely before the simulation end
                arrival += edge_info['length'] / edge_info['speed']
                
                if arrival >= 3600:
                    if edge in detector_edges:
                        not_visited_detectors += 1
                else:  # arrival time < 3600
                    saved_edges.append(edge)
                    if edge in detector_edges:
                        visited_detectors += 1
        
        # keep only edges visited within one hour
        vehicle[0].set('edges', ' '.join(saved_edges))

        if visited_detectors != 0:  # if at least one detector is visited and the vehicle is saved
            fast.add((vehicle.get('id')))
        else:
            total_inactive_pruned_vehicles += 1
            
    fast_elems = [veh for veh in vehs_root if veh.get('id') in fast]
    vehs_root[:] = fast_elems
    vehs_tree.write(output_file)
    print(f'Pruned {total_vehs - len(fast)} vehicles, which made up {not_visited_detectors} detections')
            

def update_diff(prev_diff_file, new_saved_routes_file, output_file, allow_negative=False):
    '''
    diff_1 = real - saved_1
    diff_2 = real - saved_1 - saved_2 = diff_1 - saved_2
    (saved routes file for current iteration should already exist)
    '''

    # get prev diff counts for each edge as a dictionary
    prev_diff_tree = ET.parse(prev_diff_file)
    prev_diff_root = prev_diff_tree.getroot()
    prev_diff_counts = {}
    for edge_elem in prev_diff_root[0]:
        prev_diff_counts[edge_elem.get('id')] = int(edge_elem.get('entered'))

    # get saved routes from current iteration
    veh_tree = ET.parse(new_saved_routes_file)
    veh_root = veh_tree.getroot()

    # calculate new diffs for all the edges
    for veh_elem in veh_root:
        route_elem = veh_elem[0]
        edges = route_elem.get("edges").split()

        for edge in edges:
            if edge in prev_diff_counts:
                if prev_diff_counts[edge] > 0 or allow_negative:
                    prev_diff_counts[edge] -= 1


    diff_tree = counts_to_xml(prev_diff_counts)
    diff_tree.write(output_file)


def counts_to_xml(counts_dict):
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

    
def get_edges_info(NET_FILE):
    net = sumolib.net.readNet(NET_FILE)
    print('Network processed')
    edges_info = {}

    for edge in net.getEdges():
         edges_info[edge.getID()] = {
              'speed': edge.getSpeed(),
              'length': edge.getLength()
            }

    return edges_info


def create_routesampler_config(edgedata_file, route_files:list[str], prefix, seed, output_file, mismatch_output):
    root = ET.Element("configuration")

    input_elem = ET.SubElement(root, "input")
    ET.SubElement(input_elem, "edgedata-files", value=edgedata_file)
    ET.SubElement(input_elem, "route-files", value=','.join(route_files))
    ET.SubElement(input_elem, "verbose", value="True")
    ET.SubElement(input_elem, "attributes", value='departLane="best" departSpeed="max"')
    ET.SubElement(input_elem, "prefix", value=prefix)
    ET.SubElement(input_elem, "seed", value=str(seed))
    ET.SubElement(input_elem, "begin", value=str(0))
    ET.SubElement(input_elem, "end", value=str(3600))

    output_elem = ET.SubElement(root, "output")
    ET.SubElement(output_elem, "output-file", value=output_file)
    ET.SubElement(output_elem, "mismatch-output", value=mismatch_output)

    return ET.ElementTree(root)


def create_duaiterate_config(net_file, route_files:list[str], first_step, last_step):
    root = ET.Element("configuration")

    ET.SubElement(root, "net-file", value=net_file)
    ET.SubElement(root, "routes", value=','.join(route_files))
    ET.SubElement(root, "router-verbose")
    ET.SubElement(root, "clean-alt")

    # Teleports
    ET.SubElement(root, "time-to-teleport", value="300")
    ET.SubElement(root, "time-to-teleport.highways", value="200")

    # Time
    ET.SubElement(root, "begin", value="0")
    ET.SubElement(root, "end", value="3600")

    # Steps
    ET.SubElement(root, "first-step", value=str(first_step))
    ET.SubElement(root, "last-step", value=str(last_step))

    return ET.ElementTree(root)


def create_sumo_config(net_file, route_files:list[str], vehroute_output_file, stats_output_file, errors_log_file, add_files:list[str]=None, begin_f:float=None, end_f:float=None):
    root = ET.Element('configuration')

    # Input
    input_elem = ET.SubElement(root, "input")
    ET.SubElement(input_elem, "net-file", value=net_file)
    ET.SubElement(input_elem, "route-files", value=','.join(route_files))
    if add_files != None:
        ET.SubElement(input_elem, 'additional-files', value=','.join(add_files))

    # Time
    if begin_f != None and end_f != None:
        time_elem = ET.SubElement(root, 'time')
        ET.SubElement(time_elem, 'begin', value=str(begin_f))
        ET.SubElement(time_elem, 'end', value=str(end_f))

    # Processing
    processing_elem = ET.SubElement(root, "processing")
    ET.SubElement(processing_elem, "ignore-junction-blocker", value="1")
    ET.SubElement(processing_elem, "time-to-teleport.highways", value="200")
    ET.SubElement(processing_elem, "time-to-teleport.highways.min-speed", value="0")
    ET.SubElement(processing_elem, "time-to-teleport", value="300")

    # Output
    output_elem = ET.SubElement(root, "output")
    ET.SubElement(output_elem, "statistic-output", value=stats_output_file)
    ET.SubElement(output_elem, "vehroute-output", value=vehroute_output_file)
    ET.SubElement(output_elem, "vehroute-output.sorted", value="true")
    ET.SubElement(output_elem, "vehroute-output.exit-times", value="true")

    report_elem = ET.SubElement(root, "report")
    ET.SubElement(report_elem, "error-log", value=errors_log_file)

    return ET.ElementTree(root)


def get_local_filepath(full_file_path):
    parts = full_file_path.split(os.sep)

    index = parts.index(os.getcwd())


def format_number(iter_number):
    return str(iter_number).zfill(3)


def get_rs_dir(cycle):
    '''creates rs dir for current cycle'''
    return f'{WORK_DIR}c{format_number(cycle)}/{ROUTESAMPLER_DIR_NAME}/'


def get_dua_dir(cycle):
    return f'{WORK_DIR}c{format_number(cycle)}/{DUAITERATE_DIR_NAME}/'


def get_sumo_dir(cycle):
    return f'{WORK_DIR}c{format_number(cycle)}/{SUMO_DIR_NAME}/'


def get_final_sumo_dir():
    return BASE_DIR + 'sumo_files/output/simulation/geo_runner/'


def get_rs_iter_dir(cycle, iter_number):
    '''returns 000, 001, ... dirs within rs folder for a specified cycle'''
    return f'{get_rs_dir(cycle)}{format_number(iter_number)}/'


def get_dua_step_dir(cycle, step):
    return f'{get_dua_dir(cycle)}{format_number(step)}/'


def get_sumo_iter_dir(cycle, iter_number):
    return f'{get_sumo_dir(cycle)}{format_number(iter_number)}/'


def get_cycle_dir(cycle):
    return f'{WORK_DIR}c{format_number(cycle)}/'


def create_dir_safe(dir_path):
    if not os.path.isdir(dir_path):
        os.mkdir(dir_path)


def copy_file_safe(input, output):
    if not os.path.isfile(output):
        shutil.copyfile(input, output)


def copy_file_overridable(input, output):
    shutil.copyfile(input, output)

# find slow
# read network

# run routesampler
# prune routes that even in best case can't reach the detector
# create diff file (theoretical perfect counts after pruning)
# run routesampler again
# ...
# combine all routesampler routes into one once all detectors are being reached in time


if __name__ == '__main__':
    sys.exit(main())



   


    # stations_info = get_stations_info(REAL_WORLD_CMP_FILE, SHEET_NAME, ADD_FILE)
    # stations_edges = set([s['edge'] for s in stations_info.values()])
    # edges_real_counts = {}
    # for station_info in stations_info.values():
    #     edge = station_info['edge']
    #     real = station_info['real']
    #     edges_real_counts[edge] = real

    # edges_net_info = get_edges_info(NET_FILE)

    # # # first time is different because we use OD routes
    # # print('ITERATION 0')
    # # run_routesampler(0, EDGEDATA_DIFF_FILE, DUAITERATED_OD_ROUTES)
    # # fast = keep_fast(0, edges_net_info, stations_edges)
    # # calc_diff(0, edges_real_counts, stations_edges)
    
    # # # main iterative pipeline
    # random_rs_attempts = 1
    # # for i in range(1, random_rs_attempts+1):
    # #     print(f'\nITERATION {i}')
    # #     prev_diff_file = ROUTESAMPLER_FOLDER + '/' + format_iter_number(i-1) + '/diff.xml'
    # #     run_routesampler(i, prev_diff_file, RANDOM_ROUTES)
    # #     fast = keep_fast(i, edges_net_info, stations_edges)
    # #     calc_diff(i, edges_real_counts, stations_edges)

    # # run duaiterate
    # # create folder for duaiterate
    # if not os.path.isdir(DUAITERATE_DIR):
    #     os.mkdir(DUAITERATE_DIR)
    
    # duaiterate_steps = 1
    # run_duaiterate(NET_FILE, range(0, random_rs_attempts+1), duaiterate_steps)
    # # create duaiterate config using the routes
    # # create a command
    
    # # run simulation
    # # create simulation config
    # # run simulation with exit times
    # # prune vehicles not making it through

    # # return back to the original cwd
    # os.chdir(base_cwd_dir)

