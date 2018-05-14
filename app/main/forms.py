# -*- coding: utf-8 -*-

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, SelectField, \
                    TextAreaField, FileField
from wtforms.validators import Length, Email, Regexp, DataRequired
from ..models import Role, User
from wtforms import ValidationError
from flask_pagedown.fields import PageDownField


class EditProfileForm(FlaskForm):
    name = StringField('昵称', validators=[Length(0, 64)])
    location = StringField('地区', validators=[Length(0, 64)])
    about_me = StringField('签名')
    submit = SubmitField('确定')


class EditorForm(FlaskForm):
    title = StringField('标题', validators=[DataRequired(),  Length(1, 64)])
    editor = TextAreaField('正文', id = 'content')
    submit = SubmitField('发表')

    def validate_editor(self, field):
        if not field.data:
            raise ValidationError('邮箱已被注册')


class ChangeAvatar(FlaskForm):
    avatar = FileField('', validators=[DataRequired()])
    submit = SubmitField('确定')


class EditProfileAdminForm(FlaskForm):
    email = StringField('邮箱', validators=[DataRequired(), Length(1, 64),
                                             Email()])
    username = StringField('用户名', validators=[
        DataRequired(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                          'Usernames must have only letters, '
                                          'numbers, dots or underscores')])
    confirmed = BooleanField('验证')
    role = SelectField('角色', coerce=int)
    name = StringField('昵称', validators=[Length(0, 64)])
    location = StringField('地区', validators=[Length(0, 64)])
    about_me = TextAreaField('签名')
    submit = SubmitField('确定')
    
    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name)
                             for role in Role.query.order_by(Role.name).all()]
        self.user = user
        
    def validate_email(self, field):
        if field.data != self.user.email and \
                User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')
            
    def validate_username(self, field):
        if field.data != self.user.username and \
                User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')


class PostForm(FlaskForm):
    body = PageDownField("随想", validators=[DataRequired()])
    submit = SubmitField('发表')


class CommentForm(FlaskForm):
    body = StringField('评论', validators=[DataRequired()])
    submit = SubmitField('确定')
