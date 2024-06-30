import numpy as np
import math
import random
import sumolib
import xml.etree.ElementTree as ET
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from pprint import pprint

routes_default = 'sumo_files/output/tools/reduced_area_random_trips/routes/test_default.rou.xml'
routes_test = 'sumo_files/output/tools/reduced_area_random_trips/routes/test_fringe_length_work.rou.xml'
net_file = 'sumo_files/data/reduced_cut_area_2_tl_fixed.net.xml'


def main():
    # get routes total fringe factor
    net = sumolib.net.readNet(net_file)
    print('Network processed.')
    routes_default_vehs_tree = ET.parse(routes_default)
    routes_test_vehs_tree = ET.parse(routes_test)
    
    # print('ROUTES FRINGE FACTOR FOR DEFAULT ROUTES')
    # get_routes_fringe_factor(routes_default_vehs_tree, net)

    # print('ROUTES FRINGE FACTOR FOR TEST ROUTES')
    # get_routes_fringe_factor(routes_test_vehs_tree, net)

    plot_lane_multiplies(routes_default_vehs_tree, routes_test_vehs_tree, net)

    


def plot_lane_multiplies(routes1_tree, routes2_tree, net, fringe_min_speed = 0):
    routes1_edges = {
        'fringe': defaultdict(lambda: defaultdict(lambda: 'empty')),    # set to 'empty' so that i know it's something that i set
        'non_fringe': defaultdict(lambda: defaultdict(lambda: 'empty')) # first level of dict represents the edge type, second level represents edge lanes
    }
    
    routes2_edges = {
        'fringe': defaultdict(lambda: defaultdict(lambda: 'empty')),
        'non_fringe': defaultdict(lambda: defaultdict(lambda: 'empty'))
    }

    routes1_counts = {
        'fringe': defaultdict(lambda: defaultdict(lambda: 0)),
        'non_fringe': defaultdict(lambda: defaultdict(lambda: 0))
    }

    routes2_counts = {
        'fringe': defaultdict(lambda: defaultdict(lambda: 0)),
        'non_fringe': defaultdict(lambda: defaultdict(lambda: 0))
    }


    def find_vehs(edges_dict, counts_dict, vehs_tree):
        '''
        finds one random (first selected) edge for every type and number of lanes
        to later track the number of occurences of this exact edge
        and determine how the number of lanes influeces the probability of picking this specific edge
        '''
        for veh in vehs_tree.getroot():
            edges = veh.find('route').get('edges').split()
            for edge_id in [edges[0], edges[-1]]:
                edge = net.getEdge(edge_id)
                
                # determine the edge characteristics
                category = 'fringe' if edge.is_fringe() and edge.getSpeed() >= fringe_min_speed else 'non_fringe'
                edge_type = edge.getType()
                edge_lanes = edge.getLaneNumber()
                edge_length = edge.getLength()
                
                if edges_dict[category][edge_type][edge_length] == 'empty':
                    edges_dict[category][edge_type][edge_length] = edge_id
                    counts_dict[category][edge_type][edge_length] = 1
                
                elif edges_dict[category][edge_type][edge_length] == edge_id:
                    counts_dict[category][edge_type][edge_length] += 1

                
    # Find edges
    find_vehs(routes1_edges, routes1_counts, routes1_tree)
    find_vehs(routes2_edges, routes2_counts, routes2_tree)

    def plot_data(counts_dict, title):
        '''
        Plotting the counts
        '''
        special_types = set([
            'highway.living_street', 'highway.residential', 
            'highway.tertiary', 'highway.tertiary_link', 'highway.unclassified'
        ])

        plt.figure(figsize=(10, 6))
        for category, edge_types in counts_dict.items():
            for edge_type, length in edge_types.items():
                length_counts = sorted(length.items())  # Sort by number of lanes
                if length_counts:
                    x = [lc[0] for lc in length_counts]  # Number of lanes
                    y = [lc[1] for lc in length_counts]  # Counts
                    plt.plot(x, y, label=f'{category} - {edge_type}')
        
        plt.title(title)
        plt.xlabel('Number of Lanes')
        plt.ylabel('Occurrences')
        plt.legend()
        plt.grid(True)
        plt.show()

    # Plot for fringe edges
    plot_data({k: v for k, v in routes1_counts.items() if k == 'fringe'}, 'Occurrences for Fringe Edges for default')

    # Plot for non-fringe edges
    plot_data({k: v for k, v in routes2_counts.items() if k == 'fringe'}, 'Occurrences for Fringe Edges for test')



    # # Create plots
    # plt.figure(figsize=(12, 8))
    # color_palette = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"]
    # color_index = 0

    # for edge_type, points in sorted(plot_data.items()):
    #     points.sort()  # Sort points by number of lanes
    #     lanes = [p[0] for p in points]
    #     occurrences = [p[1] for p in points]
    #     plt.plot(lanes, occurrences, label=edge_type, color=color_palette[color_index % len(color_palette)], marker='o')
    #     color_index += 1

    # plt.xlabel('Number of Lanes')
    # plt.ylabel('Number of Occurrences')
    # plt.title('Edge Usage Relative to Lane Count')
    # plt.legend(title='Edge Type')
    # plt.grid(True)
    # plt.show()



def get_routes_fringe_factor(vehs_tree, net, fringe_min_speed = 0):
    total_types = defaultdict(lambda: 0)
    fringe_types = defaultdict(lambda: 0)
    non_fringe_types = defaultdict(lambda: 0)

    fringe = 0
    non_fringe = 0

    in_in = 0
    in_out = 0
    out_in = 0
    out_out = 0

    vehs_root = vehs_tree.getroot()
    for veh in vehs_root:
        edges = veh[0].get('edges').split()
        
        orig = net.getEdge(edges[0])
        dest = net.getEdge(edges[-1])

        for edge in [orig, dest]:
            total_types[edge.getType()] += 1

            if edge.is_fringe() and edge.getSpeed() >= fringe_min_speed:
                fringe_types[edge.getType()] += 1
                fringe += 1
            else:
                non_fringe_types[edge.getType()] += 1
                non_fringe += 1

    if (non_fringe != 0):
        print('FRINGE RATIO:', fringe/non_fringe)
    else:
        print('NON-FRINGE COUNT IS 0. IMPOSSIBLE TO DETERMINE FRINGE FACTOR')
    # print('TOTAL EDGE TYPES COUNTS')
    # pprint(total_types, indent=4)
    # print()

    # print('FRINGE EDGE TYPES COUNTS')
    # pprint(fringe_types, indent=4)
    # print()
    
    # print('NON-FRINGE EDGE TYPES COUNTS')
    # pprint(non_fringe_types, indent=4)
    # print()


def get_net_fringe_factor(net, fringe_min_speed = 0):
    fringe_types = defaultdict(lambda: 0)
    non_fringe_types = defaultdict(lambda: 0)

    fringe = 0
    non_fringe = 0
    for edge in net.getEdges():
        if edge.is_fringe() and edge.getSpeed() >= fringe_min_speed:
            fringe_types[edge.getType()] += 1
        else:
            non_fringe_types[edge.getType()] += 1

    print(fringe_types)
    print(non_fringe_types)
    

def get_fringe_factor(od, sij):
    hki_indexes = sij.index[sij['KUNTANIMI'].isin(['Espoo', 'Vantaa', 'Helsinki'])].tolist()
    not_hki_indexes = sij.index[~sij['KUNTANIMI'].isin(['Espoo', 'Vantaa', 'Helsinki'])].tolist()
    # hel_beg = 1013
    # hel_end = 1393
    # van_beg = 253
    # van_end = 486
    # esp_beg = 1394

    
    mtx_keys = ["car_work", "car_leisure", "van"]
    matrices = [od[key] for key in mtx_keys]
    # print(matrices.attrs)
    # if 'mapping' in matrices.attrs:
    #     zone_labels = matrices.attrs['mapping']
    #     print('Zone labels:', zone_labels)

    # fringe = out-in / in-in or in-out / in-in
    
    mtx_len = len(matrices[0])
    in_in = 0
    in_out = 0
    out_in = 0

    # in-in
    for orig in hki_indexes:
        for dest in hki_indexes:
            for mtx in matrices:
                in_in += mtx[orig,dest]

    # in-out
    for orig in hki_indexes:
        for dest in not_hki_indexes:
            for mtx in matrices:
                in_out += mtx[orig,dest]
    
    # out-in
    for orig in not_hki_indexes:
        for dest in hki_indexes:
            for mtx in matrices:
                out_in += mtx[orig,dest]

    # for orig in range(0, mtx_len):
    #     for dest in range(0, mtx_len):
    #         trips = 0
    #         for mtx in matrices:
    #             trips += mtx[orig,dest]

    #         # get an extra car, depending on the likelihood
            
    #         # check if it's in-in, in-out, out-in or out-out
    #         # if orig in range(hel_beg, hel_end) and dest in range(hel_beg, hel_end):
    #         #     in_in += trips
    #         # elif orig in range(hel_beg, hel_end) and dest not in range(hel_beg, hel_end):
    #         #     in_out += trips
    #         # elif orig not in range(hel_beg, hel_end) and dest in range(hel_beg, hel_end):
    #         #     out_in += trips

    print(f'in_in: {in_in}')
    print(f'in_out: {in_out}')
    print(f'out_in: {out_in}\n')

    print(f'fringe factor (in_out): {in_out / in_in}')
    print(f'fringe factor (out_in): {out_in / in_in}')
    print(f'fringe factor (in_out or out_in): {(in_out + out_in) / in_in}')


if __name__ == '__main__':
    main()

