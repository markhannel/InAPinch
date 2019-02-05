#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
randomForestRegressor.py generates models for each of the 18 pumas in NYC.
"""

import pandas as pd
import numpy as np
import os
from sklearn.metrics import mean_squared_log_error, mean_squared_error
from sklearn.ensemble import RandomForestRegressor
import pprint
import pickle

DATA_ROOT = '../../data/citibike/dock_historical/'

# Error Metrics.
def rmse(ytrue, ypred):
    return np.sqrt(mean_squared_error(ytrue, ypred))

def rmsle(ytrue, ypred):
    return np.sqrt(mean_squared_log_error(ytrue, ypred))


def main():
    # Find all the PUMAS.
    csvs = [afile for afile in os.listdir(DATA_ROOT) if afile.endswith('.csv')]
    puma_csvs = sorted([DATA_ROOT + afile for afile in csvs
                        if afile.startswith('puma')])

    for puma_fn in puma_csvs:
        print('Working on: {}'.format(puma_fn))

        results = {}
        
        # Load Data.
        puma = pd.read_csv(puma_fn, index_col=0)
        puma = puma.dropna() # drop nans.

        # Find a first date that satisfies an approximate 80/20 split.
        '''
        total = puma.shape[0]
        split_date = '2018-{:02}-15'
        for i in range(1,13):
            train_ratio = puma[:split_date.format(i)].shape[0]/total
            if train_ratio > 0.8:
                split_date = split_date.format(i)
                break

        # split on preferred date.
        train = puma[:split_date]
        test =  puma[split_date:]
        '''

        # Split test and train such that no two days have the same .
        num_days = puma.dayofyear.unique().shape[0]
        train_days = np.random.choice(puma.dayofyear.unique(), int(0.8*num_days), replace=False)
        puma.loc[:, 'test'] = True
        for day in train_days:
            puma.loc[puma.dayofyear == day, 'test'] = False

        
        train = puma.query('test != True')
        test  = puma.query('test == True')
        

        # Naive model results.
        results['bikes_naive'] = {'rmse': rmse(train.avail_bikes, train['avail_bikes-1']),
                                  'rmsle': rmsle(train.avail_bikes, train['avail_bikes-1'])}

        
        results['docks_naive'] = {'rmse': rmse(train.avail_docks, train['avail_docks-1']),
                                  'rmsle': rmsle(train.avail_docks, train['avail_docks-1'])}

        ''' 
        Training model for bikes.
        '''
        
        X = train.drop(columns=['avail_bikes', 'avail_docks'])
        Y = train['avail_bikes'].values
        
        # Model for bikes.
        bike_mdl = RandomForestRegressor(n_estimators=100, n_jobs=-1, random_state=0)
        bike_mdl.fit(X.values, Y)

        # Train set results.
        bike_hat = bike_mdl.predict(X)
        results['bikes_rfregressor_train'] = {'rmse': rmse(train.avail_bikes,
                                                           bike_hat),
                                              'rmsle': rmsle(train.avail_bikes,
                                                             bike_hat)}
        # Append feature importances.
        importances = bike_mdl.feature_importances_
        std = np.std([tree.feature_importances_ for tree in bike_mdl.estimators_],
                     axis=0)
        indices = np.argsort(importances)[::-1]
        feature_tuples = [(X.columns[f], importances[indices[f]]) for f in range(X.shape[1])]
        results['bikes_rfregressor_train'].update({'feat_importance': feature_tuples})
        
        # Test set results.
        X = test.drop(columns=['avail_bikes', 'avail_docks'])
        Y = test['avail_bikes'].values
        bike_hat = bike_mdl.predict(X.values)
        
        results['bikes_rfregressor_test'] = {'rmse': rmse(test.avail_bikes,
                                                          bike_hat),
                                             'rmsle': rmsle(test.avail_bikes,
                                                            bike_hat)}
        ''' 
        Training model for docks.
        '''
        
        X = train.drop(columns=['avail_bikes', 'avail_docks'])
        Y = train['avail_docks'].values
        
        # Model for docks.
        dock_mdl = RandomForestRegressor(n_estimators=1000, n_jobs=-1, random_state=0)
        dock_mdl.fit(X.values, Y)

        # Train set results.
        dock_hat = dock_mdl.predict(X)
        results['docks_rfregressor_train'] = {'rmse': rmse(train.avail_docks,
                                                           dock_hat),
                                              'rmsle': rmsle(train.avail_docks,
                                                             dock_hat)}
        # Append feature importances.
        importances = dock_mdl.feature_importances_
        std = np.std([tree.feature_importances_ for tree in dock_mdl.estimators_],
                     axis=0)
        indices = np.argsort(importances)[::-1]
        feature_tuples = [(X.columns[f], importances[indices[f]]) for f in range(X.shape[1])]
        results['docks_rfregressor_train'].update({'feat_importance': feature_tuples})
        
        # Test set results.
        X = test.drop(columns=['avail_bikes', 'avail_docks'])
        Y = test['avail_docks'].values
        dock_hat = dock_mdl.predict(X.values)
        
        results['docks_rfregressor_test'] = {'rmse': rmse(test.avail_docks,
                                                          dock_hat),
                                             'rmsle': rmsle(test.avail_docks,
                                                            dock_hat)}
        pprint.pprint(results)

        # Save models.
        model_fn = puma_fn.replace('.csv', '')
        with open(model_fn + 'bike_model.pkl', 'wb') as f:
            pickle.dump(bike_mdl, f, protocol=pickle.HIGHEST_PROTOCOL)
            
        with open(model_fn + 'dock_model.pkl', 'wb') as f:
            pickle.dump(bike_mdl, f, protocol=pickle.HIGHEST_PROTOCOL)

        with open(model_fn + 'results.pkl', 'wb') as f:
            pickle.dump(bike_mdl, f, protocol=pickle.HIGHEST_PROTOCOL)   
        
        
        
if __name__ == '__main__':
    main()
    
