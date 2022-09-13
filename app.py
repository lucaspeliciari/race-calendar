from datetime import datetime
from tempfile import mkdtemp
import os

from flask import Flask, redirect, render_template, session, request
from flask_session import Session
import pytz
from tzwhere import tzwhere
from werkzeug.security import check_password_hash, generate_password_hash

from helpers.categories import categories
from helpers.constants import *
from helpers.database import cur, register_user, delete_user, get_user_categories, remove_user_category, update_user_categories, get_user_setting
from helpers.web import *


print('Starting app...')
app = Flask(__name__)
port = int(os.environ.get("PORT", 5000))
app.config["TEMPLATES_AUTO_RELOAD"] = True

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

tzwhere = tzwhere.tzwhere()

print('App initialized')


@app.route('/')
def index():

    if session.get('id') is not None:
        user_categories = get_user_categories(session['id'])

    # get data about races
    races = []
    datesStr = []
    datesMs = []
    for category in categories:

        if session.get('id') is None or category['name'] in user_categories:

            # request all data from sportradar.com
            data = request_data(category['api_url'])
            last_race = data['stages'][-1]['venue']['name']

            # find next race
            now = datetime.datetime.now()
            for i, stage in enumerate(data['stages']):  # should now take user preferences into account
                date_str = stage['stages'][-1]['scheduled'][:-6]  # last 6 chars in string are irrelevant
                date_obj = to_datetime(date_str)

                try:
                    status = data['stages'][i]['status']
                except KeyError:
                    status = 'Not Cancelled'

                # display past races, or don't
                # ugly
                # if are terrible
                if status == 'Cancelled':
                    continue
                elif now > date_obj:
                    if data['stages'][i]['venue']['name'] != last_race:
                        continue
                    elif session.get('id') is None or not get_user_setting(session['id'], 'Show past races'):
                        continue

                # get time remaining until race, in ms
                date_ms = milliseconds(date_obj)
                datesMs.append(date_ms)

                date_strrrrr = date_obj.strftime("%d/%B/%Y %H:%M:%S GMT")
                datesStr.append(date_strrrrr)

                # really horrible fix for track time
                try:
                    coordinates_str = data['stages'][i]['venue']['coordinates'].split(',')
                except KeyError:
                    coordinates_str = "24.739235,46.583461".split(',')  # API does not provide Marrakesh's coordinates for some reason
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


@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template('/register.html')
    elif request.method == "POST":

        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not username or not password or not confirm_password:
            return render_template('/register.html', warning="You must fill all fields")

        if password != confirm_password:
            return render_template('/register.html', warning="Passwords do not match")

        if len(password) < MIN_PASSWORD_LENGTH or len(password) > MAX_PASSWORD_LENGTH:
            return render_template('/register.html', warning=f"Password must have between {MIN_PASSWORD_LENGTH} and {MAX_PASSWORD_LENGTH} characters")

        user = cur.execute('SELECT * FROM users WHERE username == ?', (username,)).fetchall()
        if len(user) == 1:
            return render_template('/register.html', warning="User already exists")

        # register user
        categories = cur.execute('SELECT * FROM categories').fetchall()
        register_user(username, generate_password_hash(password), len(categories))

        return render_template('/login.html', success="User registered successfully, you can now log in")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        # Ensure username was submitted
        if not username or not password:
            return render_template("login.html", warning='You must fill all fields')

        # Query database for username
        rows = cur.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchall()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0][2], password):
            return render_template("login.html", warning='User / password combination is not valid')

        # Remember which user has logged in
        session["id"] = rows[0][0]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route('/logout')
@login_required
def logout():
    session.clear()
    return redirect ('/')

@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    if request.method == 'GET':
        user_categories = get_user_categories(session['id'])
        category_names = [x['name'] for x in categories]
        return render_template('/account.html', categories=category_names, user_categories=user_categories)

    elif request.method == 'POST':

        if request.form['button'] == 'change_preferences':
            checkboxes = request.form.getlist('category_checkbox')

            update_user_categories(session['id'], checkboxes)

            return redirect('/account')

        elif request.form['button'] == 'delete_account':
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            if not password or not confirm_password:
                return render_template('/account.html', warning_delete="You must fill all fields")
            if password != confirm_password:
                return render_template('/account.html', warning_delete="Passwords do not match")
            delete_user(session['id'])

            return redirect('/logout')


@app.route('/test')
def test():
    remove_user_category(session['id'], 2)
    return redirect('/account')


@app.route('/<route>')
def not_found(route):
    return f'<h1 align="center">404!</h1><p align="center">"{route}" not found</p>'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, debug=True)  # debug lets it restart when changing something
