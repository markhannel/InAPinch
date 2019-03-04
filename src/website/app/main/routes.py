import os
from flask import render_template, url_for, redirect
from flask_wtf import FlaskForm
from wtforms.fields.html5 import DateField
from wtforms import FloatField
from wtforms_components import TimeField
from wtforms.validators import DataRequired
from app.main import bp
from datetime import datetime, timedelta
import requests
from citibike import SearchRoutes, Station, Directions
import pandas as pd
from flask import current_app

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
        station_update = pd.DataFrame(cb_req['data']['stations'])
        
        # Pick a route.
        r = SR.start_to_end([form.start_lat.data,
                             form.start_long.data],
                             [form.end_lat.data,
                              form.end_long.data])

        if len(r) > 2:
            # Station information.
            start = Station(r[1])
            start.lat  = STATION_INFO.query('station_id == "{}"'.format(r[1])).lat.values[0]
            start.long = STATION_INFO.query('station_id == "{}"'.format(r[1])).lon.values[0]
            start.name = STATION_INFO.query('station_id == "{}"'.format(r[1])).name.values[0]
            start.bikes_avail = station_update.query('station_id == "{}"'.format(r[1])).num_bikes_available.values[0]
            start.docks_avail = station_update.query('station_id == "{}"'.format(r[1])).num_docks_available.values[0]
            
            # Naive Model.
            start.bikes_avail_future = start.bikes_avail
            start.docks_avail_future = start.docks_avail
        
            end = Station(r[2])
            end.lat  = STATION_INFO.query('station_id == "{}"'.format(r[2])).lat.values[0]
            end.long = STATION_INFO.query('station_id == "{}"'.format(r[2])).lon.values[0]
            end.name = STATION_INFO.query('station_id == "{}"'.format(r[2])).name.values[0]
            end.docks_avail = station_update.query('station_id == "{}"'.format(r[2])).num_docks_available.values[0]
            end.bikes_avail = station_update.query('station_id == "{}"'.format(r[2])).num_bikes_available.values[0]
        
            # Naive model.
            end.bikes_avail_future = end.bikes_avail
            end.docks_avail_future = end.docks_avail
            
            
            # Directions.
            first_leg = Directions([form.start_long.data, form.start_lat.data],
                                   [start.long, start.lat], mode='foot')
            second_leg = Directions([start.long, start.lat], [end.long, end.lat],
                                    mode='cycle')
            third_leg = Directions([end.long, end.lat], [form.end_long.data, form.end_lat.data],
                                   mode='foot')

            # Feeding the prediction engine.
            current_time = datetime.utcnow() - timedelta(hours=5)
            current_interval = (current_time.hour*60 + current_time.minute)//15
            time_left_first_interval = ((current_time.hour*60 + current_time.minute) % 15)/15
            time_to_rental = first_leg.duration//60
            time_to_return = (first_leg.duration + second_leg.duration)//60
            weekend = current_time.weekday()//5
            
            start.predict_no_bikes(current_interval, time_to_rental, weekend=weekend,
                                   timeleft = 0, raining=0.0)
            
            end.predict_no_bikes(current_interval, time_to_return, weekend=weekend,
                                 timeleft = 0, raining=0.0)

            total_prob = end.at_least_one_dock * start.at_least_one_bike * 100
            total_prob = min(total_prob, 99)
            total_prob = max(total_prob, 1)

            end.bikes_avail_future = round(end.bikes_avail_future)
            
            # Render template with stations and directions.
            return render_template('home.html', form=form, answer=True,
                                   start=start, end=end,
                                   first_leg=first_leg,
                                   second_leg=second_leg,
                                   third_leg=third_leg,
                                   total_prob=total_prob)

        else:
            # Walking directions.
            return render_template('home.html', form=form, answer='none')
    
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
                         default=40.7512341,
                         validators=[DataRequired()])
    end_long = FloatField('End Longitude',
                          default=-73.9829001,
                          validators=[DataRequired()])
