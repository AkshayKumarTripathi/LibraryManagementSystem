# imports - standard imports
from datetime import datetime
from random import randint
import sqlite3

# imports - third party imports
from flask import Flask, render_template, request, redirect, flash
from flask.helpers import url_for
from flask_sqlalchemy import SQLAlchemy
import requests
from werkzeug.wrappers import response

# setting up Flask instance
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Library.db'

db = SQLAlchemy(app)

# Creating Tables

# Table Books for storing Books.
class Books(db.Model):
    # Table Books  => | book_id | book_name | author | publisher | quantity | borrower | isbn | times_issued | 

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
    # Table members => | member_id | member_name | member_balance | member_borrowed | library_fees_given |

    member_id = db.Column(db.Integer , primary_key = True)
    member_name = db.Column(db.String(150))
    member_balance = db.Column(db.Float , default = 1000)
    member_borrowed = db.Column(db.Boolean, default = False)
    library_fees_given = db.Column(db.Float , default = 0)

# Table Transactions for storing all the transactions details.
class Transactions(db.Model):
    # Table Transactions => | _id | book_name | member_name | direction | time |

    _id = db.Column(db.Integer , primary_key = True)
    book_name =  db.Column(db.String(150))
    member_name = db.Column(db.String(150))
    direction = db.Column(db.Boolean, default = True)
    time = db.Column(db.DateTime , default = datetime.utcnow)


# Home Directory
@app.route('/')
def home():
    available_books = Books.query.all()
    return render_template('home.html' , books = available_books)


@app.route('/members', methods = ["POST" , "GET"])
def members():
    # Table members => | member_id | member_name | member_balance | member_borrowed | library_fees_given |

    # it takes the new member's information and adds in the data base.

    if request.method == "POST":

        user_name = request.form['user_name']     # getting the user Name
        member_balance = request.form['balance']  # getting the amount the user wants to add initially

        if not is_alphabets(user_name): 
            # This means the Librarian has entered wrong data
            message = "Please enter correct User-Name"
            return render_template('error.html', message = message, page = "members")
        
        if not member_balance.isnumeric():
            # This means the Librarian has entered wrong balance
            message = "Please enter correct balence"
            return render_template('error.html',
                                    message = message,
                                    page = "members"
                                    )
        
        # Every Thing is Correct
        try:
            
            # Creating record
            member = Members(
                            member_name=user_name,
                            member_balance = float(member_balance)
                            ) 
                            
            db.session.add(member)  # adding in the DB 
            db.session.commit()     # commiting changes
            
        except:

            return render_template('error.html', message = "Unexpected Error, Cannot add Member")

    # no matter if the method is GET or POST we need to render the available member list.
    members = Members.query.all()                               # Getting all the members
    return render_template('members.html', members = members)   # rendering the page for members
        

# this function loads all the transactons
@app.route('/transactions')
def transactions():
    # Table Transactions => | _id | book_name | member_name | direction | time |

    # Taking all the transactions and arranging them from most recent to least recent.

    transactions = Transactions.query.order_by(Transactions.time.desc()).all() 
    return render_template('transactions.html', transactions = transactions)


# Renders Analytics Page
@app.route('/analytics')
def analytics():

    # Table Books   => | book_id | book_name | author | publisher | quantity | borrower | isbn | times_issued
    # Table members => | member_id | member_name | member_balance | member_borrowed | library_fees_given |

    # This query takes the top 5 popular Books which were issued most number of times
    popular_books = Books.query.order_by(Books.times_issued.desc()).limit(5).all()

    # This query takes the top 5 people who have spent the most
    top_spenders  = Members.query.order_by(Members.library_fees_given.desc()).limit(5).all()

    return render_template('analytics.html', books = popular_books , people = top_spenders)


# Logic for renting out a book
@app.route('/rent_out/<int:book_id>', methods = ["POST" , "GET"])
def rent_out(book_id):

    # Table Books        => | book_id | book_name | author | publisher | quantity | borrower | isbn | times_issued
    # Table members      => | member_id| member_name | member_balance | member_borrowed | library_fees_given |
    # Table Transactions => | _id | book_name | member_name | direction | time |

    # Render only those members who have not borrowed a book
    all_members = Members.query.filter(
                            Members.member_borrowed == False
                            ).all()

    if request.method == "POST":

        # getting the id of the member.
        id_of_the_member = request.form['id']

        # if The entered member ID is invalid.
        if not id_of_the_member.isnumeric():
            return render_template('error.html', message = "Enter valid Id")

        # Get the member from the form data.
        member = Members.query.get(int(id_of_the_member))
        
        # check if member is present or not:
        if member == None:
            return render_template('error.html', message = "Not A valid Member!")

        if member.member_balance < -500:
            # Users Balance is less Than 500

            message = f'The balance of {member.member_name} is {member.member_balance} \
            which is less than -500 so please add money to your wallet before taking books.'

            return render_template('error.html', message = message)
        
        if member.member_borrowed==True:
            # User has already borrowed a book.

            message = 'The User has already Taken Books'
            return render_template('error.html' , message= message)
        

        try:

            member.member_borrowed = True   # Member has borrowed a book.
            member.member_balance -= 500    # members balance Should Decrease by 500.
            member.library_fees_given += 500    # Member paid 500 rs to the Library.

            book = Books.query.get(book_id)         # Get the book from the book_ID.
            if book == None:
                return render_template('error.html', message = "Unexpected Error Occured")
                
            
            book.quantity = 0   # Book's quantity is decreased.
            book.times_issued += 1  # books Times issued is increased by 1.
            book.borrower = member.member_id    # Books borrower is set to the id of member's id.

            # New transaction is registered and added to transactions.
            trans = Transactions(
                                book_name = book.book_name,
                                member_name = member.member_name,
                                direction = False
                                )

            db.session.add(trans)
            db.session.commit()

            return redirect(url_for('home'))

        except:

            return render_template(
                                'error.html',
                                message = "Unexpected Error Occured"
                                )
        
    return render_template(
                        'rent_out.html',
                        id = book_id,
                        members = all_members
                        )


# This function Makes the API calls and then redirects to the home page.
@app.route('/addBooks', methods = ["POST" , "GET"])
def addBooks():

    # Table Books => | book_id | book_name | author | publisher | quantity | borrower | isbn | times_issued |

    if request.method == "POST":

        # GET the data from the API.
        # pass the data in LMS and then redirect to root page.
        # render the data recieved.

        # Gets the data from The API.
        response = make_API_call()

        # going through data.
        for data in response:

            # getting the book ID from the form.
            book_id = int(data["bookID"])

            # Checking if the same data exists in the data base or not.
            to_find = Books.query.get(book_id)

            if to_find == None:

                # If book is not found in the data base then add it in the data base.
                book = Books(
                            book_id = book_id,
                            book_name = data["title"],
                            author = data["authors"],
                            publisher =data["publisher"],
                            isbn = data["isbn"]
                            )

                db.session.add(book)
                db.session.commit()
            
        # rendering page using jinja and then redirect.
        return redirect(url_for('home'))

    else:

        return render_template('add_books.html')


@app.route('/addCustomBooks', methods=["POST"])
def add_custom_books():
    if request.method == "POST":
        book_id = request.form['book_id']
        book_name = request.form['book_name']
        author = request.form['author']
        publisher = request.form['publisher']
        isbn = request.form['isbn'] or 404

        # checking for if book_id already exists or not and values are valid
        
        if not book_id.isnumeric():
            return render_template(
                                'error.html',
                                message = "Please enter a valid book ID"
                                )
        
        book_id = int(book_id)
        if Books.query.get(book_id) != None:
            return render_template('error.html', message = "Book Id already Exists in DB")

        if not is_alphabets(author):
            return render_template(
                                'error.html',
                                message = "Enter a valid author (should not contain numbers)"
                                )

        # every thing is valid 
        try:
            book = Books(
                        book_id = book_id,
                        book_name = book_name,
                        author = author,
                        publisher = publisher,
                        isbn = isbn
                        )

            db.session.add(book)
            db.session.commit()
            return redirect(url_for('home'))

        except:
            return render_template('error.html', message = "Unexpected Error")
        

    else:
        return render_template('error.html', message = "NOT AUTHORIZED")



# renders all the books which are currently rented Out.
@app.route('/return_book')
def return_book():

    #  Table Books => | book_id | book_name | author | publisher | quantity | borrower | isbn | times_issued |

    books = Books.query.filter(
                        Books.quantity == 0     # render only those books which have been issued
                        ).all()

    return render_template(
                        'return_book.html',
                        books = books
                        )


# This is the function which reverts the data to its initial stage
@app.route('/summary/<int:id>')
def summary(id):

    # Table Books        => | book_id | book_name | author | publisher | quantity | borrower | isbn | times_issued | 
    # Table members      => | member_id | member_name | member_balance | member_borrowed | library_fees_given |
    # Table Transactions => | _id | book_name | member_name | direction | time |

    book = Books.query.get(id)                  # get The book.
    book.quantity = 1                           # set its quantity to 1 again.
    member = Members.query.get(book.borrower)   # get the member using borrower column.

    # get the old transaction to get the time at which the book was issued.
    old_trans = Transactions.query.filter(
        Transactions.book_name == book.book_name
        ).first()

    # create a new transaction for the return of book
    trans = Transactions(
                        book_name = book.book_name,
                        member_name = member.member_name,
                        direction = True
                        )

    db.session.add(trans)   # Add it to the session.
    book.borrower = -1  # set the borrower to -1 again as it has no borrower now.

    # Calculate the balance of member by the formula => 10 * number of days for which the book was borrowed
    charges = (datetime.utcnow() - old_trans.time).days * 10

    # deduct the amount from the members wallet
    member.member_balance -= charges

    # add the amount deducted by the user wallet to the library profits
    member.library_fees_given += charges
    
    member.member_borrowed = False  # set this property to False as the member has not borrowed a book.
    db.session.commit()     # commit changes.

    return render_template('summary.html', member = member)


@app.route('/delete_member/<int:id>')
def delete(id):

    # Table members      => | member_id | member_name | member_balance | member_borrowed | library_fees_given |

    try:

        task_to_delete =  Members.query.get(id)
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect('/members')

    except:

        return render_template('error.html', message = "Unexpected Error Occured")


@app.route('/update/<int:id>', methods = ["POST", "GET"])
def update(id):

    # Table members      => | member_id | member_name | member_balance | member_borrowed | library_fees_given |

    if request.method == "POST":
        try:

            user = Members.query.get(id)
            user.member_balance += float(request.form['amount'])
            db.session.commit()
            return redirect(url_for('members'))

        except:

            return render_template('error.html', message = "Unexpected Error Occured")
    else:
        return render_template('update.html', id = id)


# Helper Functions
# checks if a string is alphabetical
def is_alphabets(s : str):
    return ''.join(s.split()).isalpha()
            

# Removes unnecessary spaces between characters
def remove_spaces(s : str):
    return ' '.join(s.split())


# This Function Makes The API call and returns The response
def make_API_call():
    # This is The Base Url from which we will make the imports
    BASE_URL = 'https://frappe.io/api/method/frappe-library?'

    title = remove_spaces(request.form['title'])                # Removing inconsistency in spaces
    authors = remove_spaces(request.form['author'])             # Removing inconsistency in spaces
    publisher = remove_spaces(request.form['publisher'])        # Removing inconsistency in spaces
    isbn = request.form['isbn']

    end = ''

    if title or authors or isbn or publisher:
        end = f'title={title}&authors={authors}&isbn={isbn}publisher={publisher}'
        response = requests.get(BASE_URL + end).json()['message']
    
    else:
        # No parameters passed for searching so we will search at random pages between 1 - 200
        response = requests.get(BASE_URL + f'page={randint(1,200)}').json()['message']

    return response

if __name__ == '__main__':
    app.run(debug=True)
    db.create_all()