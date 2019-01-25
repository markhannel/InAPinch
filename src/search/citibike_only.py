#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
citibike_only returns a set of citibke stations given two sets of geocoordinates.
"""

import pandas as pd
from scipy.spatial import KDTree
from collections import defaultdict
import requests
import json

FN = '../../data/citibike/citibike_stations.csv'
ROUTES_FN = '/media/mark/TOSHIBA EXT1/Projects/InAPinch/data/citibike/all_stations_durations_docks.csv'

def get_directions(start, end, mode, modes={'foot':5000, 'cycle':5001}):
    url = "http://127.0.0.1:{}/route/v1/{}/{},{};{},{}?steps=true"
    url = url.format(modes[mode], mode,
                     start[0], start[1], 
                     end[0], end[1])
    r = requests.get(url)
    return json.loads(r.content)['routes'][0]

def get_shortest_path(weighted_graph, start, end):
    """
    Calculate the shortest path for a directed weighted graph.

    Node can be virtually any hashable datatype.

    :param start: starting node
    :param end: ending node
    :param weighted_graph: {"node1": {"node2": "weight", ...}, ...}
    :return: ["START", ... nodes between ..., "END"] or None, if there is no
            path
    """

    # We always need to visit the start
    nodes_to_visit = {start}
    visited_nodes = set()
    distance_from_start = defaultdict(lambda: float("inf"))
    
    # Distance from start to start is 0
    distance_from_start[start] = 0
    tentative_parents = {}
    
    while nodes_to_visit:
        # The next node should be the one with the smallest weight
        current = min(
            [(distance_from_start[node], node) for node in nodes_to_visit]
        )[1]

        # The end was reached
        if current == end:
            break

        nodes_to_visit.discard(current)
        visited_nodes.add(current)

        for neighbour, distance in weighted_graph[current].items():
            if neighbour in visited_nodes:
                continue
            neighbour_distance = distance_from_start[current] + distance
            if neighbour_distance < distance_from_start[neighbour]:
                distance_from_start[neighbour] = neighbour_distance
                tentative_parents[neighbour] = current
                nodes_to_visit.add(neighbour)

    return _deconstruct_path(tentative_parents, end)


def _deconstruct_path(tentative_parents, end):
    if end not in tentative_parents:
        return None
    cursor = end
    path = []
    while cursor:
        path.append(cursor)
        cursor = tentative_parents.get(cursor)
    return list(reversed(path))

class SearchRoutes(object):
    def __init__(self):
        self.stations = pd.read_csv(FN, index_col=0)
        self.stations['horizontal'] = self.stations.longitude * 52.32
        self.stations['vertical'] = self.stations.latitude * 69.135
        self.tree = KDTree(self.stations[['vertical', 'horizontal']])
        self.__get_routes__()
        print('Finished Initializing.')

    def __get_routes__(self):
        self.routes = pd.read_csv(ROUTES_FN, sep='\t')
        self.routes.dock_id1 = self.routes.dock_id1.astype(int)
        self.routes.dock_id2 = self.routes.dock_id2.astype(int)
        self.routes.set_index(['dock_id1', 'dock_id2'], inplace=True)
        self.routes.sort_index(inplace=True)
        
    def start_to_end(self, start, end):
        """
        Produce a graph of time duration then find the path which minimizes
        the total duration.
        start: [latitude, longitude]
        end: [latitude, longitude]
        """
        
        # Find stations within walking distance from start and finish.
        start_miles = [start[0]*69.135, start[1]*52.32]
        end_miles = [end[0]*69.135, end[1]*52.32]
        
        inds = self.tree.query_ball_point(start_miles, 0.5)
        start_stations = self.stations.iloc[inds]
        print(start_stations.stationName)
        inds = self.tree.query_ball_point(end_miles, 0.5)
        end_stations = self.stations.iloc[inds]

        # Add walking duration from start to each of those stations.
        nodes = {}
        for _, start_row in start_stations.iterrows():
            r = get_directions(start[::-1], start_row[['longitude', 'latitude']], 'foot')
            nodes.update({start_row.id:r['duration']})
            
        graph = {'start': nodes}

        for _, end_row in end_stations.iterrows():
            r = get_directions(end[::-1], end_row[['longitude', 'latitude']], 'foot')
            graph.update({end_row.id:{'end':r['duration']}})

        # Add cycling directions from each "start" citibike to each "end" citibike.
        for _, start_row in start_stations.iterrows():
            nodes = {}
            for _, end_row in end_stations.iterrows():
                nodes.update({end_row.id : self.routes.loc[start_row.id, end_row.id]['duration']})
            graph.update({start_row.id:nodes})

        return get_shortest_path(graph, 'start', 'end')

def main():
    sr = SearchRoutes()

    start_coords = [40.677537, -73.959066]
    end_coords = [40.7395441,-73.9885504]

    print(sr.start_to_end(start_coords, end_coords))

    end_coords = [40.7006181,-73.9607287]
    start_coords = [40.7184878,-73.9927139]
    print(sr.start_to_end(start_coords, end_coords))
    
if __name__ == '__main__':
    main()
