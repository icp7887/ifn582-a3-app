from . import mysql


# CAMPAIGN FETCH FUNCTIONS

# Active campaigns with creator name and total raised, featured first
_ACTIVE_CAMPAIGNS = """
    SELECT c.*, u.username AS creatorName, COALESCE(SUM(d.amount), 0) AS raised
    FROM campaign c
    JOIN user u ON u.id = c.creatorID
    LEFT JOIN donation d ON d.campaignID = c.id AND d.status = 'Done'
    WHERE c.status = 'Active'
"""
_ACTIVE_ORDER = " GROUP BY c.id, u.username ORDER BY c.isFeatured DESC, c.startDate DESC, c.id DESC"


def get_all_campaigns():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM Campaign")
    rows = cur.fetchall()
    cur.close()
    return rows

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

def get_campaign_by_id(campaign_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM Campaign WHERE id = %s", (campaign_id,))
    row = cur.fetchone()
    cur.close()
    return row

def get_featured_campaigns():
    # Fetch all campaigns with isFeatured set to TRUE
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM campaign WHERE isFeatured = TRUE")
    rows = cur.fetchall()
    cur.close()
    return rows


# ADMIN FETCH FUNCTIONS

def get_pending_campaigns():
    # Fetch all campaigns with status 'Pending'
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM campaign WHERE status = 'Pending'")
    rows = cur.fetchall()
    cur.close()
    return rows


def get_featured_campaigns():
    # Fetch all campaigns with isFeatured set to TRUE
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM campaign WHERE isFeatured = TRUE")
    rows = cur.fetchall()
    cur.close()
    return rows


def get_flagged_campaigns():
    # Fetch all campaigns with isFlagged set to TRUE
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM campaign WHERE isFlagged = TRUE")
    rows = cur.fetchall()
    cur.close()
    return rows


# ADMIN ACTION FUNCTIONS

def update_campaign_status(campaign_id, new_status):
    # Update campaign status to Approved or Rejected
    cur = mysql.connection.cursor()
    cur.execute(
        "UPDATE campaign SET status = %s WHERE id = %s",
        (new_status, campaign_id)
    )
    mysql.connection.commit()
    cur.close()


def set_campaign_featured(campaign_id, is_featured):
    # Update campaign featured status to True or False
    cur = mysql.connection.cursor()
    cur.execute(
        "UPDATE campaign SET isFeatured = %s WHERE id = %s",
        (is_featured, campaign_id)
    )
    mysql.connection.commit()
    cur.close()


def set_campaign_flagged(campaign_id, is_flagged):
    # Update campaign flagged status to True or False
    cur = mysql.connection.cursor()
    cur.execute(
        "UPDATE campaign SET isFlagged = %s WHERE id = %s",
        (is_flagged, campaign_id)
    )
    mysql.connection.commit()
    cur.close()


# USER FETCH FUNCTIONS

def get_user_by_email(email):
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT 
            u.id, 
            u.username, 
            u.password, 
            u.email, 
            a.accessLevel AS role
        FROM user u
        LEFT JOIN admin a ON u.id = a.id
        WHERE u.email = %s
    """, (email,))
    user = cur.fetchone()
    cur.close()
    return user


def get_user_by_id(user_id):
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT * FROM user WHERE id = %s",
        (user_id,)
    )
    user = cur.fetchone()
    cur.close()
    return user

def get_categories():
    cur = mysql.connection.cursor()
    cur.execute("SELECT DISTINCT category FROM campaign ORDER BY category")
    results = cur.fetchall()
    cur.close()
    return results

def get_featured_campaigns():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM campaign WHERE isFeatured = TRUE")
    results = cur.fetchall()
    cur.close()
    return results

def get_campaign_by_id(campaign_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM campaign WHERE id = %s", (campaign_id,))
    campaign = cur.fetchone()
    cur.close()
    return campaign

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
