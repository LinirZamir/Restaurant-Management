import sqlite3

conn = sqlite3.connect('inventory.db')
c = conn.cursor()

# Create the item table
c.execute('''CREATE TABLE items
             (name text, description text, quantity integer, price real, time text)''')


# Save the changes and close the connection
conn.commit()
conn.close()