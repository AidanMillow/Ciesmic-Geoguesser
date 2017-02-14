
class Config(object):
    DEBUG = False
    TESTING = False    
    FLASK_HTPASSWD_PATH = '/secret/.htpasswd'
    SECRET_KEY = "something-something-something-dark-side"
    FLASK_SECRET = SECRET_KEY    
    DB_HOST = 'database' # a docker link


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = True    
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/test.db'
    SERVER_NAME = '127.0.0.1:5000'
