import os, math
from flask import Flask, redirect, url_for, escape, render_template, request, flash
from scripts.config import DevelopmentConfig
from scripts.model import User, Score
from scripts.photos.photos import create_photo_list, buildselect, random_photo, buildPhotoList
from scripts.database import db_session, init_db



app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
app._static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
init_db()


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

#Global variables
fullphotolist = create_photo_list() #The entire list of available photos
photolist = [] #The list  of photos the game will use, which is filled when the game starts
selection_index=[] #The indices that are used to access the photolist without affecting it directly
gameSize = 0 #The amount of photos the user has chosen to guess in one session
CurrentUser = None #The user that is currently logged in
totaldifference = 0 #The user's total score for the current session
error = None #A backup variable used in place of the flash method. Will be replaced when session data can be reduced
current_score = 0
round = 0
rounds = 0

def displayscores():
    scoretable = []
    catlist = []    
    for row in Score.query.distinct(Score.category):
        if row.category not in catlist:
            catlist.append(row.category)
            table = []
            ranking = 0
            for item in Score.query.filter(Score.category == row.category).order_by(Score.score.asc()):
                if ranking < 10:
                    ranking+=1                    
                else:
                    break       
    
    return scoretable, catlist
    
@app.route('/')
def init():
    #The home page for the app, where the user is meant to begin    
    global CurrentUser    
    scoretable, catlist = displayscores()    
    return render_template('base.html',app=app,user=CurrentUser, tables = scoretable, titles = catlist, error=error)

@app.route('/login', methods = ['POST'])
def login():    
    #The login page for the application
    global error
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
            error = "Please enter a valid username and password"
    #Once the CurrentUser has been set (or not), the page will be rendered depending on its validity    
    return redirect(url_for('init'))

def register(formname, formpass):
    #This is what transpires if the user chooses to create a new account
    global error  
    global CurrentUser
    exist = None    
    for row in User.query.filter_by(username=str(formname)):
        exist = row
    if exist == None:
        #A new user is only added when the username does not already exist
        newuser = User(str(formname),str(formpass))
        db_session.add(newuser)
        db_session.commit()
        for row in User.query.filter_by(username=str(formname)):
            #This query is just to catch potential database failures
            exist = row
        if exist != None:
            CurrentUser = exist
            buildselect(photolist)
            error = "You have successfully registered as "+ CurrentUser.username
        else:
            error = "There was an error during registration"
    else:
        error = "A user with that name already exists"
    

def signin(formname, formpass):
    #This is what transpires when the user chooses to get back on an existing account
    global error
    global CurrentUser
    exist = None
    for row in User.query.filter_by(username=str(formname), password=str(formpass)):
        exist = row
    if exist != None:
        #The query checks for username and password, they must both be correct to gain access
        CurrentUser = exist
        buildselect(photolist)
        error = "Welcome back "+ CurrentUser.username +", let us begin"
    else:
        error = "Your username or password was incorrect"
    
    
@app.route('/start', methods = ['POST','GET'])
def start_game():
    #The method that sets up a new play session for the game and displays the first photo
    global error
    global photolist
    global selection_index
    global gameSize
    global totaldifference
    global CurrentUser
    global current_score
    global Round
    gameSize=int(request.form['length'])
    selection_data = buildPhotoList(fullphotolist,gameSize)
    photolist = selection_data[0]
    selection_index=selection_data[1]
    totaldifference = 0
    current_score = 0
    Round = 1
    PhotoNo = random_photo(photolist,selection_index)
    for photo in photolist:        
        if PhotoNo == photo['PhotoNum']:            
            creator = photo['creator']
            license = photo['license']
    return render_template("guess.html",user = CurrentUser, PhotoNo = random_photo(photolist,selection_index), rounds = len(photolist), score = current_score, round = Round, creator = creator, license = license)
    
@app.route('/guess', methods = ['POST', 'GET'])
def new_guess():
    #Every photo that displays after the first is displayed on this page one at a time
    global error
    global CurrentUser
    global current_score
    global Round
    Round += 1
    PhotoNo = random_photo(photolist,selection_index)
    for photo in photolist:
        if PhotoNo == photo['PhotoNum']:
            creator = photo['creator']
            license = photo['license']
    return render_template("guess.html", user=CurrentUser, PhotoNo = random_photo(photolist,selection_index), error = error, score = current_score, rounds = len(photolist), round = Round, creator = creator, license = license)

@app.route('/check', methods =['POST'])
def check_guess():
    #The page used to calculate the user's score for a guess on any given photo in the list
    global error
    global CurrentUser    
    if request.method == 'POST':        
        global totaldifference
        global current_score
        global Round
        PhotoNo = request.form['photo']        
        for photo in photolist:
            #finds the photo the user was guessing, then removes it from the selection_index
            if PhotoNo == photo['PhotoNum']:
                latitude = photo['latitude']
                longitude = photo['longitude']
                Photo=photolist.index(photo)        
        formlat = float(request.form['latitude'])
        formlong = float(request.form['longitude'])        
        #The following line calculates the distance in meters between the guessed location and the actual one
        Guessdifference=math.sqrt(pow(110.574*(formlat-latitude),2)+pow(111.32*math.cos(math.radians(latitude))*(formlong-longitude),2))*1000
        totaldifference += Guessdifference
        Guessdifference=float("%.3f" % Guessdifference)
        try: #Removes the photo from the selection index if able
            selection_index.remove(Photo)
        except ValueError: #If unable to remove due to already being removed, the previously added Guessdifference is removed
            totaldifference -= Guessdifference
        scoreReport = report(Guessdifference)        
        global current_score
        if Guessdifference >= 37000.1:
            current_score += 1
        elif Guessdifference >= 750.1:
            current_score += 2
        elif Guessdifference >= 250.1:
            current_score += 3
        elif Guessdifference >= 100.1:
            current_score += 4
        else:
            current_score += 5
        return render_template('feedback.html', user=CurrentUser, actlat=latitude, actlong=longitude, glat=formlat, glong=formlong, scoreReport=scoreReport, score = current_score, rounds = len(photolist), round = Round)        
    else:
        return redirect(url_for('next_photo'))

    

@app.route('/finish', methods = ['POST', 'GET'])
def finished_round():
    #The end screen for the app when a user has guessed through all photos
    global error
    global totaldifference
    global selection_index
    global gameSize
    global current_score
    global Round
    error = False
    totaldifference=float("%.3f" % totaldifference) #rounds the difference to 3 decimal places
    showdifference = totaldifference #saves the difference to show so that it can safely be reset
    #the score is then saved to the database
    if CurrentUser == None:
        error = "You must login to have your score recorded"
    elif CurrentUser != None and selection_index == []:
        sessionscore = Score(CurrentUser.id, totaldifference, gameSize)
        db_session.add(sessionscore)
        db_session.commit()
        selection_index.append(0)         
    return render_template('finish.html', user=CurrentUser, difference=showdifference, gameSize=gameSize, error = error, score=current_score, round=Round, rounds=len(photolist))

def report(diff):
    #This function flashes a error for the user depending on how close they got
    error = "Your guess was <b>"+str(diff)+" m</b> away from the correct location<br>"    
    try:
        diff=float(diff)
    except Exception:
        return "There was an error reporting your score"    
    return error

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
    global error
    global CurrentUser
    scoretable, catlist = displayscores()
    CurrentUser = None   
    return render_template('base.html',user=CurrentUser, error=None, tables = scoretable, titles = catlist)
