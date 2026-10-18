from flask import Blueprint, render_template, redirect, url_for, session, request
from . import models
from .forms import LoginForm

bp = Blueprint('main', __name__)


@bp.route('/')
def index():

    return render_template('index.html')

@bp.route('/donation')
def donation():

    return render_template('donation.html')


@bp.route('/register')
def register():

    return render_template('register.html')



#admin dashboard url route
@bp.route('/admin')
def admin_dashboard():
    # Verify user is logged in as Admin
    # If the user is not logged in or does not have the 'Admin' role, return a 403 Forbidden response with an error message.
    if session.get('role') != 'Admin':
        return {"error": "Access denied. Admins only."}, 403
    pending = models.get_pending_campaigns()
    featured = models.get_featured_campaigns()
    flagged = models.get_flagged_campaigns()
    
    return render_template(
        'admin_dashboard.html',  #renders the admin_dashboard.html template and passes the fetched campaign data to it for display.
        pending=pending, 
        featured=featured, 
        flagged=flagged
    )

#admin action routes
@bp.route('/admin/approve/<int:campaign_id>', methods=['POST']) #approve campaign #<int:campaign_id> captures the campaign ID from the URL and passes it to the function as an integer parameter.
def approve_campaign(campaign_id):
    models.update_campaign_status(campaign_id, 'Approved')
    return redirect(url_for('main.admin_dashboard'))

@bp.route('/admin/reject/<int:campaign_id>', methods=['POST']) #reject campaign
def reject_campaign(campaign_id):
    models.update_campaign_status(campaign_id, 'Rejected')
    return redirect(url_for('main.admin_dashboard'))

@bp.route('/admin/feature/<int:campaign_id>/<int:status>', methods=['POST']) #toggle featured status
def toggle_feature(campaign_id, status):
    # Pass status (1 for True, 0 for False)
    models.set_campaign_featured(campaign_id, bool(status))
    return redirect(url_for('main.admin_dashboard'))

@bp.route('/admin/flag/<int:campaign_id>/<int:status>', methods=['POST']) #toggle flagged status
def toggle_flag(campaign_id, status):
    # Pass status (1 for True, 0 for False)
    models.set_campaign_flagged(campaign_id, bool(status))
    return redirect(url_for('main.admin_dashboard'))


#login route
@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    return render_template('login.html', form=form, test_accounts=[])
  



#logout route
@bp.route('/logout')
def logout():
    session.clear()  # Clear all session data
    return {"message": "Logged out successfully"}, 200