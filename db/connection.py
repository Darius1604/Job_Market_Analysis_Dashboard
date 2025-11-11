from config.config import config
import psycopg2
def connect():
    params = config()
    return psycopg2.connect(**params)

if __name__ == '__main__':
    with connect() as conn:
        with conn.cursor() as cursor:
            cursor.execute('SELECT *')
            # commit happens automatically at the end of the block if no exceptions
