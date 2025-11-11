import mysql.connector

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='mysqlpassword97',
    database='jobsdb'
)

cursor = conn.cursor()

try:
    cursor.execute("""CREATE TABLE IF NOT EXISTS jobs(
    id int AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255),
    company VARCHAR(255),
    posted_on DATE,
    location VARCHAR(255),
    experience VARCHAR(50),
    url VARCHAR(500) UNIQUE,
    scrape_date DATE,
    source_keyword VARCHAR(100));
    """)
except mysql.connector.Error as e:
    print(f"Error creating jobs table: {e}")
try:
    cursor.execute("""
                CREATE TABLE IF NOT EXISTS skills(
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) UNIQUE
    );
    """)

except mysql.connector.Error as e:
    print(f"Error creating skills table: {e}")
try:
    cursor.execute("""
                 CREATE TABLE IF NOT EXISTS job_skills(
    job_id INT,
    skill_id INT,
    PRIMARY KEY (job_id, skill_id),
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
    );"""
                     )
except mysql.connector.Error as e:
    print(f"Error creating job_skills table: {e}")

cursor.execute('SHOW TABLES;')

for table in cursor.fetchall():
    print(table)

cursor.close()
conn.close()


