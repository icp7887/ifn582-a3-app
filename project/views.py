import os
import uuid
from datetime import date
from werkzeug.security import check_password_hash, generate_password_hash
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, g, abort, current_app
from . import models
from .forms import LoginForm, RegisterForm, CampaignForm, PostForm, DonationForm, AdminUserForm

bp = Blueprint('main', __name__)

CREATOR_STATUSES = ['Active', 'Paused', 'Closed']
CAMPAIGN_STATUSES = ['Pending', 'Active', 'Paused', 'Closed', 'Rejected', 'Suspended']


@bp.before_app_request
def load_logged_in_user():
    g.user = None
    if 'user_id' in session:
        g.user = models.get_user_by_id(session['user_id'])
    if g.user and g.user['isSuspended']:
        session.clear()
        g.user = None


def require_role(role):
    if g.user is None:
        flash('Please log in to continue.', 'warning')
        abort(redirect(url_for('main.login')))
    if g.user['role'] != role:
        abort(403)


def get_own_campaign(campaign_id):
    require_role('Creator')
    campaign = models.get_campaign_detail(campaign_id)
    if campaign is None:
        abort(404)
    if campaign['creatorID'] != g.user['id']:
        abort(403)
    return campaign


@bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        taken = models.username_or_email_taken(form.username.data, form.email.data)
        if taken['username']:
            form.username.errors.append('That username is already taken.')
        if taken['email']:
            form.email.errors.append('An account with that email already exists.')
        if not taken['username'] and not taken['email']:
            password_hash = generate_password_hash(form.password.data, method='pbkdf2:sha256')
            session['user_id'] = models.create_user(form.username.data, form.email.data, password_hash, form.role.data)
            flash('Welcome, ' + form.username.data + '!', 'success')
            return redirect(url_for('main.index'))
    return render_template('register.html', form=form)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = models.get_user_for_login(form.identifier.data)
        if user is None or not check_password_hash(user['password'], form.password.data):
            flash('Invalid username/email or password.', 'danger')
        elif user['isSuspended']:
            flash('This account has been suspended. Please contact support.', 'danger')
        else:
            session['user_id'] = user['id']
            flash('Welcome, ' + user['username'] + '!', 'success')
            if user['role'] == 'Admin':
                return redirect(url_for('main.admin_dashboard'))
            if user['role'] == 'Creator':
                return redirect(url_for('main.campaign'))
            return redirect(url_for('main.index'))
    return render_template('login.html', form=form)


@bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    flash('You have been logged out.', 'secondary')
    return redirect(url_for('main.index'))


@bp.route('/')
def index():
    search = request.args.get('search', '').strip()
    selected_category = request.args.get('category', '')
    if search:
        campaigns = models.search_campaigns(search)
    elif selected_category:
        campaigns = models.get_campaigns_by_category(selected_category)
    else:
        campaigns = models.get_active_campaigns()
    return render_template('index.html', campaigns=campaigns, categories=models.get_categories(),
                           featured=models.get_featured_active_campaigns(),
                           search=search, selected_category=selected_category)


def get_visible_campaign(campaign_id):
    campaign = models.get_campaign_detail(campaign_id)
    if campaign is None:
        abort(404)
    if campaign['status'] not in ('Active', 'Paused', 'Closed'):
        if g.user is None or (g.user['role'] != 'Admin' and g.user['id'] != campaign['creatorID']):
            abort(404)
    return campaign


def render_donation_page(campaign, form):
    return render_template('donation.html', campaign=campaign, form=form,
                           tiers=models.get_creator_tiers(campaign['creatorID']),
                           donations=models.get_campaign_donations(campaign['id']),
                           posts=models.get_campaign_posts(campaign['id']))


@bp.route('/donation/<int:campaign_id>')
def campaign_donation(campaign_id):
    campaign = get_visible_campaign(campaign_id)
    form = DonationForm()
    form.set_tiers(models.get_creator_tiers(campaign['creatorID']))
    tier_id = request.args.get('tier', type=int)
    if tier_id in form.tier_prices:
        form.tier.data = tier_id
        form.amount.data = form.tier_prices[tier_id]
    return render_donation_page(campaign, form)


@bp.route('/donation/<int:campaign_id>/donate', methods=['POST'])
def donate(campaign_id):
    campaign = get_visible_campaign(campaign_id)
    if g.user is None:
        flash('Please log in or register as a Supporter to donate.', 'warning')
        return redirect(url_for('main.login'))
    if g.user['role'] != 'Customer':
        flash('Only Supporter accounts can donate.', 'warning')
        return redirect(url_for('main.campaign_donation', campaign_id=campaign_id))
    if campaign['status'] != 'Active':
        flash('This campaign is not accepting donations right now.', 'warning')
        return redirect(url_for('main.campaign_donation', campaign_id=campaign_id))
    form = DonationForm()
    form.set_tiers(models.get_creator_tiers(campaign['creatorID']))
    if not form.validate_on_submit():
        flash('Fix things below.', 'danger')
        return render_donation_page(campaign, form)
    models.add_donation(campaign_id, g.user['id'], form.amount.data, form.donor_name.data, form.email.data,
                        form.address.data, form.message.data, form.tier.data or None, form.payment_method.data)
    flash('Thank you for donating $' + str(form.amount.data) + ' to ' + campaign['title'] + '!', 'success')
    return redirect(url_for('main.campaign_donation', campaign_id=campaign_id, _anchor='supporters'))


def save_image(file):
    if not file or not file.filename:
        return None
    filename = uuid.uuid4().hex + '.' + file.filename.rsplit('.', 1)[-1].lower()
    folder = os.path.join(current_app.static_folder, 'img', 'uploads')
    os.makedirs(folder, exist_ok=True)
    file.save(os.path.join(folder, filename))
    return 'img/uploads/' + filename


def render_creator_dashboard(campaign, campaign_form=None, post_form=None):
    if campaign_form is None:
        campaign_form = CampaignForm(data={
            'title': campaign['title'], 'description': campaign['description'], 'goal': campaign['goalAmount'],
            'category': campaign['category'], 'start_date': campaign['startDate'], 'end_date': campaign['endDate']})
    return render_template('campaign.html', campaign=campaign,
                           my_campaigns=models.get_creator_campaigns(g.user['id']),
                           stats=models.get_campaign_stats(campaign['id']),
                           days_left=max((campaign['endDate'] - date.today()).days, 0),
                           donations=models.get_campaign_donations(campaign['id'], limit=1000),
                           posts=models.get_campaign_posts(campaign['id']),
                           campaign_form=campaign_form, post_form=post_form or PostForm())


@bp.route('/campaign')
def campaign():
    require_role('Creator')
    mine = models.get_creator_campaigns(g.user['id'])
    if not mine:
        return redirect(url_for('main.new_campaign'))
    return redirect(url_for('main.manage_campaign', campaign_id=mine[0]['id']))


@bp.route('/campaign/new', methods=['GET', 'POST'])
def new_campaign():
    require_role('Creator')
    form = CampaignForm()
    if form.validate_on_submit():
        new_id = models.create_creator_campaign(g.user['id'], form.title.data, form.description.data, form.goal.data,
                                                form.category.data, form.start_date.data, form.end_date.data,
                                                save_image(form.image_file.data))
        flash('Campaign created! Admin required to approve.', 'success')
        return redirect(url_for('main.manage_campaign', campaign_id=new_id))
    return render_template('campaign_new.html', form=form)


@bp.route('/campaign/<int:campaign_id>')
def manage_campaign(campaign_id):
    campaign = get_own_campaign(campaign_id)
    return render_creator_dashboard(campaign)


@bp.route('/campaign/<int:campaign_id>/edit', methods=['POST'])
def edit_campaign(campaign_id):
    campaign = get_own_campaign(campaign_id)
    if campaign['status'] == 'Suspended':
        flash('Campaign suspended by admin.', 'danger')
        return redirect(url_for('main.manage_campaign', campaign_id=campaign_id))
    form = CampaignForm()
    if not form.validate_on_submit():
        flash('Fix things in Campaign Settings.', 'danger')
        return render_creator_dashboard(campaign, campaign_form=form)
    image = save_image(form.image_file.data) or campaign['campaignImage']
    models.update_campaign_details(campaign_id, form.title.data, form.description.data, form.goal.data,
                                   form.category.data, form.start_date.data, form.end_date.data, image)
    flash('Campaign details saved.', 'success')
    return redirect(url_for('main.manage_campaign', campaign_id=campaign_id))


@bp.route('/campaign/<int:campaign_id>/status', methods=['POST'])
def creator_set_status(campaign_id):
    campaign = get_own_campaign(campaign_id)
    new_status = request.form.get('status')
    if campaign['status'] not in CREATOR_STATUSES:
        flash('This campaign is ' + campaign['status'] + '. Only an administrator can change that.', 'danger')
    elif new_status not in CREATOR_STATUSES:
        abort(400)
    else:
        models.update_campaign_status(campaign_id, new_status)
        flash('Campaign is now ' + new_status + '.', 'success')
    return redirect(url_for('main.manage_campaign', campaign_id=campaign_id))


def get_own_post(campaign_id, post_id):
    post = models.get_post(post_id)
    if post is None or post['campaignID'] != campaign_id:
        abort(404)
    return post


@bp.route('/campaign/<int:campaign_id>/posts', methods=['POST'])
def add_post(campaign_id):
    campaign = get_own_campaign(campaign_id)
    form = PostForm()
    if not form.validate_on_submit():
        flash('Fix things in Campaign Updates.', 'danger')
        return render_creator_dashboard(campaign, post_form=form)
    models.add_post(campaign_id, form.title.data, form.content.data, save_image(form.image.data))
    flash('Update posted.', 'success')
    return redirect(url_for('main.manage_campaign', campaign_id=campaign_id))


@bp.route('/campaign/<int:campaign_id>/posts/<int:post_id>/edit', methods=['GET', 'POST'])
def edit_post(campaign_id, post_id):
    campaign = get_own_campaign(campaign_id)
    post = get_own_post(campaign_id, post_id)
    form = PostForm(data=post if request.method == 'GET' else None)
    if form.validate_on_submit():
        image = save_image(form.image.data) or post['postImage']
        models.update_post(post_id, form.title.data, form.content.data, image)
        flash('Update saved.', 'success')
        return redirect(url_for('main.manage_campaign', campaign_id=campaign_id))
    return render_template('campaign_post_edit.html', form=form, post=post, campaign=campaign)


@bp.route('/campaign/<int:campaign_id>/posts/<int:post_id>/delete', methods=['POST'])
def delete_post(campaign_id, post_id):
    campaign = get_own_campaign(campaign_id)
    get_own_post(campaign_id, post_id)
    models.delete_post(post_id)
    flash('Update deleted.', 'info')
    return redirect(url_for('main.manage_campaign', campaign_id=campaign_id))


@bp.route('/admin')
def admin_dashboard():
    require_role('Admin')
    return render_template('admin_dashboard.html',
                           pending=models.get_all_campaigns_with_creator(),
                           campaigns=models.get_all_campaigns_with_details(),
                           users=models.get_all_users(),
                           reports=models.get_open_reports(),
                           featured_options=models.get_active_campaigns())


@bp.route('/admin/approve/<int:campaign_id>', methods=['POST'])
def approve_campaign(campaign_id):
    require_role('Admin')
    models.update_campaign_status(campaign_id, 'Active')
    flash('Campaign approved.', 'success')
    return redirect(url_for('main.admin_dashboard'))


@bp.route('/admin/reject/<int:campaign_id>', methods=['POST'])
def reject_campaign(campaign_id):
    require_role('Admin')
    models.update_campaign_status(campaign_id, 'Rejected')
    flash('Campaign rejected.', 'secondary')
    return redirect(url_for('main.admin_dashboard'))


@bp.route('/admin/status/<int:campaign_id>', methods=['POST'])
def admin_set_campaign_status(campaign_id):
    require_role('Admin')
    status = request.form.get('status')
    if status not in CAMPAIGN_STATUSES:
        abort(400)
    models.update_campaign_status(campaign_id, status)
    flash('Campaign status set to ' + status + '.', 'success')
    return redirect(url_for('main.admin_dashboard'))


@bp.route('/admin/featured', methods=['POST'])
def admin_set_featured():
    require_role('Admin')
    models.set_featured_campaigns(request.form.getlist('featured'))
    flash('Featured campaigns updated.', 'success')
    return redirect(url_for('main.admin_dashboard'))


@bp.route('/admin/delete/<int:campaign_id>', methods=['POST'])
def admin_delete_campaign(campaign_id):
    require_role('Admin')
    models.delete_campaign(campaign_id)
    flash('Campaign removed.', 'secondary')
    return redirect(url_for('main.admin_dashboard'))


@bp.route('/admin/report/<int:report_id>/<action>', methods=['POST'])
def admin_review_report(report_id, action):
    require_role('Admin')
    report = models.get_report_by_id(report_id)
    if report is None:
        abort(404)
    if action == 'dismiss':
        models.set_report_status(report_id, 'Dismissed')
    elif action == 'suspend':
        models.update_campaign_status(report['campaignID'], 'Suspended')
        models.set_report_status(report_id, 'Resolved')
    elif action == 'remove':
        models.delete_campaign(report['campaignID'])
    else:
        abort(400)
    flash('Report reviewed.', 'success')
    return redirect(url_for('main.admin_dashboard'))


@bp.route('/admin/user/<int:user_id>/edit', methods=['GET', 'POST'])
def admin_edit_user(user_id):
    require_role('Admin')
    user = models.get_user_by_id(user_id)
    if user is None:
        abort(404)
    form = AdminUserForm(data=user if request.method == 'GET' else None)
    if form.validate_on_submit():
        if models.taken_by_other_user(form.username.data, form.email.data, user_id):
            flash('Sorry username or email already taken.', 'danger')
        else:
            models.update_user_details(user_id, form.username.data, form.email.data)
            flash('Account details for ' + form.username.data + ' saved.', 'success')
            return redirect(url_for('main.admin_dashboard'))
    return render_template('admin_edit_user.html', form=form, user=user)


@bp.route('/admin/user/<int:user_id>/suspend', methods=['POST'])
def admin_suspend_user(user_id):
    require_role('Admin')
    if user_id == g.user['id']:
        flash('You cannot suspend your own account.', 'danger')
    else:
        suspend = request.form.get('suspend') == '1'
        models.set_user_suspended(user_id, suspend)
        flash('User suspended.' if suspend else 'User reinstated.', 'success')
    return redirect(url_for('main.admin_dashboard'))


@bp.route('/admin/delete_user/<int:user_id>', methods=['POST'])
def admin_delete_user(user_id):
    require_role('Admin')
    if user_id == g.user['id']:
        flash('You cannot delete your own account.', 'danger')
    else:
        models.delete_user(user_id)
        flash('User removed.', 'secondary')
    return redirect(url_for('main.admin_dashboard'))
