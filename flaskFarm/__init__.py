import os
from tkinter import Y

from flask import Flask, render_template, request, redirect, session, flash, jsonify
import pandas as pd
import numpy as np
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from flaskFarm import db, utils
from flaskFarm.db import get_db
from flaskFarm.utils import login_required


def create_app(test_config=None):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    app.config["DATABASE"] = os.path.join(
        app.instance_path, "flaskFarm.sqlite")
    app.config["SECRET_KEY"] = "nhu"

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.route("/hello")
    def hello():
        return "Hello, World!"

    # Register database functions with the Flask app
    db.init_app(app)

    # get the database
    with app.app_context():
        db.init_db()

    @app.route("/")
    @login_required
    def index():
        """Show homepage"""
        return render_template("index.html")

    @app.route("/register", methods=["GET", "POST"])
    def register():
        """Register user"""

        # form submitted via POST
        if request.method == "POST":

            username = request.form.get("username")
            password = request.form.get("password")
            db = get_db()
            # Ensure user input a username:
            if not username:
                flash("missing username")
                return render_template("register.html")
            # Ensure user input a password:
            elif not password or not request.form.get("confirmation"):
                flash("missing password")
                return render_template("register.html")

            # Ensure password is match with confirmation
            if request.form.get("password") != request.form.get("confirmation"):
                flash("oops, password doesn't match")
                return render_template("register.html")

            # Generate a hash of the password and add user to database
            usernameCheck = db.execute(
                "SELECT * FROM user WHERE username = ?", (username,)).fetchone()

            print('usernameCHekc', usernameCheck)

            if usernameCheck == None or len(usernameCheck) == 0:
                db.execute("INSERT INTO user (username, hash) VALUES (?, ?)",
                           (username, generate_password_hash(password)),)
                db.commit()
                return redirect("/login")

            # except the case username exist in our database
            elif len(usernameCheck) != 0:
                flash("sorry, this username already existed")
                return render_template("register.html")

        # When request via GET, display registration form
        else:
            return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        """Log user in"""

        # Forget any user_id
        session.clear()
        # User reached route via POST (as by submitting a form via POST)
        if request.method == "POST":

            username = request.form.get("username")
            password = request.form.get("password")
            db = get_db()
            # Ensure username was submitted
            if not username:
                flash("You must provide username")
                return render_template("login.html")
            # Ensure password was submitted
            elif not password:
                flash("You must provide password")
                return render_template("login.html")

            # Query database for username
            user = db.execute(
                "SELECT * FROM user WHERE username = ?", (username,)).fetchone()

            # Ensure user already registered
            if user == None:
                flash("This username haven't been registered!")
                return redirect("/register")
            # Ensure username exists
            if len(user) != 3:
                flash("invalid username")
                return render_template("login.html")
            # Ensure password is correct
            if check_password_hash(user["hash"], password) == False:
                flash("invalid password")
                return render_template("login.html")

            # Remember which user has logged in
            session["user_id"] = user["id"]
            # Redirect user to home page
            return redirect("/")

        # User reached route via GET (as by clicking a link or via redirect)
        else:
            return render_template("login.html")

    @ app.route("/logout")
    def logout():
        """Log user out"""

        # Forget any user_id
        session.clear()

        # Redirect user to login form
        return redirect("/")

    @ app.route("/upload", methods=["GET", "POST"])
    @login_required
    def uploadFiles():
        """Get the uploaded files from user"""

        # get the uploaded file
        if request.method == "POST":
            uploaded_file = request.files["file"]

            # ensure user uploaded file
            if not uploaded_file:
                flash("You need to choose a file to upload")
                return redirect("/upload")

            # set the file path
            if uploaded_file.filename != '':
                file_path = os.path.join(
                    app.instance_path, uploaded_file.filename)
                # save the file
                uploaded_file.save(file_path)
                parseCSV(file_path)
                print('file path is:', file_path)
            flash("Successfully upload")
            return redirect("/")

        # when request via GET, display form to upload a file
        else:
            return render_template('upload.html')

    def validation_data(row):
        """Validate row from db. Row is a pandas.Series of weather, location data"""

        # Validation rules (dict)
        rules = {'metric_type': ['pH', 'temperature', 'rainFall'], 'pH': [
            0, 14], 'temperature': [-50, 100], 'rainFall': [0, 500], }

        # Validate mising date in datetime row
        if not row['datetime']:
            return None
        # Validate valid metric types: only accept pH, temperature, rainFall
        metric_type = row['metric_type']
        if not metric_type in rules['metric_type']:
            return None
        # Validate value of metric type: pH in [0,14], temp [-50, 100], rainfall [0,500]
        metric_value = row['metric_value']
        if metric_value < rules.get(metric_type)[0] or metric_value > rules.get(metric_type)[1]:
            return None
        # Validate metric value is not NULL
        if np.isnan(metric_value) == True:
            return None

        # if row follows validation rules
        return row

    def parseCSV(filePath):
        # CVS Column Names
        col_names = ["Farm_name", "datetime", "metric_type", "metric_value"]
        # Use Pandas to parse the CSV file
        csvData = pd.read_csv(filePath, names=col_names, header=0)

        # get current user_id to query more information
        db = get_db()
        user_id = session.get("user_id")
        user = db.execute(
            "SELECT * FROM user WHERE id = ?", (user_id,)).fetchone()
        username = user["username"]
        # create a new table if the user is new to the site
        # Check if user have their table yet?
        user_table = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (username,)).fetchone()
        if user_table == None:
            db.execute('''CREATE TABLE {} (
                       Farm_name TEXT,
                       date NUMERIC,
                       month NUMERIC,
                       year NUMERIC,
                       metric_type TEXT,
                       metric_value NUMERIC)'''.format(username,))
            db.commit()

        # loops through the row of csvData
        for _, row in csvData.iterrows():

            row = validation_data(row)
            if row is None:
                continue

            # parsing datetime data into 3 specific columns: date, month, year
            # for better query later
            time_value = datetime.strptime(
                row['datetime'], '%Y-%m-%dT%H:%M:%S.%fZ')
            day = time_value.date().day
            month = time_value.date().month
            year = time_value.date().year

            # add data into existing table row by row
            add_to_table = '''INSERT INTO {} (Farm_name, date, month, year, metric_type, metric_Value) VALUES ("{}", {}, {}, {}, "{}", {})'''.format(
                username, row['Farm_name'], day, month, year, row['metric_type'], row['metric_value'])
            db.execute(add_to_table)
            db.commit()

    @ app.route("/visualize")
    @login_required
    def graph():
        """Showing user visualization page"""

        # connect db to query more information
        db = get_db()

        # get current user_id
        user_id = session.get("user_id")
        # from user_id get username to access user table, which is also username
        user = db.execute("SELECT * FROM user WHERE id = ?",
                          (user_id,)).fetchone()
        username = user["username"]

        # Query farm name from user database
        farm = db.execute(
            '''SELECT DISTINCT Farm_name FROM {} '''.format(username,)).fetchone()
        farm_name = farm["Farm_name"]

        flash("Click on any metric button to see your farm's data in below graph.")
        return render_template("graph.html", farm_name=farm_name)

    def queryMetricValueByTime(metric_type):
        """Query metric value by time, assuming user database only have 1 farm"""

        # initial empty dict
        yearly_data = {}

        # connect db to query more information
        db = get_db()

        # get current user_id
        user_id = session.get("user_id")
        # from user_id get username to access user table, which is also username
        user = db.execute("SELECT * FROM user WHERE id = ?",
                          (user_id,)).fetchone()
        username = user["username"]

        # Query year from user database
        years = db.execute(
            '''SELECT DISTINCT year FROM {} '''.format(username,)).fetchall()

        # loop through the year to get all min, max value by month
        for year in years:

            # initial empty dict
            yearly_data[year["year"]] = {}
            yearly_data_append = {}

            # query to get month, min, max metric value
            query = '''SELECT month, MIN(metric_value), MAX(metric_value)
                FROM {}
                WHERE metric_type = '{}' AND year = {} 
                GROUP BY month
                ORDER BY month'''.format(username, metric_type, year["year"])
            valuesByMonth = db.execute(query).fetchall()

            # loop through get all min, max value by month to the existing dict
            for i in range(len(valuesByMonth)):
                month = valuesByMonth[i]["month"]
                min_value = valuesByMonth[i]["MIN(metric_value)"]
                max_value = valuesByMonth[i]["MAX(metric_value)"]
                yearly_data_append[month] = [min_value, max_value]

            # append all values to a year
            yearly_data[year["year"]] = yearly_data_append

        return yearly_data

    @ app.route("/temperature")
    @login_required
    def temperatureData():
        """Query temperature data from user database"""

        yearly_data = queryMetricValueByTime('temperature')
        return jsonify(yearly_data)

    @ app.route("/ph")
    @login_required
    def phData():
        """Query pH data from user database"""

        yearly_data = queryMetricValueByTime('pH')
        return jsonify(yearly_data)

    @ app.route("/rainfall")
    @login_required
    def rainfallData():
        """Query rainFall data from user database"""

        yearly_data = queryMetricValueByTime('rainFall')
        return jsonify(yearly_data)

    return app
