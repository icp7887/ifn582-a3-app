import os
import uuid
from datetime import date
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, g, abort, current_app
from . import models
from .forms import LoginForm, RegisterForm, CampaignForm, PostForm,  DonationForm

bp = Blueprint('main', __name__)

# =====================================================================
# AUTH HELPERS (current user + access control decorators)
# =====================================================================

CREATOR_STATUSES = ['Active', 'Paused', 'Closed']   # what a creator may switch between once approved


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
            abort(403)                       # another fundraiser's campaign
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


def role_required(*roles): #e.g. @role_required('Admin') or @role_required('Creator', 'Admin')
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


# def _safe_next(target): #only follow ?next= links that stay on this site
#     if target and target.startswith('/') and not target.startswith('//'):
#         return target
#     return None


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


def _save_image(file): #saves an uploaded image to static/img/uploads/ and returns the path to store in the DB
    if not file or not file.filename:
        return None
    filename = uuid.uuid4().hex + '.' + file.filename.rsplit('.', 1)[-1].lower() #random name, never trust the uploaded one
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
    # Open the creator's newest campaign, or invite them to create their first one
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
    # Creators can only move an approved campaign between Active, Paused and Closed.
    # Pending, Rejected and Suspended are admin decisions, so they cannot be overridden here.
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
    # Read search text and selected category from the URL (e.g. /?search=water or /?category=Arts)
    search = request.args.get('search', '').strip()
    selected_category = request.args.get('category', '').strip()

    # Choose which campaigns to show
    if search:
        campaigns = models.search_campaigns(search)
    elif selected_category:
        campaigns = models.get_campaigns_by_category(selected_category)
    else:
        campaigns = models.get_active_campaigns()

    categories = models.get_categories()
    featured = models.get_featured_active_campaigns()

    # Show only the first few campaigns unless "SHOW ALL" was clicked (/?show=all)
    show_all = request.args.get('show') == 'all'
    total_campaigns = len(campaigns)    # Count before cutting the list
    if not show_all:
        campaigns = campaigns[:HOMEPAGE_CAMPAIGN_LIMIT]

    return render_template(
        'index.html',
        campaigns=campaigns,
        categories=categories,
        featured=featured,                       # Template expects the name 'featured'
        search=search,                           # Shown in the search box and results title
        selected_category=selected_category,     # Highlights the active category button
        total_campaigns=total_campaigns,
        limit=HOMEPAGE_CAMPAIGN_LIMIT,
        show_all=show_all,                       # Template switches between SHOW ALL / SHOW LESS
    )


@bp.route('/campaigns/<int:campaign_id>') #public page; the admin dashboard links here (/campaign/<id> is the creator's own page)
def campaign_detail(campaign_id):
    return redirect(url_for('main.campaign_donation', campaign_id=campaign_id))


# =====================================================================
# DONATION
# =====================================================================

# @bp.route('/donation/01')
# def donation_page():
#     campaign = models.get_campaign_by_id(1)
#     return render_template('donation.html', campaign=campaign)


# @bp.route('/donation/<int:campaign_id>')
# def campaign_donation(campaign_id):
#     campaign = models.get_campaign_by_id(campaign_id)

#     if campaign is None:
#         abort(404)
#     # Pending / Rejected / Suspended campaigns are hidden from the public
#     if campaign['status'] not in ('Active', 'Paused', 'Closed'):
#         is_owner = g.user is not None and g.user['id'] == campaign['creatorID']
#         is_admin = g.user is not None and g.user['role'] == 'Admin'
#         if not (is_owner or is_admin):
#             abort(404)

#     return render_template('donation.html', campaign=campaign)



@bp.route('/donation/<int:campaign_id>')
def campaign_donation(campaign_id):
    campaign = models.get_campaign_detail(campaign_id)  #includes creatorName, raised, etc.
    if campaign is None:
        abort(404)
    form = DonationForm()
    form.set_tiers(models.get_creator_tiers(campaign['creatorID']))
    return render_template('donation.html', campaign=campaign, form=form,
                           tiers=models.get_creator_tiers(campaign['creatorID']),
                           donations=models.get_campaign_donations(campaign_id),
                           posts=models.get_campaign_posts(campaign_id))


@bp.route('/donation/<int:campaign_id>/donate', methods=['POST'])
def donate(campaign_id):
    if g.user is None or g.user['role'] != 'Customer':
        flash('Please log in as a Supporter to donate.', 'warning')
        return redirect(url_for('main.login'))
    campaign = models.get_campaign_detail(campaign_id)
    if campaign is None:
        abort(404)
    form = DonationForm()
    form.set_tiers(models.get_creator_tiers(campaign['creatorID']))
    if form.validate_on_submit():
        models.add_donation(campaign_id, g.user['id'], form.amount.data, form.donor_name.data,
                            form.email.data, form.address.data, form.message.data,
                            form.tier.data or None, form.payment_method.data)
        flash('Thank you for your donation!', 'success')
    else:
        flash('Please fix the donation form and try again.', 'danger')
    return redirect(url_for('main.campaign_donation', campaign_id=campaign_id))


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
        counts=models.get_dashboard_counts(),               #the 4 stat cards
        pending=models.get_all_campaigns_with_creator(),    #Approval of Campaigns (includes creator username)
        campaigns=models.get_all_campaigns_with_details(),  #Campaign Management (includes amount raised)
        statuses=CAMPAIGN_STATUSES,
        users=models.get_all_users(),                       #User Management
        reports=models.get_open_reports(),                  #Flagged Content
        reviewed_reports=models.get_reviewed_reports(),
        featured_options=models.get_active_campaigns(),     #Featured Campaigns checkboxes (Active only)
    )


#admin action routes
@bp.route('/admin/approve/<int:campaign_id>', methods=['POST']) #approve campaign #<int:campaign_id> captures the campaign ID from the URL and passes it to the function as an integer parameter.
@admin_required
def approve_campaign(campaign_id):
    models.update_campaign_status(campaign_id, 'Active') #approved campaigns go live on the homepage
    flash('Campaign approved.', 'success')
    return redirect(url_for('main.admin_dashboard', _anchor='approval'))


@bp.route('/admin/reject/<int:campaign_id>', methods=['POST']) #reject campaign
@admin_required
def reject_campaign(campaign_id):
    models.update_campaign_status(campaign_id, 'Rejected')
    flash('Campaign rejected.', 'secondary')
    return redirect(url_for('main.admin_dashboard', _anchor='approval'))


@bp.route('/admin/status/<int:campaign_id>', methods=['POST']) #change status / suspend / reinstate from Campaign Management
@admin_required
def admin_set_campaign_status(campaign_id):
    status = request.form.get('status')
    if status not in CAMPAIGN_STATUSES:
        abort(400)
    models.update_campaign_status(campaign_id, status)
    flash('Campaign status set to ' + status + '.', 'success')
    return redirect(url_for('main.admin_dashboard', _anchor='campaigns'))


@bp.route('/admin/feature/<int:campaign_id>/<int:status>', methods=['POST']) #toggle featured status
@admin_required
def toggle_feature(campaign_id, status):
    # Pass status (1 for True, 0 for False)
    models.set_campaign_featured(campaign_id, bool(status))
    return redirect(url_for('main.admin_dashboard'))


@bp.route('/admin/featured', methods=['POST']) #save the Featured Campaigns checkboxes
@admin_required
def admin_set_featured():
    ids = [int(i) for i in request.form.getlist('featured') if i.isdigit()]
    models.set_featured_campaigns(ids)
    flash('Featured campaigns updated.', 'success')
    return redirect(url_for('main.admin_dashboard', _anchor='featured'))


@bp.route('/admin/flag/<int:campaign_id>/<int:status>', methods=['POST']) #toggle flagged status
@admin_required
def toggle_flag(campaign_id, status):
    # Pass status (1 for True, 0 for False)
    models.set_campaign_flagged(campaign_id, bool(status))
    return redirect(url_for('main.admin_dashboard'))


@bp.route('/admin/create', methods=['POST']) #add a new campaign from the create campaign form on the admin dashboard.
@admin_required
def admin_create_campaign():
  #request.form holds values typed into the form, looked up by name attribute in the form fields.
    models.create_campaign(
            request.form['title'],
            request.form['goalAmount'],
            request.form['startDate'],
            request.form['endDate'],
            request.form['creatorID'],
            request.form['category'],
            request.form.get('campaignImage') or None #image is optional, so a empty box is saved as NULL
        )
    return redirect(url_for('main.admin_dashboard'))  #redirects the user back to the admin dashboard after successfully creating a new campaign.

@bp.route('/admin/delete/<int:campaign_id>', methods=['POST']) #delete campaign
@admin_required
def admin_delete_campaign(campaign_id):
    models.delete_campaign(campaign_id)
    flash('Campaign deleted.', 'secondary')
    return redirect(url_for('main.admin_dashboard', _anchor='campaigns'))


@bp.route('/admin/report/<int:report_id>/<action>', methods=['POST']) #dismiss a report, or suspend / remove the reported campaign
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
        models.delete_campaign(report['campaignID']) #ON DELETE CASCADE removes the report too
    else:
        abort(400)
    flash('Report reviewed.', 'success')
    return redirect(url_for('main.admin_dashboard', _anchor='reports'))


@bp.route('/admin/user/<int:user_id>/edit') #Edit button in User Management
@admin_required
def admin_edit_user(user_id):
    flash('Editing user details is not built yet.', 'info')
    return redirect(url_for('main.admin_dashboard', _anchor='users'))


@bp.route('/admin/user/<int:user_id>/suspend', methods=['POST']) #suspend or reinstate a user
@admin_required
def admin_suspend_user(user_id):
    if user_id == g.user['id']: # Prevent admin from suspending their own account
        flash('You cannot suspend your own account.', 'danger')
    else:
        suspend = request.form.get('suspend') == '1'
        models.set_user_suspended(user_id, suspend)
        flash('User suspended.' if suspend else 'User reinstated.', 'success')
    return redirect(url_for('main.admin_dashboard', _anchor='users'))


@bp.route('/admin/delete_user/<int:user_id>', methods=['POST']) #delete user
@admin_required
def admin_delete_user(user_id):
    if user_id == g.user['id']: # Prevent admin from deleting their own account
        flash('You cannot delete your own account.', 'danger')
    else:
        models.delete_user(user_id)
        flash('User deleted.', 'secondary')
    return redirect(url_for('main.admin_dashboard', _anchor='users'))
