#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
citibike.py returns a set of citibke stations given two sets of geocoordinates.
"""

import pandas as pd
import numpy as np
from scipy.spatial import KDTree
from collections import defaultdict
import requests
import json
from scipy.linalg import expm
from scipy import sparse
import pickle

FN = '~/inapinch/data/citibike/citibike_stations.csv'
ROUTES_FN = '~/inapinch/data/citibike/all_stations_durations_docks.csv'

def time_intervals(h, timeleft=1.0):
    ''' Returns a list of times spent in 15 minute intervals over the next h minutes.
    timeleft allows you to set the amount of time left in the first 15 minute interval.
    '''

    # If 
    if h > 0.01 and h < timeleft:
        return [h]
    
    # Adjust for the amount of time left in the first interval.

    time = [timeleft]
    h -= timeleft*15

    # Edge case: if less than 15 minutes are left.
    if h < 0:
        return time

    while h>0:
        if h < 15:
            time.append(h/15)
        else:
            time.append(1.0)
        h -= 15

    # Clip small time intervals that would cause the prediction to underflow.
    if time[0] < 0.01:
        time = time[1:]
    if time[-1] < 0.01:
        time = time[:-1]

    return time

class Station(object):
    """Station class provides a concise way to organize station data.
    """
    def __init__(self, stat_id):
        self.id = float(stat_id)
        self.lat = None
        self.long = None
        self.name = None
        self.docks_avail = None
        self.bikes_avail = None
        self.active = True
        self.bikes_disabled = None
        self.docks_disabled = None

    def predict_no_bikes(self, interval, h, temp=30, weekend=0, raining=0, timeleft=1.0):
        '''
        Forecasts the probability distribution of the number of bikes at this station
        "h" minutes in the future starting during one of the 96 15 minute intervals of 
        a day.
        
        Updates/Sets the following instance attributes:
        prob_a_bike: probability of at least one bike.
        expected_bikes: expected number of bikes.
        prob_a_dock: probability of at least one dock.
        expected_docks: expected number of docks.
        '''
        
        num_bikes = self.bikes_avail
        total_docks = self.bikes_avail + self.docks_avail

        # Load incoming (lambda) and outgoing (mu) traffic predictions.
        with open('../../models/lambda_and_mu/stationid_{}_lambda.pkl'.format(int(self.id)), 'rb') as f:
            lamb_func = pickle.load(f)

        with open('../../models/lambda_and_mu/stationid_{}_mu.pkl'.format(int(self.id)), 'rb') as f:
            mu_func = pickle.load(f)

        '''
        Forecast the probability distribution knowing the incoming traffing traffic
        and outgoing traffic over the necessary time intervals. To do so,
        compute the transition kernel.
        '''
        
        kernel = sparse.diags([0]*(total_docks+1))
        for time in time_intervals(h, timeleft):
            # Incoming and outgoing traffic.
            lamb = lamb_func.predict([[interval, weekend, temp, raining]])[0]
            mu = mu_func.predict([[interval, weekend, temp, raining]])[0]
            
            # Construct the transition kernel.
            upper_diag = mu * np.ones(total_docks)
            lower_diag = lamb * np.ones(total_docks)
            diag = np.zeros(total_docks+1)
            diag[:-1] -= upper_diag*time
            diag[1:]  -= lower_diag*time
            kernel += sparse.diags([diag, upper_diag, lower_diag], [0, 1, -1])

            # Increment to the next time interval.
            interval += 1

        # Compute the forecasted probability distribution.
        prob = expm(kernel.toarray())

        # From the forecasted distribution, compute quantities of interest.
        bikes = np.sum(prob[num_bikes,:]*np.arange(total_docks+1))
        docks = total_docks - bikes
        self.at_least_one_bike = sum(prob[num_bikes, 1:])
        self.bikes_avail_future = np.round(bikes)
        self.at_least_one_dock = sum(prob[num_bikes, :-1])
        self.docks_avail_future = np.round(docks)

class Directions(object):
    """ Directions class provides a concise way to organize direction
    information.
    """
    def __init__(self, start, end, mode):
        self.start = start
        self.end = end
        self.mode = mode
        self.__get__directions()
        self.__get__polylines()

    def __get__directions(self):
        self.directions = get_directions(self.start,
                                         self.end,
                                         self.mode)
        self.duration = self.directions['duration']
        
    def __get__polylines(self):
        self.polylines = extract_polylines(self.directions)
    

def get_directions(start, end, mode, modes={'foot':5000, 'cycle':5002}):
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

    # We always need to visit the start.
    nodes_to_visit = {start}
    visited_nodes = set()
    distance_from_start = defaultdict(lambda: float("inf"))
    
    # Distance from start to start is 0.
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

        inds = self.tree.query_ball_point(end_miles, 0.5)
        end_stations = self.stations.iloc[inds]

        # Add walking duration from start to each of rental stations.
        nodes = {}
        for _, start_row in start_stations.iterrows():
            if start[0] != start_row.latitude and start[1] != start_row.longitude:
                r = get_directions(start[::-1], start_row[['longitude', 'latitude']], 'foot')
                nodes.update({start_row.id:r['duration']})

        # Additional node for just walking there.
        r = get_directions(start[::-1], end[::-1], 'foot')
        nodes.update({'end':r['duration']})
        graph = {'start': nodes}
        
        # Add walking duration from each return station to the final destination.
        for _, end_row in end_stations.iterrows():
            if end[0] != end_row.latitude and end[1] != end_row.longitude:
                r = get_directions(end[::-1], end_row[['longitude', 'latitude']], 'foot')
                graph.update({end_row.id:{'end':r['duration']}})

        # Add cycling directions from each "start" citibike to each "end" citibike.
        for _, start_row in start_stations.iterrows():
            nodes = {}
            for _, end_row in end_stations.iterrows():
                if start_row.id != end_row.id:
                    nodes.update({end_row.id : self.routes.loc[start_row.id, end_row.id]['duration']})
            graph.update({start_row.id:nodes})

        return get_shortest_path(graph, 'start', 'end')

def extract_polylines(directions):
    ''' Extracts directions from the OSRM feed.
    '''

    polylines = []
    for step in directions['legs'][0]['steps']: 
        for inter in step['intersections']: 
            polylines.append(inter['location'][::-1])
    return polylines

def main():
    
    sr = SearchRoutes()

    start_coords = [40.677537, -73.959066]
    end_coords = [40.7395441,-73.9885504]


    start_coords = [-73.959066, 40.677537]
    end_coords = [-73.9885504, 40.7395441]

    dirs = get_directions(start_coords, end_coords, 'cycle')
    print(extract_polylines(dirs))

    
    #print(sr.start_to_end(start_coords, end_coords))

    end_coords = [40.7006181,-73.9607287]
    start_coords = [40.7184878,-73.9927139]
    #print(sr.start_to_end(start_coords, end_coords))

def test_predict_no_bikes(num_bikes, total_docks, interval, h, station, raining=0.0,
                         temp=30, weekend=0, timeleft=1.0):
    ''' Given the number of bikes at a station on a specific 
    15 minute interval of a day, return the following for h minutes
    in the future:
    prob_a_bike: probability of at least one bike.
    expected_bikes: expected number of bikes.
    prob_a_dock: probability of at least one dock.
    expected_docks: expected number of docks.
    '''
    # Make the prediction about the number 
    # Load the necessary predictors.
    with open('../../models/lambda_and_mu/stationid_{}_lambda.pkl'.format(int(station)), 'rb') as f:
        lamb_func = pickle.load(f)
    
    with open('../../models/lambda_and_mu/stationid_{}_mu.pkl'.format(int(station)), 'rb') as f:
        mu_func = pickle.load(f)
        
    # Find the average flux over the next 15 minutes.
    kernel = sparse.diags([0]*(total_docks+1))
    for time in time_intervals(h, timeleft): # FIXME: Use timeleft
        lamb = lamb_func.predict([[interval, weekend, temp, raining]])[0]
        mu = mu_func.predict([[interval, weekend, temp, raining]])[0]
    
        # Construct the transition kernel.
        upper_diag = mu * np.ones(total_docks)
        lower_diag = lamb * np.ones(total_docks)
        diag = np.zeros(total_docks+1)
        diag[:-1] -= upper_diag*time
        diag[1:]  -= lower_diag*time
        kernel += sparse.diags([diag, upper_diag, lower_diag], [0, 1, -1])
        
        interval += 1 
    prob = expm(kernel.toarray())
    bikes = np.sum(prob[num_bikes,:]*np.arange(total_docks+1))
    docks = total_docks - bikes
    return sum(prob[num_bikes, 1:]), bikes, sum(prob[num_bikes, :-1]), docks

if __name__ == '__main__':
    #main()
    print(time_intervals(51, 0.53333))
    
    print(test_predict_no_bikes(num_bikes=10, 
                                total_docks=18, 
                                interval=40, 
                                h=45, 
                                station=264.0))
    

