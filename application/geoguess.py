import os, math
from flask import Flask, redirect, session, url_for, escape, render_template, request, flash
from scripts.config import DevelopmentConfig
from scripts.database import db, User
from scripts.photos.photos import create_photo_list, buildselect, random_photo

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
app._static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
print (app._static_folder)

db.init_app(app)
with app.app_context():        
    db.create_all()
    User.query.delete()
    brad = User('Brad', 'something')
    aidan = User('Aidan', 'something')
    testuser = User('Test', 'something')
    db.session.add(brad)
    db.session.add(aidan)
    db.session.add(testuser)
    db.session.commit()
app.app_context().push()

photolist = create_photo_list()
selection_index = buildselect(photolist)
CurrentUser = None
totaldifference = 0

def directrender(url, **kwargs):
    #This method is meant to replace render_template methods to check if a user is signed in, but it doesn't work yet    
    if CurrentUser != None:
        for row in User.query.filter_by(username=str(CurrentUser.username)):
            exist = row
            if exist != None:
                return render_template(url, **kwargs)
            else:
                flash("No user is currently signed in")
                return redirect(url_for('/'))       
                
@app.route('/')
def init():
    return render_template('base.html',app=app,user=CurrentUser)
            
@app.route('/login', methods = ['POST'])
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
                    buildselect(photolist)
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
				buildselect(photolist)
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
			return render_template('base.html',user=CurrentUser)

@app.route('/start', methods = ['POST'])
def start_game():    
    return render_template("guess.html",PhotoNo = random_photo(photolist,selection_index),difference=-1)

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
        try:
            formlat = float(request.form['latitude'])
            formlong = float(request.form['longitude'])
        except ValueError:
			flash("Please select a location")
			return redirect(url_for('guess_photo', PhotoNo = PhotoNo))        
        Guessdifference=math.sqrt(pow(110.574*(float(request.form['latitude'])-latitude),2)+pow(111.32*math.cos(math.radians(latitude))*(float(request.form['longitude'])-longitude),2))*1000
        totaldifference += Guessdifference
        Guessdifference=float("%.3f" % Guessdifference)
        Guess=str(request.form['latitude'])+','+str(request.form['longitude'])
        try:
            selection_index.remove(Photo)
        except ValueError:
            totaldifference -= Guessdifference
        return redirect(url_for('get_feedback', myPhoto=Photo, myGuess=Guess, myDiff=Guessdifference))
    else:
        return redirect(url_for('next_photo'))

    

@app.route('/finish')
def finished_round():
	#The end screen for the app when a user has guessed through all photos
	global totaldifference
	totaldifference=float("%.3f" % totaldifference) #rounds the difference to 3 decimal places
	showdifference = totaldifference #saves the difference to show so that it can safely be reset
	#the score is then saved to the database
	if CurrentUser != None and selectionindex == []:
		sessionscore = Score(CurrentUser.id, totaldifference)
		db.session.add(sessionscore)
		db.session.commit()
	#Then we build and show the high score table and rebuild the selectindex
	scoretable = []
	for item in Score.query.order_by(Score.score.asc()):
		scoretable.append({'user':item.user.username,'score':item.score})
	buildselect(photolist)
	return directrender('finish.html', difference=showdifference, table = HighScores(scoretable))

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
	
@app.route('/feedback/<myPhoto>/<myGuess>/<myDiff>')
def get_feedback(myPhoto, myGuess, myDiff):
    #Gathers values for latitude and longitude of the guess and the actual location and feeds them to an html page to place markers on a map.
    Guess=myGuess.split(",")
    guesslat=(Guess[0])
    guesslong=(Guess[1])
    myPhoto=int(myPhoto)	
    Actual=photolist[myPhoto]
    actuallat=Actual['latitude']
    actuallong=Actual['longitude']
    scoreReport = report(myDiff)
    return directrender('feedback.html', actlat=actuallat, actlong=actuallong, glat=guesslat, glong=guesslong, scoreReport=scoreReport)

@app.route('/next_photo', methods =['POST', 'GET'])
def next_photo():
	if selection_index == []:
		#selection_index will be empty once the user has guessed all photos. The user will then be redirected
		return redirect(url_for('finished_round'))
	else:
		return redirect(url_for('start',PhotoNo = random_photo(photolist,selection_index)))

@app.route('/logout',methods =['POST'])
def logout():
    #redirect page that logs out the user and returns to the login screen	
    global CurrentUser
    CurrentUser = None
    return render_template('base.html',user=CurrentUser)
