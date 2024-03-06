# Contains the application factory

import os
import base64
from urllib.parse import urlencode
from flask import Flask

def create_app(test_config=None):
    """Creating and Configuring the app"""

    app = Flask(__name__, instance_relative_config=True)
    app.secret_key = "ea9z2RkXDPefyc0G2EhaDz3JjqED-a_o7c_-o11o"


    @app.route('/hello')
    def hello():
        return 'Hello World , Again!'
    
    from . import db
    db.init_app(app) # now the init-db has been registred with the app and can be called using flask
    
    # Makes the b64encode function available to templates
    app.jinja_env.filters['b64encode'] = base64.b64encode
    app.jinja_env.filters['url_encode'] = urlencode

    from . import auth
    app.register_blueprint(auth.bp) # this blueprint conatins views to register nre users to loin
                                    # and logout

    from . import blog
    app.register_blueprint(blog.bp)
    app.add_url_rule('/', endpoint='index')
    """
    unlike the auth blueprint, the blog blueprint does not have a url_prefix. So the index view will be
    at /, the create view at /create and so on.
    blog is the main feature of Flaskr, so it makes sense that the blog index will be the main index
    """
    return app

"""
app = Flask(__name__, instance_relative_config=True) -> creates Flask instance
        __name__ -> is the name of the current module
                 -> its a conventional way to tell the app where it is located
        instance_relative_config=True -> tells the app that configuration files are relative to the instance folder

app.config.from_mapping() -> sets some default configuration that the app will use

        SECRET_KEY  -> used by flask and extensions to keep data safe
        DATABASE  -> is the path where the SQLlite database file will be saved

app.config.from_pyfile()  ->  overrides the default configuration with values taken from the config.py file in the
                            instance folder if exists

os.makedirs()  -> ensures that app.instance_path exists
"""