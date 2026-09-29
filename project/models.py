from . import mysql

def get_all_items():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM items")
    rows = cur.fetchall()
    cur.close()
    return rows

def add_item(name, description):
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO items (name, description) VALUES (%s, %s)",
                (name, description))
    mysql.connection.commit()
    cur.close()
