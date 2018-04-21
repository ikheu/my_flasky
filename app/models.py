import bleach
import hashlib
from datetime import datetime
from markdown import markdown
from . import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app, request, url_for
from flask_login import UserMixin, AnonymousUserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from app.exceptions import ValidationError

class Permission:
    '''权限'''
    FOLLOW = 0x01             # 关注
    COMMENT = 0x02            # 评论
    WRITE_ARTICLES = 0x04     # 写博客
    MODERATE_COMMENTS = 0x08  # 管理评论
    ADMINISTER = 0x80         # 管理员权限

class Role(db.Model):
    '''角色'''
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)                        # id号
    name = db.Column(db.String(64), unique=True)                        # 名字
    default = db.Column(db.Boolean, default = False, index = True)      # 默认权限
    permissions = db.Column(db.Integer)                                 # 权限
    users = db.relationship('User', backref='role', lazy='dynamic')     # 用户
    
    def __repr__(self):
        return '<Role %r>' % self.name
    
    @staticmethod
    def insert_roles():
        '''插入角色'''
        roles = {
            'User': (Permission.FOLLOW |
                     Permission.COMMENT |
                     Permission.WRITE_ARTICLES, True),
            'Moderator': (Permission.FOLLOW |
                          Permission.COMMENT |
                          Permission.WRITE_ARTICLES |
                          Permission.MODERATE_COMMENTS, False),
            'Administrator': (0xff, False)
        }
        
        for r in roles:
            role = Role.query.filter_by(name = r).first()
            if role is None:
                role = Role(name = r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()


class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'),   # 关注者id
                            primary_key = True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'),   # 被关注者id
                            primary_key = True)
    timestamp = db.Column(db.DateTime, default = datetime.utcnow)    # 时间       

        
class User(UserMixin, db.Model):
    '''用户'''
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)                     # 姓名
    email = db.Column(db.String(64), unique=True, index=True)        # 邮箱
    username = db.Column(db.String(64), unique=True, index=True)     # 用户名
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))       # 角色id
    password_hash = db.Column(db.String(128))                        # 密码hash
    confirmed = db.Column(db.Boolean, default=False)                 # 验证信息
    name = db.Column(db.String(64))                                  # 姓名
    location = db.Column(db.String(64))                              # 地区
    about_me = db.Column(db.Text())                                  # 简介
    member_since = db.Column(db.DateTime(), default=datetime.utcnow) # 注册时间
    last_seen = db.Column(db.DateTime(), default = datetime.utcnow)  # 上次登陆时间
    avatar_hash = db.Column(db.String(32))                           # 头像hash
    posts = db.relationship('Post', backref='author', lazy='dynamic')# 博文
    followed = db.relationship('Follow',                             # 关注
                               foreign_keys=[Follow.follower_id],
                               backref=db.backref('follower', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')
    followers = db.relationship('Follow',                            # 粉丝
                               foreign_keys=[Follow.followed_id],
                               backref=db.backref('followed', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='author', lazy='dynamic') #评论
    real_avatar = db.Column(db.String(128), default = None)
    
    
    def follow(self, user):
        '''关注操作'''
        if not self.is_following(user):
            f = Follow(follower=self, followed=user)
            db.session.add(f)
        
    def unfollow(self, user):
        '''取关操作'''
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)
            
    def is_following(self, user):
        '''关注了吗'''
        return self.followed.filter_by(followed_id=user.id).first() is not None
    
    def is_followed_by(self, user):
        '''被粉了吗'''
        return self.followers.filter_by(follower_id=user.id).first() is not None
    
    @property
    def followed_posts(self):
        return Post.query.join(Follow, Follow.followed_id==Post.author_id)\
                .filter(Follow.follower_id==self.id)
                
    @staticmethod
    def add_self_follows():
        for user in User.query.all():
            if not user.is_following(user):
                user.follow(user)
                db.session.add(user)
                db.session.commit()
        
            
    
    @staticmethod
    def generate_fake(count=100):
        '''虚拟用户'''
        from sqlalchemy.exc import IntegrityError
        from random import seed
        import forgery_py
        seed()
        for i in range(count):
            username_tmp = forgery_py.internet.user_name(True)
            email_tmp =  forgery_py.internet.email_address()
            password_tmp = forgery_py.lorem_ipsum.word()
            print(username_tmp, email_tmp, password_tmp)
            u = User(email=email_tmp,
                     username=username_tmp,
                     password=password_tmp,
                     confirmed=True,
                     name=forgery_py.name.full_name(),
                     location=forgery_py.address.city(),
                     about_me=forgery_py.lorem_ipsum.sentence(),
                     member_since=forgery_py.date.date(True))
            db.session.add(u)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
    
    def __init__(self, **kw):
        super().__init__(**kw)
        if self.role is None:
            if self.email == current_app.config['FLASKY_ADMIN']:
                self.role = Role.query.filter_by(permissions = 0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
            if self.email is not None and self.avatar_hash is None:
                self.avatar_hash = hashlib.md5(
                        self.email.encode('utf-8')).hexdigest()
        self.followed.append(Follow(followed=self))
    
    @property
    def password(self):
        '''获取密码'''
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        '''设置密码'''
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        '''验证密码'''
        return check_password_hash(self.password_hash, password)
    
    def generate_confirmation_token(self, expiration = 3600):
        '''产生确认信息'''
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})
    
    def confirm(self, token):
        '''确认'''
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True
    
    def generate_change_email_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.id, 'new_email': new_email})
    
    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        self.avatar_hash = hashlib.md5(
            self.email.encode('utf-8')).hexdigest()
        db.session.add(self)
        return True
    
    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def reset_password(self, token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        return True
        

    def __repr__(self):
        return '<User %r>' % self.username
            
    def can(self, permissions):
        '''角色验证'''
        return self.role is not None and \
            (self.role.permissions & permissions) == permissions
        
    def is_administrator(self):
        '''管理员验证'''
        return self.can(Permission.ADMINISTER)
    
    def ping(self):
        '''时间信息'''
        self.last_seen = datetime.utcnow()
        db.session.add(self)
        
    def gravatar(self, size=100, default='identicon', rating='g'):
        '''用户头像'''
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        hash = self.avatar_hash or hashlib.md5(
            self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)
        
    def generate_auth_token(self, expiration):
        s = Serializer(current_app.config['SECRET_KEY'],
                       expires_in=expiration)
        return s.dumps({'id': self.id}).decode('ascii')
    
    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        return User.query.get(data['id'])
    
    def to_json(self):
        json_user = {
            'url': url_for('api.get_user',id=self.id,
                           _external=True),
            'username': self.username,
            'member_since': self.member_since,
            'last_seen': self.last_seen,
            'posts': url_for('api.get_user_posts', id=self.id, _external=True),
            'followed_posts': url_for('api.get_user_followed_posts',
                                      id=self.id, _external=True),
            'post_count': self.posts.count()
        }
        return json_user
        

class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False
    
    def is_administrator(self):
        return False


login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Post(db.Model):
    '''文章'''
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    comments = db.relationship('Comment', backref='post', lazy='dynamic')
    
    @staticmethod
    def generate_fake(count=100):
        from random import seed, randint
        import forgery_py

        seed()
        user_count = User.query.count()
        for i in range(count):
            u = User.query.offset(randint(0, user_count - 1)).first()
            p = Post(body=forgery_py.lorem_ipsum.sentences(randint(1, 5)),
                     timestamp=forgery_py.date.date(True),
                     author=u)
            db.session.add(p)
            db.session.commit()
            
    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p', 'code']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))
        
        
    def to_json(self):
        json_post = {
            'url': url_for('api.get_post', id=self.id, _external=True),
            'body': self.body,
            'body_html': self.body_html,
            'timestamp': self.timestamp,
            'author': url_for('api.get_user', id=self.author_id,
                              _external=True),
            'comments': url_for('api.get_post_comments', id=self.id,
                                _external=True),
            'comment_count': self.comments.count()
        }
        return json_post
    
    @staticmethod
    def from_json(json_post):
        body = json_post.get('body')
        if body is None or body == '':
            raise ValidationError('post does not have a body')
        return Post(body = body)
        
    
db.event.listen(Post.body, 'set', Post.on_changed_body)


class Comment(db.Model):
    '''评论'''
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    disabled = db.Column(db.Boolean)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
    
    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'code', 'em', 'i', 
                        'strong']
        target.body_html = bleach.linkify(bleach.clean(
                markdown(value, output_format='html'),
                tags=allowed_tags, strip=True))
        
    def to_json(self):
        json_comment = {
            'url': url_for('api.get_comment', id=self.id, _external=True),
            'post': url_for('api.get_post', id=self.post_id, _external=True),
            'body': self.body,
            'body_html': self.body_html,
            'timestamp': self.timestamp,
            'author': url_for('api.get_user', id=self.author_id,
                              _external=True),
        }
        return json_comment

    @staticmethod
    def from_json(json_comment):
        body = json_comment.get('body')
        if body is None or body == '':
            raise ValidationError('comment does not have a body')
        return Comment(body=body)

db.event.listen(Comment.body, 'set', Comment.on_changed_body)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    