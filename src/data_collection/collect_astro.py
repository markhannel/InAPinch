#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
collect_astro collects astrological data from wunderground.com.
"""

import pandas as pd
import requests
import numpy as np
from time import sleep 

def main():
    # Range of dates to consider.
    date_rng = pd.date_range(start='1/1/2017', end='12/31/2018', freq='D')
    
    # Website info.
    URL = 'https://api.weather.com/v2/astro?apiKey=6532d6454b8aa370768e63d6ba5a832e&geocode=40.77000046%2C-73.98000336&days=1&date={}&format=json'

    # Astro DataFrame
    idx = pd.date_range('2017-01-01', '2018-12-31', freq="H", tz='America/New_York')
    df = pd.DataFrame(0, columns={'Daylight'}, index=idx)
    
    for date in date_rng:
        # Format request.
        date_str = date.strftime("%Y%m%d")
        print(date_str)
        r = requests.get(URL.format(date_str)).json()

        # Format rise and set times.
        try:
            rise_time = pd.to_datetime(r['astroData'][0]['sun']['riseSet']['riseUTC'])
            set_time = pd.to_datetime(r['astroData'][0]['sun']['riseSet']['setUTC'])
            rise_time = rise_time.tz_localize('UTC').tz_convert("America/New_York")
            set_time = set_time.tz_localize('UTC').tz_convert("America/New_York")

            df[rise_time:set_time] = 1
        except KeyError:
            df[date:date] = np.nan
               
        sleep(0.01)
    # Fix time index.
    df.to_csv('../../data/weather/astro.csv')
    
if __name__ == '__main__':
    main()
