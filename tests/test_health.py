import os

import psycopg
from pymongo import MongoClient


def test_postgres_answers():
    conn = psycopg.connect(
        host="localhost",
        port=5432,
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    )
    result = conn.execute("SELECT 1").fetchone()
    conn.close()
    assert result == (1,)


def test_mongo_answers():
    client = MongoClient(
        host="localhost",
        port=27017,
        serverSelectionTimeoutMS=3000,
        username=os.environ["MONGO_INITDB_ROOT_USERNAME"],
        password=os.environ["MONGO_INITDB_ROOT_PASSWORD"],
    )
    result = client.admin.command("ping")
    client.close()
    assert result["ok"] == 1
