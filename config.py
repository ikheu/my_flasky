import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECURET_KEY') or 'hard to guess string'
    SQLALCHEMY_COMMIT_ON_TEARDOWN  = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FLASKY_MAIL_SUBJECT_PREFIX = '[Flasky]'
    #'Flasky Admin <flasky@example.com>'
    FLASKY_MAIL_SENDER = 'wbcsddc@126.com'
    #os.environ.get('FLASK_ADMIN')
    FLASKY_ADMIN = '1311242552@qq.com'
    
    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True
    MAIL_SERVER = 'smtp.126.com'
    MAIL_PORT = 25
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    #os.environ.get('MAIL_USERNAME')
    MAIL_USERNAME = 'wbcsddc@126.com'
    #os.environ.get('MAIL_PASSWORD')
    MAIL_PASSWORD = 'what7078384'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')
    
class TestingConfig(Config):
    TESTING  =True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')
    
class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
    'sqlite:///' + os.path.join(basedir, 'data.sqlite')
        
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    
    'default': DevelopmentConfig
}
    
    
    
    
    
    
    
