import numpy as np
import openmatrix as omx
import math
import random
import simpledbf as dbf
import sumolib
import xml.etree.ElementTree as ET

def main(demand_omx_file, zone_info_file, net_file, routes_file):
    od = omx.open_file(demand_omx_file, mode='r')
    sij = dbf.Dbf5(zone_info_file).to_dataframe().set_index('FID_1')
    net = sumolib.net.readNet(net_file)
    vehs_tree = ET.parse(routes_file)

    get_routes_fringe_factor(vehs_tree, net)
    #get_net_fringe_factor(net, 13)
    #get_fringe_factor(od, sij)

def get_routes_fringe_factor(vehs_tree, net):
    in_in = 0
    in_out = 0
    out_in = 0
    out_out = 0

    vehs_root = vehs_tree.getroot()
    for veh in vehs_root:
        edges = veh[0].get('edges').split()
        
        orig = net.getEdge(edges[0])
        dest = net.getEdge(edges[-1])
        
        if orig.is_fringe() and dest.is_fringe():
            out_out += 1
        elif orig.is_fringe() and not dest.is_fringe():
            out_in += 1
        elif not orig.is_fringe() and dest.is_fringe():
            in_out += 1
        elif not orig.is_fringe() and not dest.is_fringe():
            in_in += 1
        else:
            raise ValueError('idk something weird')

    print(f'routes in_in: {in_in}')
    print(f'routes in_out: {in_out}')
    print(f'routes out_in: {out_in}')
    print(f'routes out_out: {out_out}')
    print(f'routes (at least one fringe): {in_out + out_in + out_out}\n')

    print(f'routes fringe factor (in_out): {in_out / in_in}')
    print(f'routes fringe factor (out_in): {out_in / in_in}')
    print(f'routes fringe factor (out_out): {out_out / in_in}')
    print(f'routes fringe factor (at least one fringe): {(in_out + out_in + out_out) / in_in}')


def get_net_fringe_factor(net, fringe_min_speed = 0):
    fringe = 0
    non_fringe = 0
    for edge in net.getEdges():
        if edge.is_fringe() and edge.getSpeed() >= fringe_min_speed:
            fringe += 1
        else:
            non_fringe += 1

    print(f'fringe edges: {fringe}')
    print(f'non-fringe edges: {non_fringe}')
    print(f'fringe ratio: {fringe / non_fringe}')
    
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
    demand_omx_file = 'WP4/sumo-hki-cm/demand_data/demand_aht.omx'
    zone_info_file = 'WP4/sumo-hki-cm/demand_data/sijoittelualueet2019.dbf'
    net_file = 'WP4/sumo-hki-cm/sumo_files/data/reduced_cut_area_2_tl_fixed.net.xml'
    routes_file = 'WP4/sumo-hki-cm/sumo_files/output/tools/reduced_area_routesampler_iterative_past/reduced_area_routesampler_iterative_1mil/demo/best_output/sumo_c008_001_routes_fast.rou.xml'

    print(f'routes: {routes_file}')


    main(demand_omx_file, zone_info_file, net_file, routes_file)

