from sqlalchemy import Column, Integer, String, ForeignKey, Float, Table
from sqlalchemy.orm import relationship, mapper
from database import Base

class User(Base):
    __tablename__ = 'users'
    #Represents the list of users in the database. Users have an ID, username, and password    
    username = Column(String(80), primary_key = True)
    password = Column(String(20))    
	
    #IDs are generated automatically. When a user is declared, only the username and password needs to be set
    def __init__(self, username, password):        
        self.username = username
        self.password = password
		
    def __repr__(self):
        return '<User %r>' % self.username
        
    
    def get_id(self):
        return str(self.username).decode("utf-8")
		
class Score(Base):
	__tablename__ = 'scores'
    #Represents the high scores list in the database. Scores have a many to one relationship with Users
	id = Column(Integer, primary_key = True)
	user_id = Column(Integer, ForeignKey('users.username'))
	user = relationship('User', backref='scores')
	score = Column(Float)
	category = Column(Integer)
	rank = Column(Integer)
    
	def __init__(self, user_id, score, category):
		self.user_id = user_id
		self.score = score
		self.category = category
	
	def __repr__(self):
		return '<Score %r>' % self.score

