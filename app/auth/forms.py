# -*- coding: utf-8 -*-

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from ..models import User


class LoginForm(FlaskForm):
    ''' 登录表单 '''
    email = StringField('邮箱', validators=[DataRequired(), Length(1, 64),
                                             Email()], id = '111')
    password = PasswordField('密码', validators=[DataRequired()])
    verify_code = StringField('验证码', validators=[DataRequired()])
    remember_me = BooleanField('保持登录')
    submit = SubmitField('确定')


class RegistrationForm(FlaskForm):
    ''' 注册表单 '''
    email = StringField('邮箱', validators = [DataRequired(), Length(1, 64),
                                              Email()])
    username = StringField('用户名',validators = [DataRequired(), Length(1, 64),
                            Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, 
                            'Usernames must have only letters, '
                            'numbers, dots or underscores')])
    password = PasswordField('密码', validators=[
                DataRequired(), EqualTo('password2', message='Password must match.')])
    password2 = PasswordField('确认密码', validators = [DataRequired()])
    submit = SubmitField('Register')
    
    def validate_email(self, field):
        ''' 验证邮箱 '''
        if User.query.filter_by(email = field.data).first():
            raise ValidationError('邮箱已被注册')
            
    def validate_username(self, field):
        ''' 验证用户名 '''
        if User.query.filter_by(username = field.data).first():
            raise ValidationError('用户名已存在')


class ChangePasswordForm(FlaskForm):
    ''' 修改密码表单 '''
    old_password = PasswordField('旧密码', validators=[DataRequired()])
    password = PasswordField('新密码', validators=[
                DataRequired(), EqualTo('password2', message='Password must match.')])
    password2 = PasswordField('确认新密码', validators = [DataRequired()])
    submit = SubmitField('确定')


class ChangeEmailForm(FlaskForm):
    ''' 修改邮箱表单 '''
    new_email = StringField('新邮箱', validators = [DataRequired(), Length(1, 64),
                                              Email()])
    password = PasswordField('密码', validators=[DataRequired()])
    submit = SubmitField('确定')
    
    def validate_new_email(self, field):
        if User.query.filter_by(email = field.data).first():
            raise ValidationError('邮箱已被注册')


class PasswordResetRequestForm(FlaskForm):
    ''' 重置密码请求表单 '''
    email = StringField('邮箱', validators=[DataRequired(), Length(1, 64),
                                            Email()])
    submit = SubmitField('确定')


class PasswordResetForm(FlaskForm):
    ''' 重置密码表单 '''
    email = StringField('邮箱', validators=[DataRequired(), Length(1, 64),
                                             Email()])
    password = PasswordField('新密码', validators=[
        DataRequired(), EqualTo('password2', message='Passwords must match')])
    password2 = PasswordField('确认密码', validators=[DataRequired()])
    submit = SubmitField('确定')