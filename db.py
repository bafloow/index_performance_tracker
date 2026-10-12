import os 
from dotenv import load_dotenv
import psycopg

def get_connection():

    load_dotenv()

    host = os.getenv('DB_HOST')
    user = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    database = os.getenv('DB_NAME')
    port = os.getenv('DB_PORT') 

    connection = psycopg.connect(
        host=host,
        user=user,
        password=password,
        dbname=database,
        port=port
     )
    return connection

def get_available_indexes():
    con = get_connection()
    try:
        with con.cursor() as cur:
            cur.execute("""SELECT DISTINCT name FROM indexes""")

            index_names = [item[0] for item in cur.fetchall()]
    finally:
        con.close()
    return index_names
        
