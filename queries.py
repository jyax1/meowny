# Angel Liu, Angel Xu, Jennifer Shan
# queries.py

import cs304dbi as dbi

# get aid given username
def aidGivenUsername(conn,username):
    curs = dbi.dict_cursor(conn)
    curs.execute('''
        select aid from user where name = %s''', [username])
    return curs.fetchall()

# for displaying user's spending history
def dataEntryGivenAID(conn,aid):
    curs = dbi.dict_cursor(conn)
    curs.execute('''
        select * from dataEntry where aid = %s''', [aid])
    return curs.fetchall()