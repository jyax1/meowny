# Angel Liu, Angel Xu, Jennifer Shan
# app.py

from flask import (Flask, render_template, make_response, url_for, request,
                   redirect, flash, session, send_from_directory, jsonify)
from werkzeug.utils import secure_filename
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

@app.route('/welcome')
def welcome():
    return render_template('welcome.html', page_title = 'Welcome')

# main page
@app.route('/', methods=["GET", "POST"])
def index():
    # if user is logged in, the "home" nav bar will direct to userpage
    if 'username' in session:
        username = session['username']
        aid = session['aid']
        return redirect(url_for('user', username=username))
    # if user is not logged in, the "home" nav bar will direct to login
    else:
        if request.method == 'GET':
            return render_template('main.html',page_title='Hello')
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
                flash('you do not have an account')
                flash('please join first')
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
                return redirect(url_for('user', username = username))
            else:
                flash('login incorrect')
                flash('try again or join')
                return redirect(url_for('index'))

# create new user
@app.route('/join/', methods=["GET", "POST"])
def join():
    if request.method == 'GET':
        return render_template('join.html', page_title = 'Hello')
    else:
        # get the entered value and check if two passwords match
        username = request.form.get('username')
        passwd1 = request.form.get('password1')
        passwd2 = request.form.get('password2')
        goal = request.form.get('goal')
        if passwd1 != passwd2:
            flash('passwords do not match')
            return redirect(url_for('index'))
        # hash the entered value
        hashed = bcrypt.hashpw(passwd1.encode('utf-8'),
                            bcrypt.gensalt())
        stored = hashed.decode('utf-8')
        conn = dbi.connect()
        curs = dbi.dict_cursor(conn)
        # store the information into a new row of the table
        try:
            curs.execute('''INSERT INTO user(aid,name,password,goal)
                            VALUES(null,%s,%s,%s)''',
                        [username, stored,goal])
            conn.commit()
        except Exception as err:
        # if username is taken, redirect to the login page
            flash('that username is taken: {}'.format(repr(err)))
            return redirect(url_for('index'))
        # get the id and update session data
        curs.execute('select last_insert_id()')
        aid = curs.fetchone()['last_insert_id()']
        session['username'] = username
        session['aid'] = aid
        session['logged_in'] = True
        session['visits'] = 1
        return redirect(url_for('user', username = username))

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
            flash('you are not logged in')
            flash('please log in or sign up')
            return redirect(url_for('index'))
    except Exception as err:
        flash('there is an error '+str(err))
        return redirect(url_for('index'))

    conn = dbi.connect()
    goal = queries.getGoal(conn,aid)
    dataList = queries.dataEntryGivenAID(conn, aid)

    if request.method == 'GET': 
        conn = dbi.connect()
        dataList = queries.dataEntryGivenAID(conn, aid)
        return render_template('personalPg.html', page_title = 'inserting spendings',
                                username = username, goal = goal,
                                dataList = dataList)
    else:
        try:
            data = dict(request.form)
            if all(value == "" for value in data.values()):
                flash('please submit spendings')
                raise Exception
            conn = dbi.connect()
            queries.insert(conn, aid, data)
            dataList = queries.dataEntryGivenAID(conn, aid)
            flash('thank you for submitting your weekly spendings')
            return render_template('personalPg.html', page_title ='Inserting Spendings',
                                    username = username, dataList = dataList,
                                    goal = goal)
        except Exception as err:
            flash('form submission incomplete')
            return render_template('personalPg.html', page_title = 'Inserting Spendings',
                                    username = username)

@app.route('/update/<username>', methods=['GET','POST'])
def update(username):
    '''Display a form with existing data to update movies 
       and implement queries to update the new movie
    '''
    try:
        # get the user data if logged in
        if 'username' in session:
            username = session['username']
            aid = session['aid']
        # redirect to login if no session data found
        else:
            flash('you are not logged in')
            flash('please log in or sign up')
            return redirect(url_for('index'))
    except Exception as err:
        flash('there is an error '+str(err))
        return redirect(url_for('index'))

    if request.method == 'GET':
        return render_template('update.html',
                               method=request.method,
                               username = username)
    elif request.method == 'POST':
        # extract the data entered
        newGoal = request.form.get('goal')
        conn = dbi.connect()
        queries.updateGoal(conn,aid,newGoal)
        flash('your goal was updated successfully')
        return redirect(url_for('update', 
                        username = username))

@app.route('/commStats/', methods=['GET','POST'])
def commStats():
    # will include average, max, min of community spendings for each catergory,
    # the percentile the user is in, and hopefully some graphs
    conn = dbi.connect()
    weekList = queries.getWeekNum(conn)

    if 'username' in session:
        username = session['username']
        aid = session['aid']
        # redirect to login if no session data found
    else:
        flash('you are not logged in')
        flash('please log in or sign up')
        return redirect(url_for('index'))

    if request.method == 'GET':
        maxWeek = queries.commStatsMaxWeek(conn)['max(year_and_weekNum)']
        total_avg = queries.commStatsTotalAvg(conn,maxWeek)['avg(total_spending)']
        food_avg = queries.commStatsFoodAvg(conn,maxWeek)["avg(food_spending)"]
        clothing_avg = queries.commStatsClothingAvg(conn,maxWeek)["avg(clothing_spending)"]
        transp_avg = queries.commStatsTranspAvg(conn,maxWeek)["avg(transp_spending)"]
        entert_avg = queries.commStatsEntertAvg(conn,maxWeek)["avg(entert_spending)"]
        personal_avg = queries.commStatsPersonalAvg(conn,maxWeek)["avg(personal_spending)"]
        miscel_avg = queries.commStatsMiscelAvg(conn,maxWeek)["avg(miscel_spending)"]

        queries.commStatsInsert(conn,maxWeek,total_avg,food_avg,
                                clothing_avg,transp_avg,entert_avg,
                                personal_avg,miscel_avg)
        commList = queries.commStatsGivenWeek(conn,maxWeek)

        if 'username' in session:
             yourList = queries.dataEntryGivenWeek(conn,aid,maxWeek)

        return render_template('commStats.html', commList = commList,
                                method = 'GET', weekList = weekList,
                                yourList = yourList)
    else:
        weekNum = request.form.get('menu-time')
        total_avg = queries.commStatsTotalAvg(conn,weekNum)['avg(total_spending)']
        food_avg = queries.commStatsFoodAvg(conn,weekNum)["avg(food_spending)"]
        clothing_avg = queries.commStatsClothingAvg(conn,weekNum)["avg(clothing_spending)"]
        transp_avg = queries.commStatsTranspAvg(conn,weekNum)["avg(transp_spending)"]
        entert_avg = queries.commStatsEntertAvg(conn,weekNum)["avg(entert_spending)"]
        personal_avg = queries.commStatsPersonalAvg(conn,weekNum)["avg(personal_spending)"]
        miscel_avg = queries.commStatsMiscelAvg(conn,weekNum)["avg(miscel_spending)"]

        queries.commStatsInsert(conn,weekNum,total_avg,food_avg,
                                clothing_avg,transp_avg,entert_avg,
                                personal_avg,miscel_avg)
        commList = queries.commStatsGivenWeek(conn,weekNum)
    
        if 'username' in session:
            yourList = queries.dataEntryGivenWeek(conn,aid,weekNum)

        return render_template('commStats.html', commList = commList,
                                method = 'POST', weekList = weekList,
                                weekNum = weekNum, yourList = yourList)

@app.route('/logout/')
def logout():
    if 'username' in session:
        username = session['username']
        session.pop('username')
        session.pop('aid')
        session.pop('logged_in')
        flash('you are logged out')
        return redirect(url_for('index'))
    else:
        flash('you are not logged in')
        flash('please log in or join')
        return redirect(url_for('index'))

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
