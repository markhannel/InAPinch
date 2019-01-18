#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
download.py downloads all necessary static data from the webs if necessary.
"""

import os
import requests

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

if __name__ == '__main__':
    main()
