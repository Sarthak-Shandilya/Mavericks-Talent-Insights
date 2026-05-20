import sqlite3
conn = sqlite3.connect('mavericks.db')
cursor = conn.cursor()
cursor.execute('SELECT id, email, full_name FROM users LIMIT 5')
print('Users in database:')
for row in cursor.fetchall():
    print(f'  ID: {row[0]}')
    print(f'  Email: {row[1]}')
    print(f'  Name: {row[2]}')
    print()
conn.close()
