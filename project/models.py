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
            u.passwordHASH, 
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