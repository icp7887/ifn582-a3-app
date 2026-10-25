import os
import uuid
from datetime import date
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, g, abort, current_app
from . import models
from .forms import LoginForm, RegisterForm, CampaignForm, PostForm, DonationForm, AdminUserForm

bp = Blueprint('main', __name__)

# =====================================================================
# AUTH HELPERS (current user + access control decorators)
# =====================================================================

CREATOR_STATUSES = ['Active', 'Paused', 'Closed']  


def campaign_owner_required(view):
    """Custom ownership decorator: the logged-in creator must own the campaign in the URL.
    Loads the campaign into g.campaign so the view does not query it again."""
    @wraps(view)
    @creator_required
    def wrapped(campaign_id, *args, **kwargs):
        campaign = models.get_campaign_detail(campaign_id)
        if campaign is None:
            abort(404)
        if campaign['creatorID'] != g.user['id']:
            abort(403)                       
        g.campaign = campaign
        return view(campaign_id, *args, **kwargs)
    return wrapped

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    g.user = models.get_user_by_id(user_id) if user_id else None
    if g.user and g.user['isSuspended']:
        session.clear()
        g.user = None


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('main.login'))
        return view(*args, **kwargs)
    return wrapped


def role_required(*roles): 
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if g.user['role'] not in roles:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator


admin_required = role_required('Admin')
creator_required = role_required('Creator')


# =====================================================================
# REGISTER
# =====================================================================

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if g.user:
        return redirect(url_for('main.index'))
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        email = form.email.data.strip().lower()
        taken = models.username_or_email_taken(username, email)
        if taken['username']:
            form.username.errors.append('That username is already taken.')
        if taken['email']:
            form.email.errors.append('An account with that email already exists.')
        if not (taken['username'] or taken['email']):
            # pbkdf2 so the hashes match the seeded accounts in database.sql
            user_id = models.create_user(username, email, generate_password_hash(form.password.data, method='pbkdf2:sha256'), form.role.data)
            session.clear()
            session['user_id'] = user_id
            flash('Welcome to Superchat, ' + username + '!', 'success')
            return redirect(url_for('main.index'))
    return render_template('register.html', form=form)


# =====================================================================
# LOGIN / LOGOUT
# =====================================================================

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if g.user:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = models.get_user_for_login(form.identifier.data.strip())

        # Passwords are stored hashed, so compare with check_password_hash
        if user and user.get('password') and check_password_hash(user['password'], form.password.data):
            if user['isSuspended']:
                flash('This account has been suspended. Please contact support.', 'danger')
            else:
                session.clear()  # start a fresh session on login
                session['user_id'] = user['id']
                flash('Welcome back, ' + user['username'] + '!', 'success')
                if user['role'] == 'Admin':
                    return redirect(url_for('main.admin_dashboard'))
                elif user['role'] == 'Creator':
                    return redirect(url_for('main.campaign'))
                else:
                    return redirect(url_for('main.index'))
        else:
            flash('Invalid username/email or password.', 'danger')

    return render_template('login.html', form=form)


@bp.route('/logout', methods=['POST']) #POST + CSRF token so other sites can't log you out
def logout():
    session.clear()  # Clear all session data
    flash('You have been logged out.', 'secondary')
    return redirect(url_for('main.index'))


def _save_image(file):
    if not file or not file.filename:
        return None
    filename = uuid.uuid4().hex + '.' + file.filename.rsplit('.', 1)[-1].lower()
    folder = os.path.join(current_app.static_folder, 'img', 'uploads')
    os.makedirs(folder, exist_ok=True)
    file.save(os.path.join(folder, filename))
    return 'img/uploads/' + filename


def _render_creator_dashboard(campaign, campaign_form=None, post_form=None, status=200):
    if campaign_form is None:
        campaign_form = CampaignForm(data={
            'title': campaign['title'], 'description': campaign['description'], 'goal': campaign['goalAmount'],
            'category': campaign['category'], 'start_date': campaign['startDate'], 'end_date': campaign['endDate']})
    stats = models.get_campaign_stats(campaign['id'])
    days_left = max((campaign['endDate'] - date.today()).days, 0)
    return render_template(
        'campaign.html',
        campaign=campaign,
        my_campaigns=models.get_creator_campaigns(g.user['id']),
        stats=stats,
        days_left=days_left,
        donations=models.get_campaign_donations(campaign['id'], limit=1000),
        posts=models.get_campaign_posts(campaign['id']),
        campaign_form=campaign_form,
        post_form=post_form or PostForm(),
        creator_statuses=CREATOR_STATUSES,
    ), status


@bp.route('/campaign')
@creator_required
def campaign():
    mine = models.get_creator_campaigns(g.user['id'])
    if not mine:
        return redirect(url_for('main.new_campaign'))
    return redirect(url_for('main.manage_campaign', campaign_id=mine[0]['id']))


@bp.route('/campaign/new', methods=['GET', 'POST'])
@creator_required
def new_campaign():
    form = CampaignForm()
    if request.method == 'GET':
        form.start_date.data = date.today()
    if form.validate_on_submit():
        image = _save_image(form.image_file.data)
        new_id = models.create_creator_campaign(
            g.user['id'], form.title.data.strip(), form.description.data.strip(), form.goal.data,
            form.category.data, form.start_date.data, form.end_date.data, image)
        flash('Campaign created! It will go public once an administrator approves it.', 'success')
        return redirect(url_for('main.manage_campaign', campaign_id=new_id))
    return render_template('campaign_new.html', form=form,
                           my_campaigns=models.get_creator_campaigns(g.user['id'])), (400 if form.errors else 200)


@bp.route('/campaign/<int:campaign_id>')
@campaign_owner_required
def manage_campaign(campaign_id):
    return _render_creator_dashboard(g.campaign)


@bp.route('/campaign/<int:campaign_id>/edit', methods=['POST'])
@campaign_owner_required
def edit_campaign(campaign_id):
    campaign = g.campaign
    if campaign['status'] == 'Suspended':
        flash('This campaign has been suspended by an administrator and cannot be edited.', 'danger')
        return redirect(url_for('main.manage_campaign', campaign_id=campaign_id))
    form = CampaignForm()
    if not form.validate_on_submit():
        flash('Please fix the highlighted fields in Campaign Settings.', 'danger')
        return _render_creator_dashboard(campaign, campaign_form=form, status=400)
    # keep the old image unless a new one was uploaded
    image = _save_image(form.image_file.data) or campaign['campaignImage']
    models.update_campaign_details(campaign_id, form.title.data.strip(), form.description.data.strip(),
                                   form.goal.data, form.category.data, form.start_date.data,
                                   form.end_date.data, image)
    flash('Campaign details saved.', 'success')
    return redirect(url_for('main.manage_campaign', campaign_id=campaign_id, _anchor='settings'))


@bp.route('/campaign/<int:campaign_id>/status', methods=['POST'])
@campaign_owner_required
def creator_set_status(campaign_id):
    campaign = g.campaign
    new_status = request.form.get('status')
    if campaign['status'] not in CREATOR_STATUSES:
        flash(f'This campaign is {campaign["status"]}. Only an administrator can change that.', 'danger')
    elif new_status not in CREATOR_STATUSES:
        abort(400)
    else:
        models.update_campaign_status(campaign_id, new_status)
        flash(f'Campaign is now {new_status}.', 'success')
    return redirect(url_for('main.manage_campaign', campaign_id=campaign_id, _anchor='status'))


# ---------- campaign posts / updates ----------
def _owned_post_or_404(campaign_id, post_id):
    post = models.get_post(post_id)
    if post is None or post['campaignID'] != campaign_id:   # post must belong to this (owned) campaign
        abort(404)
    return post


@bp.route('/campaign/<int:campaign_id>/posts', methods=['POST'])
@campaign_owner_required
def add_post(campaign_id):
    form = PostForm()
    if not form.validate_on_submit():
        flash('Please fix the highlighted fields in Campaign Updates.', 'danger')
        return _render_creator_dashboard(g.campaign, post_form=form, status=400)
    models.add_post(campaign_id, form.title.data.strip(), form.content.data.strip(), _save_image(form.image.data))
    flash('Update posted.', 'success')
    return redirect(url_for('main.manage_campaign', campaign_id=campaign_id, _anchor='updates'))


@bp.route('/campaign/<int:campaign_id>/posts/<int:post_id>/edit', methods=['GET', 'POST'])
@campaign_owner_required
def edit_post(campaign_id, post_id):
    post = _owned_post_or_404(campaign_id, post_id)
    form = PostForm(data={'title': post['title'], 'content': post['content']} if request.method == 'GET' else None)
    if form.validate_on_submit():
        image = _save_image(form.image.data) or (None if form.remove_image.data else post['postImage'])
        models.update_post(post_id, form.title.data.strip(), form.content.data.strip(), image)
        flash('Update saved.', 'success')
        return redirect(url_for('main.manage_campaign', campaign_id=campaign_id, _anchor='updates'))
    return render_template('campaign_post_edit.html', form=form, post=post, campaign=g.campaign), (400 if form.errors else 200)


@bp.route('/campaign/<int:campaign_id>/posts/<int:post_id>/delete', methods=['POST'])
@campaign_owner_required
def delete_post(campaign_id, post_id):
    _owned_post_or_404(campaign_id, post_id)
    models.delete_post(post_id)
    flash('Update deleted.', 'info')
    return redirect(url_for('main.manage_campaign', campaign_id=campaign_id, _anchor='updates'))

# =====================================================================
# HOMEPAGE (search, categories, featured campaigns, campaign list)
# =====================================================================

HOMEPAGE_CAMPAIGN_LIMIT = 3   # Campaigns shown before "SHOW ALL" is clicked


@bp.route('/')
def index():
    search = request.args.get('search', '').strip()
    selected_category = request.args.get('category', '').strip()
    if search:
        campaigns = models.search_campaigns(search)
    elif selected_category:
        campaigns = models.get_campaigns_by_category(selected_category)
    else:
        campaigns = models.get_active_campaigns()

    categories = models.get_categories()
    featured = models.get_featured_active_campaigns()

    show_all = request.args.get('show') == 'all'
    total_campaigns = len(campaigns)    
    if not show_all:
        campaigns = campaigns[:HOMEPAGE_CAMPAIGN_LIMIT]

    return render_template(
        'index.html',
        campaigns=campaigns,
        categories=categories,
        featured=featured,                       
        search=search,                           
        selected_category=selected_category,     
        total_campaigns=total_campaigns,
        limit=HOMEPAGE_CAMPAIGN_LIMIT,
        show_all=show_all,                       
    )


# =====================================================================
# DONATION
# =====================================================================


def _visible_campaign_or_404(campaign_id):
    campaign = models.get_campaign_detail(campaign_id)
    if campaign is None:
        abort(404)
    if campaign['status'] not in ('Active', 'Paused', 'Closed'):
        is_owner = g.user is not None and g.user['id'] == campaign['creatorID']
        is_admin = g.user is not None and g.user['role'] == 'Admin'
        if not (is_owner or is_admin):
            abort(404)
    return campaign


def _render_donation_page(campaign, form, status=200):
    tiers = models.get_creator_tiers(campaign['creatorID'])
    return render_template('donation.html', campaign=campaign, form=form, tiers=tiers,
                           donations=models.get_campaign_donations(campaign['id']),
                           posts=models.get_campaign_posts(campaign['id'])), status


@bp.route('/donation/<int:campaign_id>')
def campaign_donation(campaign_id):
    campaign = _visible_campaign_or_404(campaign_id)
    form = DonationForm()
    form.set_tiers(models.get_creator_tiers(campaign['creatorID']))
    if g.user and g.user['role'] == 'Customer':
        form.donor_name.data = g.user['username']
        form.email.data = g.user['email']
    tier_id = request.args.get('tier', type=int)
    if tier_id in form.tier_prices:
        form.tier.data = tier_id
        form.amount.data = form.tier_prices[tier_id]
    return _render_donation_page(campaign, form)


@bp.route('/donation/<int:campaign_id>/donate', methods=['POST'])
def donate(campaign_id):
    campaign = _visible_campaign_or_404(campaign_id)
    page = url_for('main.campaign_donation', campaign_id=campaign_id)
    if g.user is None:
        flash('Please log in or register as a Supporter to donate.', 'warning')
        return redirect(url_for('main.login'))
    if g.user['role'] != 'Customer':
        flash('Only Supporter accounts can donate.', 'warning')
        return redirect(page + '#donate')
    if campaign['status'] != 'Active':
        flash('This campaign is not accepting donations right now.', 'warning')
        return redirect(page)
    form = DonationForm()
    form.set_tiers(models.get_creator_tiers(campaign['creatorID']))
    if not form.validate_on_submit():
        flash('Please fix the highlighted fields below.', 'danger')
        return _render_donation_page(campaign, form, status=400)
    models.add_donation(campaign_id, g.user['id'], form.amount.data, form.donor_name.data.strip(),
                        form.email.data.strip().lower(), form.address.data.strip(),
                        (form.message.data or '').strip() or None, form.tier.data or None, form.payment_method.data)
    flash(f'Thank you for donating ${form.amount.data:,.2f} to {campaign["title"]}!', 'success')
    return redirect(page + '#supporters')


# =====================================================================
# ADMIN (every route here is Admin only)
# =====================================================================

CAMPAIGN_STATUSES = ['Pending', 'Active', 'Paused', 'Closed', 'Rejected', 'Suspended']


#admin dashboard url route
@bp.route('/admin')
@admin_required
def admin_dashboard():
    return render_template(
        'admin_dashboard.html',
        pending=models.get_all_campaigns_with_creator(),    
        campaigns=models.get_all_campaigns_with_details(),  
        users=models.get_all_users(),                       
        reports=models.get_open_reports(),                  
        featured_options=models.get_active_campaigns(),     
    )



@bp.route('/admin/approve/<int:campaign_id>', methods=['POST']) 
@admin_required
def approve_campaign(campaign_id):
    models.update_campaign_status(campaign_id, 'Active') 
    flash('Campaign approved.', 'success')
    return redirect(url_for('main.admin_dashboard', _anchor='approval'))


@bp.route('/admin/reject/<int:campaign_id>', methods=['POST']) 
@admin_required
def reject_campaign(campaign_id):
    models.update_campaign_status(campaign_id, 'Rejected')
    flash('Campaign rejected.', 'secondary')
    return redirect(url_for('main.admin_dashboard', _anchor='approval'))


@bp.route('/admin/status/<int:campaign_id>', methods=['POST']) 
@admin_required
def admin_set_campaign_status(campaign_id):
    status = request.form.get('status')
    if status not in CAMPAIGN_STATUSES:
        abort(400)
    models.update_campaign_status(campaign_id, status)
    flash('Campaign status set to ' + status + '.', 'success')
    return redirect(url_for('main.admin_dashboard', _anchor='campaigns'))


@bp.route('/admin/featured', methods=['POST']) 
@admin_required
def admin_set_featured():
    ids = [int(i) for i in request.form.getlist('featured') if i.isdigit()]
    models.set_featured_campaigns(ids)
    flash('Featured campaigns updated.', 'success')
    return redirect(url_for('main.admin_dashboard', _anchor='featured'))


@bp.route('/admin/delete/<int:campaign_id>', methods=['POST']) 
@admin_required
def admin_delete_campaign(campaign_id):
    models.delete_campaign(campaign_id)
    flash('Campaign deleted.', 'secondary')
    return redirect(url_for('main.admin_dashboard', _anchor='campaigns'))


@bp.route('/admin/report/<int:report_id>/<action>', methods=['POST']) 
@admin_required
def admin_review_report(report_id, action):
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
    return redirect(url_for('main.admin_dashboard', _anchor='reports'))


@bp.route('/admin/user/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_user(user_id):
    user = models.get_user_by_id(user_id)
    if user is None:
        abort(404)
    form = AdminUserForm(data={'username': user['username'], 'email': user['email'],
                               'verified': bool(user['verifiedStatus'])} if request.method == 'GET' else None)
    if form.validate_on_submit():
        username = form.username.data.strip()
        email = form.email.data.strip().lower()
        if models.taken_by_other_user(username, email, user_id):
            flash('Another account already uses that username or email.', 'danger')
        else:
            models.update_user_details(user_id, username, email)
            if user['role'] == 'Creator':
                models.set_creator_verified(user_id, form.verified.data)
            flash('Account details for ' + username + ' saved.', 'success')
            return redirect(url_for('main.admin_dashboard', _anchor='users'))
    return render_template('admin_edit_user.html', form=form, user=user), (400 if form.errors else 200)


@bp.route('/admin/user/<int:user_id>/suspend', methods=['POST']) 
@admin_required
def admin_suspend_user(user_id):
    if user_id == g.user['id']: 
        flash('You cannot suspend your own account.', 'danger')
    else:
        suspend = request.form.get('suspend') == '1'
        models.set_user_suspended(user_id, suspend)
        flash('User suspended.' if suspend else 'User reinstated.', 'success')
    return redirect(url_for('main.admin_dashboard', _anchor='users'))


@bp.route('/admin/delete_user/<int:user_id>', methods=['POST']) 
@admin_required
def admin_delete_user(user_id):
    if user_id == g.user['id']: 
        flash('You cannot delete your own account.', 'danger')
    else:
        models.delete_user(user_id)
        flash('User deleted.', 'secondary')
    return redirect(url_for('main.admin_dashboard', _anchor='users'))
