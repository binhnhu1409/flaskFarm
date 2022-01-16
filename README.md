# :herb: flaskFarm :herb: 
**flaskFarm** is a humble Flask based web application for farm management, for instance, loading & visualization data and etc. Potential users could be a farm manager or a farmer. Once users register, this tool will allow them to upload their farm data, which might take a while if the data is big. It will also show uploaded data in form of graphs when users click in any metric button. In regarding of uploading farm data, the users need to follow certain requirements as mentioned on the page itself. This version *currently  only support a farm for each user* meaning your [Farm name] should be the same when upload CSV file.

## [flaskFarm deploy page](https://flask-farm-ii6rp.ondigitalocean.app/register)

As I deployed this project on DigitalOcean with low budget, there is a limitation on how big your CSV file is without crashing the app. You can register as a user to play around with this [sample data](https://github.com/binhnhu1409/flaskFarm/blob/main/flaskFarm/static/sample_data_Nooras_farm.csv)

![image](https://github.com/binhnhu1409/flaskFarm/blob/main/flaskFarm/static/readme_image/sample.JPG)
![image](https://github.com/binhnhu1409/flaskFarm/blob/main/flaskFarm/static/readme_image/sample2.JPG)

![image](https://github.com/binhnhu1409/flaskFarm/blob/main/flaskFarm/static/readme_image/upload_page.png)

## Project structure
This is my first project working on backend.
```
FARM
│   .gitignore
│   LICENSE
│   README.md
│   setup.cfg
│   setup.py
│
└───flaskFarm
    |    db.py
    │    schema.sql
    │    utils.py
    │    __init__.py
    │
    ├───static
    │       style.css
    |       image
    │
    └───templates
            index.html
            graph.html
            layout.html
            login.html
            register.html
            upload.html
```
### Feature included:
- User login/ logout/ register
- Upload data in CSV format
- Visualization farm's data in bar chart by monthly min, max values.

### Tasks have been done:
- CSV parsing and validation
- Endpoints to fetch data by metric
- Show summarized data in graphs
- Add filtering options by metric
- Add user login for data manipulation


## How to run this web application
This project was built on **Window** using **Visual Studio Code**. So the instruction currently is available for Window only as no test has been done on other operating systems. Before compiling and run the project, make sure:

### Installation: create new environment
- **Python 3.9.5**
- Python should include **pip** by itself, however, make sure your Python including pip by executing in Command Prompt (CMD):
	```
	python.exe -m pip
	```
- To avoid conflict among libraries on your default global environment, you need to create and activate a **virtual environment** for this web app by executing the below command in CMD in the same cmd default path location *(C:/Users/[user_name])*
	```
	py -m venv FlaskEnv
	```
    If you have more than one version of Python in your computer, you should clarify which version of Python you would like to create virtual environment.
	```
	FlaskEnv\Scripts\activate.bat
	```
    You can use whatever name you like, however, as I created this project based on Flask, I gave it the name FlaskEnv, which is short for "this virtual environment is using for Flask". For demo purpose, I'll use the name FlaskEnv for virtual environment that I installed from now on.

After activate your CMD should look like:

![image](https://github.com/binhnhu1409/flaskFarm/blob/main/flaskFarm/static/readme_image/activate_venv.png)

### Install FLASK
- Before install Flask, remember to activate your virtual environment whenever you open a new CMD:
- In default path location, install Python package of Flask using:
		```
		pip install Flask
		```
### Download flaskFarm
- Download the whole flaskFarm repository from: [flaskFarm](https://github.com/binhnhu1409/flaskFarm)
- Open Visual Studio Code, in the left bottom corner, choose virtual environment creating for this project by choosing the file **python.exe** inside *Scripts* folder of *FlaskEnv*.
- In terminal window, activate virtual environment, then run:
    ```
    set FLASK_APP=flaskFarm
    set FLASK_ENV=development
    flask run
    ```
- After *flask run* you should be see a link like this, click into that link to access the web app:

![image](https://github.com/binhnhu1409/flaskFarm/blob/main/flaskFarm/static/readme_image/flask%20run.png)


## Used technologies:
### Front-end:
- HTML
- CSS
- Chartjs
- JavaScript
- Bootstrap

### Back-end:
- Python
- Flask
- SQLite3
- RestAPI 















 
