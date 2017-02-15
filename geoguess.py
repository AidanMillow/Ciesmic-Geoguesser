import os, math, ast
from flask import Flask, redirect, url_for, escape, render_template, request, flash, make_response
from scripts.config import DevelopmentConfig
from scripts.model import User, Score
from scripts.photos.photos import create_photo_list, buildselect, random_photo, buildPhotoList
from scripts.database import db_session, init_db



app = Flask(__name__)
init_db()

#Global variables
fullphotolist = create_photo_list() #The entire list of available photos
user_error = None
game_error = None

def displayscores():
    #This is the method used for displaying high score tables on any given page
    scoretable = [] #The array that stores the information in the high scores table
    catlist = []    #The list of different categories that have been guessed
    for row in Score.query.distinct(Score.category):
        if row.category not in catlist:
            catlist.append(row.category) #The method creates a seperate high score table for each category in the catlist
            table = [] #And assigns each to an array
            ranking = 0 #A score's rank is not recorded in the table, so it is calculated during the loop
            for item in Score.query.filter(Score.category == row.category).order_by(Score.score.desc()):
                if ranking < 10: #Each table only displays the top ten scores
                    ranking+=1
                    Username=str(item.user.username)
                    displayscore=str(item.score)
                    displayscore=displayscore[:-2]
                    table.append({'ranking':ranking, 'user':Username,'score':displayscore})                 
                else:
                    break       
            scoretable.append(table)
    return scoretable, catlist
    
    
@app.route('/')
def init():
    #The home page for the app, where the user is meant to begin     
    global user_error
    scoretable, catlist = displayscores()   
    resp = make_response(render_template('base.html',app = app, tables = scoretable, titles = catlist, user_error = user_error, photolist = fullphotolist))
    return resp	

    
@app.route('/start', methods = ['POST','GET'])
def start_game():
    #The method that sets up a new play session for the game and displays the first photo
    global user_error
    Round = 1
    gameSize=int(request.form['length'])
    selection_data = buildPhotoList(fullphotolist,gameSize)
    photolist = selection_data[0]
    selection_index=selection_data[1]
    totaldifference = 0
    current_score = 0
    PhotoNo = random_photo(photolist,selection_index)
    for photo in photolist:        
        if PhotoNo == photo['PhotoNum']:            
            creator = photo['creator']
            license = photo['license']
    error = user_error
    user_error = None
    resp = make_response(render_template("guess.html", PhotoNo = random_photo(photolist,selection_index), rounds = len(photolist), score = current_score, round = Round, creator = creator, license = license, locked='false', error=flash))
    resp.set_cookie('imagenumber', str(Round))
    resp.set_cookie('rounds', str(gameSize))
    resp.set_cookie('photolist', str(photolist))
    resp.set_cookie('selection_index', str(selection_index))
    resp.set_cookie('totaldifference', str(totaldifference))
    resp.set_cookie('current_score', str(current_score))
    return resp
    
@app.route('/guess', methods = ['POST', 'GET'])
def new_guess():
    #Every photo that displays after the first is displayed on this page one at a time
    global user_error
    photolist = ast.literal_eval(request.cookies.get('photolist'))
    selection_index = ast.literal_eval(request.cookies.get('selection_index'))
    current_score = int(request.cookies.get('current_score'))
    Round = int(request.cookies.get('imagenumber'))
    PhotoNo = random_photo(photolist,selection_index)
    for photo in photolist:
        if PhotoNo == photo['PhotoNum']:
            creator = photo['creator']
            license = photo['license']
    error = user_error
    user_error = None
    resp = make_response(render_template("guess.html", PhotoNo = random_photo(photolist,selection_index), error = flash, score = current_score, rounds = len(photolist), round = Round, creator = creator, license = license, locked = 'false'))
    return resp

@app.route('/check', methods =['POST'])
def check_guess():
    #The page used to calculate the user's score for a guess on any given photo in the list
    global user_error
    locked = 'false'
    if request.method == 'POST':
        photolist = ast.literal_eval(request.cookies.get('photolist'))
        selection_index = ast.literal_eval(request.cookies.get('selection_index'))
        totaldifference = float(request.cookies.get('totaldifference'))
        current_score = int(request.cookies.get('current_score'))		
        Round = int(request.cookies.get('imagenumber'))
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
        if Round==int(request.form['imagenumber']):
            scoredifference = Guessdifference // 10
            roundscore = 100 - scoredifference
            roundscore = max(0.0, roundscore)
            current_score += int(roundscore)
        else:
            locked='true'		
        scoreReport = report(Guessdifference) 			
        resp = make_response(render_template('feedback.html', actlat=latitude, actlong=longitude, glat=formlat, glong=formlong, scoreReport=scoreReport, score = current_score, rounds = len(photolist), round = Round, image=PhotoNo, locked=locked))
        if Round==int(request.form['imagenumber']):
            Round+=1
        resp.set_cookie('imagenumber',str(Round))
        resp.set_cookie('selection_index',str(selection_index))
        resp.set_cookie('totaldifference', str(totaldifference))
        resp.set_cookie('current_score', str(current_score))
        return resp        
    else:
        return redirect(url_for('next_photo'))

    

@app.route('/finish', methods = ['POST', 'GET'])
def finished_round():
    #The end screen for the app when a user has guessed through all photos
    photolist = ast.literal_eval(request.cookies.get('photolist'))
    selection_index = ast.literal_eval(request.cookies.get('selection_index'))
    current_score = int(request.cookies.get('current_score'))
    totaldifference = float(request.cookies.get('totaldifference'))
    Round = int(request.cookies.get('imagenumber'))
    gameSize = request.cookies.get('rounds')
    message = None
    displaytable = "none"
    totaldifference=float("%.3f" % totaldifference) #rounds the difference to 3 decimal places
    showdifference = totaldifference #saves the difference to show so that it can safely be reset
    #the score is then saved to the database
    highscore = high_score(current_score, gameSize)
    resp = make_response(render_template('finish.html', difference=showdifference, gameSize=gameSize, message = message, score=current_score, round=Round, rounds=len(photolist), highscore = highscore))
    return resp
	
def high_score(score, gameSize):
	ranking = 0
	for item in Score.query.filter(Score.category == gameSize).order_by(Score.score.desc()):
		if score > item.score:
			return None #The HTML will check for None and display a form if it finds it
		ranking += 1
		if ranking >= 10:
			return "Score to beat: " + str(item.score)
	return None
	
def display_final_scores():
    displaytable = []
    scoretable = []
    ranking=0
    for item in Score.query.filter(Score.category == gameSize).order_by(Score.score.desc()):
        ranking+=1
        scoretable.append({'ranking':ranking, 'user':item.user.username, 'score':item.score})        
    myranking = None
    for item in scoretable:
        if item['user']==CurrentUser.username and item['score']==current_score:
            myranking=item['ranking']
            break
    for item in scoretable:
        if item['ranking']>myranking-5 and item['ranking']<myranking+5:
            displayscore=str(item['score'])
            displayscore=displayscore[:-2]
            displaytable.append({'ranking':item['ranking'], 'user':item['user'], 'score':displayscore})
    return displaytable	

def report(diff):
    #This function flashes a error for the user depending on how close they got
	
    error = "Your guess was <b>"+str(diff)+" m</b> away from the correct location."    
    try:
        diff=float(diff)
    except Exception:
        return "There was an error reporting your score"    
    return error

@app.route('/submit', methods = ['POST'])
def submitScore():
	gameSize = request.cookies.get('rounds')
	current_score = int(request.cookies.get('current_score'))
	player = str(request.form["player"]).lower()
	bad = {"anus":"ants", "arse":"donkey", "arsehole":"anthill", "ass":"donkey", "asshole":"anthill", "bastard":"mustard", "bitch":"dog", "boner":"loner", "boob":"fruit", 
	"butt":"tub", "chode":"choir", "cock":"bird", "cooter":"kitten", " cum":" can", "cunt":"cat", "damn":"darn", "dick":"richard", "dildo":"dodo", "douche":"soap", 
	"fag":"bag", "fuck":"fudge", "gay":"happy", "gringo":"orange", "hell":"well", "jizz":"jazz", "kunt":"cat", "lesbian":"lasagna", "lesbo":"limbo", "nigg":"bigg", 
	"penis":"pants", "piss":"pine", "pussy":"kitten", "semen":"sailor", "shit":"soot", "vagina":"kitten" }
	indb = False
	for badword, goodword in bad.items():
		player = player.replace(badword,goodword)
	for item in User.query.filter(User.username == player):
		indb = True
	if not indb:
		db_session.add(User(player, "something"))
	db_session.add(Score(player, current_score, gameSize))
	db_session.commit()
	return redirect(url_for('init'))
		
@app.route('/next_photo', methods =['POST', 'GET'])
def next_photo():
    selection_index = ast.literal_eval(request.cookies.get('selection_index'))
    if selection_index == []:
        #selection_index will be empty once the user has guessed all photos. The user will then be redirected
        return redirect(url_for('finished_round'))
    else:
        return redirect(url_for('new_guess'))
        
@app.route('/view_image', methods =['POST', 'GET'])
def view_image():
    if request.method == 'POST':
        image_pid = request.form['image']
        return redirect("http://quakestudies.canterbury.ac.nz/store/part/" + image_pid)
    

@app.route('/logout',methods =['POST'])
def logout():
    #redirect page that logs out the user and returns to the login screen    
    global user_error
    scoretable, catlist = displayscores()   
    resp = make_response(render_template('base.html', user_error=user_error, tables = scoretable, titles = catlist))
    error = None
    return resp
    
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
