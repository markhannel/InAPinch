#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
live_citibike_feed requests the latest citibike feed and appends it to the postgreSQL 
database with historical live feed data.
"""

import requests
import psycopg2
import os
import json
from dotenv import load_dotenv
from datetime import datetime
import time
import pytz

# Load necessary environment variables.
dotenv_path = 'citibike_live_feed.env'
load_dotenv(dotenv_path)
DB_NAME = os.environ.get("DB_NAME")
DB_PW = os.environ.get("DBPW")
HOST = os.environ.get("HOST")
USER = os.environ.get("USER")
LIVE_URL = 'https://gbfs.citibikenyc.com/gbfs/es/station_status.json'

# SQL Commands.
CREATION_CMD = """CREATE TABLE citibike_station_feed (
        id         SERIAL PRIMARY KEY,
        station_id           SMALLINT NOT NULL,
        num_bikes_available  SMALLINT NOT NULL,
        num_ebikes_available SMALLINT NOT NULL,
        num_bikes_disabled   SMALLINT NOT NULL,
        num_docks_available  SMALLINT NOT NULL,
        num_docks_disabled   SMALLINT NOT NULL,
        is_installed         SMALLINT NOT NULL,
        is_renting           SMALLINT NOT NULL,
        is_returning         SMALLINT NOT NULL,
        last_reported        INT      NOT NULL,
        eightd_has_available_keys BOOL NOT NULL,
        eightd_active_station_services VARCHAR,
        datetime             TIMESTAMPTZ NOT NULL
        );"""

LOAD_CMD = """INSERT INTO citibike_station_feed VALUES (
       DEFAULT,
       %s,
       %s,
       %s,
       %s,
       %s,
       %s,
       %s,
       %s,
       %s,
       %s,
       %s,
       %s,
       %s
       );"""


def main():
    
    connection = None # Declared in case of failed connection.
    try:
        # Connect to DB.
        connection = psycopg2.connect(database=DB_NAME,
                                      password=DB_PW,
                                      user=USER,
                                      host=HOST)

        cursor = connection.cursor()
        print("Connected!")

        # Create Table.
        cursor.execute(CREATION_CMD)
        print("Table created!")
        



        
        starttime=time.time()
        while True:
            print('Pinging citibike.')
            # Load Citibike feed.
            r = requests.get(LIVE_URL).json()
            for station in r['data']['stations']:

                
                # Correct for possibly missing entry.            
                if 'eightd_active_station_services' not in station.keys():
                    station.update({'eightd_active_station_services':'none'})
                else:
                    station['eightd_active_station_services'] = station['eightd_active_station_services'][0]['id']
                    
                station['datetime'] = datetime.now(pytz.timezone("America/New_York"))
                cursor.execute(LOAD_CMD, (station['station_id'],
                                          station['num_bikes_available'],
                                          station['num_ebikes_available'],
                                          station['num_bikes_disabled'],
                                          station['num_docks_available'],
                                          station['num_docks_disabled'],
                                          station['is_installed'],
                                          station['is_renting'],
                                          station['is_returning'],
                                          station['last_reported'],
                                          station['eightd_has_available_keys'],
                                          station['eightd_active_station_services'],
                                          station['datetime']))

            try:
                time.sleep(10.0 - ((time.time() - starttime) % 10.0))
            except KeyboardInterrupt:
                raise 
        
        # Close cursor.
        cursor.close()

    except psycopg2.OperationalError:
        print("Connection failed. Try again.")
        
    finally:
        if connection is not None:
            connection.commit()
            connection.close()
            print("Connection closed!")
        
        
    # Request the livefeed data.

    # Update the database with information.

if __name__ == '__main__':
    main()
