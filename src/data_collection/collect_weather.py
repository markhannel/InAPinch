#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
collect_weather collects weather from wunderground.com.
"""

import pandas as pd
import requests
from time import sleep 

def main():
    # Range of dates to consider.
    date_rng = pd.date_range(start='1/1/2017', end='12/31/2018', freq='D')
    
    # Website info.
    URL = 'https://api.weather.com/v1/geocode/40.70000076/-74.01000214/observations/'
    URL += 'historical.json?apiKey=6532d6454b8aa370768e63d6ba5a832e&startDate={}&endDate={}&units=e'

    # Creating the first data frame with an example entry.
    temp_url = URL.format('20180605', '20180605')
    r = requests.get(temp_url).json()

    cols = list(r['observations'][0].keys())
    df = pd.DataFrame(columns=cols)

    for date in date_rng:
        # Format request.
        date_str = date.strftime("%Y%m%d")
        print(date_str)
        r = requests.get(URL.format(date_str, date_str)).json()
        
        # Get next 24 entries.
        temp_df = pd.DataFrame(columns=cols)
        try:
            for obsv in r['observations']:
                temp_df = temp_df.append(obsv, ignore_index=True)
            df = df.append(temp_df)
        except KeyError:
            continue
        sleep(0.01)
    # Fix time index.
    df.loc[:, 'time'] = pd.to_datetime(df.expire_time_gmt, unit='s')
    df.loc[:, 'time'] -= pd.Timedelta('7 hours') # Fix the GMT shift.
    df.to_csv('../../data/weather/weather.csv')
    
if __name__ == '__main__':
    main()
