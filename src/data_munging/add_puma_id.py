#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
add_puma_id creates a dictionary which maps dock_ids to their associated
puma index.
"""

import pandas as pd
import pylab as pl
import shapely.geometry
import json
import numpy as np
import os

def add_puma(df,lat_key='latitude', lon_key='longitude', id_key='id'):
    '''Create puma dictionary and apply it to the dataframe.
    '''
    # Load the PUMA polygons into shapely.geometry.Polygons.
    with open('../../data/nyc_data/PublicUseMicrodataAreasPUMA.geojson') as f:
        puma_geo = json.load(f)

    # Create set of unique (lat, lon, id) pairs.
    docks = []
    for dock_id in df[id_key].unique():
        red = df[df[id_key] == dock_id].iloc[0]        
        docks.append((shapely.geometry.Point(red[lat_key],
                                            red[lon_key]),
                      red[id_key]))
                     
    # Create dock dictionary.
    dock_dict = {}
    for i, feature in enumerate(puma_geo['features']):
        print(i)
        puma_id = feature['properties']['puma']
        shape = shapely.geometry.asShape(feature['geometry'])
        for dock in docks:
            point, dock_id = dock
            if shape.contains(point):
                dock_dict.update({dock_id:int(puma_id)})
                docks.remove(dock)

    # Apply dictionary to dataframe.
    df['PUMA'] = df[id_key].map(dock_dict)
    return df

def main():
    # Load historical station data.
    fn = '../../data/citibike/dock_historical/historical_data_puma.csv'
    if not os.path.exists(fn):
        station_df = pd.read_csv('../../data/citibike/dock_historical/historical_data.csv', index_col=0)
        new_station_df = add_puma(station_df,'_long', '_lat', 'dock_id')
        new_station_df.to_csv(fn)
    
    # Load live station information.
    fn = '../../data/citibike/citibike_stations_puma.csv'
    if not os.path.exists(fn):
        station_df = pd.read_csv('../../data/citibike/citibike_stations.csv', index_col=0)
        new_station_df = add_puma(station_df)
        new_station_df.to_csv(fn)
    
if __name__ == '__main__':
    main()

