import os
from flask import render_template, url_for, redirect
from flask_wtf import FlaskForm
from wtforms.fields.html5 import DateField
from wtforms import FloatField
from wtforms_components import TimeField
from wtforms.validators import DataRequired
from app.main import bp
from datetime import datetime
import requests
from citibike_only_copy import SearchRoutes, get_directions, extract_polylines
import pandas as pd

# Global variables for route information.
CB_INFO_URL = "https://gbfs.citibikenyc.com/gbfs/es/station_information.json"
CB_STATUS_URL = "https://gbfs.citibikenyc.com/gbfs/en/station_status.json"
OSRM_URL = 'https://127.0.0:5000/route/v1/bicycle/{},{};{},{}?steps=true'
SR = SearchRoutes()
#ROUTES = pd.read_csv('../../data/citibike/all_stations_docks.csv', sep='\t')

# Get Station information.
r = requests.get(CB_INFO_URL).json()
STATION_INFO = pd.DataFrame(r['data']['stations'])


@bp.route('/', methods=['POST','GET'])
@bp.route('/home', methods=['POST','GET'])
def home():

    form = ExampleForm()
    if form.validate_on_submit():
        # Get latest Citi Bike info.
        cb_req = requests.get(CB_STATUS_URL).json()        
        
        # Pick a route.
        r = SR.start_to_end([form.start_lat.data,
                             form.start_long.data],
                             [form.end_lat.data,
                              form.end_long.data])


        # Walking directions to station.
        start_station_lat = STATION_INFO.query('station_id == "{}"'.format(r[1])).lat.values[0]
        start_station_lon = STATION_INFO.query('station_id == "{}"'.format(r[1])).lon.values[0]
        
        end_station_lat = STATION_INFO.query('station_id == "{}"'.format(r[2])).lat.values[0]
        end_station_lon = STATION_INFO.query('station_id == "{}"'.format(r[2])).lon.values[0]
        
        start_station_name = STATION_INFO.query('station_id == "{}"'.format(r[1])).name.values[0]
        end_station_name   = STATION_INFO.query('station_id == "{}"'.format(r[2])).name.values[0]

        walk_to_station = get_directions([form.start_long.data, form.start_lat.data],
                                         [start_station_lon, start_station_lat], mode='foot')
        bike_directions = get_directions([start_station_lon, start_station_lat],
                                         [end_station_lon, end_station_lat], mode='cycle')
        walk_to_destination = get_directions([end_station_lon, end_station_lat],
                                         [form.end_long.data, form.end_lat.data], mode='foot')

        station_polylines = extract_polylines(walk_to_station)
        bike_polylines = extract_polylines(bike_directions)
        destination_polylines = extract_polylines(walk_to_destination)

        # Get route directions.
        return render_template('home.html', form=form, answer=True,
                               start_station=start_station_name,
                               end_station = end_station_name,
                               start_lat=start_station_lat,
                               start_lon=start_station_lon,
                               end_lat=end_station_lat,
                               end_lon=end_station_lon,
                               station_polylines=station_polylines,
                               bike_polylines=bike_polylines,
                               destination_polylines=destination_polylines,
                               station_duration = walk_to_station['duration'],
                               bike_duration = bike_directions['duration'],
                               destination_duration = walk_to_destination['duration'])
    return render_template('home.html', form=form, answer='none')

@bp.route('/aboutme')
def aboutme():
    return render_template('aboutme.html')

class ExampleForm(FlaskForm):
    dt = DateField('DatePicker', format='%Y-%m-%d',
                   default=datetime.today,
                   validators=[DataRequired()])
    
    start_time = TimeField('Start Time', default=datetime.now,
                       validators=[DataRequired()])
    
    start_lat = FloatField('Start Latitude',
                           default=40.670589,
                           #default=40.677537,
                           validators=[DataRequired()])
    start_long = FloatField('Start Longitude',
                            default=-73.9498344,
                            #default=-73.959066,
                            validators=[DataRequired()])
    
    end_lat = FloatField('End Latitude',
                         default=40.7395441,
                         validators=[DataRequired()])
    end_long = FloatField('End Longitude',
                          default=-73.9885504,
                          validators=[DataRequired()])
