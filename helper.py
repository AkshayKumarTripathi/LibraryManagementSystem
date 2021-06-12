from flask import Flask, render_template ,request , redirect
from datetime import datetime
from flask.helpers import url_for
from flask_sqlalchemy import SQLAlchemy
import requests

app = Flask(__name__)

app.config ['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Library.db'
db = SQLAlchemy(app)

# This is The Base Url from which we will make the imports
BASE_URL = 'https://frappe.io/api/method/frappe-library?'

# Table Books for storing Books.
class Books(db.Model):
    book_id = db.Column(db.Integer , primary_key = True)
    book_name = db.Column(db.String(150))
    author = db.Column(db.String(75))
    publisher = db.Column(db.String(75))
    quantity = db.Column(db.Integer , default = 1)
    borrower = db.Column(db.Integer , default = -1)
    isbn = db.Column(db.String(15))
    times_issued = db.Column(db.Integer , default = 0)
    
# Table Members for storing the member details.
class Members(db.Model):
    member_id = db.Column(db.Integer , primary_key = True)
    member_name = db.Column(db.String(150))
    member_balance = db.Column(db.Float , default = 1000)
    member_borrowed = db.Column(db.Boolean, default = False)
    library_fees_given = db.Column(db.Float , default = 0)

# Table Transactions for storing all the transactions details.
class Transactions(db.Model):
    _id = db.Column(db.Integer , primary_key = True)
    book_name =  db.Column(db.String(150))
    member_name = db.Column(db.String(150))
    direction = db.Column(db.Boolean, default = True)
    time = db.Column(db.DateTime , default = datetime.utcnow)


# checks if a string is alphabetical
def is_alphabets(s : str):
    return ''.join(s.split()).isalpha()


# This Function Makes The API call and returns The response
def make_API_call():
    title , authors , isbn , publisher = request.form['title'] , request.form['author'], request.form['isbn'], request.form['publisher']

    end = ''

    if title or authors or isbn or publisher:
        end = f'title={title}&authors={authors}&isbn={isbn}publisher={publisher}'
    
    response = requests.get(BASE_URL+end).json()['message']

    return response