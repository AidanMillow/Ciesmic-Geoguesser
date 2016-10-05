import math, random, os
from flask import Flask, redirect, session, url_for, escape, render_template, request, flash
from flask_sqlalchemy import SQLAlchemy
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.secret_key = "something-something-something-dark-side"
app.sqlalchemy_database_uri = 'sqlite:///' + os.path.join(basedir, 'app.db') #path to database file, required by SQLAlchemy extention
app.sqlalchemy_track_modifications = True
db = SQLAlchemy(app)
#API key=AIzaSyB6RMRQRaSaFs3eKtk3JxRn7vNtQX5MQ38

totaldifference=0
photolist = [{'PhotoNum':55233,'latitude':-43.5329,'longitude':172.639},
			{'PhotoNum':64422,'latitude':-43.5396,'longitude':172.6373},
			{'PhotoNum':81851,'latitude':-43.5321,'longitude':172.6374},
			{'PhotoNum':135054, 'latitude':-43.5306, 'longitude':172.631},
			{'PhotoNum':149953, 'latitude':-43.5312, 'longitude':172.6413},
			{'PhotoNum':173308, 'latitude':-43.5316, 'longitude':172.6323},
			{'PhotoNum':175357, 'latitude':-43.5322, 'longitude':172.6391},
			{'PhotoNum':175561, 'latitude':-43.5312, 'longitude':172.6394},
			{'PhotoNum':176751, 'latitude':-43.5322, 'longitude':172.6372}]

selectionindex = []
i=0
for photo in photolist:
	selectionindex.append(i)
	i+=1

class User(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	username = db.Column(db.String(80), unique = True)
	password = db.Column(db.String(20))
	
	def __init__(self, username, password):
		self.username = username
		self.password = password
		
	def __repr__(self):
		return '<User %r>' % self.username
		
class Score(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	user = db.relationship('User', backref=db.backref('scores', lazy='dynamic'))
	score = db.Column(db.Float)
	
	def __init__(self, user_id, score):
		self.user_id = user_id
		self.score = score
	
	def __repr__(self):
		return '<Score %r>' % self.score

db.create_all()
brad = User('Brad', 'something')
aidan = User('Aidan', 'something')
db.session.add(brad)
db.session.add(aidan)
db.session.commit()
	
@app.route('/geoguess')
def init():
	return redirect(url_for('guess_photo',PhotoNo = random_photo()))

@app.route('/geoguess/guess/<int:PhotoNo>')
def guess_photo(PhotoNo):
    return render_template('guess.html', photo = PhotoNo, difference=-1)

@app.route('/geoguess/check/<int:PhotoNo>', methods =['POST', 'GET'])
def check_guess(PhotoNo):
    if request.method == 'POST':
		global totaldifference
		for photo in photolist:
			if PhotoNo == photo['PhotoNum']:
				latitude = photo['latitude']
				longitude = photo['longitude']
		Guessdifference=math.sqrt(pow(110.574*(float(request.form['latitude'])-latitude),2)+pow(111.32*math.cos(math.radians(latitude))*(float(request.form['longitude'])-longitude),2))*1000
		totaldifference += Guessdifference
		Guessdifference=float("%.3f" % Guessdifference)
		if selectionindex == []:
			return redirect(url_for('finished_round'))
		report(Guessdifference)
		return render_template('guess.html', photo = random_photo(), guess=0)
    else:
		return redirect(url_for('guess_photo',PhotoNo = random_photo()))
def random_photo():
	myChoice=random.choice(selectionindex)
	selectionindex.remove(myChoice)
	return photolist[myChoice]['PhotoNum']
	

@app.route('/geoguess/finish')
def finished_round():
	global totaldifference
	totaldifference=float("%.3f" % totaldifference)
	return render_template('finish.html', difference=totaldifference)	

def report(diff):
	message = "Your last guess was "+str(diff)+" m away from the actual location"
	flash(message)
	if diff >= 10000.1:
		message = "Woah! That is really far away! (-_-;)"
	elif diff >= 1000.1:
		message = "A bit far out, try again ('.')"
	elif diff >= 100.1:
		message = "Getting there, but try and get a bit closer ('u')"
	else:
		message = "That's really close, good job! \\(^o^)/"
	flash(message)


if __name__ == '__main__':
	app.run(debug=True)