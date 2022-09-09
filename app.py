from flask import Flask, redirect, render_template
from datetime import datetime
from web import *
from urls import *
from tzwhere import tzwhere
import pytz
import sqlite3


app = Flask(__name__)
tzwhere = tzwhere.tzwhere()

categories = [  # replace with user preferences, if ever adding that
        {
        'name': 'Formula 1',
         'api_url': FORMULA1_URL,
         'official_website': 'https://www.formula1.com/en/racing/2022.html'
         },
          {
          'name': 'NTT IndyCar Series', 
          'api_url': INDYCAR_URL, 
          'official_website': 'https://www.indycar.com/Schedule'
          },
          {
          'name': 'Formula E', 
          'api_url': FORMULAE_URL, 
          'official_website': 'https://www.fiaformulae.com/br/championship/race-calendar'
          },
          {
          'name': 'Indy Lights', 
          'api_url': INDYLIGHTS_URL, 
          'official_website': 'https://www.indycar.com/IndyLights'
          },
          # {
          # 'name': 'MotoGP', # not working because sportradar data is different
          # 'api_url': MOTOGP_URL, 
          # 'official_website': 'https://www.motogp.com/en/calendar'
          # },
          {
          'name': 'SuperBike',
          'api_url': SUPERBIKE_URL, 
          'official_website': 'https://www.worldsbk.com/en/calendar'
          },
          # {
          # 'name': 'World Rally Championship',   # not working because sportradar data is different
          # 'api_url': WRC_URL, 
          # 'official_website': 'https://www.wrc.com/en/championship/calendar/wrc/'
          # },

          # nascar not working because sportradar data is different
          ]


@app.route('/')
def index():
    # get data about races
    races = []
    datesStr = []
    datesMs = []
    for category in categories:

        # request all data from sportradar.com
        data = request_data(category['api_url'])

        # find next race
        now = datetime.datetime.now()
        for i, stage in enumerate(data['stages']):
            date_str = stage['stages'][-1]['scheduled'][:-6]  # last 6 chars in string are irrelevant
            date_obj = to_datetime(date_str)

            # ignore past races
            if now > date_obj:
                continue

            # get time remaining until race, in ms
            date_ms = milliseconds(date_obj)
            datesMs.append(date_ms)

            date_strrrrr = date_obj.strftime("%d/%B/%Y %H:%M:%S GMT")
            datesStr.append(date_strrrrr)


            # really horrible fix for track time
            coordinates_str = data['stages'][i]['venue']['coordinates'].split(',')
            latitude, longitude = (float(coordinates_str[0]), float(coordinates_str[1]))
            timezone_str = tzwhere.tzNameAt(latitude, longitude)
            timezone = pytz.timezone(timezone_str)
            trackDateStr = str(timezone.localize(date_obj))
            trackDate = datetime.datetime.strptime(trackDateStr[:-6], "%Y-%m-%d %H:%M:%S")
            symbol = trackDateStr[-6]
            offset = datetime.timedelta(hours=int(trackDateStr[-5:-3]))
            if symbol == '+': 
                trackDate += offset
            else:
                trackDate -= offset

            # get other data
            tmp = {}
            tmp['category'] = category['name']
            tmp['location'] = data['stages'][i]['venue']['name'] + ', ' + data['stages'][i]['venue']['city'] + ', ' + data['stages'][i]['venue']['country']
            tmp['greenwich_time'] = date_obj.strftime("%d/%B/%Y %H:%M:%S")  # %m for month's number (integer), %B for month's name (string)
            tmp['track_time'] = str(trackDate)  
            tmp['user_time'] = date_str # placeholder, not done yet
            tmp['website'] = category['official_website']
            races.append(tmp)

            break

    return render_template('/index.html', races=races, datesMs=datesMs, datesStr=datesStr)


@app.route('/test')
def test():
    return render_template('/test.html')


@app.route('/<route>')
def not_found(route):
    return f'<h1 align="center">404!</h1><p align="center">"{route}" not found</p>'


if __name__ == '__main__':
    app.run()
