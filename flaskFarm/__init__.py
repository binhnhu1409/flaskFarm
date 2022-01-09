import os
from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
from flaskFarm import db


def create_app(test_config=None):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    app.config["DATABASE"] = os.path.join(
        app.instance_path, "flaskFarm.sqlite")

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.route("/hello")
    def hello():
        return "Hello, World!"

    db.init_app(app)

    # get the database
    with app.app_context():
        db.init_db()

    # Get the uploaded files

    @app.route("/upload", methods=["GET", "POST"])
    def uploadFiles():

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
        col_names = ["Farm name", "datetime", "metric type", "metric value"]
        # Use Pandas to parse the CSV file
        csvData = pd.read_csv(filePath, names=col_names, header=None)
        print(csvData)

    return app
