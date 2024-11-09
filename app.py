from flask import Flask, flash, redirect, render_template, request, session, url_for, make_response, jsonify
from flask_session import Session
import sqlite3
from datetime import datetime, date, timedelta
import re
import calendar
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_requiered


# Configure the database connection
app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/", methods = ['GET'])
@login_requiered
def home():
    connection = sqlite3.connect('doctrack.db')
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM applications WHERE user_id = ? ORDER BY date ASC", (session["user_id"],))
    applications = cursor.fetchall()
    connection.close()
    
    return render_template("index.html", applications=applications)

@app.route('/login', methods = ['GET','POST']) 
def login():

    session.clear()

    if request.method == 'POST':
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        username = request.form.get("username")

        connection = sqlite3.connect('doctrack.db')
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        rows = cursor.fetchall()
        connection.close()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)
        
        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get("username")
        if not username:
            return apology("Please enter username")

        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        if not password or not confirmation:
            return apology("Please password and confirmation")
        if password != confirmation:
            return apology("Passwords do not match")
        
        hashed_password = generate_password_hash(password)

        try:
            with sqlite3.connect('doctrack.db') as connection:
                cursor = connection.cursor()
                cursor.execute("INSERT INTO users (username, hash) VALUES (?, ?)", (username, hashed_password))
                connection.commit()
        except ValueError:
            return apology("Username is taken", 403)

        username = request.form.get("username")

        connection = sqlite3.connect('doctrack.db')
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        rows = cursor.fetchall()
        connection.close()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)
        
        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        return redirect("/custom")

    else:
        return render_template("register.html")

@app.route("/profile", methods = ['GET'])
@login_requiered
def profile():
    connection = sqlite3.connect('doctrack.db')
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM info WHERE user_id = ? ORDER BY id DESC", (session["user_id"],))
    info = cursor.fetchmany(1)
    connection.close()
    
    return render_template("profile.html", info=info)


@app.route("/forgot", methods=["GET", "POST"])
def forget():

    if request.method == "POST":
        username = request.form.get("username")
        if not username:
            return apology("please enter username")
        password = request.form.get("new_password")
        confirmation = request.form.get("confirm_password")
        if not password or not confirmation:
            return apology("Please provide password and confirmation")
        
        if password != confirmation:
            return apology("Passwords do not match")
        
        with sqlite3.connect('doctrack.db') as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            rows = cursor.fetchall()
           # connection.close()
        # Ensure username exists and password is correct
        if len(rows) != 1:
            return apology("invalid username", 403)
        
        hashed_password = generate_password_hash(password)
        with sqlite3.connect('doctrack.db') as connection:
            cursor = connection.cursor()
            cursor.execute("UPDATE users SET hash = ? WHERE username = ?", (hashed_password, username))
            connection.commit()
            
        return redirect("/login")
        
    return render_template("forgot_pass.html")

@app.route("/add", methods = ['GET', 'POST'])
@login_requiered
def add():
    if request.method == "POST":
        job_title = request.form.get("job_title")
        if not job_title:
            return apology("Please enter job title")
        
        company = request.form.get("company")
        if not company:
            return apology("Please enter company name")
        
        salary = request.form.get("salary")
        if not salary:
            return apology("Please enter salary")

        location = request.form.get("location")
        if not location:
            return apology("Please enter location")
        
        date = request.form.get("date")
        if not date:
            return apology("Please enter date")
        
        with sqlite3.connect('doctrack.db') as connection:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO applications (user_id, job_title, company, salary, location, date) VALUES (?, ?, ?, ?, ?, ?)", (session["user_id"], job_title, company, salary, location, date))
            connection.commit()
        
        return redirect("/")
    
    return render_template("add.html")

@app.route("/custom", methods = ['GET', 'POST'])
def custom():
    if request.method == "POST":
        full_name = request.form.get("full_name")
        if not full_name:
            return apology("Please enter your name")
        
        current_job = request.form.get("current_job")
        if not current_job:
            return apology("Please enter your current employer")
        
        current_salary = request.form.get("current_salary")
        if not current_salary:
            return apology("Please enter your current salary")

        current_location = request.form.get("current_location")
        if not current_location:
            return apology("Please enter your current location")
        
        dob = request.form.get("dob")
        if not dob:
            return apology("Please enter your date of birth")
        
        with sqlite3.connect('doctrack.db') as connection:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO info (user_id, full_name, current_job, current_salary, current_location, dob) VALUES (?, ?, ?, ?, ?, ?)", (session["user_id"], full_name, current_job, current_salary, current_location, dob))
            connection.commit()
        
        return redirect("/")
    
    return render_template("custom.html")
    

@app.route("/calendar", methods=['GET'])
def calendar_disp():
    today=date.today()
    cal = calendar.Calendar()
    month_days = cal.itermonthdates(today.year, today.month)
    weeks = []
    week = []
    for day in month_days:
        week.append(day)
        if day.weekday() == 6:  # Sunday is the last day of the week
            weeks.append(week)
            week = []
    if week:  # Add the last week if it's not empty
        weeks.append(week)
    #first_day_of_month = today.replace(day=1)
    #last_day_of_month = (first_day_of_month.replace(month=today.month + 1) - timedelta(days=1)) if today.month != 12 else (first_day_of_month.replace(year=today.year + 1, month=1) - timedelta(days=1))
    #first_weekday = first_day_of_month.weekday()
    #days_in_month = [first_day_of_month + timedelta(days=i) for i in range((last_day_of_month - first_day_of_month).days + 1)]
    connection = sqlite3.connect('doctrack.db')
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM applications WHERE user_id = ? AND date >= ? ORDER BY date ASC", (session["user_id"], today,))
    events = cursor.fetchall()
    connection.close()
    return render_template('calendar.html', events=events, today=today, weeks=weeks)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
   return render_template("contact.html")

@app.route("/resources")
@login_requiered
def resources():
   return render_template("resources.html")

@app.route("/logout")
@login_requiered
def logout():
    session.clear()
    return redirect("/")

#this route is extra but potentially useful to call this file

#@app.route("/api/data")
#def get_data():
 #   return app.send_static_file("data.json")

#setcookie and getcookie are extra
#@app.route('/setcookie') 
#def setcookie(): 
      # Initializing response object 
 #   resp = make_response('Setting the cookie')  
  ## return resp 
  
#@app.route('/getcookie') 
#def getcookie(): 
 #   GFG = request.cookies.get('GFG') 
  #  return 'GFG is a '+ GFG
