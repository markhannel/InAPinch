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

def citibike_station(data_root):
    url = 'https://feeds.citibikenyc.com/stations/stations.json'
    fn = '../../data/citibike/citibike_stations_raw.json'

    if not os.path.exists(fn):
        print('Downloading Citibike station data.')
        r = requests.get(url)
        with open(fn, 'wb') as f:
            f.write(r.content)
        print('Cleaning Citibike data.')
        clean_citibike_stations_data()
    else:
        print('(Skipping) Downloading Citibike station data.')

def mta_stations(data_root):
    
    data_urls = 'http://web.mta.info/developers/data/nyct/subway/Stations.csv'
    fn  = data_root + 'mta/mta_stations.csv'
    if not os.path.exists(fn):
        r = requests.get(url)
        with open(fn, 'wb') as f:
            f.write(r.content)
    else:
        print("(Skipping) Downloading MTA station data.")
        
def mta(data_root):
    mta_stations(data_root)
        
def citibike(data_root):
    citibike_station(data_root)

def main():
    """
    Collect and clean the necessary data.
    """

    
    # Get root of data directory.
    data_root = '../../data/'
    mta(data_root)
    citibike(data_root)
        
if __name__ == '__main__':
    main()
