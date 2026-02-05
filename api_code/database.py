import psycopg2

def get_db():
    return psycopg2.connect(
        host="localhost",
        database="multimedia_db",
        user="postgres",
        password="123456"
    )
