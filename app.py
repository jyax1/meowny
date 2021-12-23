# Angel Liu, Angel Xu, Jennifer Shan
# app.py

from flask import (Flask, render_template, make_response, url_for, request,
                   redirect, flash, session, send_from_directory, jsonify, Response)
from werkzeug.utils import secure_filename
app = Flask(__name__)

import pymysql
import cs304dbi as dbi
import bcrypt
import sys, os, imghdr, random

from datetime import datetime
import pandas as pd
import json
import plotly
import plotly.express as px
import queries 

app.secret_key = 'your secret here'
# replace that with a random key
app.secret_key = ''.join([ random.choice(('ABCDEFGHIJKLMNOPQRSTUVXYZ' +
                                          'abcdefghijklmnopqrstuvxyz' +
                                          '0123456789'))
                           for i in range(20) ])

# This gets us better error messages for certain common request errors
app.config['TRAP_BAD_REQUEST_ERRORS'] = True

# for file upload
app.config['UPLOADS'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024 # 1 MB

@app.route('/', methods = ["GET", "POST"])
def index():
    '''Main page with the login form'''
    # if user is logged in, the "home" nav bar will direct to userpage
    if 'username' in session:
        username = session['username']
        aid = session['aid']
        return redirect(url_for('user', username = username))
    # if user is not logged in, the "home" nav bar will direct to login
    else:
        if request.method == 'GET':
            return render_template('main.html', page_title = 'Home')
        else:
            username = request.form.get('username')
            passwd = request.form.get('password')
            conn = dbi.connect()
            curs = dbi.dict_cursor(conn)
            # check if the user is in the database
            curs.execute('''SELECT aid, password
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
                return redirect(url_for('user', username=username) )
            else:
                flash('login incorrect')
                flash('try again or join')
                return redirect(url_for('index'))

@app.route('/join/', methods = ["GET", "POST"])
def join():
    '''A page for new users to register'''
    if request.method == 'GET':
        return render_template('join.html', page_title = 'Join')
    else:
        # get the entered value and check if two passwords match
        username = request.form.get('username')
        passwd1 = request.form.get('password1')
        passwd2 = request.form.get('password2')
        goal = request.form.get('goal')
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
            curs.execute('''INSERT INTO user(aid,name,password,goal)
                            VALUES(null,%s,%s,%s)''',
                        [username, stored,goal])
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

        try:
            f = request.files['pic']
            user_filename = f.filename
            ext = user_filename.split('.')[-1]
            filename = secure_filename('{}.{}'.format(aid,ext))
            pathname = os.path.join(app.config['UPLOADS'],filename)
            f.save(pathname)
            conn = dbi.connect()
            curs = dbi.dict_cursor(conn)
            curs.execute(
                '''insert into picfile(aid,filename) values (%s,%s)
                   on duplicate key update filename = %s''',
                [aid, filename, filename])
            conn.commit()
            flash('upload successful')
        except Exception as err:
            flash('upload failed {why}'.format(why = err))
        
        return redirect(url_for('user', username = username))

@app.route('/pic/<aid>')
def pic(aid):
    conn = dbi.connect()
    curs = dbi.dict_cursor(conn)
    numrows = curs.execute(
        '''select filename from picfile where aid = %s''',
        [aid])
    if numrows == 0:
        flash('error: no picture for {}'.format(aid))
        return redirect(url_for('index'))
    row = curs.fetchone()
    return send_from_directory(app.config['UPLOADS'],row['filename'])

@app.route('/user/<username>', methods=["GET", "POST"])
def user(username):
    '''User's personal page with data-insertion form and their
    spending trajectory'''
    # get the user data if logged in
    if 'username' in session:
        username = session['username']
        aid = session['aid']
    # redirect to login if no session data found
    else:
        flash('you are not logged in')
        flash('please log in or sign up')
        return redirect(url_for('index'))

    conn = dbi.connect()
    # retrieve the spending goal user put in during registration
    goal = queries.getGoal(conn,aid)
    
    if request.method == 'GET': 
        conn = dbi.connect()
        # retrieve all the spending entries user entered
        dataList = queries.dataEntryGivenAID(conn, aid)
        return render_template('personalPg.html', page_title = 'Personal Page',
                                username = username, goal = goal,
                                dataList = dataList, aid = aid)
    else:
        try:
            data = dict(request.form)
            # if no spending is submitted, flash a reminder
            if all(value == "" for value in data.values()):
                flash('please submit spendings')
                raise Exception
            try:
                # insert data entries into the database
                conn = dbi.connect()
                queries.insert(conn, aid, data)
            except Exception as err:
                flash('there is an error '+ str(err))
                return redirect(url_for('index'))
            # retrieve all the spending entries user entered
            dataList = queries.dataEntryGivenAID(conn, aid)
            flash('thank you for submitting your weekly spendings')

            # retrieve the week number of the most recent week
            maxWeek = queries.commStatsMaxWeek(conn)['max(year_and_weekNum)']
            try:
                # extract averages for each category using one query
                total_avg = queries.commStatsAvg(conn, maxWeek)[0]['avg(total_spending)']
                food_avg = queries.commStatsAvg(conn, maxWeek)[0]["avg(food_spending)"]
                clothing_avg = queries.commStatsAvg(conn, maxWeek)[0]["avg(clothing_spending)"]
                transp_avg = queries.commStatsAvg(conn, maxWeek)[0]["avg(transp_spending)"]
                entert_avg = queries.commStatsAvg(conn, maxWeek)[0]["avg(entert_spending)"]
                personal_avg = queries.commStatsAvg(conn, maxWeek)[0]["avg(personal_spending)"]
                miscel_avg = queries.commStatsAvg(conn, maxWeek)[0]["avg(miscel_spending)"]
                # insert the averages into community stats table
                queries.commStatsInsert(conn, maxWeek, total_avg, food_avg,
                                        clothing_avg, transp_avg, entert_avg,
                                        personal_avg, miscel_avg)
            except Exception as err:
            # if insertion failed, redirect to the home page
                flash('an error occured: {}'.format(repr(err)))
                return redirect(url_for('index'))

            return render_template('personalPg.html', page_title = 'Personal Page',
                                    username = username, dataList = dataList,
                                    goal = goal, aid = aid)
        except Exception as err:
            flash('form submission incomplete')
            return render_template('personalPg.html', page_title = 'Personal Page',
                                    username = username, aid = aid)

@app.route('/update/<username>', methods = ['GET','POST'])
def update(username):
    '''Display a form and implement queries to update spending goals'''
    # get the user data if logged in
    if 'username' in session:
        username = session['username']
        aid = session['aid']
    # redirect to login if no session data found
    else:
        flash('you are not logged in')
        flash('please log in or sign up')
        return redirect(url_for('index'))

    # display the update form if GET
    if request.method == 'GET':
        return render_template('update.html',
                               method = request.method,
                               username = username)
    elif request.method == 'POST':
        # extract the goal entered
        newGoal = request.form.get('goal')
        conn = dbi.connect()
        # update the user table
        queries.updateGoal(conn, aid, newGoal)
        # update profile picture
        try:
            f = request.files['pic']
            user_filename = f.filename
            ext = user_filename.split('.')[-1]
            filename = secure_filename('{}.{}'.format(aid,ext))
            pathname = os.path.join(app.config['UPLOADS'],filename)
            f.save(pathname)
            conn = dbi.connect()
            curs = dbi.dict_cursor(conn)
            curs.execute(
                '''insert into picfile(aid,filename) values (%s,%s)
                   on duplicate key update filename = %s''',
                [aid, filename, filename])
            conn.commit()
            flash('upload successful')
        except Exception as err:
            flash('upload failed {why}'.format(why = err))
            
        flash('your profile info was updated successfully')
        return redirect(url_for('user', 
                        username = username))

@app.route('/commStats/', methods = ['GET','POST'])
def commStats():
    '''Community statistics page that include averages of community 
    spendings for each catergory, and the user's data for comparison'''
    conn = dbi.connect()
    weekList = queries.getWeekNum(conn)

    # get the user data if logged in
    if 'username' in session:
        username = session['username']
        aid = session['aid']
    # redirect to login if no session data found
    else:
        flash('you are not logged in')
        flash('please log in or sign up')
        return redirect(url_for('index'))

    if request.method == 'GET':
        # retrieve the week number of the most recent week
        conn = dbi.connect()
        maxWeek = queries.commStatsMaxWeek(conn)['max(year_and_weekNum)']
        # retrieve the community average from the table
        commList = queries.commStatsGivenWeek(conn, maxWeek)
        # retrive the user's spending from the table
        yourList = queries.dataEntryGivenWeek(conn, aid, maxWeek)

        # DataFrame to store data
        df = pd.DataFrame({
        'spending type': ['total', 'food', 'clothing', 'transportation',
        'entertainment', 'personal', 'miscellaneous'],
        'community average': [commList[0]['total_avg'], commList[0]['food_avg'],
        commList[0]['clothing_avg'], commList[0]['transp_avg'],
        commList[0]['entert_avg'], commList[0]['personal_avg'],
        commList[0]['miscel_avg']],
        'your spendings': [yourList[0]['sum(total_spending)'],
        yourList[0]['sum(food_spending)'], yourList[0]['sum(clothing_spending)'],
        yourList[0]['sum(transp_spending)'], yourList[0]['sum(entert_spending)'],
        yourList[0]['sum(personal_spending)'], yourList[0]['sum(miscel_spending)']]
        })

        # bar chart
        fig = px.bar(df, x = 'spending type', y = ['community average',
        'your spendings'], barmode = 'group', text_auto = True)
        graphJSON = json.dumps(fig, cls = plotly.utils.PlotlyJSONEncoder)

        return render_template('commStats.html', page_title = 'Community Stats',
                                commList = commList, method = 'GET',
                                weekList = weekList, yourList = yourList,
                                graphJSON = graphJSON)
    else:
        # get the weekNum user requested in the drop-down menu
        conn = dbi.connect()
        weekNum = request.form.get('menu-time')

        # extract averages for each category using one query
        total_avg = queries.commStatsAvg(conn, weekNum)[0]['avg(total_spending)']
        food_avg = queries.commStatsAvg(conn, weekNum)[0]["avg(food_spending)"]
        clothing_avg = queries.commStatsAvg(conn, weekNum)[0]["avg(clothing_spending)"]
        transp_avg = queries.commStatsAvg(conn, weekNum)[0]["avg(transp_spending)"]
        entert_avg = queries.commStatsAvg(conn, weekNum)[0]["avg(entert_spending)"]
        personal_avg = queries.commStatsAvg(conn, weekNum)[0]["avg(personal_spending)"]
        miscel_avg = queries.commStatsAvg(conn, weekNum)[0]["avg(miscel_spending)"]

        try:
            # insert the averages into community stats table
            queries.commStatsInsert(conn, weekNum, total_avg, food_avg,
                                    clothing_avg, transp_avg, entert_avg,
                                    personal_avg, miscel_avg)
        except Exception as err:
        # if insert failed, redirect to the home page
            flash('an error occured: {}'.format(repr(err)))
            return redirect(url_for('index'))
    
        # retrive the user's spending from the table
        yourList = queries.dataEntryGivenWeek(conn, aid, weekNum)
        
        # retrieve the community average from the table
        commList = queries.commStatsGivenWeek(conn, weekNum)

        # DataFrame to store data
        df = pd.DataFrame({
        'spending type': ['total', 'food', 'clothing', 'transportation',
        'entertainment', 'personal', 'miscellaneous'],
        'community average': [commList[0]['total_avg'], commList[0]['food_avg'],
        commList[0]['clothing_avg'], commList[0]['transp_avg'],
        commList[0]['entert_avg'], commList[0]['personal_avg'],
        commList[0]['miscel_avg']],
        'your spendings': [yourList[0]['sum(total_spending)'],
        yourList[0]['sum(food_spending)'], yourList[0]['sum(clothing_spending)'],
        yourList[0]['sum(transp_spending)'], yourList[0]['sum(entert_spending)'],
        yourList[0]['sum(personal_spending)'], yourList[0]['sum(miscel_spending)']]
        })

        # bar chart 
        fig = px.bar(df, x = 'spending type', y = ['community average',
        'your spendings'], barmode = 'group', text_auto = True)
        graphJSON = json.dumps(fig, cls = plotly.utils.PlotlyJSONEncoder)

        return render_template('commStats.html', page_title = 'Community Stats',
                                commList = commList, method = 'POST',
                                weekList = weekList, weekNum = weekNum,
                                yourList = yourList, graphJSON = graphJSON)

@app.route('/logout/')
def logout():
    '''Logging the user out of their session'''
    if 'username' in session:
        username = session['username']
        session.pop('username')
        session.pop('aid')
        session.pop('logged_in')
        flash('you are logged out')
        return redirect(url_for('index'))
    else:
        flash('you are not logged in')
        flash('please login or join')
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