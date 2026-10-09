"""Connection settings, read from environment variables (see .env.example)."""

import os
from dataclasses import dataclass

import psycopg
from pymongo import MongoClient


@dataclass(frozen=True)
class PostgresSettings:
    host: str
    port: int
    user: str
    password: str
    dbname: str

    @classmethod
    def from_env(cls) -> "PostgresSettings":
        user = os.environ["POSTGRES_USER"]
        return cls(
            host=os.environ.get("POSTGRES_HOST", "localhost"),
            port=int(os.environ.get("POSTGRES_PORT", "5432")),
            user=user,
            password=os.environ["POSTGRES_PASSWORD"],
            # The postgres image creates a database named after the user unless POSTGRES_DB is set.
            dbname=os.environ.get("POSTGRES_DB", user),
        )

    def connect(self, dbname: str | None = None, **kwargs) -> psycopg.Connection:
        return psycopg.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            dbname=dbname or self.dbname,
            **kwargs,
        )


@dataclass(frozen=True)
class MongoSettings:
    host: str
    port: int
    username: str
    password: str
    database: str

    @classmethod
    def from_env(cls) -> "MongoSettings":
        return cls(
            host=os.environ.get("MONGO_HOST", "localhost"),
            port=int(os.environ.get("MONGO_PORT", "27017")),
            username=os.environ["MONGO_INITDB_ROOT_USERNAME"],
            password=os.environ["MONGO_INITDB_ROOT_PASSWORD"],
            database=os.environ.get("MONGO_RAW_DB", "statsbomb_raw"),
        )

    def client(self) -> MongoClient:
        return MongoClient(
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            serverSelectionTimeoutMS=5000,
        )
