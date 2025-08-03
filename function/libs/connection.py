import psycopg2

from libs.get_database_uri import get_database_uri


def get_connection():
    return psycopg2.connect(get_database_uri())
