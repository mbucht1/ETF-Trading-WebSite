from flask import Flask, redirect, url_for, render_template, request, session, flash
from datetime import timedelta

import hashlib
import queries

app = Flask(__name__)
app.secret_key = "3286a6fb8f8a52f30af11409c742888f"
app.permanent_session_lifetime = timedelta(minutes=60)


@app.route("/home")
def home():
    currentFunds = queries.getCurrentFunds(session["user"])
    return render_template("home.html", currentFunds = currentFunds)


@app.route("/home/buyetf", methods=["POST", "GET"])
def buyETF():
    if request.method == "POST":
        etf = request.form["etf"]
        amount = request.form["amount"]
        username = session["user"]
        userId = queries.getUserID(username)
        funds = queries.getCurrentFunds(username)


        if int(amount) != float(amount):
            flash("Must buy whole shares", "error")
        if int(amount) <= 0:
            flash("Invalid number", "error")
        else:
            try:
                amountAvailableCheck = queries.amountAvailable(etf)
                if amountAvailableCheck[0][0] >= int(amount):
                    potentialBuy = float(amountAvailableCheck[0][1]) * int(amount)
                    if potentialBuy <= funds:
                        try:
                            newAmount = amountAvailableCheck[0][0] - int(amount)  # subtracts ETF's bought from ETF table
                            queries.updateEtfAmount(etf, newAmount)
                            newFunds = float(funds) - float(potentialBuy)  # subtract funds from users table
                            queries.updateUserFunds(newFunds, username)
                            queries.insertEtfOrder(userId, etf, amount)
                        except Exception as error:
                            flash("Exception TYPE:", type(error))
                    else:
                        flash("Not enough funds", "error")
                else:
                    flash("Not Enough ETF's", "error")    
            except:
                flash("ETF Does not Exist", "error")
    return render_template("buyetf.html")


@app.route("/home/selletf", methods=["POST", "GET"])
def sellETF():
    if request.method == "POST":
        etf = request.form["etf"]
        sellAmount = request.form["amount"]
        username = session["user"]
        userId = queries.getUserID(username)
        funds = queries.getCurrentFunds(username)
        
        try:
            userStockAmount = queries.getUserStockAmount(username, etf)
            stockAvailable = userStockAmount[0][0] - int(sellAmount)
            if(stockAvailable >= 0):
                try:
                    amountAvailable = queries.amountAvailable(etf)
                    newAmount = amountAvailable[0][0] + int(sellAmount)
                    potentialSell = float(amountAvailable[0][1]) * int(sellAmount)
                    queries.updateEtfAmount(etf, newAmount)
        
                    newFunds = float(funds) + float(potentialSell)
                    queries.updateUserFunds(newFunds, username)
                    
                    queries.insertEtfOrder(userId, etf, -abs(int(sellAmount)))
                except:
                    flash("An error has occured!", "error")
            else:
                flash("Not Enough ETFs owned", "error")     
        except:
            flash("ETF Does not Exist", "error")
    
    return render_template("selletf.html")

@app.route("/home/etflookup")
def ETFLookup():
    etfList = []
    etf = queries.getETFTable()
    tickers = [t[0] for t in etf]
    name = [t[1] for t in etf]
    price = [t[2] for t in etf]
    ytd = [t[3] for t in etf]
    available = [t[4] for t in etf]

    tableLen = len(tickers)
    for i in range(tableLen):
        row = []
        row.append(tickers[i])
        row.append(name[i])
        row.append(price[i])
        row.append(ytd[i])
        row.append(available[i])
        etfList.append(row)
    return render_template("etflookup.html", etfList = etfList)



@app.route("/home/funds", methods=["POST", "GET"])
def funds():
    if request.method == "POST":
        amount = request.form["amount"]


        if int(amount) <= 0:
            flash("Invalid input", "error")
            return redirect("addfunds.html")
        else:
            if "user" in session:
                queries.addFunds(amount, session["user"])
                return redirect(url_for("home"))
    return render_template("addfunds.html", currentFunds = queries.getCurrentFunds(session["user"]))


@app.route("/home/portfolio")
def portfolio():
    username = session["user"]
    portfolioList = []
    portfolio = queries.getPortfolio(username)
    tickers = [t[0] for t in portfolio]
    name = [t[1] for t in portfolio]
    ytd = [t[2] for t in portfolio]
    amount = [t[3] for t in portfolio]
    price = [t[4] for t in portfolio]    
    total = [t[5] for t in portfolio]

    etfTotal = 0
    for i in range(len(total)):
        etfTotal += total[i]
    
    tableLen = len(tickers)
    
    for i in range(tableLen):
        row = []
        row.append(tickers[i])
        row.append(name[i])
        row.append(ytd[i])
        row.append(amount[i])
        row.append(price[i])
        row.append(total[i])
        portfolioList.append(row)
    row = [' ' for t in range(5)]
    row.append(etfTotal)
    portfolioList.append(row)
    return render_template("portfolio.html", portfolioList = portfolioList)



@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        session.permanent = True
        username = request.form["username"]
        password = request.form["password"]
        hashedPW = hashlib.sha256(password.encode())
        user = queries.getUser(username, hashedPW)  
        if user:
            if user[0][1] == username and user[0][2] == hashedPW.hexdigest():
                session["user"] = username
                session["userID"] = queries.getUserID(username)
                return redirect(url_for("home"))
            # else:
            #     flash("Invalid username or password!")
        else:
            flash("Incorrect username or password", "error")
    else:
        if "user" in session:
            flash("Already logged in!")
            return redirect(url_for("home"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    if "user" in session:
        user = session["user"]
        flash(f"logged out, {user}", "info")
    session.pop("user", None)
    session.pop("userID", None)
    return redirect(url_for("login"))


@app.route("/register",  methods=["POST", "GET"])
def register():
    if request.method == "POST":
        fname = request.form["firstname"]
        lname = request.form["lastname"]
        username = request.form["username"]
        password = request.form["password"]


        # check if user already exists
        if not(fname and lname and username and password):
            flash("Please enter each field with information", "error")
        elif queries.isUser(username):
            userID = queries.createUserID()
            queries.insertUser(userID, fname, lname, username, password)
            return redirect(url_for("login"))
        else:
            flash("User already exists!", "error")
    return render_template("register.html")
    

if __name__ == "__main__":
    app.run(debug=True)