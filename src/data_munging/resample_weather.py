#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
resample_weather resamples the weather data to be on a per hour basis.
"""

import pandas as pd

def main():
    # Load data with puma index.
    fn = '../../data/weather/weather.csv'
    historical = pd.read_csv(fn, index_col=0)
    historical.time = pd.to_datetime(historical.time) + pd.Timedelta('9 min')
    historical = historical[['time', 'temp', 'wx_phrase', 'heat_index', 'rh', 'vis', 'gust', 'precip_total', 'precip_hrly', 'snow_hrly']]
    historical['minute'] = historical.time.dt.minute

    historical.to_csv('../../data/weather/weather_resampled.csv')
    
if __name__ == '__main__':
    main()

