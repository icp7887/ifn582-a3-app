from flask import Blueprint, render_template, redirect, url_for, session, request
from . import models

bp = Blueprint('main', __name__)


# HOME PAGE

@bp.route('/')
def index():
    campaigns = models.get_all_campaigns()
    return render_template('index.html', campaigns=campaigns)


# ADMIN TEST ROUTE
# This can be deleted later once the admin dashboard is confirmed working.

@bp.route('/admin-dashboard-test')
def admin_dashboard_test():
    pending = models.get_pending_campaigns()
    featured = models.get_featured_campaigns()

    return {
        "pending": pending,
        "featured": featured
    }


# ADMIN DASHBOARD

@bp.route('/admin-dashboard')
def admin_dashboard():

    # Verify user is logged in as Admin
    if session.get('role') != 'Admin':
        return {"error": "Access denied. Admins only."}, 403

    pending = models.get_pending_campaigns()
    featured = models.get_featured_campaigns()
    flagged = models.get_flagged_campaigns()

    return render_template(
        'admin_dashboard.html',
        pending=pending,
        featured=featured,
        flagged=flagged
    )


# ADMIN ACTION ROUTES

@bp.route('/admin/approve/<int:campaign_id>', methods=['POST'])
def approve_campaign(campaign_id):
    models.update_campaign_status(campaign_id, 'Approved')
    return redirect(url_for('main.admin_dashboard'))


@bp.route('/admin/reject/<int:campaign_id>', methods=['POST'])
def reject_campaign(campaign_id):
    models.update_campaign_status(campaign_id, 'Rejected')
    return redirect(url_for('main.admin_dashboard'))


@bp.route('/admin/feature/<int:campaign_id>/<int:status>', methods=['POST'])
def toggle_feature(campaign_id, status):
    models.set_campaign_featured(campaign_id, bool(status))
    return redirect(url_for('main.admin_dashboard'))


@bp.route('/admin/flag/<int:campaign_id>/<int:status>', methods=['POST'])
def toggle_flag(campaign_id, status):
    models.set_campaign_flagged(campaign_id, bool(status))
    return redirect(url_for('main.admin_dashboard'))


# LOGIN

@bp.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        data = request.get_json(silent=True) or request.form

        email = data.get('email')
        password = data.get('password')

        user = models.get_user_by_email(email)

        # NOTE:
        # Password hashing still needs to be handled properly.
        # The assignment requires hashed passwords.

        if user and user.get('password') == password:

            session['user_id'] = user['id']
            session['username'] = user['username']

            # Default to User if the account is not in the Admin table
            session['role'] = user.get('role') or 'User'

            return {
                "message": "Login successful!",
                "user": {
                    "id": user['id'],
                    "username": user['username'],
                    "role": session['role']
                }
            }, 200

        else:
            return {
                "error": "Invalid email or password"
            }, 401

    # GET request
    try:
        return render_template('login.html')

    except:
        return '''
            <form method="POST">
                <h2>Test Login</h2>

                <p>
                    <label>
                        Email:
                        <input type="email" name="email" required>
                    </label>
                </p>

                <p>
                    <label>
                        Password:
                        <input type="password" name="password" required>
                    </label>
                </p>

                <button type="submit">Log In</button>
            </form>
        '''


# LOGOUT

@bp.route('/logout')
def logout():
    session.clear()
    return {
        "message": "Logged out successfully"
    }, 200