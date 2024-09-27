import functools

from flask import (Blueprint, flash, g, redirect, render_template, request,
                   session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

from app.db import get_db

bp = Blueprint('auth',__name__,url_prefix='/auth')

#注册
@bp.route('/register',methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        #获取数据库
        db = get_db()
        error = None

        if not username:
            error = '请输入用户名'
        elif not password:
            error = '请输入密码'    
        if error is None:
            try:
                db.execute(
                    "insert into user (username,password) values (?,?)",
                    (username,generate_password_hash(password=password))
                )
                db.commit()
            except db.IntegrityError:
                error = f'用户 {username} 已存在'    
            else:
                return redirect(url_for("auth.login"))
        flash(error)                    
    return render_template('auth/register.html')

#登录
@bp.route('/login',methods=('GET','POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        print(f"username:{username}")
        user = db.execute(
            'select * from user where username = ?',
            (username,)
        ).fetchone()

        if user is None:
            error = '用户名错误'
        elif not check_password_hash(user['password'],password=password):
            error = '密码错误'    
        
        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('index'))
        
        flash(error)
    return render_template('auth/login.html')

#前置拦截
@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'select * from user where id = ?',
            (user_id)
        ).fetchone()

#退出
@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))        

def login_required(view):
    @functools.wraps(view)
    def weapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    return weapped_view