from flask_sqlalchemy import SQLAlchemy
from flask_table import Table, Col

db = SQLAlchemy()
    
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
	category = db.Column(db.Integer)
	
	def __init__(self, user_id, score, category):
		self.user_id = user_id
		self.score = score
		self.category = category
	
	def __repr__(self):
		return '<Score %r>' % self.score

		
class HighScores(Table):
	#This class represents the HTML table that will be built on the final page of the application    
    __tablename__ = "HighScores"
    user = Col('User')
    score = Col('Score')