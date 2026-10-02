from flask import Blueprint, render_template
from . import models

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    campaigns = models.get_all_campaigns()
    return render_template('index.html', campaigns=campaigns)