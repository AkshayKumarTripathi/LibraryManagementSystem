from helper import *

# Home Directory
@app.route('/')
def home():
    available_books = Books.query.all()
    return render_template('home.html' , books = available_books)


@app.route('/members', methods = ["POST" , "GET"])
def members():
    # Table members => | member_id | member_name | member_balance | member_borrowed | library_fees_given |

    # it takes the new member information and adds in the data base.

    if request.method == "POST":

        user_name = request.form['user_name']     # getting the user Name
        member_balance = request.form['balance']  # getting the amount the user wants to add initially

        if not is_alphabets(user_name) or not member_balance.isnumeric():

            # This means the user has entered wrong data
            message = "Please enter correct User-Name or Balance"
            return render_template('error.html', message = message, page = "members")
        
        # Every Thing is Correct
        try:
        
            member = Members( member_name = user_name, member_balance = float(member_balance) )
            db.session.add(member)
            db.session.commit()

        except:

            return render_template('error.html', message = "Unexpected Error")

    
    members = Members.query.all()
    return render_template('members.html', members = members)
        

# this function loads all the transactons
@app.route('/transactions')
def transactions():
    # Table Transactions => | _id | book_name | member_name | direction | time |

    # Taking all the transactions and arranging them in descending order.

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

    # Select all the members from the table Members
    all_members = Members.query.filter(Members.member_borrowed == False).all()

    if request.method == "POST":

        #Before Rendering Check if the debt is greater than 500 rs => Throw Error

        id_of_the_member = request.form['id']

        if not id_of_the_member.isnumeric():
            return render_template('error.html', message = "Enter valid Id")


        member = Members.query.get(int(request.form['id']))
        
        # check if member is present or not:
        if member == None:
            return render_template('error.html', message = "Enter valid Id")

        if member.member_balance < -500:
            # Users Balance is less Than 500

            message = f'The balance of {member.member_name} is {member.member_balance} which is less than -500 so please add money to your wallet before taking books '
            return render_template('error.html', message = message)
        
        if member.member_borrowed==True:
            # User has already borrowed a book

            message = 'The User has already Taken Books'
            return render_template('error.html' , message= message)
        

        try:
            # Member has borrowed a book
            # members balance Should Decrease by 500
            # Members library balance should increase by 500
            member.member_borrowed = True
            member.member_balance -= 500
            member.library_fees_given += 500

            # Book's quantity is decreased
            # books Times issued is increased by 1
            # Books borrower is set to the id of member's id
            book = Books.query.get(book_id)

            if book == None:
                return render_template('error.html', message = "Unexpected Error Occured")
            book.quantity = 0
            book.times_issued += 1
            book.borrower = member.member_id


            # New transaction is registered and added to transactions

            trans = Transactions(book_name = book.book_name, member_name = member.member_name, direction = False)
            db.session.add(trans)
            db.session.commit()

            return redirect(url_for('home'))

        except:

            return render_template('error.html', message = "Unexpected Error Occured")
        
    return render_template('rent_out.html', id = book_id , members = all_members)


# This function Makes the API calls and then redirects to the home page
@app.route('/addBooks', methods = ["POST" , "GET"])
def addBooks():

    # Table Books => | book_id | book_name | author | publisher | quantity | borrower | isbn | times_issued |

    if request.method == "POST":

        # GET the data from the API
        # pass the data in LMS and then redirect to root page
        # render the data recieved

        # Gets the data from The API
        response = make_API_call()

        for data in response:
            to_find = Books.query.get(int(data["bookID"]))
            if to_find == None:
                book = Books(book_id = int(data["bookID"]),book_name=  data["title"], author = data["authors"], publisher =data["publisher"] , isbn = data["isbn"])
                db.session.add(book)
                db.session.commit()
            
        # rendering page using jinja and then redirect
        return redirect(url_for('home'))

    else:

        return render_template('add_books.html')


# renders all the books which are currently rented Out
@app.route('/return_book')
def return_book():
    #  Table Books => | book_id | book_name | author | publisher | quantity | borrower | isbn | times_issued |

    books = Books.query.filter(Books.quantity == 0).all()
    return render_template('return_book.html', books = books)


# This is the function which reverts the data to its initial stage
@app.route('/summary/<int:id>')
def summary(id):

    # Table Books        => | book_id | book_name | author | publisher | quantity | borrower | isbn | times_issued | 
    # Table members      => | member_id | member_name | member_balance | member_borrowed | library_fees_given |
    # Table Transactions => | _id | book_name | member_name | direction | time |

    # get The book
    book = Books.query.get(id)
    # set its quantity to 1 again
    book.quantity = 1
    # get the member using book.borrower column
    member = Members.query.get(book.borrower)
    # get the old transaction to get teh time at which the book was issued
    old_trans = Transactions.query.filter(Transactions.book_name == book.book_name).first()
    # create a new transaction for the return of book
    trans = Transactions(book_name = book.book_name, member_name = member.member_name , direction = True)
    # Add it to the session
    db.session.add(trans)
    # set the borrower to -1 again as it has no borrower now
    book.borrower = -1
    # Calculate the balance of member by the formula 
    # 10 * number of days for which the book was borrowed
    member.member_balance -= (datetime.utcnow() - old_trans.time).days * 10
    # add the amount deducted by the user wallet to the library profits
    member.library_fees_given += (datetime.utcnow() - old_trans.time).days * 10
    # set the member_borrowed property to False as the member has not borrowed a book
    member.member_borrowed = False
    db.session.commit()

    return render_template('summary.html', member = member)


@app.route('/delete_member/<int:id>')
def delete(id):

    # Table Books        => | book_id | book_name | author | publisher | quantity | borrower | isbn | times_issued |
    # Table members      => | member_id | member_name | member_balance | member_borrowed | library_fees_given |
    # Table Transactions => | _id | book_name | member_name | direction | time |  

    try:
        task_to_delete =  Members.query.get(id)
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect('/members')

    except:

        return render_template('error.html', message = "Unexpected Error Occured")


@app.route('/errorOccured')
def errorOccured():
    return render_template('error.html', message = "Unexpected Error Occured")


@app.route('/update/<int:id>', methods = ["POST", "GET"])
def update(id):
    #  Table Books => book_id| book_name | author | publisher | quantity | borrower | isbn | times_issued
    # Table members => member_id| member_name | member_balance | member_borrowed | library_fees_given |
    # Table Transactions => _id | book_name | member_name | direction | time |
    if request.method == "POST":
        try:
            user = Members.query.get(id)
            user.member_balance += float(request.form['amount'])
            db.session.commit()
            return redirect(url_for('members'))
        except:
            return render_template('error.html', message = "Unexpected Error Occured")
    return render_template('update.html', id = id)


if __name__ == '__main__':
    app.run(debug=True)
    db.create_all()