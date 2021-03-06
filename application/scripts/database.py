import os
from flask_sqlalchemy import SQLAlchemy
from flask_table import Table, Col
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base


working_dir = os.getcwd()
engine = create_engine('sqlite:///' + working_dir + '/application/scripts/database/geoguesser.db', convert_unicode=True)
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

def init_db():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    import model
    Base.metadata.create_all(bind=engine)
    
                                         
                                         
                                         