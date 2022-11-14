from flask import Blueprint, render_template, redirect, url_for, request, flash, session
# from app import records
import bcrypt
import datetime
import pymongo


client = pymongo.MongoClient("mongodb+srv://serban:serban@cluster0.oi6hu.mongodb.net/?retryWrites=true&w=majority")
db = client.get_database('medic')
records = db.users
auth = Blueprint('auth', __name__)

@auth.route('/profile')
def profile():
    if "email" in session:
        return render_template('profile.html')
    else:
        return redirect(url_for('index'))

@auth.route('/login')
def login():
    return render_template('login.html')

@auth.route('/changepassword', methods=['POST'])
def changepass():
    # login code goes here
    if "email" in session:
        
        cur_password = request.form.get('currentpassword')
        new_password = request.form.get('newpassword')

        email_found = records.find_one({"email": session["email"]})
        if email_found:
                email_val = email_found['email']
                passwordcheck = email_found['password']
                
                if bcrypt.checkpw(cur_password.encode('utf-8'), passwordcheck):
                    records.find_one_and_update({"email": email_val}, 
                                 {"$set": {"password": bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())}})
                    return redirect(url_for('auth.profile'))
                else:
                    flash("Check credentials")
                    return redirect(url_for('auth.profile'))

    return redirect(url_for('auth.login'))

@auth.route('/deleteaccount', methods=['POST'])
def deleteaccount():
    # login code goes here
    if "email" in session:
        records.delete_one({"email": session["email"]})
        session.pop("email", None)
        return redirect(url_for('index'))

    return redirect(url_for('auth.login'))

@auth.route('/login', methods=['POST'])
def login_post():
    # login code goes here
    email = request.form.get('email')
    password = request.form.get('password')

    email_found = records.find_one({"email": email})
    if email_found:
            email_val = email_found['email']
            passwordcheck = email_found['password']
            
            if bcrypt.checkpw(password.encode('utf-8'), passwordcheck):
                session["email"] = email_val
                session.permanent = True
                session["subscription_status"] = email_found["subscription_status"]
                session["subscription_end_date"] = email_found["subscription_end_date"].strftime("%d-%m-%Y")
                return redirect(url_for('index'))
            else:
                flash('Please check your login details and try again.')
                return redirect(url_for('auth.login'))
    flash('Please check your login details and try again.')
    return redirect(url_for('auth.login'))

@auth.route('/signup')
def signup():
    return render_template('signup.html')

@auth.route('/signup', methods=['POST'])
def signup_post():
    email = request.form.get('email')
    password = request.form.get('password')

    email_found = records.find_one({"email": email})
    if email_found:
        flash('Email address already exists')
        return redirect(url_for('auth.signup'))
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    user_input = {'email': email, 'password': hashed, "subscription_status":False, "subscription_end_date": datetime.datetime.utcnow()}
    records.insert_one(user_input)


    # code to validate and add user to database goes here
    return redirect(url_for('auth.login'))

@auth.route('/logout')
def logout():
    if "email" in session:
        session.clear()
        return redirect(url_for('index'))
    else:
        return redirect(url_for('index'))