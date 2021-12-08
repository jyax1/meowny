# Angel Liu, Angel Xu, Jennifer Shan
# queries.py

import cs304dbi as dbi

# get aid given username
def aidGivenUsername(conn,username):
    curs = dbi.dict_cursor(conn)
    curs.execute('''
        select aid from user where name = %s''', [username])
    return curs.fetchone()

# for displaying user's spending history
def dataEntryGivenAID(conn,aid):
    curs = dbi.dict_cursor(conn)
    curs.execute('''
        select * from dataEntry where aid = %s''', [aid])
    return curs.fetchall()

# for displaying user's spending history
def dataEntryGivenWeek(conn,aid,weekNum):
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
    curs = dbi.dict_cursor(conn)
    curs.execute('''select goal from user
                    where aid = %s''',
                    [aid])
    return curs.fetchone()['goal']

def updateGoal(conn,aid,newGoal):
    curs = dbi.dict_cursor(conn)
    curs.execute('''update user set goal = %s
                    where aid = %s''',
                    [newGoal,aid])
    conn.commit()

def commStatsMaxWeek(conn):
    curs = dbi.dict_cursor(conn)
    curs.execute('''
        select max(year_and_weekNum) 
        from dataEntry''')
    return curs.fetchone()

def commStatsTotalAvg(conn,year_and_weekNum):
    curs = dbi.dict_cursor(conn)
    curs.execute('''
        select avg(total_spending) from dataEntry 
        where year_and_weekNum = %s
        group by aid''', 
        [year_and_weekNum])
    return curs.fetchone()

def commStatsFoodAvg(conn,year_and_weekNum):
    curs = dbi.dict_cursor(conn)
    curs.execute('''
        select avg(food_spending) from dataEntry 
        where year_and_weekNum = %s
        group by aid''', 
        [year_and_weekNum])
    return curs.fetchone()

def commStatsClothingAvg(conn,year_and_weekNum):
    curs = dbi.dict_cursor(conn)
    curs.execute('''
        select avg(clothing_spending) from dataEntry 
        where year_and_weekNum = %s
        group by aid''', 
        [year_and_weekNum])
    return curs.fetchone()

def commStatsTranspAvg(conn,year_and_weekNum):
    curs = dbi.dict_cursor(conn)
    curs.execute('''
        select avg(transp_spending) from dataEntry 
        where year_and_weekNum = %s
        group by aid''', 
        [year_and_weekNum])
    return curs.fetchone()

def commStatsEntertAvg(conn,year_and_weekNum):
    curs = dbi.dict_cursor(conn)
    curs.execute('''
        select avg(entert_spending) from dataEntry 
        where year_and_weekNum = %s
        group by aid''', 
        [year_and_weekNum])
    return curs.fetchone()

def commStatsPersonalAvg(conn,year_and_weekNum):
    curs = dbi.dict_cursor(conn)
    curs.execute('''
        select avg(personal_spending) from dataEntry 
        where year_and_weekNum = %s
        group by aid''', 
        [year_and_weekNum])
    return curs.fetchone()

def commStatsMiscelAvg(conn,year_and_weekNum):
    curs = dbi.dict_cursor(conn)
    curs.execute('''
        select avg(miscel_spending) from dataEntry 
        where year_and_weekNum = %s
        group by aid''', 
        [year_and_weekNum])
    return curs.fetchone()

def commStatsInsert(conn,year_and_weekNum,total_avg,food_avg,
                    clothing_avg,transp_avg,entert_avg,
                    personal_avg,miscel_avg):
    curs = dbi.dict_cursor(conn)
    curs.execute('''insert into commStats(year_and_weekNum,total_avg,food_avg, clothing_avg,transp_avg,entert_avg,personal_avg,miscel_avg)
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
    curs = dbi.dict_cursor(conn)
    curs.execute('''
        select * from commStats where year_and_weekNum = %s''', [weekNum])
    return curs.fetchall()

def getWeekNum(conn):
    curs = dbi.dict_cursor(conn)
    curs.execute('''
        select distinct year_and_weekNum 
        from dataEntry''')
    return curs.fetchall()