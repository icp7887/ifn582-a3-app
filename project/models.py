from . import mysql

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