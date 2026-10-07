from flask import Flask
from flask_mysqldb import MySQL

mysql = MySQL() # Initialize MySQL without app context. Global object to be used across the application.

def create_app(): #configures flask app and initializes MySQL with app context
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'superchat-secret-key-123' #used for securely signing the session cookie and can be used for other security-related needs by extensions or your application.
    app.config['MYSQL_HOST'] = 'localhost'
    app.config['MYSQL_USER'] = 'root'
    app.config['MYSQL_PASSWORD'] = 'admin'  # Change to your MySQL password
    app.config['MYSQL_PORT'] = 3306
    app.config['MYSQL_DB'] = 'superchat'
    app.config['MYSQL_CURSORCLASS'] = 'DictCursor' #returns rows as dictionaries for Jinja2 templates

    mysql.init_app(app) #binds the MySQL instance to the Flask app context, allowing it to be used throughout the application.

    from .views import bp
    app.register_blueprint(bp) #registers the blueprint from views.py, allowing the routes defined in that file to be part of the Flask application.

    return app
