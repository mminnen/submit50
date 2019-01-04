import os

from flask import Flask, session, render_template, request, redirect, url_for, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import requests, json

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

# Get API key to query Goodreads
goodreads_key = os.getenv("GOODREADS_KEY")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        if db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).rowcount != 0:
           message="That name already exists."  
           return render_template("register.html", message=message) 
        else:
           db.execute("INSERT INTO users (username, password) VALUES (:username, :password)", {"username": username, "password": password })   
           db.commit()
           return render_template("register.html", username=username)  
    else:
        return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        query_user = db.execute("SELECT * FROM users WHERE username = :username AND password = :password", {"username": username, "password": password }).fetchone()       

        if query_user == None:
           message="Login unsuccesful."
           return render_template("login.html", message=message) 

        if query_user[1] == username and query_user[2] == password:
#           message = query_user
           session['logged_in'] = True
           session['username'] = username        
#           return render_template("login.html", username=username)
           return redirect(url_for("search"))

        else:
           message="Login unsuccesful."
           return render_template("login.html", message=message)    

    else:
       return render_template("login.html")


@app.route("/logout")
def logout():
    session['logged_in'] = False
    message="You have been logged out."
    return render_template("Login.html", message=message)

@app.route("/search", methods=['GET', 'POST'])
def search():
    session['logged_in'] = session.get('logged_in', 'False')
    if session['logged_in'] == True:
        if request.method == "POST":
           isbn = "%"+request.form.get('isbn')+"%"
           title = "%"+request.form.get('title')+"%"
           author = "%"+request.form.get('author')+"%"
           results = db.execute("SELECT * FROM books WHERE isbn LIKE :isbn AND title LIKE :title AND author LIKE :author LIMIT 20", {"isbn": isbn, "title": title, "author": author }).fetchall()
#           results = "<a href="+(url_for("result.html")+">"+searchresults+"</a>"
           return render_template("search.html", search=True, results=results)
        
        else:
           return render_template("search.html", search=True)
    else:
           return render_template("search.html", search=False)

@app.route("/result/<isbn>", methods=["GET", "POST"])
def result(isbn):
    if request.method == "GET":
       if session['logged_in'] == True:
          if db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).rowcount != 0:
              message=isbn
              book_result = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchall()
              good_reads = query_goodreads(isbn)

              book_reviews = db.execute("SELECT * FROM review").fetchall()
              if book_reviews == []:
                 reviews = "There are no reviews yet, leave yours now."
              else:
                 reviews = book_reviews

              print(reviews)
              return render_template("result.html", search=True, message=message, book_result=book_result, good_reads=good_reads, reviews=reviews)
          else:
              return render_template('404.html'), 404
       else:
           message = "Unauthorized!"
           return render_template("result.html", search=False, message=message)
    if request.method == "POST":
        username = session['username']
        comment = request.form.get('comment')
        rating = request.form.get('rating')
        if 1 == 1:
           book_result = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchall()
           good_reads = query_goodreads(isbn)
           db.execute("INSERT INTO review (rating, comment, username) VALUES (:rating, :comment, :username)", {"rating": rating, "comment": comment, "username": username })
           reviews = "Your review has been submitted"
           return render_template("result.html", search=True, reviews=reviews, book_result=book_result)
        else:
           reviews = "You cannot leave (another) review!"
           return render_template("result.html", reviews=reviews)
    else:
       return render_template('404.html'), 404

def query_goodreads(isbn):
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": goodreads_key, "isbns": isbn })
    goodreads_avg_rating = res.json()['books'][0]['average_rating']
    return goodreads_avg_rating

@app.route("/api", methods=['GET'])
def api(isbn):
    return render_template("api.html")

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404
