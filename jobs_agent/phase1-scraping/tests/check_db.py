import sqlite3

conn = sqlite3.connect('data/jobs.db')
cursor = conn.execute('SELECT COUNT(*) FROM jobs')
print(f'Jobs in DB: {cursor.fetchone()[0]}')

cursor = conn.execute('SELECT job_id, title, company, location, is_remote FROM jobs LIMIT 3')
print('\nSample jobs:')
for row in cursor.fetchall():
    print(row)

conn.close()
