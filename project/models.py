from . import mysql


# =====================================================================
# HOMEPAGE (campaign list, search, categories, featured)
# =====================================================================

# Active campaigns with creator name and total raised, featured first
_ACTIVE_CAMPAIGNS = """
    SELECT c.*, u.username AS creatorName, COALESCE(SUM(d.amount), 0) AS raised
    FROM campaign c
    JOIN user u ON u.id = c.creatorID
    LEFT JOIN donation d ON d.campaignID = c.id AND d.status = 'Done'
    WHERE c.status = 'Active'
"""
_ACTIVE_ORDER = " GROUP BY c.id, u.username ORDER BY c.isFeatured DESC, c.startDate DESC, c.id DESC"


def get_active_campaigns():
    cur = mysql.connection.cursor()
    cur.execute(_ACTIVE_CAMPAIGNS + _ACTIVE_ORDER)
    rows = cur.fetchall()
    cur.close()
    return rows


def search_campaigns(search):
    # Matches campaign title, category or creator name
    like = '%' + search + '%'
    cur = mysql.connection.cursor()
    cur.execute(
        _ACTIVE_CAMPAIGNS + " AND (c.title LIKE %s OR c.category LIKE %s OR u.username LIKE %s)" + _ACTIVE_ORDER,
        (like, like, like)
    )
    results = cur.fetchall()
    cur.close()
    return results


def get_campaigns_by_category(category):
    cur = mysql.connection.cursor()
    cur.execute(_ACTIVE_CAMPAIGNS + " AND c.category = %s" + _ACTIVE_ORDER, (category,))
    results = cur.fetchall()
    cur.close()
    return results


def get_categories():
    cur = mysql.connection.cursor()
    cur.execute("SELECT DISTINCT category FROM campaign WHERE status = 'Active' ORDER BY category")
    results = cur.fetchall()
    cur.close()
    return results


def get_featured_active_campaigns():
    # Featured campaigns with the creator's photo and tagline for the homepage cards
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT c.*, u.username AS creatorName, cr.tagline AS creatorTagline, cr.profileImage AS creatorImage
        FROM campaign c
        JOIN user u ON u.id = c.creatorID
        JOIN creator cr ON cr.id = c.creatorID
        WHERE c.status = 'Active' AND c.isFeatured = TRUE
        ORDER BY c.id
    """)
    rows = cur.fetchall()
    cur.close()
    return rows


# =====================================================================
# CAMPAIGN (general lookups)
# =====================================================================


# CAMPAIGN DETAIL PAGE

def get_campaign_detail(campaign_id):
    # One campaign with its creator's profile, total raised and number of supporters
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT c.*, u.username AS creatorName, cr.bio AS creatorBio, cr.verifiedStatus AS creatorVerified,
               COALESCE(SUM(d.amount), 0) AS raised,
               COUNT(DISTINCT d.customerID) AS supporterCount,
               COUNT(d.transactionID) AS donationCount
        FROM campaign c
        JOIN user u ON u.id = c.creatorID
        JOIN creator cr ON cr.id = c.creatorID
        LEFT JOIN donation d ON d.campaignID = c.id AND d.status = 'Done'
        WHERE c.id = %s
        GROUP BY c.id, u.username, cr.bio, cr.verifiedStatus
    """, (campaign_id,))
    row = cur.fetchone()
    cur.close()


# CREATOR DASHBOARD

def get_creator_campaigns(creator_id):
    # Every campaign owned by this creator, newest first, with the amount raised so far
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT c.*, COALESCE(SUM(d.amount), 0) AS raised
        FROM campaign c
        LEFT JOIN donation d ON d.campaignID = c.id AND d.status = 'Done'
        WHERE c.creatorID = %s
        GROUP BY c.id
        ORDER BY c.id DESC
    """, (creator_id,))
    rows = cur.fetchall()
    cur.close()
    return rows

def get_campaign_stats(campaign_id):
    # Statistics worked out from the donation table every time the page loads
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT COUNT(*) AS donations,
               COUNT(DISTINCT customerID) AS supporters,
               COALESCE(SUM(amount), 0) AS raised,
               COALESCE(AVG(amount), 0) AS average,
               COALESCE(MAX(amount), 0) AS largest,
               COALESCE(SUM(CASE WHEN transactionDate BETWEEN NOW() - INTERVAL 7 DAY AND NOW() THEN amount END), 0) AS last7days,
               MAX(transactionDate) AS lastDonation
        FROM donation
        WHERE campaignID = %s AND status = 'Done'
    """, (campaign_id,))
    stats = cur.fetchone()
    cur.execute("""
        SELECT COALESCE(t.tierName, 'One-off') AS tier, COUNT(*) AS donations, SUM(d.amount) AS total
        FROM donation d
        LEFT JOIN subscriptionTier t ON t.id = d.tierID
        WHERE d.campaignID = %s AND d.status = 'Done'
        GROUP BY tier
        ORDER BY total DESC
    """, (campaign_id,))
    stats['by_tier'] = cur.fetchall()
    cur.close()
    return stats

def create_creator_campaign(creator_id, title, description, goal_amount, category, start_date, end_date, image):
    # New campaigns start as Pending, so an admin has to approve them before they are public
    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO campaign (title, description, goalAmount, status, campaignImage, startDate, endDate,
                              isFeatured, isFlagged, creatorID, category)
        VALUES (%s, %s, %s, 'Pending', %s, %s, %s, FALSE, FALSE, %s, %s)
    """, (title, description, goal_amount, image, start_date, end_date, creator_id, category))
    mysql.connection.commit()
    new_id = cur.lastrowid
    cur.close()
    return new_id

def update_campaign_details(campaign_id, title, description, goal_amount, category, start_date, end_date, image):
    # Status is not changed here: approval/rejection/suspension stay with the admin
    cur = mysql.connection.cursor()
    cur.execute("""
        UPDATE campaign
        SET title = %s, description = %s, goalAmount = %s, category = %s,
            startDate = %s, endDate = %s, campaignImage = %s
        WHERE id = %s
    """, (title, description, goal_amount, category, start_date, end_date, image, campaign_id))
    mysql.connection.commit()
    cur.close()

def get_post(post_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM campaign_post WHERE id = %s", (post_id,))
    row = cur.fetchone()
    cur.close()
    return row

def add_post(campaign_id, title, content, image):
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO campaign_post (campaignID, title, content, postImage, postDate) VALUES (%s, %s, %s, %s, CURDATE())",
                (campaign_id, title, content, image))
    mysql.connection.commit()
    cur.close()

def update_post(post_id, title, content, image):
    cur = mysql.connection.cursor()
    cur.execute("UPDATE campaign_post SET title = %s, content = %s, postImage = %s WHERE id = %s",
                (title, content, image, post_id))
    mysql.connection.commit()
    cur.close()

def delete_post(post_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM campaign_post WHERE id = %s", (post_id,))
    mysql.connection.commit()
    cur.close()


# =====================================================================
# ADMIN FETCH FUNCTIONS
# =====================================================================


# =====================================================================
# ADMIN ACTION FUNCTIONS
# =====================================================================

def update_campaign_status(campaign_id, new_status):
    # Update campaign status to Approved or Rejected
    cur = mysql.connection.cursor()
    cur.execute(
        "UPDATE campaign SET status = %s WHERE id = %s",
        (new_status, campaign_id)
    )
    mysql.connection.commit()
    cur.close()


# =====================================================================
# USERS + AUTH
# =====================================================================

#a user's role comes from which table they are in: admin, creator, or customer (Supporter)
_USER_WITH_ROLE = """
    SELECT
        u.id, u.username, u.password, u.email, u.isSuspended,
        CASE WHEN a.id IS NOT NULL THEN 'Admin'
             WHEN cr.id IS NOT NULL THEN 'Creator'
             ELSE 'Customer' END AS role,
        a.accessLevel,
        cr.verifiedStatus
    FROM user u
    LEFT JOIN admin a ON a.id = u.id
    LEFT JOIN creator cr ON cr.id = u.id
"""


def get_user_for_login(identifier): #login accepts either the username or the email
    cur = mysql.connection.cursor()
    cur.execute(_USER_WITH_ROLE + " WHERE u.username = %s OR u.email = %s", (identifier, identifier))
    user = cur.fetchone()
    cur.close()
    return user


def get_user_by_id(user_id): #used on every request to load the logged-in user into g.user
    cur = mysql.connection.cursor()
    cur.execute(_USER_WITH_ROLE + " WHERE u.id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()
    return user


def username_or_email_taken(username, email):
    cur = mysql.connection.cursor()
    cur.execute("SELECT username, email FROM user WHERE username = %s OR email = %s", (username, email))
    rows = cur.fetchall()
    cur.close()
    return {
        'username': any(r['username'].lower() == username.lower() for r in rows),
        'email': any(r['email'].lower() == email.lower() for r in rows),
    }


def create_user(username, email, password_hash, role): #adds the user row plus their creator or customer row in one transaction
    cur = mysql.connection.cursor()
    try:
        cur.execute("INSERT INTO user (username, password, email) VALUES (%s, %s, %s)", (username, password_hash, email))
        user_id = cur.lastrowid
        if role == 'Creator':
            cur.execute("INSERT INTO creator (id, verifiedStatus) VALUES (%s, FALSE)", (user_id,)) #new creators start unverified
        else:
            cur.execute("INSERT INTO customer (id) VALUES (%s)", (user_id,))
        mysql.connection.commit()
    except Exception:
        mysql.connection.rollback()
        raise
    finally:
        cur.close()
    return user_id


def get_all_users(): #for the admin User Management section
    cur = mysql.connection.cursor()
    cur.execute(_USER_WITH_ROLE + " ORDER BY role, u.username")
    rows = cur.fetchall()
    cur.close()
    return rows


def set_user_suspended(user_id, is_suspended): #suspended users cannot log in
    cur = mysql.connection.cursor()
    cur.execute("UPDATE user SET isSuspended = %s WHERE id = %s", (is_suspended, user_id))
    mysql.connection.commit()
    cur.close()


# =====================================================================
# ADMIN DASHBOARD + CAMPAIGN / USER MANAGEMENT
# =====================================================================

def get_dashboard_counts(): #counts for the 4 stat cards at the top of the admin page (Pending, Active, Flagged Items, Users)
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT 
            SUM(status = 'Pending') AS pending, 
            SUM(status = 'Active') AS active
        FROM campaign
    """)
    counts = cur.fetchone()
    cur.execute("SELECT COUNT(*) AS reports FROM report WHERE status = 'Open'") #open reports are the "Flagged Items"
    counts['reports'] = cur.fetchone()['reports']
    cur.execute("SELECT COUNT(*) AS users, SUM(isSuspended) AS suspended FROM user")
    counts.update(cur.fetchone())
    cur.close()
    return {key: int(value or 0) for key, value in counts.items()} #SUM() returns None on an empty table and a Decimal otherwise, so convert every value to a plain whole number

def get_all_campaigns_with_creator(): #for the Approval of Campains section: pending campaigns plus the creator's username for each card
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT 
            c.*, c.title, c.category, u.username AS creatorName
        FROM campaign c
        JOIN user u ON c.creatorID = u.id
        WHERE c.status = 'Pending'
    """)
    rows = cur.fetchall()
    cur.close()
    return rows

def get_all_campaigns_with_details(): #for the Campaign Management and Featured sections: every campaign plus the creator's username and the amount raised
    cur = mysql.connection.cursor()
    #JOIN user gets the creator's username
    #LEFT JOIN donation keeps camapaigns with no donations (they show 0 raised). Only donations with status 'Done' are counted 
    cur.execute("""
        SELECT 
            c.*,
            u.username AS creatorName,
            COALESCE(SUM(d.amount), 0) AS amountRaised
        FROM campaign c
        JOIN user u ON c.creatorID = u.id
        LEFT JOIN donation d ON d.campaignID = c.id AND d.status = 'Done'
        GROUP BY c.id, u.username
        ORDER BY c.id
    """)
    rows = cur.fetchall()
    cur.close()
    return rows


def delete_campaign(campaign_id): #deletes a campaigN. ON DELETE CASCADE in the database schema ensures that all related donations are also deleted when a campaign is removed.
  cur = mysql.connection.cursor()
  cur.execute("DELETE FROM campaign WHERE id = %s", (campaign_id,))
  mysql.connection.commit() #save changes to the database
  cur.close()   

def delete_user(user_id): #deletes a user. ON DELETE CASCADE also deletes thier creator/customer/admin row and, for a creator, all thier campaigns, tiers and the donationa to those campaiagns
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM user WHERE id = %s", (user_id,))
    mysql.connection.commit() #save changes to the database
    cur.close()


# =====================================================================
# ADMIN REPORTS + FEATURED
# =====================================================================

_REPORTS = """
    SELECT r.*, c.title AS campaignTitle, c.status AS campaignStatus, u.username AS reporterName
    FROM report r
    JOIN campaign c ON c.id = r.campaignID
    LEFT JOIN user u ON u.id = r.reporterID
"""


def get_open_reports():
    cur = mysql.connection.cursor()
    cur.execute(_REPORTS + " WHERE r.status = 'Open' ORDER BY r.reportedAt")
    rows = cur.fetchall()
    cur.close()
    return rows


def get_reviewed_reports(limit=5):
    cur = mysql.connection.cursor()
    cur.execute(_REPORTS + " WHERE r.status <> 'Open' ORDER BY r.reviewedAt DESC LIMIT %s", (limit,))
    rows = cur.fetchall()
    cur.close()
    return rows


def get_report_by_id(report_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM report WHERE id = %s", (report_id,))
    row = cur.fetchone()
    cur.close()
    return row


def set_report_status(report_id, status): #Resolved or Dismissed
    cur = mysql.connection.cursor()
    cur.execute("UPDATE report SET status = %s, reviewedAt = NOW() WHERE id = %s", (status, report_id))
    mysql.connection.commit()
    cur.close()


def set_featured_campaigns(campaign_ids): #only the ticked Active campaigns stay featured
    cur = mysql.connection.cursor()
    cur.execute("UPDATE campaign SET isFeatured = FALSE")
    if campaign_ids:
        placeholders = ', '.join(['%s'] * len(campaign_ids))
        cur.execute("UPDATE campaign SET isFeatured = TRUE WHERE status = 'Active' AND id IN (" + placeholders + ")", tuple(campaign_ids))
    mysql.connection.commit()
    cur.close()


# =====================================================================
# CREATOR DASHBOARD (own campaigns, stats, donations, posts)
# =====================================================================

def get_campaign_detail(campaign_id):
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT c.*, u.username AS creatorName, cr.bio AS creatorBio, cr.verifiedStatus AS creatorVerified,
               COALESCE(SUM(d.amount), 0) AS raised,
               COUNT(DISTINCT d.customerID) AS supporterCount,
               COUNT(d.transactionID) AS donationCount
        FROM campaign c
        JOIN user u ON u.id = c.creatorID
        JOIN creator cr ON cr.id = c.creatorID
        LEFT JOIN donation d ON d.campaignID = c.id AND d.status = 'Done'
        WHERE c.id = %s
        GROUP BY c.id, u.username, cr.bio, cr.verifiedStatus
    """, (campaign_id,))
    row = cur.fetchone()
    cur.close()
    return row


def get_creator_campaigns(creator_id):
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT c.*, COALESCE(SUM(d.amount), 0) AS raised
        FROM campaign c
        LEFT JOIN donation d ON d.campaignID = c.id AND d.status = 'Done'
        WHERE c.creatorID = %s
        GROUP BY c.id
        ORDER BY c.id DESC
    """, (creator_id,))
    rows = cur.fetchall()
    cur.close()
    return rows


def create_creator_campaign(creator_id, title, description, goal_amount, category, start_date, end_date, image):
    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO campaign (title, description, goalAmount, status, campaignImage, startDate, endDate,
                              isFeatured, isFlagged, creatorID, category)
        VALUES (%s, %s, %s, 'Pending', %s, %s, %s, FALSE, FALSE, %s, %s)
    """, (title, description, goal_amount, image, start_date, end_date, creator_id, category))
    mysql.connection.commit()
    new_id = cur.lastrowid
    cur.close()
    return new_id


def update_campaign_details(campaign_id, title, description, goal_amount, category, start_date, end_date, image):
    cur = mysql.connection.cursor()
    cur.execute("""
        UPDATE campaign
        SET title = %s, description = %s, goalAmount = %s, category = %s,
            startDate = %s, endDate = %s, campaignImage = %s
        WHERE id = %s
    """, (title, description, goal_amount, category, start_date, end_date, image, campaign_id))
    mysql.connection.commit()
    cur.close()


def get_campaign_stats(campaign_id):
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT COUNT(*) AS donations,
               COUNT(DISTINCT customerID) AS supporters,
               COALESCE(SUM(amount), 0) AS raised,
               COALESCE(AVG(amount), 0) AS average,
               COALESCE(MAX(amount), 0) AS largest,
               COALESCE(SUM(CASE WHEN transactionDate BETWEEN NOW() - INTERVAL 7 DAY AND NOW() THEN amount END), 0) AS last7days,
               MAX(transactionDate) AS lastDonation
        FROM donation
        WHERE campaignID = %s AND status = 'Done'
    """, (campaign_id,))
    stats = cur.fetchone()
    cur.execute("""
        SELECT COALESCE(t.tierName, 'One-off') AS tier, COUNT(*) AS donations, SUM(d.amount) AS total
        FROM donation d
        LEFT JOIN subscriptionTier t ON t.id = d.tierID
        WHERE d.campaignID = %s AND d.status = 'Done'
        GROUP BY tier
        ORDER BY total DESC
    """, (campaign_id,))
    stats['by_tier'] = cur.fetchall()
    cur.close()
    return stats


def get_campaign_donations(campaign_id, limit=10):
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT d.*, t.tierName
        FROM donation d
        LEFT JOIN subscriptionTier t ON t.id = d.tierID
        WHERE d.campaignID = %s AND d.status = 'Done'
        ORDER BY d.transactionID DESC
        LIMIT %s
    """, (campaign_id, limit))
    rows = cur.fetchall()
    cur.close()
    return rows


def get_campaign_posts(campaign_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM campaign_post WHERE campaignID = %s ORDER BY postDate DESC, id DESC", (campaign_id,))
    rows = cur.fetchall()
    cur.close()
    return rows


def get_post(post_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM campaign_post WHERE id = %s", (post_id,))
    row = cur.fetchone()
    cur.close()
    return row


def add_post(campaign_id, title, content, image):
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO campaign_post (campaignID, title, content, postImage, postDate) VALUES (%s, %s, %s, %s, CURDATE())",
                (campaign_id, title, content, image))
    mysql.connection.commit()
    cur.close()


def update_post(post_id, title, content, image):
    cur = mysql.connection.cursor()
    cur.execute("UPDATE campaign_post SET title = %s, content = %s, postImage = %s WHERE id = %s",
                (title, content, image, post_id))
    mysql.connection.commit()
    cur.close()


def delete_post(post_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM campaign_post WHERE id = %s", (post_id,))
    mysql.connection.commit()
    cur.close()


def get_creator_tiers(creator_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM subscriptionTier WHERE creatorID = %s ORDER BY price", (creator_id,))
    rows = cur.fetchall()
    cur.close()
    return rows


def add_donation(campaign_id, customer_id, amount, name, email, address, message, tier_id, payment):
    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO donation (amount, donorName, donorEmail, donorAddress, message, tierID,
                              paymentNetwork, status, customerID, campaignID)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'Done', %s, %s)
    """, (amount, name, email, address, message, tier_id, payment, customer_id, campaign_id))
    mysql.connection.commit()
    cur.close()

# =====================================================================
# ADMIN: EDIT USER
# =====================================================================

def taken_by_other_user(username, email, user_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM user WHERE (username = %s OR email = %s) AND id != %s", (username, email, user_id))
    row = cur.fetchone()
    cur.close()
    return row is not None


def update_user_details(user_id, username, email):
    cur = mysql.connection.cursor()
    cur.execute("UPDATE user SET username = %s, email = %s WHERE id = %s", (username, email, user_id))
    mysql.connection.commit()
    cur.close()


def set_creator_verified(user_id, verified):
    cur = mysql.connection.cursor()
    cur.execute("UPDATE creator SET verifiedStatus = %s WHERE id = %s", (verified, user_id))
    mysql.connection.commit()
    cur.close()
