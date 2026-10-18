from . import mysql

#admin fetch functions
def get_pending_campaigns(): #data retrieval function to fetch all campaigns with status 'Pending' from the database, returns a list of dictionaries representing each campaign.
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM campaign WHERE status = 'Pending'")
    rows = cur.fetchall()
    cur.close()
    return rows

def get_featured_campaigns(): #data retrieval function to fetch all campaigns with isFeatured set to TRUE from the database, returns a list of dictionaries representing each campaign.
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM campaign WHERE isFeatured = TRUE")
    rows = cur.fetchall()
    cur.close()
    return rows

def get_flagged_campaigns(): #data retrieval function to fetch all campaigns with isFlagged set to TRUE from the database, returns a list of dictionaries representing each campaign.
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM campaign WHERE isFlagged = TRUE")
    rows = cur.fetchall()
    cur.close()
    return rows

#ADMIN ACTION FUNCTIONS
def update_campaign_status(campaign_id, new_status): #update campaign status to Approved or Rejected
    cur = mysql.connection.cursor()
    cur.execute("UPDATE campaign SET status = %s WHERE id = %s", (new_status, campaign_id))
    mysql.connection.commit() #save changes to the database
    cur.close()

def set_campaign_featured(campaign_id, is_featured): #update campaign featured status to True or False
    cur = mysql.connection.cursor()
    cur.execute("UPDATE campaign SET isFeatured = %s WHERE id = %s", (is_featured, campaign_id))
    mysql.connection.commit() #save changes to the database
    cur.close()

def set_campaign_flagged(campaign_id, is_flagged): #update campaign flagged status to True or False
    cur = mysql.connection.cursor()
    cur.execute("UPDATE campaign SET isFlagged = %s WHERE id = %s", (is_flagged, campaign_id))
    mysql.connection.commit() #save changes to the database
    cur.close()

#USER FETCH FUNCTIONS
#queries both user and admin tables to get user info and role based on email via left join, returns None if no user found
#%s is a placeholder for the email parameter, which is passed as a tuple (email,) to prevent SQL injection attacks. The function returns a dictionary containing user details and role if found, or None if no user exists with the provided email.
#we alias u and a for user and admin tables respectively, and alias accessLevel as role for clarity in the returned dictionary. This is done in SQL to make it clear that the accessLevel column from the admin table represents the user's role in the application.
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

#user fetch function
def get_user_by_id(user_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM user WHERE id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()
    return user

#admin fetch function for dashboard
def get_dashboard_counts(): #counts for the 4 stat cards at the top of the admin page (Pending, Active, Flagged Items, Users Pending)
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT 
            SUM(status = 'Pending') AS pending, 
            SUM(status = 'Active') AS active, 
            SUM(isFlagged = TRUE) AS flagged
        FROM campaign
    """)
    counts = cur.fetchone()
    cur.execute("SELECT COUNT(*) AS users_pending FROM user WHERE verifiedStatus = FALSE") #creators who are not verfied yet are the "Users Pending"
    counts['users_pending'] = cur.fetchone()['users_pending']
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

def get_all_creators(): #for the User Management section and the Create Campaign drop down: every user with role 'Creator' plus their verified status
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT 
            u.id, 
            u.username, 
            u.email, 
            cr.verifiedStatus
        FROM creator cr
        JOIN user u ON cr.id = u.id
        ORDER BY cr.verifiedStatus, u.username
    """)
    rows = cur.fetchall()
    cur.close()
    return rows    

#ADMIN CREATE FUNCTION
def create_campaign(title, goal_amount, start_date, end_date, creator_id, category, campiagn_image=None): #adds a new campaign with status 'Pending', so it still has to be approved
    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO campaign (title, goalAmount, startDate, endDate, creatorID, category, campaignImage, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'Pending')
    """, (title, goal_amount, start_date, end_date, creator_id, category, campiagn_image))
    mysql.connection.commit() #save changes to the database
    cur.close()

#ADMIN DELETE FUNCTION
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
