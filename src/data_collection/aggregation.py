#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
aggregation.py aggregates the data from TheOpenBus.com into one csv.
"""

import pandas as pd
import os

def main():
    # Naming conventions.
    res_dir = '../../data/citibike/dock_historical/'
    res_fn = res_dir + 'historical_data.csv'
    
    # Find all the datasets.
    csvs = [ res_dir + afile for afile in sorted(os.listdir(res_dir))
             if afile.endswith('.csv')]

    # Load the first one.
    df = pd.read_csv(csvs[0], sep='\t')

    # Open and join all the remaining data sets.
    for afile in csvs[1:]:
        print('working on {}.'.format(afile))
        df = df.append(pd.read_csv(afile, sep='\t'), ignore_index=True)


    # Fix the pm debacle.
    df['date'] = pd.to_datetime(df['date'], format="%y-%m-%d")
    mask = (df.hour==12) & (df.pm==1)
    df.loc[mask, 'date'] += pd.DateOffset(days=1)
    df.loc[mask, 'hour'] -= 12
    df.loc[mask, 'pm'] -= 1
    df.loc[~mask, 'hour'] = df.loc[~mask,'hour'] + 12*df.loc[~mask, 'pm']

    df['newhour'] = df.hour.apply(lambda x: '{:02}'.format(x))
    df['newmin'] = df.minute.apply(lambda x: '{:02}'.format(x))
    df['time'] = df['date'].astype(str) + '-' + df.newhour + ':' + df.newmin
    
    df.time = pd.to_datetime(df.time, format="%Y-%m-%d-%H:%M")
    df = df.drop(columns=['date', 'hour', 'minute', 'pm', 'newhour', 'newmin'])

    
    # Save cleaned data.
    df.to_csv(res_fn)

if __name__ == '__main__':
    main()
