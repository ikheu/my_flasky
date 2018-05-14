# -*- coding: utf-8 -*-

from flask_login import login_required, current_user
from flask_sqlalchemy import get_debug_queries
from flask import flash, redirect, render_template, url_for , \
        request, current_app, abort, make_response
from . import main
from .forms import EditProfileForm, EditProfileAdminForm, PostForm, CommentForm, \
        ChangeAvatar, EditorForm
from .. models import User, Role, Post, Permission, Comment
from .. import db
from ..decorators import admin_required, permission_required


@main.route('/', methods=['GET', 'POST'])
def index():
    ''' 主页 '''
    form = PostForm()
    if current_user.can(Permission.WRITE_ARTICLES) and \
            form.validate_on_submit():
        post = Post(body=form.body.data,
                    author=current_user._get_current_object())
        db.session.add(post)
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    show_followed = False
    if current_user.is_authenticated:
        show_followed = bool(request.cookies.get('show_followed', ''))
    if show_followed:
        query = current_user.followed_posts
    else:
        query = Post.query
    pagination = query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    return render_template('index.html', form=form, posts=posts,
                           show_followed=show_followed, pagination=pagination)


@main.route('/all')
@login_required
def show_all():
    ''' 显示所有用户的文章 '''
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '', max_age=30*24*60*60)
    return resp


@main.route('/followed')
@login_required
def show_followed():
    ''' 显示关注的用户文章 '''
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '1', max_age=30*24*60*60)
    return resp


@main.route('/user/<username>')
def user(username):
    ''' 个人界面 '''
    user = User.query.filter_by(username=username).first_or_404()
    show_tags = {'edit', 'delete', 'content'}
    page = request.args.get('page', 1, type=int)
    pagination = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    # print(os.access('app' + user.real_avatar, os.F_OK))
    return render_template('user.html', user=user, posts=posts,
                           show_tags = show_tags,
                           pagination=pagination)


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    ''' 编辑资料界面 '''
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash('Your profile has been updated.')
        return redirect(url_for('.user', username = current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)


@main.route('/change-avatar', methods=['GET', 'POST'])
@login_required
def change_avatar():
    '''修改头像'''
    form = ChangeAvatar()
    if form.validate_on_submit():
        #文件对象
        avatar = request.files['avatar']
        fname = avatar.filename     
        #存储路径 
        upload_folder = current_app.config['UPLOAD_FOLDER']      
        #允许格式
        allowed_extensions = ['png', 'jpg', 'jpeg', 'gif']      
        #后缀名
        fext = fname.rsplit('.',1)[-1] if '.' in fname else ''
        #判断是否符合要求
        if fext not in allowed_extensions:   
            flash('File error.')
            return redirect(url_for('.user', username=current_user.username))
        # 路径+用户名+后缀名
        target = '{}{}.{}'.format(upload_folder, current_user.username, fext)
        avatar.save(target)
        current_user.real_avatar = '/static/avatars/{}.{}'.format(current_user.username, fext)
        db.session.add(current_user)
        flash('Your avatar has been updated.')
        return redirect(url_for('.user', username = current_user.username))
    return render_template('change_avatar.html', form=form)


@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    ''' 修改资料页面 '''
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        flash('The profile has been updated.')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user)


@main.route('/post/<int:id>', methods=['GET', 'POST'])
def post(id):
    ''' 文章 '''
    post = Post.query.get_or_404(id)
    form = CommentForm()
    show_tags = {'edit', 'delete', 'content'}
    if form.validate_on_submit():
        comment = Comment(body=form.body.data,
                          post=post,
                          author=current_user._get_current_object())
        db.session.add(comment)
        flash('Your comment has been published.')
        return redirect(url_for('.post', id=post.id, page=-1))
    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (post.comments.count() - 1) // \
                current_app.config['FLASKY_COMMENTS_PER_PAGE'] + 1
    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    target = 'post.html'if post.body else 'aiticle.html'
    return render_template(target, posts=[post], form=form,
                           comments=comments, pagination=pagination,
                           show_tags = show_tags)


@main.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    ''' 编辑文章 '''
    post = Post.query.get_or_404(id)
    if post.author != current_user and \
        not current_user.can(Permission.ADMINISTER):
            abort(403)
    if post.body:
        form = PostForm()
        if form.validate_on_submit():
            post.body = form.body.data
            db.session.add(post)
            flash('The post has been updated.')
            return redirect(url_for('.post', id=post.id))
        form.body.data = post.body
        return render_template('edit_post.html', form=form)
    else:
        form = EditorForm()
        if request.method == 'POST':
            if not form.editor.data:
                flash('请输入正文')
                return render_template('editor.html', form=form)
            post.body_html = request.form['editor']
            post.title = request.form['title']
            db.session.add(post)
            return redirect(url_for('.post', id=post.id))
        form.editor.data = post.body_html
        form.title.data = post.title
        return render_template('editor.html', form=form)


@main.route('/editor', methods=['GET', 'POST'])
@login_required
def editor():
    ''' 编辑器界面 '''
    form = EditorForm()
    if request.method == 'POST':
        if not form.editor.data:
            flash('Write something.')
            return render_template('editor.html', form=form)
        if current_user.can(Permission.WRITE_ARTICLES):
            print(request.form)
            post = Post(title=request.form['title'],
                        body_html=request.form['editor'],
                        author=current_user._get_current_object())
            db.session.add(post)
            db.session.commit()
            return redirect(url_for('.post', id=post.id))
    return render_template('editor.html', form = form)


@main.route('/delete/<int:id>')
@login_required
def delete(id):
    ''' 删除文章 '''
    post = Post.query.get_or_404(id)
    if post.author != current_user and \
        not current_user.can(Permission.ADMINISTER):
            abort(403)
    db.session.delete(post)
    flash('博文已删除')
    return redirect(url_for('.user', username=current_user.username))


@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    ''' 关注 '''
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    if current_user.is_following(user):
        flash('You are already following this user.')
        return redirect(url_for('.user', username=username))
    current_user.follow(user)
    flash('You are now following %s.' % username)
    return redirect(url_for('.user', username=username))


@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    ''' 取关 '''
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    if not current_user.is_following(user):
        flash('You are not following this user.')
        return redirect(url_for('.user', username=username))
    current_user.unfollow(user)
    flash('You are not following %s anymore.' % username)
    return redirect(url_for('.user', username=username))


@main.route('/followers/<username>')
def followers(username):
    """ 关注者 """
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followers.paginate(
        page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.follower, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title="Followers of",
                           endpoint='.followers', pagination=pagination,
                           follows=follows)


@main.route('/followed-by/<username>')
def followed_by(username):
    """ 粉丝 """
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followed.paginate(
        page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.followed, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title="Followed by",
                           endpoint='.followed_by', pagination=pagination,
                           follows=follows)


@main.route('/moderate')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate():
    """ 评论 """
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
            page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
            error_out=False)
    comments = pagination.items
    return render_template('moderate.html', comments=comments,
                           pagination=pagination, page=page)


@main.route('/moderate/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_enable(id):
    """ 评论有效 """
    comment = Comment.query.get_or_404(id)
    comment.disabled = False
    db.session.add(comment)
    return redirect(url_for('.moderate',
                            page=request.args.get('page', 1, type=int)))


@main.route('/moderate/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_disable(id):
    """ 评论无效 """
    comment = Comment.query.get_or_404(id)
    comment.disabled = True
    db.session.add(comment)
    return redirect(url_for('.moderate',
                            page=request.args.get('page', 1, type=int)))


@main.route('/shutdown')
def server_shutdown():
    """ 测试完成后关闭服务 """
    if not current_app.testing:
        abort(404)
    shutdown = request.environ.get('werkzeug.server.shutdown')
    if not shutdown:
        abort(500)
    shutdown()
    return 'Shutting down...'


@main.after_app_request
def after_request(response):
    """ 记录查询缓慢的信息 """
    for query in get_debug_queries():
        if query.duration >= current_app.config['FLASKY_SLOW_DB_QUERY_TIME']:
            current_app.logger.warnning(
                'Slow query: %s\nParameters: %s\nDuration: %fs\nContext: %s\n'
                % (query.statement, query.parameters, query.duration,
                   query.context))
    return response
