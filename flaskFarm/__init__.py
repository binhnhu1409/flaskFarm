import os

from flask import Flask, render_template, request, redirect, session, flash
import pandas as pd
from werkzeug.security import check_password_hash, generate_password_hash

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
            return redirect("/")

        # when request via GET, display form to upload a file
        else:
            return render_template('upload.html')

    def parseCSV(filePath):
        # CVS Column Names
        col_names = ["Farm_name", "datetime", "metric_type", "metric_value"]
        # Use Pandas to parse the CSV file
        csvData = pd.read_csv(filePath, names=col_names, header=None)
        print(csvData)

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
        print('user table:', user_table)
        if user_table == None:
            db.execute('''CREATE TABLE {} (
                       Farm_name TEXT NOT NULL,
                       datetime DATETIME,
                       metric_type TEXT NOT NULL, 
                       metric_value NUMERIC NOT NULL)'''.format(username,))
            db.commit()

        else:

            db.execute()
    return app
