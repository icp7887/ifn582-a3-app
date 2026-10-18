import os

# Use the mysqlclient driver if it is installed, otherwise fall back to PyMySQL
# (pure Python, so it installs anywhere: Windows, Mac, Linux, Replit).
try:
    import MySQLdb  # noqa: F401
except ImportError:
    import pymysql
    pymysql.install_as_MySQLdb()

from flask import Flask, render_template, abort, g
from flask_mysqldb import MySQL as _MySQL
from flask_wtf.csrf import CSRFProtect


def _load_env_file(path):
    """Read KEY=VALUE lines from a local .env file (never committed) into the environment.
    Real environment variables (e.g. Replit Secrets) always win over the file."""
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_env_file(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))


class MySQL(_MySQL):
    @property
    def connection(self):
        if 'mysql_db' not in g:          # first DB use in this request
            g.mysql_db = self.connect    # open a connection and keep it on g
        return g.mysql_db

    def teardown(self, exception):       # runs when the request ends
        db = g.pop('mysql_db', None)
        if db is not None:
            db.close()

csrf = CSRFProtect() # adds a CSRF token check to every POST form
mysql = MySQL() # Initialize MySQL without app context. Global object to be used across the application.

def create_app(): #configures flask app and initializes MySQL with app context
    app = Flask(__name__)
    #settings come from environment variables (or the .env file); see .env.example
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-only-change-me') #signs the session cookie
    app.config['SESSION_COOKIE_HTTPONLY'] = True   # JavaScript cannot read the session cookie
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # other sites cannot send it with their form posts
    app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024    # uploaded images can be at most 4 MB
    app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST', 'localhost')
    app.config['MYSQL_PORT'] = int(os.environ.get('MYSQL_PORT', 3306))
    app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER', 'root')
    app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD', '')
    app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB', 'superchat')
    app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

    csrf.init_app(app)
    mysql.init_app(app) #binds the MySQL instance to the Flask app context, allowing it to be used throughout the application.

    from .views import bp
    app.register_blueprint(bp) #registers the blueprint from views.py, allowing the routes defined in that file to be part of the Flask application.

    # @app.route('/500')
    # def force_500():
    #     # Intentionally trigger a 500 error for testing purposes
    #     abort(500)

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template(
            'error.html',
            title="403 Forbidden",
            message="You do not have permission to access this page."
        ), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template(
            'error.html', 
            title="404 Not Found", 
            message="This page is not found. Please return home"
        ), 404

    # 400 and 500 error handlers live in views.py

    return app
