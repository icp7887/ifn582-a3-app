from . import mysql


def fetch_all(sql, args=None):
    cur = mysql.connection.cursor()
    cur.execute(sql, args)
    rows = cur.fetchall()
    cur.close()
    return rows


def fetch_one(sql, args=None):
    cur = mysql.connection.cursor()
    cur.execute(sql, args)
    row = cur.fetchone()
    cur.close()
    return row


def run(sql, args=None):
    cur = mysql.connection.cursor()
    cur.execute(sql, args)
    mysql.connection.commit()
    new_id = cur.lastrowid
    cur.close()
    return new_id


ACTIVE_CAMPAIGNS = """
    SELECT c.*, u.username AS creatorName, COALESCE(SUM(d.amount), 0) AS raised
    FROM campaign c
    JOIN user u ON u.id = c.creatorID
    LEFT JOIN donation d ON d.campaignID = c.id AND d.status = 'Done'
    WHERE c.status = 'Active'
"""
ACTIVE_ORDER = " GROUP BY c.id, u.username ORDER BY c.isFeatured DESC, c.startDate DESC, c.id DESC"


def get_active_campaigns():
    return fetch_all(ACTIVE_CAMPAIGNS + ACTIVE_ORDER)


def search_campaigns(search):
    like = '%' + search + '%'
    return fetch_all(ACTIVE_CAMPAIGNS + " AND (c.title LIKE %s OR c.category LIKE %s OR u.username LIKE %s)" + ACTIVE_ORDER,
                     (like, like, like))


def get_campaigns_by_category(category):
    return fetch_all(ACTIVE_CAMPAIGNS + " AND c.category = %s" + ACTIVE_ORDER, (category,))


def get_categories():
    return fetch_all("SELECT DISTINCT category FROM campaign WHERE status = 'Active' ORDER BY category")


def get_featured_active_campaigns():
    return fetch_all("""
        SELECT c.*, u.username AS creatorName, cr.tagline AS creatorTagline, cr.profileImage AS creatorImage
        FROM campaign c
        JOIN user u ON u.id = c.creatorID
        JOIN creator cr ON cr.id = c.creatorID
        WHERE c.status = 'Active' AND c.isFeatured = TRUE
        ORDER BY c.id
    """)


def get_campaign_detail(campaign_id):
    return fetch_one("""
        SELECT c.*, u.username AS creatorName, cr.bio AS creatorBio, cr.verifiedStatus AS creatorVerified,
               COALESCE(SUM(d.amount), 0) AS raised, COUNT(d.transactionID) AS donationCount
        FROM campaign c
        JOIN user u ON u.id = c.creatorID
        JOIN creator cr ON cr.id = c.creatorID
        LEFT JOIN donation d ON d.campaignID = c.id AND d.status = 'Done'
        WHERE c.id = %s
        GROUP BY c.id, u.username, cr.bio, cr.verifiedStatus
    """, (campaign_id,))


def get_creator_tiers(creator_id):
    return fetch_all("SELECT * FROM subscriptionTier WHERE creatorID = %s ORDER BY price", (creator_id,))


def get_campaign_donations(campaign_id, limit=10):
    return fetch_all("""
        SELECT d.*, t.tierName
        FROM donation d
        LEFT JOIN subscriptionTier t ON t.id = d.tierID
        WHERE d.campaignID = %s AND d.status = 'Done'
        ORDER BY d.transactionID DESC
        LIMIT %s
    """, (campaign_id, limit))


def add_donation(campaign_id, customer_id, amount, name, email, address, message, tier_id, payment):
    run("""
        INSERT INTO donation (amount, donorName, donorEmail, donorAddress, message, tierID,
                              paymentNetwork, status, customerID, campaignID)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'Done', %s, %s)
    """, (amount, name, email, address, message, tier_id, payment, customer_id, campaign_id))


def get_creator_campaigns(creator_id):
    return fetch_all("SELECT * FROM campaign WHERE creatorID = %s ORDER BY id DESC", (creator_id,))


def get_campaign_stats(campaign_id):
    return fetch_one("""
        SELECT COUNT(DISTINCT customerID) AS supporters, COALESCE(SUM(amount), 0) AS raised
        FROM donation
        WHERE campaignID = %s AND status = 'Done'
    """, (campaign_id,))


def create_creator_campaign(creator_id, title, description, goal_amount, category, start_date, end_date, image):
    return run("""
        INSERT INTO campaign (title, description, goalAmount, status, campaignImage, startDate, endDate, creatorID, category)
        VALUES (%s, %s, %s, 'Pending', %s, %s, %s, %s, %s)
    """, (title, description, goal_amount, image, start_date, end_date, creator_id, category))


def update_campaign_details(campaign_id, title, description, goal_amount, category, start_date, end_date, image):
    run("""
        UPDATE campaign
        SET title = %s, description = %s, goalAmount = %s, category = %s, startDate = %s, endDate = %s, campaignImage = %s
        WHERE id = %s
    """, (title, description, goal_amount, category, start_date, end_date, image, campaign_id))


def update_campaign_status(campaign_id, new_status):
    run("UPDATE campaign SET status = %s WHERE id = %s", (new_status, campaign_id))


def get_campaign_posts(campaign_id):
    return fetch_all("SELECT * FROM campaign_post WHERE campaignID = %s ORDER BY postDate DESC, id DESC", (campaign_id,))


def get_post(post_id):
    return fetch_one("SELECT * FROM campaign_post WHERE id = %s", (post_id,))


def add_post(campaign_id, title, content, image):
    run("INSERT INTO campaign_post (campaignID, title, content, postImage, postDate) VALUES (%s, %s, %s, %s, CURDATE())",
        (campaign_id, title, content, image))


def update_post(post_id, title, content, image):
    run("UPDATE campaign_post SET title = %s, content = %s, postImage = %s WHERE id = %s", (title, content, image, post_id))


def delete_post(post_id):
    run("DELETE FROM campaign_post WHERE id = %s", (post_id,))


USER_WITH_ROLE = """
    SELECT u.id, u.username, u.password, u.email, u.isSuspended,
           CASE WHEN a.id IS NOT NULL THEN 'Admin'
                WHEN cr.id IS NOT NULL THEN 'Creator'
                ELSE 'Customer' END AS role
    FROM user u
    LEFT JOIN admin a ON a.id = u.id
    LEFT JOIN creator cr ON cr.id = u.id
"""


def get_user_for_login(identifier):
    return fetch_one(USER_WITH_ROLE + " WHERE u.username = %s OR u.email = %s", (identifier, identifier))


def get_user_by_id(user_id):
    return fetch_one(USER_WITH_ROLE + " WHERE u.id = %s", (user_id,))


def get_all_users():
    return fetch_all(USER_WITH_ROLE + " ORDER BY role, u.username")


def username_or_email_taken(username, email):
    return {
        'username': fetch_one("SELECT id FROM user WHERE username = %s", (username,)) is not None,
        'email': fetch_one("SELECT id FROM user WHERE email = %s", (email,)) is not None,
    }


def create_user(username, email, password_hash, role):
    user_id = run("INSERT INTO user (username, password, email) VALUES (%s, %s, %s)", (username, password_hash, email))
    if role == 'Creator':
        run("INSERT INTO creator (id, verifiedStatus) VALUES (%s, FALSE)", (user_id,))
    else:
        run("INSERT INTO customer (id) VALUES (%s)", (user_id,))
    return user_id


def taken_by_other_user(username, email, user_id):
    return fetch_one("SELECT id FROM user WHERE (username = %s OR email = %s) AND id != %s", (username, email, user_id)) is not None


def update_user_details(user_id, username, email):
    run("UPDATE user SET username = %s, email = %s WHERE id = %s", (username, email, user_id))


def set_user_suspended(user_id, is_suspended):
    run("UPDATE user SET isSuspended = %s WHERE id = %s", (is_suspended, user_id))


def delete_user(user_id):
    run("DELETE FROM user WHERE id = %s", (user_id,))


def get_all_campaigns_with_creator():
    return fetch_all("""
        SELECT c.*, u.username AS creatorName
        FROM campaign c JOIN user u ON u.id = c.creatorID
        WHERE c.status = 'Pending'
    """)


def get_all_campaigns_with_details():
    return fetch_all("""
        SELECT c.*, u.username AS creatorName
        FROM campaign c JOIN user u ON u.id = c.creatorID
        ORDER BY c.id
    """)


def delete_campaign(campaign_id):
    run("DELETE FROM campaign WHERE id = %s", (campaign_id,))


def get_open_reports():
    return fetch_all("""
        SELECT r.*, c.title AS campaignTitle
        FROM report r JOIN campaign c ON c.id = r.campaignID
        WHERE r.status = 'Open'
        ORDER BY r.reportedAt
    """)


def get_report_by_id(report_id):
    return fetch_one("SELECT * FROM report WHERE id = %s", (report_id,))


def set_report_status(report_id, status):
    run("UPDATE report SET status = %s, reviewedAt = NOW() WHERE id = %s", (status, report_id))


def set_featured_campaigns(campaign_ids):
    run("UPDATE campaign SET isFeatured = FALSE")
    for campaign_id in campaign_ids:
        run("UPDATE campaign SET isFeatured = TRUE WHERE status = 'Active' AND id = %s", (campaign_id,))
