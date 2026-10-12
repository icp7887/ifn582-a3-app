from . import mysql


# CAMPAIGN FETCH FUNCTIONS

def get_all_campaigns():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM Campaign")
    rows = cur.fetchall()
    cur.close()
    return rows


def get_campaign_by_id(campaign_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM Campaign WHERE id = %s", (campaign_id,))
    row = cur.fetchone()
    cur.close()
    return row


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