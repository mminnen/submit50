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
           session['logged_in'] = True
           session['username'] = username        
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
           return render_template("search.html", search=True, results=results)
        
        else:
           return render_template("search.html", search=True)
    else:
           return render_template("search.html", search=False)

@app.route("/result/<isbn>", methods=["GET", "POST"])
def result(isbn):
    book_result = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchall()
    book_reviews = db.execute("SELECT username, rating, comment FROM review JOIN users ON users.id = username_id JOIN books ON books.id = isbn_id WHERE books.isbn = :isbn", {"isbn": isbn}).fetchall()
    if request.method == "GET":
       if session['logged_in'] == True:
          if db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).rowcount != 0:
              message=isbn
              good_reads = query_goodreads(isbn)
              if book_reviews == []:
                 reviews = "There are no reviews yet, leave yours now."
              else:
                 reviews = "Reviews:"
              return render_template("result.html", search=True, message=message, book_result=book_result, good_reads=good_reads, reviews=reviews, book_reviews=book_reviews)
          else:
              return render_template('404.html'), 404
       else:
           message = "Unauthorized!"
           return render_template("result.html", search=False, message=message)
    if request.method == "POST":
        username = session['username']
        comment = request.form.get('comment')
        rating = request.form.get('rating')
        isbn_id = db.execute("SELECT id FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()[0]
        username_id = db.execute("SELECT id FROM users WHERE username = :username", {"username": username}).fetchone()[0]
        if db.execute("SELECT * FROM review WHERE username_id = :username_id AND isbn_id = :isbn_id", {"username_id": username_id, "isbn_id": isbn_id}).rowcount == 0:
           db.execute("INSERT INTO review (rating, comment, username_id, isbn_id) VALUES (:rating, :comment, :username_id, :isbn_id)", {"rating": rating, "comment": comment, "username_id": username_id, "isbn_id": isbn_id })
           db.commit()
           reviews = "Your review has been submitted"
           return render_template("result.html", search=True, reviews=reviews, book_result=book_result)
        else:
           reviews = "You cannot leave (another) review!"
           return render_template("result.html", search=True, reviews=reviews, book_result=book_result)
    else:
       return render_template('404.html'), 404

def query_goodreads(isbn):
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": goodreads_key, "isbns": isbn })
    goodreads_avg_rating = res.json()['books'][0]['average_rating']
    return goodreads_avg_rating

@app.route("/api/<isbn>", methods=['GET'])
def api(isbn):
    if db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).rowcount != 0:
       api_result = db.execute("SELECT title, author, year, isbn, COUNT(rating), AVG(rating) FROM review JOIN books on books.id = isbn_id WHERE books.isbn = :isbn GROUP by title, author, year, isbn", {"isbn": isbn}).fetchall()
       title = api_result[0][0]
       author = api_result[0][1]
       year = api_result [0][2]
       # isbn = api_result [0][3]
       review_count = api_result [0][4]
       average_score = round(api_result [0][5], 1)
       return render_template("api.json", title=title, author=author, year=year, isbn=isbn, review_count=review_count, average_score=average_score)
    else:
       return render_template('404.html'), 404

@app.errorhandler(404)
def page_not_found(e):
   return render_template('404.html'), 404
