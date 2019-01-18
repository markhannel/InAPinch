#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
download.py downloads all necessary static data from the webs if necessary.
"""

import os
import requests
import json
import pandas as pd

def clean_citibike_stations_data():
    # Read in raw file. Save the 'stationBeanList' information as a pandas DF.
    with open('../../data/citibike/citibike_stations_raw.json') as f:
        df = pd.DataFrame(json.load(f)['stationBeanList'])

    # Drop columns that are useless.
    drop_cols = []
    for col in df:
        if df[col].unique()[0] == 1:
            drop_cols.append(col)

    df = df.drop(columns=drop_cols)
    df.to_csv('../../data/citibike/citibike_stations.json')

def main():
    """
    Aggregate
    """
    # Get root of data directory.
    data_root = '../../data/'
    
    # List of necessary downloads.
    data_urls = ['http://web.mta.info/developers/data/nyct/subway/Stations.csv', 
                 'https://feeds.citibikenyc.com/stations/stations.json'] 
    
    # Parallel list for where to download the data.
    # FIXME (MDH): Possibly use a more general method for absolute path.
    data_fns = [data_root + fn for fn in ['mta/mta_stations.csv',
                                          'citibike/citibike_stations_raw.json']]

    # Downloads of each test.
    for url, fn in zip (data_urls, data_fns):
        if not os.path.exists(fn):
            r = requests.get(url)
            with open(fn, 'wb') as f:
                f.write(r.content)
        else:
            print("Skip.. I have the data.")

    if os.path.exists('../../data/citibike/citibike_stations_raw.json'):
        clean_citibike_stations_data()
    else:
        print('... Raw citibike data not found.')
        raise FileNotFoundError
if __name__ == '__main__':
    main()
