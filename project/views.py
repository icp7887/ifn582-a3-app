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
            return redirect(url_for('main.login', next=request.full_path if request.method == 'GET' else None))
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

    return render_template('login.html', form=form, test_accounts=[])


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
            'category': campaign['category'], 'start_date': campaign['startDate'], 'end_date': campaign['endDate'],
            'image_url': campaign['campaignImage'] if (campaign['campaignImage'] or '').startswith('http') else ''})
    stats = models.get_campaign_stats(campaign['id'])
    days_left = (campaign['endDate'] - date.today()).days
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
        image = _save_image(form.image_file.data) or (form.image_url.data or '').strip() or None
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
    # keep the old image unless a new upload or link was given
    image = _save_image(form.image_file.data) or (form.image_url.data or '').strip() or campaign['campaignImage']
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


@bp.route('/campaigns/<int:campaign_id>')
def campaign_detail(campaign_id):
    return redirect(url_for('main.campaign_donation', campaign_id=campaign_id,
                            tier=request.args.get('tier', type=int), _anchor='donate' if request.args.get('tier') else None))


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
# ADMIN DASHBOARD (Campaign and User Management)
# =====================================================================

CAMPAIGN_STATUSES = ['Pending', 'Active', 'Paused', 'Closed', 'Rejected', 'Suspended']

@bp.route('/admin_dashboard', methods=['GET'])
@admin_required
def admin_dashboard():
    counts = models.get_dashboard_counts()
    campaigns = models.get_all_campaigns_with_details()
    open_reports = models.get_open_reports()
    all_users = models.get_all_users()

    pending_list = [
        c for c in campaigns 
        if c['status'].lower() in ['pending', 'paused', 'suspended']
    ]
    
    flagged_list = [c for c in campaigns if c['isFlagged']] 
    active_list = [c for c in campaigns if c['status'].lower() == 'active' and not c['isFlagged']]

    counts['pending'] = len([
        c for c in campaigns 
        if c['status'].lower() in ['pending', 'suspended']
    ])
    
    counts['active'] = len(active_list)
    counts['reports'] = len(flagged_list)
    counts['users'] = len(all_users)
    counts['suspended'] = len([u for u in all_users if u['isSuspended']])
    
    return render_template(
        'admin_dashboard.html',
        counts=counts,
        campaigns=campaigns,
        flagged=flagged_list,
        pending=pending_list, 
        reports=open_reports,
        users=all_users
    )

# ---------- Update Campaign Status --------

@bp.route('/admin/campaign/<int:campaign_id>/status', methods=['GET', 'POST'])
@admin_required
def change_campaign_status(campaign_id):
    campaign = models.get_campaign_detail(campaign_id)
    if campaign is None:
        abort(404)

    new_status = (request.args.get('status') or request.form.get('status') or '').strip().lower()
    allowed_statuses = ['active', 'rejected', 'pending', 'paused', 'suspended', 'closed']
    
    if new_status in allowed_statuses:
        db_status = new_status.lower()

        keep_flagged = 1 if db_status == 'Rejected' else 0

        cur = mysql.connection.cursor()
        cur.execute(
            """UPDATE campaign SET status = %s, isFlagged = %s WHERE id = %s""",
            (db_status, keep_flagged, campaign_id)
        )
        mysql.connection.commit()
        cur.close()
        
        if db_status == 'Active':
            flash(f"'{campaign['title']}' has been approved and is now live on the platform!", "success")
        elif db_status == 'Paused':
            flash(f"'{campaign['title']}' has been temporarily paused.", "info")
        elif db_status == 'Suspended':
            flash(f"'{campaign['title']}' has been suspended from the public feed.", "warning")
        else:
            flash(f"'{campaign['title']}' status updated to {db_status}.", "secondary")
    else:
        abort(400)
        
    return redirect(url_for('main.admin_dashboard'))


# ---------------- Flag Campaign --------------------

@bp.route('/admin/campaign/<int:campaign_id>/flag', methods=['GET', 'POST'])
@admin_required
def admin_toggle_flag(campaign_id):
    campaign = models.get_campaign_detail(campaign_id)
    if campaign is None:
        abort(404)

    is_flagged_param = request.args.get('is_flagged') or request.form.get('is_flagged') or 'True'
    is_flagged = True if is_flagged_param == 'True' else False
    
    models.set_campaign_flagged(campaign_id, is_flagged)
    
    if is_flagged:
        flash(f"'{campaign['title']}' has been flagged for review.", 'warning')
    else:
        flash(f"Flag status removed for '{campaign['title']}'.", 'success')
        
    return redirect(url_for('main.admin_dashboard'))



# ------------------- Delete Campaign ----------------------------------- 

@bp.route('/admin/campaign/<int:campaign_id>/delete', methods=['GET', 'POST'])
@admin_required
def admin_delete_campaign(campaign_id):
    campaign = models.get_campaign_detail(campaign_id)
    if campaign is None:
        abort(404) 

    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM campaign WHERE id = %s", (campaign_id,))
    mysql.connection.commit()
    cur.close()

    flash(f"Campaign '{campaign['title']}' has been deleted successfully.", 'danger')
    return redirect(url_for('main.admin_dashboard'))




# -------------------- Featured Campaign --------------------

@bp.route('/admin/configure-featured', methods=['POST'])
@admin_required
def configure_featured_showcase():
    selected_campaign_ids = request.form.getlist('featured_campaigns', type=int)
    models.set_featured_campaigns(selected_campaign_ids)
    
    flash("Your homepage featured campaigns showcase has been successfully updated!", "success")
    return redirect(url_for('main.admin_dashboard'))


# -------------------- User Management & Reports --------------------

@bp.route('/admin/report/<int:report_id>/resolve', methods=['GET', 'POST'])
@admin_required
def resolve_incident_report(report_id):
    report = models.get_report_by_id(report_id)
    if report is None:
        abort(404)

        campaign_id = request.args.get('campaign_id') or request.form.get('campaign_id')or request.args.get('campaignID') or request.form.get('campaignID')
        models.set_report_status(report_id, 'Resolved')

    if campaign_id:
        models.set_campaign_flagged(int(campaign_id), True)
        cur = mysql.connection.cursor()
        cur.execute("UPDATE campaign SET status = 'Rejected' WHERE id = %s", (int(campaign_id),))
        mysql.connection.commit()
        cur.close()

    flash('The user report has been marked as resolved', 'success')
    return redirect(url_for('main.admin_dashboard'))


@bp.route('/admin/report/<int:report_id>/dismiss', methods=['GET', 'POST'])
@admin_required
def dismiss_incident_report(report_id):
    report = models.get_report_by_id(report_id)
    if report is None:
        abort(404)

    models.set_report_status(report_id, 'Dismissed')
    flash('The user report is officially dismissed', 'secondary')
    return redirect(url_for('main.admin_dashboard'))


@bp.route('/admin/user/<int:user_id>/toggle-suspension', methods=['GET', 'POST'])
@admin_required
def admin_toggle_user_suspension(user_id):
    if user_id == g.user['id']:
        flash('Security Check: You cannot suspend your own active account session!', 'danger')
        return redirect(url_for('main.admin_dashboard'))

    user = models.get_user_by_id(user_id)
    if user is None:
        abort(404)

    should_suspend_str = request.args.get('is_suspended') or request.form.get('is_suspended') or 'True'
    should_suspend = True if should_suspend_str == 'True' else False

    models.set_user_suspended(user_id, should_suspend)

    if should_suspend:
        flash(f"User account '{user['username']}' has been suspended. User cannot log into account.", 'danger')
    else:
        flash(f"User account '{user['username']}' is successfully reinstated.", 'success')
    return redirect(url_for('main.admin_dashboard'))


@bp.route('/admin/user/<int:user_id>/delete', methods=['GET', 'POST'])
@admin_required
def admin_delete_user_account(user_id):
    if user_id == g.user['id']:
        flash('WARNING: You cannot delete your own admin account!', 'danger')
        return redirect(url_for('main.admin_dashboard'))

    user = models.get_user_by_id(user_id)
    if user is None:
        abort(404)

    models.delete_user(user_id)
    flash(f"User account '{user['username']}' Superchat history is permanently deleted.", "secondary")
    return redirect(url_for('main.admin_dashboard'))


# -------------------- Edit Campaign --------------------

@bp.route('/admin/campaign/<int:campaign_id>/edit', methods=['GET','POST'])
@admin_required
def admin_edit_campaign_details(campaign_id):
    campaign = models.get_campaign_detail(campaign_id)
    if campaign is None:
        abort(404)

    if request.method == 'POST':
        updated_title = request.form.get('title').strip()
        updated_description = request.form.get('description').strip()
        updated_goal = request.form.get('goalAmount').strip()
        updated_category = request.form.get('category').strip()
        updated_start = request.form.get('startDate').strip()
        updated_end = request.form.get('endDate').strip()
        updated_image = request.form.get('campaignImage') or campaign['campaignImage']

        models.update_campaign_details(
            campaign_id, updated_title, updated_description, updated_goal, updated_category, updated_start, updated_end, updated_image
        )
        flash(f"Campaign details for '{updated_title}' is successfully updated.", 'success')
        return redirect(url_for('main.admin_dashboard'))

    return render_template('admin_campaign_edit.html', campaign=campaign)

@bp.route('/admin/user/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_user_details(user_id):
    user = models.get_user_by_id(user_id)
    if user is None:
        abort(404)

    if request.method == 'POST':
        updated_username = request.form.get('username').strip()
        updated_email = request.form.get('email').strip().lower()

        cur = mysql.connection.cursor()
        cur.execute(
            "UPDATE user SET username = %s, email = %s WHERE id = %s",
            (updated_username, updated_email, user_id)
        )
        mysql.connection.commit()
        cur.close()

        flash(f"Account details for '{updated_username}' have been updated successfully.", "success")
        return redirect(url_for('main.admin_dashboard'))

    return render_template('admin_edit_user.html', user=user)
