#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
create_puma_training_set creates a training set for the historical dock data.
"""

import pandas as pd

DATA_ROOT = '../../data/citibike/dock_historical/'

def main():
    # Load data with puma index.
    hist_fn = DATA_ROOT + 'historical_data_puma.csv'
    historical = pd.read_csv(hist_fn, index_col=0)

    # Clean data.
    historical = historical.query('_long > -74.03') # Remove NJ.
    historical = historical.query('time >= "2018-01"') # Only consider 2018.
    historical.PUMA = historical.PUMA.astype(int)   # PUMA as an int.
    historical.time = pd.to_datetime(historical.time) # time as as pd.datetime obj.

    for puma_id, puma in historical.groupby('PUMA'):
        print('Working on puma: {}'.format(puma_id))
        fn = DATA_ROOT + 'puma_{}_data.csv'

        # Useful quantities for later.
        tot_docks = puma.set_index('time').groupby('time')['tot_docks'].sum()
        tot_stations = puma.set_index('time').groupby('time')['dock_id'].count()

        # Correct time.
        puma.loc[:, 'dayofyear'] = puma.time.dt.dayofyear
        puma.loc[:, 'dayofweek'] = puma.time.dt.dayofweek
        puma.loc[:, 'hour'] = puma.time.dt.hour
        puma = puma.drop(columns=['PUMA', 'status_key', 'dock_name', 'time'])

        # Aggregate by hour since sampling is sometimes multiple times an hour.
        final = puma.groupby(['dock_id', 'dayofweek', 'dayofyear', 'hour'])['avail_bikes', 'avail_docks', 'in_service'].agg({'avail_bikes':'mean', 'avail_docks':'mean', 'in_service':'min'})
        final = final.groupby(['dayofyear', 'dayofweek', 'hour']).sum().reset_index()

        # Resample time to even hours.
        final.loc[:, 'time'] = '2018-' + final.dayofyear.apply(lambda x: '{:03}'.format(x)) + ' ' + final.hour.apply(lambda x: '{:02}'.format(x))
        final.loc[:, 'time'] = pd.to_datetime(final.time, format='%Y-%j %H')
        final = final.set_index('time')
        ix = pd.date_range(final.index[0], final.index[-1], freq="H")
        final = final.reindex(ix)

        # Load previous 4 times in each row for bikes and docks.
        final['avail_bikes-1'] = final.avail_bikes.shift(+1)
        final['avail_bikes-2'] = final.avail_bikes.shift(+2)
        final['avail_bikes-3'] = final.avail_bikes.shift(+3)
        final['avail_bikes-4'] = final.avail_bikes.shift(+4)
        final['avail_bikes-5'] = final.avail_bikes.shift(+5)

        final['avail_docks-1'] = final.avail_docks.shift(+1)
        final['avail_docks-2'] = final.avail_docks.shift(+2)
        final['avail_docks-3'] = final.avail_docks.shift(+3)
        final['avail_docks-4'] = final.avail_docks.shift(+4)
        final['avail_docks-5'] = final.avail_docks.shift(+5)

        # Resample tot_docks and tot_stations.
        # (FIXME) Repeated code.. refactor.
        tot_docks = tot_docks.resample('D').mean().round().fillna(method='ffill').reindex(ix)
        tot_docks[0] = tot_docks[tot_docks.first_valid_index()]
        tot_docks = tot_docks.fillna(method='ffill').astype('int')
        tot_stations = tot_stations.resample('D').mean().round().fillna(method='ffill').reindex(ix)
        tot_stations[0] = tot_stations[tot_stations.first_valid_index()]
        tot_stations = tot_stations.fillna(method='ffill').astype('int')
        final.loc[:, 'tot_docks'] = tot_docks
        final.loc[:, 'tot_stations'] = tot_stations

        # Save result.
        final.to_csv(fn.format(puma_id))

        
if __name__ == '__main__':
    main()
