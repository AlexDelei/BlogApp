import functools
import pymysql
from flask import Blueprint
from flask import flash
from flask import render_template
from flask import redirect
from flask import g
from flask import request
from flask import session
from flask import url_for
from flask import Flask
from werkzeug.security import check_password_hash, generate_password_hash
from Flask_blog.db import get_db
from Flask_blog.db_connection import exec_query

"""
A view function is the code you write to respond to requests to your application
The view returns data that Flask turns into an outgoing response

A Blueprint is a way to organize a group of related views and other code.
"""
bp = Blueprint('auth', __name__, url_prefix='/auth')
db = pymysql.connect(host='localhost', user='root', password='', database='Flask_Blog_app')

@bp.before_app_request
def load_logged_in_user():
    """
    @bp.before_app_request registers a funtion that runs before the view function no matter
    what URL is requested.
    load_logged_in_user checks if a user is stored in the session and gets the data from the database
    storing it on g.user which lasts for the length of the request
    """
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        try:
            with db.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
                g.user = cursor.fetchone()

                db.commit()
        except pymysql.Error as e:
            print(f"{user_id}Error from retrieving user info: {e}")
        

def login_required(view):
    """
    This decorator returns a new view function that wraps the original
    view it's applied to.It checks if a user is loaded and redirects to the login
    page otherwise
    """
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if not g.user:
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    return wrapped_view

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """Saves user's username and pass in our sqlite db file"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        

        if not username:
            error = 'Username required'
        elif not password:
            error = 'Password required'

        hashed_pwd = generate_password_hash(password, method='pbkdf2:sha256')
        session['hashed_pwd'] = hashed_pwd
        try:
            exec_query(
                "INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_pwd),
            )
        except pymysql.IntegrityError:
            error = f"User {username} is already registered."
        else:
            return redirect(url_for('auth.login'))
            
        flash(error) # flash stores messages that can be retrieved when rendering the template
    return render_template('auth/register.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        error = None
        
        user = exec_query('SELECT * FROM users WHERE username = %s', (username,))# returns one row from the query
        hashed_pwd = session.get('hashed_pwd')

        if user is None:
            error = 'Incorrect username.'
        elif  not check_password_hash(user[0][2], password):
            error = 'Incorrect password.'
        id_ = int(user[0][0])

        if error is None:
            session.clear()
            session['user_id'] = id_
            return redirect(url_for('index'))
        
        flash(error)
    return render_template('auth/login.html')

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))