# -*- coding: utf-8 -*-

from io import BytesIO
from flask import render_template, redirect, request, url_for, flash, \
        session, make_response
from flask_login import login_user, logout_user, login_required, \
        current_user
from . import auth
from . get_verify_code import get_verify_code
from .forms import LoginForm, RegistrationForm, ChangePasswordForm, \
        ChangeEmailForm, PasswordResetRequestForm, PasswordResetForm
from ..email import send_email
from .. import db
from ..models import User




@auth.before_app_request
def before_request():
    ''' 钩子函数, auth 蓝本下每次请求前运行 '''
    if current_user.is_authenticated:
        current_user.ping()
        if not current_user.confirmed \
                        and request.endpoint \
                        and request.endpoint[:5] != 'auth.' \
                        and request.endpoint != 'static':
                return redirect(url_for('auth.unconfirmed'))
        
        
@auth.route('/unconfirmed')
def unconfirmed():
    ''' 未验证 '''
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    ''' 登录 '''
    # 这里使用了 flask-login 提供的方法, 实际上登录登出功能可通过 session 机制实现
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if session.get('image') != form.verify_code.data:
            flash('Wrong verify code.')
            return render_template('auth/login.html', form=form)
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('Invalid username or password.')
    return render_template('auth/login.html', form=form)


@auth.route('/code')
def get_code():
    ''' 获得登录验证码 '''
    image, code = get_verify_code()
    # 将验证码图片以二进制形式写入在内存中，防止将图片都放在文件夹中，占用大量磁盘
    buf = BytesIO()
    image.save(buf, 'jpeg')
    buf_str = buf.getvalue()
    # 把二进制作为response发回前端，并设置首部字段
    response = make_response(buf_str)
    response.headers['Content-Type'] = 'image/gif'
    # 将验证码字符串储存在session中
    session['image'] = code
    return response


@auth.route('/logout')
@login_required
def logout():
    ''' 登出 '''
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.index'))

    
@auth.route('/register', methods=['GET', 'POST'])
def register():
    ''' 注册 '''
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    username=form.username.data,
                    password=form.password.data)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_email(user.email, 'Confirm Your Account',
                   'auth/email/confirm', user = user, token = token)
        flash('A confirmation email has been sent to you by email.')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form = form)

    
@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    ''' 验证 '''
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        flash('You have confirmed your account. Thanks!')
    else:
        flash('The confirmation link is invalid or has expired.')
    return redirect(url_for('main.index'))
    

@auth.route('/confirm')
@login_required
def resend_confirmation():
    ''' 重新验证 '''
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, 'Confirm Your Account',
                'auth/email/confirm', user = current_user, token = token)
    flash('A new confirmation email has been sent to you by email.')
    return redirect(url_for('main.index'))


@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    ''' 修改密码 '''
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.password.data
            db.session.add(current_user)
            flash('Your password has been updated.')
            return redirect(url_for('main.index'))
        flash('Invalid old password.')
    return render_template('auth/change_password.html', form = form)


@auth.route('/change-email', methods=['GET', 'POST'])
@login_required
def change_email_request():
    ''' 修改邮箱请求 '''
    form = ChangeEmailForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.password.data):
            new_email = form.new_email.data
            token = current_user.generate_change_email_token(new_email)
            send_email(form.new_email.data, 'Confirm Your New Email Address',
                   'auth/email/change_email', user = current_user, token = token)
            flash('A confirmation email has been sent to your new email.')
            return redirect(url_for('main.index'))
        flash('Invalid email or password.')
    form.new_email.data = current_user.email
    return render_template('auth/change_email.html', form=form)


@auth.route('/change-email/<token>')
@login_required
def change_email(token):
    ''' 修改邮箱 '''
    if current_user.change_email(token):
        flash('Your email address has been updated.')
    else:
        flash('Invalid request.')
    return redirect(url_for('main.index'))


@auth.route('/reset', methods=['GET', 'POST'])
def password_reset_request():
    ''' 重置密码请求 '''
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.generate_reset_token()
            send_email(user.email, 'Reset Your Password',
                       'auth/email/reset_password',
                       user=user, token=token,
                       next=request.args.get('next'))
        flash('An email with instructions to reset your password has been '
              'sent to you.')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)


@auth.route('/reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
    ''' 重置密码 '''
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = PasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            return redirect(url_for('main.index'))
        if user.reset_password(token, form.password.data):
            flash('Your password has been updated.')
            return redirect(url_for('auth.login'))
        else:
            return redirect(url_for('main.index'))
    return render_template('auth/reset_password.html', form=form)
