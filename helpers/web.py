import http.client
import json
import datetime
import sys

from flask import session, redirect

from functools import wraps

conn = http.client.HTTPSConnection("api.sportradar.com")


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def request_data(url):
	conn.request("GET", url)
	res = conn.getresponse()
	data = res.read()
	data_string = data.decode("utf-8")
	data_json = json.loads(data_string)
	return data_json


# convert string to datetime
def to_datetime(date_str):
	datetime_format = "%Y-%m-%dT%H:%M:%S"
	datetime_object = datetime.datetime.strptime(date_str, datetime_format)
	d = datetime.datetime(datetime_object.year, datetime_object.month, datetime_object.day, datetime_object.hour, datetime_object.minute, datetime_object.second)
	return d


# convert datetime to something that javascript can use (integer: milliseconds)
def milliseconds(date_obj):
	ms = date_obj.timestamp() * 1000
	return ms
