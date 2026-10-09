"""Connection settings, read from environment variables (see .env.example)."""

import os
from dataclasses import dataclass

from pymongo import MongoClient


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
