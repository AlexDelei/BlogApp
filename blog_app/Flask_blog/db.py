# Connetction to my sqlite database
import sqlite3
import click
from flask import current_app, g
# g is a special object that is unique for each request

def get_db():
    """Establishing a connection with sqlite database
    the connection is to the file pointed by DATABASE configuration key
    """

    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DATABASE'], detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row # tells the connection to return row behaving like dicts

    return g.db

def close_db(e=None):
    """Close the connection obviously"""

    db = g.pop('db', None)
    
    if db is not None:
        db.close()

def init_db():
    """
    open_resource() opens a file relative to the flaskr package.
    since you wont necessarily know where the location is when deploying
    """
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf-8'))

@click.command('init-db')
def init_db_command():
    """Clear existing data and create new tables
    defines a command called init-db that calls the init_db function
    and shows a success message to the user
    """
    init_db()
    click.echo('Initialized the database.')

def init_app(app):
    """
    app.teardown_appcontext() tells Flask to call that function when cleaning up
    after returning the response

    app.cli.add_command() adds a new commmand that can be called with the flask command
    """
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)