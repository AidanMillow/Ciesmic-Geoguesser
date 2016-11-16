import os, math
from flask import Flask, redirect, session, url_for, escape, render_template, request, flash
from scripts.config import DevelopmentConfig
from scripts.database import db, User, Score, HighScores
from scripts.photos.photos import create_photo_list, buildselect, random_photo, buildPhotoList

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
app._static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
print (app._static_folder)

db.init_app(app)
with app.app_context():
	db.create_all()
	User.query.delete()
	Score.query.delete()
	brad = User('Brad', 'something')
	aidan = User('Aidan', 'something')
	testuser = User('Test', 'something')
	db.session.add(brad)
	db.session.add(aidan)
	db.session.add(testuser)
	db.session.commit()
app.app_context().push()

fullphotolist = create_photo_list()
photolist = []
selection_index=[]
gameSize = 0
CurrentUser = None
totaldifference = 0

def directrender(url, **kwargs):
    #This method is meant to replace render_template methods to check if a user is signed in, but it doesn't work yet    
    if CurrentUser != None:
        for row in User.query.filter_by(username=str(CurrentUser.username)):
            exist = row
            if exist != None:
                return render_template(url, user=CurrentUser, **kwargs)
    flash("No user is currently signed in")
    return redirect(url_for('init'))

@app.route('/')
def init():
    return render_template('base.html',app=app,user=CurrentUser)

@app.route('/login', methods = ['POST'])
def login():    
    #The login page for the application
	if request.method == 'POST':
		formname = request.form['username']
		formpass = request.form['password']
		invalids = (" ","\\","/",":",";","[","]","{","}","(",")","-","+","=","\"","'")
		if (1 <= len(formname) <= 15 and len(formpass) >= 1 and not any(i in formname for i in invalids) and not any(i in formpass for i in invalids)):
			if request.form['type'] == 'register':			
				register(formname, formpass)
			elif request.form['type'] == 'signin':
				signin(formname, formpass)
		else:
			flash("Please enter a valid username and password. Valid usernames are 1-15 characters long.")
	#Once the CurrentUser has been set (or not), the page will be rendered depending on its validity
	return redirect(url_for('init'))

def register(formname, formpass):
	#This is what transpires if the user chooses to create a new account
	global CurrentUser
	exist = None
	for row in User.query.filter_by(username=str(formname)):
		exist = row
	if exist == None:
		#A new user is only added when the username does not already exist
		newuser = User(str(formname),str(formpass))
		db.session.add(newuser)
		db.session.commit()
		for row in User.query.filter_by(username=str(formname)):
			#This query is just to catch potential database failures
			exist = row
		if exist != None:
			CurrentUser = exist
			buildselect(photolist)
		else:
			flash("There was an error during registration")
	else:
		flash("A user with that name already exists")

def signin(formname, formpass):
	#This is what transpires when the user chooses to get back on an existing account
	global CurrentUser
	exist = None
	for row in User.query.filter_by(username=str(formname), password=str(formpass)):
		exist = row
	if exist != None:
		#The query checks for username and password, they must both be correct to gain access
		CurrentUser = exist
		buildselect(photolist)
		flash("Welcome back "+ CurrentUser.username +", let us begin")
	else:
		flash("Your username or password was incorrect")

@app.route('/start', methods = ['POST','GET'])
def start_game():
    global photolist
    global selection_index
    global gameSize
    gameSize=int(request.form['length'])
    selection_data = buildPhotoList(fullphotolist,gameSize)
    photolist = selection_data[0]
    selection_index=selection_data[1]
    return render_template("guess.html",PhotoNo = random_photo(photolist,selection_index))
	
@app.route('/guess', methods = ['POST','GET'])
def new_guess():
	return render_template("guess.html",PhotoNo = random_photo(photolist,selection_index))

@app.route('/check', methods =['POST'])
def check_guess():
    #The page used to calculate the user's score    
    if request.method == 'POST':        
        global totaldifference
        PhotoNo = request.form['photo']
        for photo in photolist:
            #finds the photo the user was guessing, then removes it from the selection_index
            if PhotoNo == photo['PhotoNum']:
                latitude = photo['latitude']
                longitude = photo['longitude']
                Photo=photolist.index(photo)
                myPhoto=photo
        try:
            formlat = float(request.form['latitude'])
            formlong = float(request.form['longitude'])
        except ValueError:
			flash("Please select a location")
			return render_template('guess.html', PhotoNo=myPhoto)     
        Guessdifference=math.sqrt(pow(110.574*(float(request.form['latitude'])-latitude),2)+pow(111.32*math.cos(math.radians(latitude))*(float(request.form['longitude'])-longitude),2))*1000
        totaldifference += Guessdifference
        Guessdifference=float("%.3f" % Guessdifference)
        Guess=str(request.form['latitude'])+','+str(request.form['longitude'])
        try:
            selection_index.remove(Photo)
        except ValueError:
			totaldifference -= Guessdifference
        Guess=Guess.split(',')
        guesslat=(Guess[0])
        guesslong=(Guess[1])
        actuallat=myPhoto['latitude']
        actuallong=myPhoto['longitude']
        scoreReport = report(Guessdifference)
        return render_template('feedback.html', actlat=actuallat, actlong=actuallong, glat=guesslat, glong=guesslong, scoreReport=scoreReport)		
    else:
        return redirect(url_for('next_photo'))

    

@app.route('/finish')
def finished_round():
	#The end screen for the app when a user has guessed through all photos
	global totaldifference
	global selection_index
	totaldifference=float("%.3f" % totaldifference) #rounds the difference to 3 decimal places
	showdifference = totaldifference #saves the difference to show so that it can safely be reset
	#the score is then saved to the database
	if CurrentUser == None:
		message = "<h1>"
		message += "You total error was " + str(totaldifference) + ". "
		message += "You must login to have your score recorded </h1>"
		return render_template('noscore.html', message=message)
	else: 
		if CurrentUser != None and selection_index == []:
			sessionscore = Score(CurrentUser.id, totaldifference)
			db.session.add(sessionscore)
			db.session.commit()
		#Then we build and show the high score table and rebuild the selectindex
		scoretable = []
		for item in Score.query.order_by(Score.score.asc()):
			scoretable.append({'user':item.user.username,'score':item.score})
		return render_template('finish.html', difference=showdifference, table = HighScores(scoretable))

def report(diff):
	#This function flashes a message for the user depending on how close they got
	message = "<h1>Your last guess was "+str(diff)+" m away from the actual location<br>"
	try:
		diff=float(diff)
	except Exception:
		return "There was an error reporting your score"
	if diff >= 37000.1:
		message += "Was that even in christchurch?</h1>"
	elif diff >= 2500.1:
		message += "That's a long way off</h1>"
	elif diff >= 500.1:
		message += "Getting there, try and get a bit closer</h1>"
	elif diff >= 100.1:
		message += "You're in the right area, but you can still do better</h1>"
	else:
		message += "That's really close, good job!</h1>"
	return message

@app.route('/next_photo', methods =['POST', 'GET'])
def next_photo():
	if selection_index == []:
		#selection_index will be empty once the user has guessed all photos. The user will then be redirected
		return redirect(url_for('finished_round'))
	else:
		return redirect(url_for('new_guess'))

@app.route('/logout',methods =['POST'])
def logout():
    #redirect page that logs out the user and returns to the login screen	
    global CurrentUser
    CurrentUser = None
    return render_template('base.html',user=CurrentUser)
