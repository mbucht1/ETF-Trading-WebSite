import psycopg2
import hashlib

conn = psycopg2.connect(
    host='localhost',
    user='postgres',
    password='1234',
    dbname='etf',
    port=5432
)

mycursor = conn.cursor()


def getUser(username, password): 
    sql = "SELECT * From public.logins WHERE username = %s AND passwd = %s;"
    val = (username, password.hexdigest())
    mycursor.execute(sql, val)
    userQuery = mycursor.fetchall()
    return userQuery

def getUserID(user):
    try:
        idQuery = "SELECT userid FROM public.logins WHERE username = '{}';".format(user)
        mycursor.execute(idQuery)
        userID = mycursor.fetchall()
        return userID[0][0]
    except Exception as error:
        print ("Oops! An exception has occured:", error)
        print ("Exception TYPE:", type(error))



def isUser(username):
    try:
        sql = "SELECT * FROM public.users NATURAL JOIN public.logins WHERE username = '{}';".format(username)
        mycursor.execute(sql)
        register_query = mycursor.fetchall()
        if register_query: return False
        return True
    except Exception as error:
        print ("Exception TYPE:", type(error))
        clear()

def getETFTable():
    sql = "SELECT * FROM public.etf;"
    mycursor.execute(sql)
    return mycursor.fetchall()
   


def getCurrentFunds(username):
    sql = "SELECT availablefunds FROM public.users WHERE userid IN (SELECT userid FROM public.logins WHERE username = '{}');".format(username)
    mycursor.execute(sql)
    funds = mycursor.fetchall()
    return funds[0][0]

def getPortfolio(user):
    portfolio_sql = "SELECT *, (CAST(amt as NUMERIC(9,0)) * CAST(price as NUMERIC(30,2))) as total FROM (SELECT etfid, ename, ytd,\
    sum(amount) as amt, price FROM public.owns NATURAL JOIN public.etf NATURAL JOIN logins WHERE username = '{}' GROUP BY etfid, ename, price, ytd) t;".format(user)
    mycursor.execute(portfolio_sql)
    portfolio_query = mycursor.fetchall()
    return portfolio_query  


def getUserStockAmount(username , etf):
    userStockAmount = "SELECT SUM(amount) FROM owns NATURAL JOIN logins WHERE username = '{}' AND etfid = '{}' GROUP BY etfid;".format(username, etf)  # Calculates how many shares a user owns
    mycursor.execute(userStockAmount)
    return mycursor.fetchall()  # Number of shares user owns

def createUserID():
    try:
        nextval = "SELECT nextval('users_userid_seq');"  # Grabs next id from sequence
        mycursor.execute(nextval)
        return mycursor.fetchall()
    except Exception as error:
        print ("Oops! An exception has occured:", error)
        print ("Exception TYPE:", type(error))



def amountAvailable(etf):
    amountavaialblecheck_sql = "SELECT amountavailable, price FROM public.etf WHERE etfid = '{}';".format(etf)
    mycursor.execute(amountavaialblecheck_sql, {'etf': etf.upper()})
    return mycursor.fetchall()


def insertUser(userID, fname, lname, username, password):

    hashedPW = hashlib.sha256(password.encode())
    try:
        sql = "INSERT INTO public.users(userid, fname, lname, availablefunds) values({},\
        '{}', '{}', 0.0); INSERT INTO public.logins(userid, username, passwd) values({},\
        '{}', '{}');".format(userID[0][0], fname, lname, userID[0][0], username, hashedPW.hexdigest())  # Inserts new user info
        mycursor.execute(sql)
        conn.commit()
    except Exception as error:
        print ("Oops! An exception has occured:", error)
        print ("Exception TYPE:", type(error))


def addFunds(add, username):
   
    new_value = float(getCurrentFunds(username)) + float(add)
    addingfunds_sql = "UPDATE users SET availablefunds = %(value)s FROM public.logins WHERE users.userid = logins.userid AND username = %(username)s;"  # Updates available funds to new val
    mycursor.execute(addingfunds_sql, {'value': new_value, 'username': username})
    try:
        conn.commit()
    except:
        conn.rollback()  



def updateEtfAmount(etf, newAmount):
    try:
        subtractamountetf_sql = "UPDATE public.etf SET amountavailable = '{}' WHERE etfid = '{}';".format(newAmount, etf.upper())  # Lowers ETF amount in database
        mycursor.execute(subtractamountetf_sql)
    except Exception as error:
        print ("Exception TYPE:", type(error))

def updateUserFunds(newFunds, username):
    try:
        subtractamountuser_sql = "UPDATE public.users SET availablefunds = '{}' FROM logins WHERE users.userid = logins.userid AND username = '{}';".format(newFunds, username)  # Subtracts funds from user
        mycursor.execute(subtractamountuser_sql)
    except Exception as error:
        print ("Exception TYPE:", type(error))
def insertEtfOrder(userId, etf, newAmount):

    try:
        ownsbuy_sql = "INSERT INTO public.owns(userid, etfid, amount) VALUES ('{}', '{}', '{}');".format(userId, etf.upper(), newAmount)  # Inserts order into owns
        mycursor.execute(ownsbuy_sql)
        conn.commit()
        clear()
    except Exception as error:
        print ("Exception TYPE:", type(error))
    # clear(userId)

def clear(): # prevents SQL command from executing later from a commit
    conn.rollback()
    # menu(user)