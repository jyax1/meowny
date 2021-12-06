# Angel Liu, Angel Xu, Jennifer Shan
# app.py

from flask import (Flask, render_template, make_response, url_for, request,
                   redirect, flash, session, send_from_directory, jsonify)
from werkzeug.utils import secure_filename
from datetime import datetime
app = Flask(__name__)

# one or the other of these. Defaults to MySQL (PyMySQL)
# change comment characters to switch to SQLite

import pymysql
import cs304dbi as dbi
import bcrypt
import random
import queries 

app.secret_key = 'your secret here'
# replace that with a random key
app.secret_key = ''.join([ random.choice(('ABCDEFGHIJKLMNOPQRSTUVXYZ' +
                                          'abcdefghijklmnopqrstuvxyz' +
                                          '0123456789'))
                           for i in range(20) ])

# This gets us better error messages for certain common request errors
app.config['TRAP_BAD_REQUEST_ERRORS'] = True

# for user to submit data into dataEntry table in meowny database
def insert(aid, data):
    '''Insert all the data for one entry given 
       spendings from all categories
    '''
    now = datetime.now()
    foodData = data['food']
    clothingData = data['clothing']
    transpData = data['transp'] 
    entertData = data['entert'] 
    personalData = data['personal'] 
    miscelData = data['miscel'] 

    conn = dbi.connect()
    curs = dbi.dict_cursor(conn)
    curs.execute('''insert into dataEntry (aid, dataTime, food_spending,
                    clothing_spending, transp_spending, entert_spending,
                    personal_spending, miscel_spending) 
                    values (%s,%s,%s,%s,%s,%s,%s,%s)''',
                    [aid, now, foodData, clothingData, transpData,
                    entertData, personalData, miscelData])
    conn.commit()
    return

# main page
@app.route('/', methods=["GET", "POST"])
def index():
    # if user is logged in, the "home" nav bar will direct to userpage
    if 'username' in session:
        username = session['username']
        aid = session['aid']
        return redirect( url_for('user', username=username) )
    # if user is not logged in, the "home" nav bar will direct to login
    else:
        if request.method == 'GET':
            return render_template('main.html',title='Hello')
        else:
            username = request.form.get('username')
            passwd = request.form.get('password')
            conn = dbi.connect()
            curs = dbi.dict_cursor(conn)
            # check if the user is in the database
            curs.execute('''SELECT aid,password
                            FROM user
                            WHERE name = %s''',
                        [username])
            row = curs.fetchone()
            if row is None:
                flash('you do not have an account. Please join first.')
                return redirect( url_for('index'))
            # compare the stored password with the one entered
            stored = row['password']
            hashed2 = bcrypt.hashpw(passwd.encode('utf-8'),
                                    stored.encode('utf-8')[0:29])
            hashed2_str = hashed2.decode('utf-8')
            if hashed2_str == stored:
                flash('successfully logged in as '+username)
                # update session data
                session['username'] = username
                session['aid'] = row['aid']
                session['logged_in'] = True
                session['visits'] = 1
                return redirect( url_for('user', username=username) )
            else:
                flash('login incorrect. try again or join')
                return redirect( url_for('index'))

# create new user
@app.route('/join/', methods=["GET", "POST"])
def join():
    if request.method == 'GET':
        return render_template('join.html',title='Hello')
    else:
        # get the entered value and check if two passwords match
        username = request.form.get('username')
        passwd1 = request.form.get('password1')
        passwd2 = request.form.get('password2')
        if passwd1 != passwd2:
            flash('passwords do not match')
            return redirect( url_for('index'))
        # hash the entered value
        hashed = bcrypt.hashpw(passwd1.encode('utf-8'),
                            bcrypt.gensalt())
        stored = hashed.decode('utf-8')
        conn = dbi.connect()
        curs = dbi.dict_cursor(conn)
        # store the information into a new row of the table
        try:
            curs.execute('''INSERT INTO user(aid,name,password)
                            VALUES(null,%s,%s)''',
                        [username, stored])
            conn.commit()
        except Exception as err:
        # if username is taken, redirect to the login page
            flash('That username is taken: {}'.format(repr(err)))
            return redirect(url_for('index'))
        # get the id and update session data
        curs.execute('select last_insert_id()')
        aid = curs.fetchone()['last_insert_id()']
        session['username'] = username
        session['aid'] = aid
        session['logged_in'] = True
        session['visits'] = 1
        return redirect( url_for('user', username=username) )

# user's personal page
@app.route('/user/<username>', methods=["GET", "POST"])
def user(username):
    try:
        # get the user data if logged in
        if 'username' in session:
            username = session['username']
            aid = session['aid']
            session['visits'] = 1+int(session['visits'])
        # redirect to login if no session data found
        else:
            flash('You are not logged in. Please log in or sign up!')
            return redirect(url_for('index'))
    except Exception as err:
        flash('There is an error '+str(err))
        return redirect(url_for('index'))
    if request.method == 'GET': 
        return render_template('personalPg.html', title='inserting spendings',
                                    username = username)
    else:
        try:
            data = dict(request.form)
            if all(value == "" for value in data.values()):
                flash('please submit spendings')
                raise Exception
            insert(aid, data)
            flash('thank you for submitting your weekly spendings')
            conn = dbi.connect()
            dataList = queries.dataEntryGivenAID(conn, aid)
            return render_template('personalPg.html', title='inserting spendings',
                                    username = username, dataList = dataList)
        except Exception as err:
            flash('form submission incomplete')
            return render_template('personalPg.html', title='inserting spendings',
                                    username = username)

@app.route('/commStats/')
def commStats():
    # to be implemented
    # will include average, max, min of community spendings for each catergory,
    # the percentile the user is in, and hopefully some graphs
    return render_template('commStats.html',title='Hello')

@app.route('/logout/')
def logout():
    if 'username' in session:
        username = session['username']
        session.pop('username')
        session.pop('aid')
        session.pop('logged_in')
        flash('You are logged out')
        return redirect(url_for('index'))
    else:
        flash('you are not logged in. Please login or join')
        return redirect( url_for('index') )

@app.before_first_request
def init_db():
    dbi.cache_cnf()
    # set this local variable to 'wmdb' or your personal or team db
    db_to_use = 'meowny_db' 
    dbi.use(db_to_use)

if __name__ == '__main__':
    import sys, os
    if len(sys.argv) > 1:
        # arg, if any, is the desired port number
        port = int(sys.argv[1])
        assert(port>1024)
    else:
        port = os.getuid()
    app.debug = True
    app.run('0.0.0.0',port)
