from flask import Flask, render_template
from flask_mysqldb import MySQL
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect() #checks the CSRF token on every POST form
mysql = MySQL()

ERROR_MESSAGES = {
    400: 'Bad Request. Please try again.',
    403: 'You do not have permission to access this page.',
    404: 'Sorry no page found. Please go back.',
    500: 'Server side error. Please try again later.',
}


def error_page(error): #every error uses the shared error.html template
    return render_template('error.html', title=f'{error.code} {error.name}', message=ERROR_MESSAGES[error.code]), error.code


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'superchat-secret-key'
    app.config['MYSQL_HOST'] = 'localhost'
    app.config['MYSQL_USER'] = 'root'
    app.config['MYSQL_PASSWORD'] = 'compassion' #put your MySQL password here
    app.config['MYSQL_DB'] = 'superchat'
    app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

    csrf.init_app(app)
    mysql.init_app(app)

    from .views import bp
    app.register_blueprint(bp)

    for code in ERROR_MESSAGES:
        app.register_error_handler(code, error_page)

    return app
