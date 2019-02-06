#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
resample_history resamples the historical dock data to be on a per hour 
basis.
"""

import pandas as pd

def main():
    # Load data with puma index.
    fn = '../../data/citibike/dock_historical/historical_data_puma.csv'
    historical = pd.read_csv(fn, index_col=0)
    historical.time = pd.to_datetime(historical.time)

    # Save time bits.
    historical.loc[:, 'dayofyear'] = historical.time.dt.dayofyear
    historical.loc[:, 'hour'] = historical.time.dt.hour
    historical.loc[:, 'year'] = historical.time.dt.year

    # Aggregate on hour.
    historical = historical.groupby(['dock_id', 'year', 'dayofyear', 'hour'])['avail_bikes', 'avail_docks', 'in_service', 'tot_docks', '_lat', '_long', 'PUMA'].agg({'avail_bikes':'mean', 'avail_docks':'mean', 'in_service':'min', 'tot_docks':'min', '_lat':'min', '_long':'min', 'PUMA':'min'}).reset_index()


    historical.loc[:, 'time'] = pd.to_datetime(historical.year.astype(str) + '-'+ historical.dayofyear.apply(lambda x: '{:03}'.format(x)) + ' ' + historical.hour.apply(lambda x: '{:02}'.format(x)), format='%Y-%j %H')
    
    historical = historical.drop(columns=['year', 'hour', 'dayofyear']).set_index('time')

    historical.to_csv('../../data/citibike/dock_historical/historical_data_puma_resampled.csv')
    
if __name__ == '__main__':
    main()

