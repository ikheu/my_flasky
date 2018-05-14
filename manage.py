# -*- coding: utf-8 -*-

import os


# 覆盖测试
COV = None
if os.environ.get('FLASK_COVERAGE'):
    import coverage
    COV = coverage.coverage(branch=True, include='app/*')
    COV.start()


from app import create_app, db
from app.models import User, Role, Permission, Post, Follow
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand


app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    ''' 加入命令行 '''
    return dict(app=app, db=db, User=User, Follow = Follow, Role=Role,
                Permission=Permission, Post=Post)


manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@manager.command
def test(coverage = False):
    ''' 运行单元测试 '''
    if coverage and not os.environ.get('FLASK_COVERAGE'):
        import sys
        os.environ['FLASK_COVERAGE'] = '1'
        os.execvp(sys.executable, [sys.executable] + sys.argv)
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)
    if COV:
        COV.stop()
        COV.save()
        print('Coverage Summary:')
        COV.report()
        basedir = os.path.abspath(os.path.dirname(__file__))
        covdir = os.path.join(basedir, 'tmp/conerage')
        COV.html_report(directory=covdir)
        print('HTML version: file://%s/index.html' % covdir)
        COV.erase()


@manager.command
def profile(length=25, profile_dir=None):
    ''' 性能分析 '''
    from werkzeug.contrib.profiler import ProfilerMiddleware
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[length],
                                      profile_dir=profile_dir)
    app.run()


@manager.command
def deploy():
    ''' 命令部署 '''
    from flask_migrate import upgrade
    from app.models import Role, User
    upgrade()
    Role.insert_roles()
    User.add_self_follows()


@manager.command
def reset_data():
    ''' 重载数据 '''
    from app.models import Role, User, Post
    from app import db
    db.drop_all()
    db.create_all()
    Role.insert_roles()
    User.add_self_follows()
    User.generate_fake(10)
    Post.generate_fake(10)


@manager.command
def test_zh():
    ''' 中文测试 '''
    from app.models import User
    from app import db
    u = User(username = '我')
    db.session.add(u)
    db.session.commit()
    
if __name__ == '__main__':
    manager.run()