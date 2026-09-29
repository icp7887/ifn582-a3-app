from flask import Blueprint, render_template, redirect, url_for, flash
from .forms import ItemForm
from . import models

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return render_template('index.html', items=models.get_all_items())

@bp.route('/add', methods=['GET', 'POST'])
def add():
    form = ItemForm()
    if form.validate_on_submit():
        models.add_item(form.name.data, form.description.data)
        flash('Item added.')
        return redirect(url_for('main.index'))
    return render_template('add.html', form=form)
