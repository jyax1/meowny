# Angel Liu, Angel Xu, Jennifer Shan
# queries.py

import cs304dbi as dbi
from datetime import datetime

def insert(conn, aid, data):
    '''Insert all the data for one entry given 
       spendings from all categories
    '''
    now = datetime.now()
    year_and_weekNum = str(now.year) + now.strftime("%U")
    foodData = data['food']
    clothingData = data['clothing']
    transpData = data['transp'] 
    entertData = data['entert'] 
    personalData = data['personal'] 
    miscelData = data['miscel'] 

    total_spending = (float(foodData) + float(clothingData) + float(transpData) +
                    float(entertData) + float(personalData) + float(miscelData))

    curs = dbi.dict_cursor(conn)
    curs.execute('''insert into dataEntry (aid, dataTime, year_and_weekNum, 
                    food_spending, clothing_spending, transp_spending, 
                    entert_spending, personal_spending, miscel_spending, 
                    total_spending) 
                    values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
                    [aid, now, year_and_weekNum, foodData, clothingData, 
                    transpData, entertData, personalData, miscelData, 
                    total_spending])
    conn.commit()

def aidGivenUsername(conn,username):
    '''get aid from user table given the username
    '''
    curs = dbi.dict_cursor(conn)
    curs.execute('''
        select aid from user where name = %s''', [username])
    return curs.fetchone()

def dataEntryGivenAID(conn,aid):
    '''output all data entries one user has inserted
    '''
    curs = dbi.dict_cursor(conn)
    curs.execute('''
        select * from dataEntry where aid = %s''', [aid])
    return curs.fetchall()

def dataEntryGivenWeek(conn,aid,weekNum):
    '''output the sum of all data entries one user has inserted
       in a given week (for the commStats page)
    '''
    curs = dbi.dict_cursor(conn)
    curs.execute('''
        select aid, year_and_weekNum, sum(total_spending), sum(food_spending), 
        sum(clothing_spending), sum(transp_spending), sum(entert_spending), 
        sum(personal_spending), sum(miscel_spending)
        from
            (select * from dataEntry 
            where aid = %s
            and year_and_weekNum = %s) as dataGivenWeek''', [aid, weekNum])
    return curs.fetchall()

def getGoal(conn,aid):
    '''output the goal stored in the user table
    '''
    curs = dbi.dict_cursor(conn)
    curs.execute('''select goal from user
                    where aid = %s''',
                    [aid])
    return curs.fetchone()['goal']

def updateGoal(conn,aid,newGoal):
    '''update the goal stored in the user table
    '''
    curs = dbi.dict_cursor(conn)
    curs.execute('''update user set goal = %s
                    where aid = %s''',
                    [newGoal,aid])
    conn.commit()

def commStatsMaxWeek(conn):
    '''output the most recent weeknumber
    '''
    curs = dbi.dict_cursor(conn)
    curs.execute('''
        select max(year_and_weekNum) 
        from dataEntry''')
    return curs.fetchone()

def commStatsAvg(conn,year_and_weekNum):
    '''output the community average for every spendings
       in a given week
    '''
    curs = dbi.dict_cursor(conn)
    curs.execute('''
        select avg(total_spending), avg(food_spending), avg(clothing_spending), 
        avg(transp_spending), avg(entert_spending), avg(personal_spending), 
        avg(miscel_spending)
        from dataEntry 
        where year_and_weekNum = %s''', 
        [year_and_weekNum])
    return curs.fetchall()

def commStatsInsert(conn,year_and_weekNum,total_avg,food_avg,
                    clothing_avg,transp_avg,entert_avg,
                    personal_avg,miscel_avg):
    '''insert the community averages into the commStats table
    '''
    curs = dbi.dict_cursor(conn)
    curs.execute('''insert into commStats(year_and_weekNum,total_avg,food_avg, 
                    clothing_avg,transp_avg,entert_avg,personal_avg,miscel_avg)
                    values(%s, %s, %s, %s, %s, %s, %s, %s)
                    on duplicate key update year_and_weekNum = %s, 
                    total_avg = %s,food_avg = %s, clothing_avg = %s,
                    transp_avg = %s,entert_avg = %s,personal_avg = %s,
                    miscel_avg = %s''', 
                    [year_and_weekNum,total_avg,food_avg,clothing_avg,
                    transp_avg, entert_avg, personal_avg,miscel_avg,
                    year_and_weekNum,total_avg,food_avg,clothing_avg,
                    transp_avg, entert_avg, personal_avg,miscel_avg])
    conn.commit()

def commStatsGivenWeek(conn,weekNum):
    '''output the community averages for all categories
       in a given week
    '''
    curs = dbi.dict_cursor(conn)
    curs.execute('''
        select * from commStats where year_and_weekNum = %s''', [weekNum])
    return curs.fetchall()

def getWeekNum(conn):
    '''output all the weeknumbers we have in the dataEntry table
    '''
    curs = dbi.dict_cursor(conn)
    curs.execute('''
        select distinct year_and_weekNum 
        from dataEntry''')
    return curs.fetchall()