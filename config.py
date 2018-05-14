# -*- coding: utf-8 -*-

import os
# 根目录
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    ''' 配置 '''
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'  # 密匙
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True                                 # 自动提交
    SQLALCHEMY_TRACK_MODIFICATIONS = False                               # 追踪修改
    MAIL_SERVER = 'smtp.126.com'                                         # 邮件服务器
    MAIL_PORT = 25                                                       # 端口号
    MAIL_USE_TLS = True                                                  # TLS设置
    MAIL_USE_SSL = False                                                 # SSL设置
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'wbcsddc@126.com' # 邮箱用户名
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'what7078384'     # 密码
    FLASKY_MAIL_SUBJECT_PREFIX = '[Flasky]'                              # 邮件主题
    FLASKY_MAIL_SENDER = 'wbcsddc@126.com'                               # 发件箱
    FLASKY_ADMIN = os.environ.get('FLASKY_ADMIN') or '1311242552@qq.com' # 管理员邮箱
    FLASKY_POSTS_PER_PAGE = 20                                           # 每页文章数
    FLASKY_FOLLOWERS_PER_PAGE = 50                                       # 每页关注数
    FLASKY_COMMENTS_PER_PAGE = 20                                        # 每页评论数
    SQLALCHEMY_RECORD_QUERIES = True                                     # 禁用查询记录
    FLASKY_SLOW_DB_QUERY_TIME = 0.5                                      # 查询缓慢阈值设置
    UPLOAD_FOLDER = os.getcwd() + '/app/static/avatars/'                 # 头像目录
    
    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    ''' 开发模式 '''
    DEBUG = True
    #SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
    #   'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
       'mysql+mysqlconnector://root:admin@localhost/mydata'

class TestingConfig(Config):
    ''' 测试模式 '''
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite://'
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    ''' 生产模式 '''
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data.sqlite')
    
    @classmethod
    def init_app(cls, app):
        ''' 日志处理程序 '''
        Config.init_app(app)
        import logging
        from logging.handlers import SMTPHandler
        credentials = None
        secure = None
        if getattr(cls, 'MAIL_USERNAME', None) is not None:
            credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
            if getattr(cls, 'MAIL_USE_TLS', None):
                secure= ()
        mail_handler = SMTPHandler(
            mailhost = (cls.MAIL_SERVER, cls.MAIL_PORT),
            fromaddr = cls.FLASKY_MAIL_SENDER,
            toaddrs = [cls.FLASKY_ADMIN],
            subject = cls.FLASKY_MAIL_SUBJECT_PREFIX + ' Application Error',
            credentials = credentials,
            secure = secure)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)
        
        
# 配置字典
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,

    'default': DevelopmentConfig
}
