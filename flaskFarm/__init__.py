import os

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

    @ app.route("/demoapi")
    def demo():
        demoData = [{'Farm_name': 'Friman Metsola collective', 'date': 31, 'month': 12,
                     'year': 2018, 'metric_type': 'pH', 'metric_value': 6.52},
                    {'Farm_name': 'Friman Metsola collective', 'date': 31, 'month': 12,
                     'year': 2018, 'metric_type': 'rainFall', 'metric_value': 2.6},
                    {'Farm_name': 'Friman Metsola collective', 'date': 1, 'month': 1,
                     'year': 2019, 'metric_type': 'temperature', 'metric_value': -9},
                    {'Farm_name': 'Friman Metsola collective', 'date': 1, 'month': 1,
                     'year': 2019, 'metric_type': 'temperature', 'metric_value': -12.2},
                    {'Farm_name': 'Friman Metsola collective', 'date': 1, 'month': 1,
                     'year': 2019, 'metric_type': 'temperature', 'metric_value': -8.9},
                    {'Farm_name': 'Friman Metsola collective', 'date': 1, 'month': 1,
                     'year': 2019, 'metric_type': 'temperature', 'metric_value': -8.6},
                    {'Farm_name': 'Friman Metsola collective', 'date': 1, 'month': 1,
                     'year': 2019, 'metric_type': 'temperature', 'metric_value': -8.4},
                    {'Farm_name': 'Friman Metsola collective', 'date': 31, 'month': 12,
                     'year': 2018, 'metric_type': 'temperature', 'metric_value': -13.9}]
        return jsonify(demoData)

    @ app.route("/demograph")
    def graph():

        return render_template("graph.html")

    @ app.route("/temperature")
    @login_required
    def temperatureData():
        yearly_data = {
            2018: {'Jan': [-13.9, -2], 'Feb': [-8.8, 0], 'Mar': [-8, 1], 'Apr': [-7, 3]},
            2019: {'Jan': [-1, 5], 'Feb': [-8.8, 4], 'Mar': [-5, 1], 'Apr': [-1, 10]}
        }
        return jsonify(yearly_data)

    @ app.route("/ph")
    @login_required
    def phData():
        yearly_data = {
            2018: {'Jan': [0, 2], 'Feb': [2, 3], 'Mar': [2, 5], 'Apr': [4, 8]},
            2019: {'Jan': [0, 4], 'Feb': [2, 6], 'Mar': [8, 10], 'Apr': [5, 10]}
        }
        return jsonify(yearly_data)

    @ app.route("/rainfall")
    @login_required
    def rainfallData():
        yearly_data = {
            2018: {'Jan': [0, 0], 'Feb': [100, 500], 'Mar': [400, 500], 'Apr': [200, 300]},
            2019: {'Jan': [0, 50], 'Feb': [40, 150], 'Mar': [200, 300], 'Apr': [100, 400]}
        }
        return jsonify(yearly_data)

    return app
