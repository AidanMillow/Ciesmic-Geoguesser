import math, random, os
from flask import Flask, redirect, session, url_for, escape, render_template, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_table import Table, Col
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.secret_key = "something-something-something-dark-side"
app.sqlalchemy_database_uri = 'sqlite:///' + os.path.join(basedir, 'app.db') #path to database file, required by SQLAlchemy extention
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)
#API key=AIzaSyB6RMRQRaSaFs3eKtk3JxRn7vNtQX5MQ38

totaldifference = 0 #used to calculate the user's total score
selectionindex = [] #array for building a random order for photos to be guessed with
photolist = [{'PhotoNum':55233,'latitude':-43.5329,'longitude':172.639},
			{'PhotoNum':64422,'latitude':-43.5396,'longitude':172.6373},
			{'PhotoNum':81851,'latitude':-43.5321,'longitude':172.6374},
			{'PhotoNum':95497,'latitude':-43.5366,'longitude':172.6446},			
			{'PhotoNum':135054, 'latitude':-43.5306, 'longitude':172.631},
			{'PhotoNum':163358,'latitude':-43.5323,'longitude':172.6398},
			{'PhotoNum':172289,'latitude':-43.5383,'longitude':172.6465},
			{'PhotoNum':173308, 'latitude':-43.5316, 'longitude':172.6323},
			{'PhotoNum':283179, 'latitude':-43.5361, 'longitude':172.6365}]

def buildselect():
	#This function adds a number for each photo in the photolist dictionary
	global selectionindex
	global totaldifference
	totaldifference=0
	selectionindex = []
	i=0
	for photo in photolist:
		selectionindex.append(i)
		i+=1
			
buildselect()

''' The following classes are tables in the database, used for its construction and querying. '''

class User(db.Model):
	#Represents the list of users in the database. Users have an ID, username, and password
	id = db.Column(db.Integer, primary_key = True)
	username = db.Column(db.String(80), unique = True)
	password = db.Column(db.String(20))
	
	#IDs are generated automatically. When a user is declared, only the username and password needs to be set
	def __init__(self, username, password):
		self.username = username
		self.password = password
		
	def __repr__(self):
		return '<User %r>' % self.username
		
class Score(db.Model):
	#Represents the high scores list in the database. Scores have a many to one relationship with Users
	id = db.Column(db.Integer, primary_key = True)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	user = db.relationship('User', backref=db.backref('scores', lazy='dynamic'))
	score = db.Column(db.Float)
	
	def __init__(self, user_id, score):
		self.user_id = user_id
		self.score = score
	
	def __repr__(self):
		return '<Score %r>' % self.score

		
class HighScores(Table):
	#This class represents the HTML table that will be built on the final page of the application
	user = Col('User')
	score = Col('Score')
		
''' The following code builds the database and adds test users to it. The test users may be removed once the application is complete '''		

db.create_all()
brad = User('Brad', 'something')
aidan = User('Aidan', 'something')
testuser = User('Test', 'something')
db.session.add(brad)
db.session.add(aidan)
db.session.add(testuser)
db.session.commit()
CurrentUser = None #This is the variable that tracks which user is currently logged in

def directrender(url, **kwargs):
	#This method is meant to replace render_template methods to check if a user is signed in, but it doesn't work yet
	global CurrentUser
	if CurrentUser != None:
		for row in User.query.filter_by(username=str(CurrentUser.username)):
			exist = row
		if exist != None:
			return render_template(url, **kwargs)
	else:
		flash("No user is currently signed in")
		return redirect(url_for('login'))
	
@app.route('/geoguess')
def init():
	#The default url on startup
	return redirect(url_for('login',PhotoNo = random_photo()))
	
@app.route('/geoguess/login', methods = ['POST', 'GET'])
def login():
	#The login page for the application
	global CurrentUser
	if request.method == 'POST':
		exist = None
		if request.form['type'] == 'register':
			#This is what transpires if the user chooses to create a new account
			for row in User.query.filter_by(username=str(request.form['username'])):
				exist = row
			if exist == None:
				#A new user is only added when the username does not already exist
				newuser = User(str(request.form['username']),str(request.form['password']))
				db.session.add(newuser)
				db.session.commit()
				for row in User.query.filter_by(username=str(request.form['username'])):
					#This query is just to catch potential database failures
					exist = row
				if exist != None:
					CurrentUser = exist
					buildselect()
					flash("Welcome "+ CurrentUser.username +", let us begin")
				else:
					flash("There was an error during registration")
			else:
				flash("A user with that name already exists")
		elif request.form['type'] == 'signin':
			#This is what transpires when the user chooses to get back on an existing account
			for row in User.query.filter_by(username=str(request.form['username']), password=str(request.form['password'])):
				exist = row
			if exist != None:
				#The query checks for username and password, they must both be correct to gain access
				CurrentUser = exist
				buildselect()
				flash("Welcome back "+ CurrentUser.username +", let us begin")
			else:
				flash("Your username or password was incorrect")
	exist = None
	#Once the CurrentUser has been set (or not), the page will be rendered depending on its validity
	if CurrentUser != None:
		#If the user is not set, the login page displays as normal
		for row in User.query.filter_by(username=str(CurrentUser.username)):
			exist = row
		if exist != None:
			if request.method == 'GET':
				#If the CurrentUser is set and the user manually reopens the login page, they will be notified as such
				flash("You are already signed in")
			return redirect(url_for('guess_photo', PhotoNo = random_photo()))
	return render_template('login.html')

@app.route('/geoguess/guess/<int:PhotoNo>')
def guess_photo(PhotoNo):
	#The page used to view and guess any of the photos in the photolist
    return directrender('guess.html', photo = PhotoNo, difference=-1)

@app.route('/geoguess/check/<int:PhotoNo>', methods =['POST', 'GET'])
def check_guess(PhotoNo):
	#The page used to calculate the user's score
    if request.method == 'POST':
		global totaldifference
		for photo in photolist:
			#finds the photo the user was guessing, then removes it from the selectionindex
			if PhotoNo == photo['PhotoNum']:
				latitude=photo['latitude']
				longitude=photo['longitude']
				Photo=photolist.index(photo)
		Guessdifference=math.sqrt(pow(110.574*(float(request.form['latitude'])-latitude),2)+pow(111.32*math.cos(math.radians(latitude))*(float(request.form['longitude'])-longitude),2))*1000
		totaldifference += Guessdifference
		Guessdifference=float("%.3f" % Guessdifference)
		Guess=str(request.form['latitude'])+','+str(request.form['longitude'])
		report(Guessdifference)
		return redirect(url_for('get_feedback', myPhoto=Photo, myGuess=Guess))
    else:
		return redirect(url_for('next_photo'))
def random_photo():
	#picks a random photo from the list, then removes it from the selectionindex
	myChoice=random.choice(selectionindex)
	return photolist[myChoice]['PhotoNum']


@app.route('/geoguess/set_values/<int:PhotoNo>', methods =['POST', 'GET'])
def confirm_values(PhotoNo):
	if request.method == 'POST':
		latitude=request.form['latitude']
		longitude=request.form['longitude']
		return directrender('confirm.html', photo=PhotoNo, lat=latitude, long=longitude)
	

@app.route('/geoguess/finish')
def finished_round():
	#The end screen for the app when a user has guessed through all photos
	global totaldifference
	totaldifference=float("%.3f" % totaldifference) #rounds the difference to 3 decimal places
	showdifference = totaldifference #saves the difference to show so that it can safely be reset
	#the score is then saved to the database
	if CurrentUser != None:
		sessionscore = Score(CurrentUser.id, totaldifference)
		db.session.add(sessionscore)
		db.session.commit()
	#Then we build and show the high score table and rebuild the selectindex
	scoretable = []
	for item in Score.query.order_by(Score.score.asc()):
		scoretable.append({'user':item.user.username,'score':item.score})
	buildselect()
	return directrender('finish.html', difference=showdifference, table = HighScores(scoretable))

def report(diff):
	#This function flashes a message for the user depending on how close they got
	message = "Your last guess was "+str(diff)+" m away from the actual location"
	flash(message)
	if diff >= 37000.1:
		message = "Was that even in christchurch?"
	elif diff >= 2500.1:
		message = "That's a long way off"
	elif diff >= 500.1:
		message = "Getting there, try and get a bit closer"
	elif diff >= 100.1:
		message = "You're in the right area, but you can still do better"
	else:
		message = "That's really close, good job!"
	flash(message)
	
@app.route('/geoguess/feedback/<myPhoto>/<myGuess>')
def get_feedback(myPhoto, myGuess):
	#Gathers values for latitude and longitude of the guess and the actual location and feeds them to an html page to place markers on a map.
	Guess=myGuess.split(",")
	guesslat=(Guess[0])
	guesslong=(Guess[1])
	myPhoto=int(myPhoto)
	selectionindex.remove(myPhoto)
	Actual=photolist[myPhoto]
	actuallat=Actual['latitude']
	actuallong=Actual['longitude']
	return render_template('feedback.html', actlat=actuallat, actlong=actuallong, glat=guesslat, glong=guesslong)

@app.route('/geoguess/next_photo', methods =['POST', 'GET'])
def next_photo():
	if selectionindex == []:
		#selectionindex will be empty once the user has guessed all photos. The user will then be redirected
		return redirect(url_for('finished_round'))
	else:
		return redirect(url_for('guess_photo',PhotoNo = random_photo()))

@app.route('/geoguess/logout')
def logout():
	#redirect page that logs out the user and returns to the login screen
	global CurrentUser
	CurrentUser = None
	return redirect(url_for('login'))

if __name__ == '__main__':
	app.run(debug=True)