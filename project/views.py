from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from .forms import ItemForm
from . import models

bp = Blueprint('main', __name__)


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

@bp.route('/donation.html')
def donation_page():
    return render_template('donation.html')


@bp.route('/donation/<int:campaign_id>')
def campaign_donation(campaign_id):
    campaign = models.get_campaign_by_id(campaign_id)

    if campaign is None:
        return "Campaign not found", 404

    return render_template('donation.html', campaign=campaign)


# =====================================================================
# ITEMS
# =====================================================================

@bp.route('/add', methods=['GET', 'POST'])
def add():
    form = ItemForm()
    if form.validate_on_submit():
        models.add_item(form.name.data, form.description.data)
        flash('Item added.')
        return redirect(url_for('main.index'))
    return render_template('add.html', form=form)


# =====================================================================
# ADMIN
# =====================================================================

#this is just a test route, delete later. It is used to verify that the admin dashboard fetch functions are working without the front-end.#
@bp.route('/admin-dashboard-test')
def admin_dashboard_test():
    pending = models.get_pending_campaigns()
    featured = models.get_featured_campaigns()
    return {"pending": pending, "featured": featured}


#admin dashboard url route
@bp.route('/admin-dashboard')
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


# =====================================================================
# LOGIN / LOGOUT
# =====================================================================

#login route
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json(silent=True) or request.form #get_json(silent=True) attempts to parse the incoming request data as JSON. If the request does not contain valid JSON, it returns None instead of raising an error. This is useful for handling cases where the client might send form data instead of JSON.
        email = data.get('email')
        password = data.get('password')

        user = models.get_user_by_email(email)

        #note for team meeting - ask wether we should implement password hashing or use plain-text for demo purposes. If we implement password hashing, we will need to modify the login function to check the hashed password instead of plain-text. This would involve using a library like bcrypt or werkzeug.security to hash the password when creating a user and then verifying the hash during login.

        # Check plain-text password against passwordHASH column
        if user and user.get('password') == password:
            session['user_id'] = user['id']
            session['username'] = user['username']
            # Fallback to 'User' if the account is not in the admin table
            session['role'] = user.get('role') or 'User' #defaults to 'User' if the account is not in the admin table, ensuring that every logged-in user has a role assigned in the session.

            return {
                "message": "Login successful!",
                "user": {
                    "id": user['id'],
                    "username": user['username'],
                    "role": session['role']
                }
            }, 200 # HTTP status code 200 indicates that the request was successful and the server has returned the requested data. In this case, it confirms that the login was successful and provides user details in the response.
        else:
            return {"error": "Invalid email or password"}, 401 # HTTP status code 401 indicates that the request has not been applied because it lacks valid authentication credentials for the target resource. In this case, it informs the client that the provided email or password is incorrect, preventing unauthorized access.

    # If the request method is GET, render the login page. If rendering fails (e.g., template not found), return a simple HTML form as a fallback. change if necessary to match front-end framework. This is a temporary solution for testing purposes and should be replaced with proper error handling and user feedback in a production environment.
    try:
        return render_template('login.html')
    except:
        return '''
            <form method="POST">
                <h2>Test Login</h2>
                <p><label>Email: <input type="email" name="email" required></label></p>
                <p><label>Password: <input type="password" name="password" required></label></p>
                <button type="submit">Log In</button>
            </form>
        '''


#logout route
@bp.route('/logout')
def logout():
    session.clear()  # Clear all session data
    return {"message": "Logged out successfully"}, 200
