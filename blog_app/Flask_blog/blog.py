import pymysql
import base64
import uuid
from flask import Blueprint
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask import g
from flask import session
from werkzeug.exceptions import abort
from Flask_blog.auth import login_required
from Flask_blog.db import get_db
from Flask_blog.db_connection import exec_query
from flask_wtf import FlaskForm
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from secrets import token_urlsafe

bp = Blueprint('blog', __name__)

class UplaodForm(FlaskForm):
    """
    defining a flask form for file upload
    """
    file = FileField(validators=[FileRequired()])


mysql = pymysql.connect(host='localhost', user='root', password='', database = 'Flask_Blog_app')

@bp.route('/')
def index():
    posts = exec_query(
        'SELECT p.id, title, body, created_at, author_id, username, image_upload, likes '
        'FROM post p JOIN users u ON p.author_id = u.id '
        'ORDER BY created_at DESC'
    )
    return render_template('blog/index.html', posts = posts)

@bp.route('/create', methods=['POST', 'GET'])
@login_required
def create():
    if request.method == 'GET':
        form = UplaodForm()
        return render_template('blog/create.html', form = form)
    
    if request.method == 'POST':
        form = UplaodForm(request.form)

        file = request.files['file']
        image_data = file.read()
        
        title = request.form['title']
        body = request.form['body']
               

        error = None

        if not title:
            error = 'Title is required.'
        if error is not None:
            flash(error)
        else:
            try:    
                exec_query('INSERT INTO post (title, body, author_id, image_upload) VALUES (%s, %s, %s, %s)', (title, body, g.user[0], image_data))
            except pymysql.Error as e:
                print(f"An error occurred while trying to save data for id {g.user[0][0]}: {e}")
            else:
                return redirect(url_for('blog.index'))

def get_post(id, check_author = True):
    """
    both update and delete views will need to fecth a 'post' by 'id'
    and check if the author matches the logged in user. To avoid duplicating
    code , this function fetches the entities and is called in each view.

    abort()  -> will raise a special exception that returns a HTTP status code.
    it accepts an optional message to show with error, otherwise a default message
    used. 404 means NOT FOUND , 403 means FORBIDDEN, 401 means UNAUTHORIZED
    """
    post = exec_query(
        'SELECT p.id, title, body, created_at, author_id, username, image_upload, likes '
        'FROM post p JOIN users u ON p.author_id = u.id '
        'WHERE p.id = %s', (id,)
    )

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")


    return post

@bp.route('/<int:id>/update', methods=['GET', 'POST'])
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required'

        if error is not None:
            flash(error)

        else:
            exec_query(
                'UPDATE post SET title = %s, body = %s'
                'WHERE id = %s', (title, body, id)
            )
            return redirect(url_for('blog.index'))
    return render_template('blog/update.html', post = post)

@bp.route('/<int:id>/single')
@login_required
def single_post(id):
    post = get_post(id)
    """Comments section"""

    comments = exec_query(
        'SELECT c.body, u.username, c.comment_time, c.id, c.author, c.post_id '
        'FROM comments c '
        'JOIN users u ON c.author = u.id '
        'WHERE c.post_id = %s', (id,))


    result = exec_query(
        'SELECT u.username, r.reply_text, comm_pst '
        'FROM replies r '
        'JOIN users u ON r.comm_usr = u.id '
    )
    both = exec_query(
        'SELECT comments.body, replies.reply_text '
        'FROM comments '
        'JOIN replies ON comments.post_id = replies.comm_pst '
        'WHERE comments.post_id = %s', (id,)
    )
    no_replies_but_commented = exec_query(
        'SELECT comments.body, replies.reply_text '
        'FROM comments '
        'LEFT JOIN replies ON replies.comm_pst = comments.post_id '
        'WHERE  comments.post_id = %s'
        , (id,)
        
    )
       
    zipped = zip(comments, result)

    len_ = len(comments)
    len_2 = len(result)
    return render_template('blog/post.html', post = post, zipped = zipped , len_ = len_, len_2 = len_2)


@bp.route('/<int:id>/single/unreplied/')
@login_required
def unreplied_comments(id):
    post = get_post(id)

    comments = exec_query(
        'SELECT c.body, u.username, c.comment_time, c.id, c.author, c.post_id '
        'FROM comments c '
        'JOIN users u ON c.author = u.id '
        'WHERE c.post_id = %s', (id,))
    
    if  not comments:
        return render_template('blog/unreplied.html', error = 'No comments in here😉', post = post)
    else:
        result = exec_query(
                'SELECT u.username, r.reply_text, comm_pst '
                'FROM replies r '
                'JOIN users u ON r.comm_usr = u.id '
                'WHERE r.comm_pst = %s', (comments[0][5],)
            )
    

    return render_template('blog/unreplied.html', post=post, comments = comments, result = result)

@bp.route('/<int:id>/comment', methods=['POST'])
@login_required
def comment_post(id):
    """
    Comments a post and saves the comment to the database
    under comments table
    """
    #form = UplaodForm(request.form)
    #files = request.files['file']
    
    text = request.form['body']

    try:
        with mysql.cursor() as cursor:
            author = g.user[0]
            post_id = id

            result = cursor.execute("INSERT INTO comments (post_id, author, body) VALUES (%s, %s, %s)", (post_id, author, text))

            mysql.commit()
            if result > 0:
                flash('Comments posted successfully')
            else:
                flash('Failed to post comment')

            return redirect(url_for('blog.index'))
    except pymysql.Error as e:
        print(f"An error occured tring to insert vales: {e}")
    
@bp.route('/<int:id>/<int:author>/reply_comment', methods=['POST'])
@login_required
def reply_comment(id, author):
    """
    Takes user reply through a textarea and stores it in the table comments.
    For now its only storing  replies
    """
    reply = request.form['reply']
    token = uuid.uuid4()

    if not reply:
        flash("Your reply can't be empty")
    
    try:
        if id:
            with mysql.cursor() as cursor:
                result = cursor.execute("INSERT INTO replies (comm_usr, comm_pst, reply_text) VALUES (%s, %s, %s)", (author, id, reply))
                mysql.commit()
                if result :
                    flash("Reply sent")
                    return redirect(url_for('blog.single_post', id=id, author=author, t=token))
            
    except pymysql.Error as a:
        print(f"An error occured while trying to save a comment reply:{a}")
    return redirect(url_for('blog.index'))


@bp.route('/like/<int:id>', methods=['POST'])
@login_required
def like_post(id):
    user_id = g.user[0]
    liked = is_post_liked(id, user_id)

    if liked:
        """Unlike the post if want to"""
        remove_liked(id, user_id)
        flash('You unliked the post', 'success')
    else:
        """Like the post"""
        add_like(id, user_id)
        flash('You liked the post.', 'success')

    return redirect(url_for('blog.index'))

def is_post_liked(id, user_id):
    """Checks if the user has liked the post"""
    try:
        with mysql.cursor() as cursor:
            cursor.execute("SELECT likes FROM post WHERE id = %s AND author_id = %s", (id, user_id))
            like_cnt = cursor.fetchone()
            
            mysql.commit()
            return like_cnt and like_cnt[0] > 0
    except pymysql.Error:
        print('An error occured while trying to retrieve likes')

def add_like(id, user_id):
    """
    Increment the likes count in out table
    """
    if not is_post_liked(id, user_id):
        try:
            with mysql.cursor() as cursor:
                cursor.execute("UPDATE post SET likes = likes + 1 WHERE id = %s", (id,))
                
                mysql.commit()
        except pymysql.Error:
            print('An error occured while trying to increment likes')

def remove_liked(id, user_id):
    """Decrement the likes count in the post table"""
    try:
        with mysql.cursor() as cursor:
            cursor.execute("UPDATE post SET likes = likes - 1 WHERE id = %s", (id,))

            mysql.commit()
    except pymysql.Error:
        print('An error occured while trying to decrement likes')

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    get_post(id)
    exec_query('DELETE FROM post WHERE id = %s', (id,))

    return redirect(url_for('blog.index'))