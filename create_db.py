import psycopg2 as db
from psycopg2.errors import DuplicateDatabase

try:
    p='postgres'
    con=db.connect(dbname=p,host='localhost',user=p,password=p)
    con.autocommit=True;con.cursor().execute('CREATE DATABASE orders')
except DuplicateDatabase as e:
    print('Database "orders" already exists')