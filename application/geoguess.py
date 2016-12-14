import os, math
from flask import Flask, redirect, session, url_for, escape, render_template, request, flash
from scripts.config import DevelopmentConfig
from scripts.database import db, User, Score, HighScores
from scripts.photos.photos import create_photo_list, buildselect, random_photo, buildPhotoList

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
app._static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
print (app._static_folder)

#Sets up database info for the session
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

#Global variables
fullphotolist = create_photo_list() #The entire list of available photos
photolist = [] #The list  of photos the game will use, which is filled when the game starts
selection_index=[] #The indices that are used to access the photolist without affecting it directly
gameSize = 0 #The amount of photos the user has chosen to guess in one session
CurrentUser = None #The user that is currently logged in
totaldifference = 0 #The user's total score for the current session
flashmessage = None #A backup variable used in place of the flash method. Will be replaced when session data can be reduced

def directrender(url, **kwargs):
    #This method is meant to replace render_template methods to check if a user is signed in, but is currently not in use  
    if CurrentUser != None:
        for row in User.query.filter_by(username=str(CurrentUser.username)):
            exist = row
            if exist != None:
                return render_template(url, user=CurrentUser, **kwargs)
    flash("No user is currently signed in")
    return redirect(url_for('init'))

def displayscores():
	scoretable = []
	catlist = []
	for row in Score.query.distinct(Score.category):
		if row.category not in catlist:
			catlist.append(row.category)
			table = []
			for item in Score.query.filter(Score.category == row.category).order_by(Score.score.asc()):
				table.append({'user':item.user.username,'score':item.score})
			scoretable.append(HighScores(table))
	return scoretable, catlist
	
@app.route('/')
def init():
	#The home page for the app, where the user is meant to begin
	global flashmessage
	scoretable, catlist = displayscores()
	flashing = flashmessage
	flashmessage = None
	return render_template('base.html',app=app,user=CurrentUser, flashed = flashing, tables = scoretable, titles = catlist)

@app.route('/login', methods = ['POST'])
def login():    
    #The login page for the application
	global flashmessage
	if request.method == 'POST':
		formname = request.form['username']
		formpass = request.form['password']
		#Currently a login will fail if the following characters are used in the input boxes
		invalids = (" ","\\","/",":",";","[","]","{","}","(",")","-","+","=","\"","'")
		if (1 <= len(formname) <= 15 and len(formpass) >= 8 and not any(i in formname for i in invalids) and not any(i in formpass for i in invalids)):
			if request.form['type'] == 'register':			
				register(formname, formpass)
			elif request.form['type'] == 'signin':
				signin(formname, formpass)
		else:
			flashmessage = "Please enter a valid username and password. Valid usernames are 1-15 characters long, and valid passwords are at least 8 characters."
	#Once the CurrentUser has been set (or not), the page will be rendered depending on its validity
	return redirect(url_for('init'))

def register(formname, formpass):
	#This is what transpires if the user chooses to create a new account
	global flashmessage
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
			flashmessage = "There was an error during registration"
	else:
		flashmessage = "A user with that name already exists"

def signin(formname, formpass):
	#This is what transpires when the user chooses to get back on an existing account
	global flashmessage
	global CurrentUser
	exist = None
	for row in User.query.filter_by(username=str(formname), password=str(formpass)):
		exist = row
	if exist != None:
		#The query checks for username and password, they must both be correct to gain access
		CurrentUser = exist
		buildselect(photolist)
		flashmessage = "Welcome back "+ CurrentUser.username +", let us begin"
	else:
		flashmessage = "Your username or password was incorrect"

@app.route('/start', methods = ['POST','GET'])
def start_game():
	#The method that sets up a new play session for the game and displays the first photo
    global flashmessage
    global photolist
    global selection_index
    global gameSize
    gameSize=int(request.form['length'])
    selection_data = buildPhotoList(fullphotolist,gameSize)
    photolist = selection_data[0]
    selection_index=selection_data[1]
    flashing = flashmessage
    flashmessage = None
    return render_template("guess.html",PhotoNo = random_photo(photolist,selection_index), flashed = flashing)
	
@app.route('/guess', methods = ['POST', 'GET'])
def new_guess():
	#Every photo that displays after the first is displayed on this page one at a time
	global flashmessage
	flashing = flashmessage
	flashmessage = None
	return render_template("guess.html",PhotoNo = random_photo(photolist,selection_index), flashed = flashing)

@app.route('/check', methods =['POST'])
def check_guess():
    #The page used to calculate the user's score for a guess on any given photo in the list
    global flashmessage
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
			flashmessage = "Please select a location"
			return redirect(url_for('new_guess'))
		#The following line calculates the distance in meters between the guessed location and the actual one
        Guessdifference=math.sqrt(pow(110.574*(float(request.form['latitude'])-latitude),2)+pow(111.32*math.cos(math.radians(latitude))*(float(request.form['longitude'])-longitude),2))*1000
        totaldifference += Guessdifference
        Guessdifference=float("%.3f" % Guessdifference)
        try:
            selection_index.remove(Photo)
        except ValueError:
			totaldifference -= Guessdifference
        guesslat=(str(request.form['latitude']))
        guesslong=(str(request.form['longitude']))
        actuallat=myPhoto['latitude']
        actuallong=myPhoto['longitude']
        scoreReport = report(Guessdifference)
        flashing = flashmessage
        flashmessage = None
        return render_template('feedback.html', actlat=actuallat, actlong=actuallong, glat=guesslat, glong=guesslong, scoreReport=scoreReport, flashed = flashing)		
    else:
        return redirect(url_for('next_photo'))

    

@app.route('/finish', methods = ['POST', 'GET'])
def finished_round():
	#The end screen for the app when a user has guessed through all photos
	global flashmessage
	global totaldifference
	global selection_index
	global gameSize
	message = False
	totaldifference=float("%.3f" % totaldifference) #rounds the difference to 3 decimal places
	showdifference = totaldifference #saves the difference to show so that it can safely be reset
	#the score is then saved to the database
	if CurrentUser == None:
		message = "You must login to have your score recorded"
	elif CurrentUser != None and selection_index == []:
		sessionscore = Score(CurrentUser.id, totaldifference, gameSize)
		db.session.add(sessionscore)
		db.session.commit()
		selection_index.append(0)
	#Then we build and show the high score table and rebuild the selectindex
	scoretable = []
	for item in Score.query.filter(Score.category == gameSize).order_by(Score.score.asc()):
		scoretable.append({'user':item.user.username,'score':item.score})
	flashing = flashmessage
	flashmessage = None
	return render_template('finish.html', difference=showdifference, table = HighScores(scoretable), gameSize=gameSize, message = message, flashed = flashing)

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

@app.route('/next_photo', methods =['POST'])
def next_photo():
	if selection_index == []:
		#selection_index will be empty once the user has guessed all photos. The user will then be redirected
		return redirect(url_for('finished_round'))
	else:
		return redirect(url_for('new_guess'))

@app.route('/logout',methods =['POST'])
def logout():
    #redirect page that logs out the user and returns to the login screen	
    global flashmessage
    global CurrentUser
    scoretable, catlist = displayscores()
    CurrentUser = None
    flashing = flashmessage
    flashmessage = None
    return render_template('base.html',user=CurrentUser, flashed = flashing, tables = scoretable, titles = catlist)
