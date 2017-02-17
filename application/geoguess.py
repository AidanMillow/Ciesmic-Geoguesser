import os, math, ast
from flask import Flask, redirect, url_for, escape, render_template, request, flash, make_response
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
user_error = None
game_error = None

def displayscores():
    #This is the method used for displaying high score tables on any given page
    scoretable = []
    catlist = []
    for row in Score.query.distinct(Score.category): #This query searches for each unique category in the database's score tables
        if row.category not in catlist:
            catlist.append(row.category) #The method creates a seperate high score table for each category in the catlist
            table = [] 
            ranking = 0 #A score's rank is not recorded in the table, so it is calculated during the loop
            for item in Score.query.filter(Score.category == row.category).order_by(Score.score.desc()):
                if ranking < 5: #Each table only displays the top ten scores
                    ranking+=1
                    Username=str(item.user.username)
                    displayscore=str(item.score)
                    displayscore=displayscore[:-2]
                    table.append({'ranking':ranking, 'user':Username,'score':displayscore})                 
                else: #loop stops once it reaches the tenth score
                    break       
            scoretable.append(table) #The final table to be printed will consist of every category's table
    return scoretable, catlist
    
    
@app.route('/')
def init():
    #The home page for the app, where the user is meant to begin     
    global user_error
    scoretable, catlist = displayscores()   
    resp = make_response(render_template('base.html',app = app, tables = scoretable, titles = catlist, user_error = user_error))
    return resp	

    
@app.route('/start', methods = ['POST','GET'])
def start_game():
    #The method that sets up a new play session for the game and displays the first photo
    global user_error
	#All of these variables are needed to make the game work, set up here for a new game
    Round = 1 #The number of photos the player will have guessed after the current one
    gameSize=int(request.form['length']) #The amount of photos the player will guess in total this game
    selection_data = buildPhotoList(fullphotolist,gameSize)
    photolist = selection_data[0]
    selection_index=selection_data[1]
    totaldifference = 0 #The total distance between the user's guess and the actual location for all photos
    current_score = 0 #The user's current score
    PhotoNo = random_photo(photolist,selection_index) #The ID of the photo currently being guessed
    for photo in photolist: 
        if PhotoNo == photo['PhotoNum']:            
            creator = photo['creator']
            license = photo['license']
    error = user_error
    user_error = None
    resp = make_response(render_template("guess.html", PhotoNo = random_photo(photolist,selection_index), rounds = len(photolist), score = current_score, round = Round, creator = creator, license = license, locked='false', error=flash))
    #Cookies are then set using the variables set up earlier, so that they may be used on every page
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
	#Variables are set using the cookies set up on the first photo
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
    locked = 'false' #This variable being false allows the user to view this page normally
    if request.method == 'POST':
        photolist = ast.literal_eval(request.cookies.get('photolist'))
        selection_index = ast.literal_eval(request.cookies.get('selection_index'))
        totaldifference = float(request.cookies.get('totaldifference'))
        current_score = int(request.cookies.get('current_score'))		
        Round = int(request.cookies.get('imagenumber'))
        PhotoNo = request.form['photo']     
        for photo in photolist:
            #finds the photo the user was guessing
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
		#Score is calculated based on the diference in meters. Farther distances are worth less points, with a distance of 1km or more being worth 0
        if Round==int(request.form['imagenumber']):
            scoredifference = Guessdifference // 10
            roundscore = 100 - scoredifference
            roundscore = max(0.0, roundscore)
            current_score += int(roundscore)
        else: #Score will only be submitted if the image is the one that the user was assigned last
            locked='true' #When locked is true, the first guess is shown along with an error message
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
    #the user is then offered to save their score if it was high enough
    highscore = high_score(current_score, gameSize)
    resp = make_response(render_template('finish.html', difference=showdifference, gameSize=gameSize, message = message, score=current_score, round=Round, rounds=len(photolist), highscore = highscore))
    return resp
	
def high_score(score, gameSize):
	#This function tells the Jinja code whether or not to display the form for submitting high scores
	ranking = 0
	#Query searches the high scores for the category the user just played
	for item in Score.query.filter(Score.category == gameSize).order_by(Score.score.desc()):
		if score > item.score:
			return None #The HTML will check for None and display a form if it finds it
		ranking += 1
		#The user does not add their score if they are not in the top 10 and instead are shown the 10th highest score
		if ranking >= 10:
			return "Score to beat: " + str(item.score)
	#If the query ends without returning, it means there are less than ten scores in the database
	return None 
	
def display_final_scores():
	#Shows the high score table for the category the user just played. The function is depricated and is currently not in use
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
    #This function flashes an error for the user depending on how close they got
    error = "Your guess was <b>"+str(diff)+" m</b> away from the correct location."    
    try:
        diff=float(diff)
    except Exception:
        return "There was an error reporting your score"    
    return error

@app.route('/submit', methods = ['POST'])
def submitScore():
	#The page that is called when a player submits their name for the high scores
	gameSize = request.cookies.get('rounds')
	current_score = int(request.cookies.get('current_score'))
	player = str(request.form["player"]).lower() #The player's name is converted to lower case to make the filter work
	'''	The following is a dictionary of swears that will be filtered out of the high score table, along with appropriate words that they will be replaced with. 
	Any additional swears or names can be added to the filter with an appropriate replacement without changing the function at all.	'''
	bad = {"anus":"ants", "arse":"donkey", "arsehole":"anthill", "ass":"donkey", "asshole":"anthill", "bastard":"mustard", "bitch":"dog", "boner":"loner", "boob":"fruit", 
	"butt":"tub", "chode":"choir", "cock":"bird", "cooter":"kitten", "cum":"can", "cunt":"cat", "damn":"darn", "dick":"richard", "dildo":"dodo", "douche":"soap", 
	"fag":"bag", "fuck":"fudge", "gay":"happy", "gringo":"orange", "hell":"well", "jizz":"jazz", "kunt":"cat", "lesbian":"lasagna", "lesbo":"limbo", "nigg":"bigg", 
	"penis":"pants", "piss":"pine", "pussies":"kittens", "pussy":"kitten", "queer":"happy", "schlong":"rope", "semen":"sailor", "shit":"soot", "slut":"salt", "spook":"ghost",
	"tard":"tent", "testicle":"popsicle", "testies":"tasty", "titty":"kitty", "vagina":"kitten", "wank":"plank", "whore":"lady"}
	indb = False
	#This for loop will use the above dictionary to filter bad words from the player's name
	for badword, goodword in bad.items():
		player = player.replace(badword,goodword)
	player = player.title() #The player's name is then converted back to camel case for presentation
	#This for loop checks if the name they entered is a user in the database
	for item in User.query.filter(User.username == player):
		indb = True
	#The user's name is added to the database if it is not in it already. Currently this is useless since no users are signing in
	if not indb:
		db_session.add(User(player, "something"))
	db_session.add(Score(player, current_score, gameSize))
	db_session.commit()
	#Since the high scores are displayed on the home page, the function redirects to it instead of a new one
	return redirect(url_for('init'))
		
@app.route('/next_photo', methods =['POST', 'GET'])
def next_photo():
	#Selects the next photo in the list to be guessed and redirects to it
    selection_index = ast.literal_eval(request.cookies.get('selection_index'))
    if selection_index == []:
        #selection_index will be empty once the user has guessed all photos. The user will then be redirected to the end
        return redirect(url_for('finished_round'))
    else:
        return redirect(url_for('new_guess'))
        
@app.route('/view_image', methods =['POST', 'GET'])
def view_image():
	#Redirects to the official quakestudies site where the image is stored
    if request.method == 'POST':
        image_pid = request.form['image']
        return redirect("http://quakestudies.canterbury.ac.nz/store/part/" + image_pid)
    

@app.route('/logout',methods =['POST'])
def logout():
    #Redirect page that logs out the user and returns to the login screen    
    global user_error
    scoretable, catlist = displayscores()   
    resp = make_response(render_template('base.html', user_error=user_error, tables = scoretable, titles = catlist))
    error = None
    return resp