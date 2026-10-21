from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, g, abort
from . import models
from .forms import LoginForm, RegisterForm

bp = Blueprint('main', __name__)


# =====================================================================
# AUTH HELPERS (current user + access control decorators)
# =====================================================================

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
                    default = url_for('main.admin_dashboard')
                else:
                    default = url_for('main.index')
                return redirect(_safe_next(request.args.get('next')) or default)
        else:
            flash('Invalid username/email or password.', 'danger')

    return render_template('login.html', form=form, test_accounts=[])


@bp.route('/logout', methods=['POST']) #POST + CSRF token so other sites can't log you out
def logout():
    session.clear()  # Clear all session data
    flash('You have been logged out.', 'secondary')
    return redirect(url_for('main.index'))


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


# =====================================================================
# DONATION
# =====================================================================

@bp.route('/donation/01')
def donation_page():
    campaign = models.get_campaign_by_id(1)
    return render_template('donation.html', campaign=campaign)


@bp.route('/donation/<int:campaign_id>')
def campaign_donation(campaign_id):
    campaign = models.get_campaign_by_id(campaign_id)

    if campaign is None:
        abort(404)
    # Pending / Rejected / Suspended campaigns are hidden from the public
    if campaign['status'] not in ('Active', 'Paused', 'Closed'):
        is_owner = g.user is not None and g.user['id'] == campaign['creatorID']
        is_admin = g.user is not None and g.user['role'] == 'Admin'
        if not (is_owner or is_admin):
            abort(404)

    return render_template('donation.html', campaign=campaign)


@bp.route('/campaign/<int:campaign_id>') #the admin dashboard links here
def campaign_detail(campaign_id):
    return redirect(url_for('main.campaign_donation', campaign_id=campaign_id))

@bp.route('/donation')
def donation():
    return render_template('donation.html')


# =====================================================================
# CREATOR
# =====================================================================

@bp.route('/creator') #creator dashboard (linked from the nav for Creator accounts)
@creator_required
def campaign():
    flash('The creator dashboard is not built yet.', 'info')
    return redirect(url_for('main.index'))


# =====================================================================
# ADMIN (every route here is Admin only)
# =====================================================================

CAMPAIGN_STATUSES = ['Pending', 'Active', 'Paused', 'Closed', 'Rejected', 'Suspended']

#this is just a test route, delete later. It is used to verify that the admin dashboard fetch functions are working without the front-end.#
@bp.route('/admin-dashboard-test')
@admin_required
def admin_dashboard_test():
    pending = models.get_pending_campaigns()
    featured = models.get_featured_campaigns()
    return {"pending": pending, "featured": featured}


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
