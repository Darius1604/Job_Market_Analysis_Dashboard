from config.config import config
import psycopg2
def connect():
    """ Connect to the PostgreSQL database server"""
    conn = None
    try:
        # Read connection parameters
        params = config()
        
        # Connect to the PostgreSQL server
        print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(**params)
        
        # create a cursor
        cursor = conn.cursor()
    
        # execute a statement
        print('PostgreSQL database version:')
        cursor.execute('SELECT version()')
        
        # display the PostgreSQL database server version
        db_version = cursor.fetchone()
        print(db_version)
        
        # Close the communication with the PostgreSQL
        cursor.close()
    except(Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
            print('Database connection closed')

if __name__ == '__main__':
    connect()
