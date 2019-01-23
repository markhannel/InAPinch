#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
citibike_station_to_station queries all the possible
station to station routes in the NYC Citi Bike station 
system.

Method for hosting a local OSRM.
https://medium.com/@janakachathuranga/leaving-google-maps-use-osrm-for-routing-aa1afc912df3
"""

import pandas as pd
import numpy as np
import itertools
import requests
from pprint import pprint
import json

def main():
    # Load Citi Bike station GPS information.
    stations = '../../data/citibike/citibike_stations.csv'
    df = pd.read_csv(stations)
    result_fn = '/media/mark/TOSHIBA EXT1/Projects/InAPinch/data/citibike/all_stations.csv'
    
    # Form all pairs.
    count = 0
    with open(result_fn, 'a+') as f:
        f.write("lat1\tlong1\tlat2\tlong2\tresponse\n")        
        for pair in itertools.product(df[['latitude','longitude']].values,
                                      df[['latitude','longitude']].values):
            if not count % 1000:
                print(count)
            if not np.array_equal(pair[0], pair[1]):
                url = "http://127.0.0.1:5000/route/v1/bicycle/{},{};{},{}?steps=true"
                url = url.format(pair[0][1], pair[0][0], pair[1][1], pair[1][0])
                r = requests.get(url)
                r = '{}\t{}\t{}\t{}\t{}\n'.format(pair[0][1], pair[0][0], pair[1][1], pair[1][0], r.content)
                f.write(r)
                count += 1
            
    # Query  OSRM for results and save as you go.
    
    
if __name__ == '__main__':
    main()
