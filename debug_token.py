import jwt
import sqlite3

token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI3YmU1YTQ0MC1mN2M4LTQzOTctYmM5Ni0xMWI2ZWJhMjYyNDMiLCJyb2xlIjoic3lzdGVtX2FkbWluIiwiaWF0IjoxNzc5MDI3Njc1LCJleHAiOjE3NzkwMzEyNzV9.YyPexYiHq4sPqELTYMwGjOkYblDuSqK0ul_TI_WOaM0'

# Decode without verification to see payload
payload = jwt.decode(token, options={'verify_signature': False})
print('Token Payload:')
print(f'  User ID (sub): {payload["sub"]}')
print(f'  Role: {payload["role"]}')

# Check if user exists with this ID
conn = sqlite3.connect('mavericks.db')
c = conn.cursor()
c.execute('SELECT id, email, full_name FROM users WHERE id = ?', (payload['sub'],))
user = c.fetchone()

if user:
    print(f'\nUser Found in DB:')
    print(f'  ID: {user[0]}')
    print(f'  Email: {user[1]}')
    print(f'  Name: {user[2]}')
else:
    print(f'\nERROR: User ID {payload["sub"]} NOT FOUND in database!')
    
    print('\nAll users in database:')
    c.execute('SELECT id, email FROM users')
    for row in c.fetchall():
        print(f'  {row[0]} - {row[1]}')

conn.close()
