import os
from flask import render_template, url_for, redirect
from flask_wtf import FlaskForm
from wtforms.fields.html5 import DateField
from wtforms import FloatField
from wtforms_components import TimeField
from wtforms.validators import DataRequired
from app.main import bp
from datetime import datetime

@bp.route('/')
@bp.route('/home')
def home():
    user = {'username': 'Miguel'}
    posts = [
        {
            'author': {'username': 'John'},
            'body': 'Beautiful day in Portland!'
        },
        {
            'author': {'username': 'Susan'},
            'body': 'The Avengers movie was so cool!'
        }
    ]
    return render_template('home.html', title='Home', user=user, posts=posts)

@bp.route('/aboutme')
def aboutme():
    return render_template('aboutme.html')

@bp.route('/categories')
def categories():
    return render_template('categories.html')

@bp.route('/posts')
def posts():
    return render_template('posts.html')

@bp.route('/posts/<year>/<month>/<date>/<title>')
def blogpost(year, month, date, title):
    if title.endswith('.html') == False:
        title += '.html'
    url = os.path.join('posts', year, month, date, title)
    return render_template(url)


class ExampleForm(FlaskForm):
    dt = DateField('DatePicker', format='%Y-%m-%d',
                   default=datetime.today,
                   validators=[DataRequired()])
    
    start_time = TimeField('Start Time', default=datetime.now,
                       validators=[DataRequired()])
    
    start_lat = FloatField('Start Latitude',
                           default=40.677537,
                           validators=[DataRequired()])
    start_long = FloatField('Start Longitude',
                            default=-73.959066,
                            validators=[DataRequired()])
    
    end_lat = FloatField('End Latitude',
                         default=40.7395441,
                         validators=[DataRequired()])
    end_long = FloatField('End Longitude',
                          default=-73.9885504,
                          validators=[DataRequired()])

from citibike_only_copy import SearchRoutes
    
@bp.route('/query_map', methods=['POST','GET'])
def query_map():

    form = ExampleForm()
    if form.validate_on_submit():
        """
        sr = SearchRoutes()
        r = sr.start_to_end([form.start_lat.data,
                             form.start_long.data],
                             [form.end_lat.data,
                              form.end_long.data])


        inds =  sr.stations['id'] == r[1]

        answer = 'Walk to the citibike station at {}.\n'.format(sr.stations[inds].stationName.values[0])
        inds = sr.stations['id'] == r[2]
        answer += 'Bike to the citibike station at {}.\n'.format(sr.stations[inds].stationName.values[0])
        answer += "Continue to your final location."
        """
        answer = """
        Walk to the citibike station at Classon Ave & St Marks Ave. 
Bike to the citibike station at Broadway & W 41 St. Continue to your final location.
        """
        start_station = "Classon Ave & St Marks Ave."
        end_station = "Broadway & W 41 St."
        return render_template('query_map.html', form=form, answer=answer,
                               start_station=start_station, end_station = end_station)
    return render_template('query_map.html', form=form, answer='none')
    
