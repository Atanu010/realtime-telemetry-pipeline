"""Shared Database handle with automatic MongoDB connection and resilient in-memory fallback."""

import asyncio
import copy
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING, IndexModel

load_dotenv(Path(__file__).parent.parent / ".env")

logger = logging.getLogger(__name__)

mongo_url = os.environ.get("MONGO_URL", "")
db_name = os.environ.get("DB_NAME", "telemetry")

class InMemoryCursor:
    def __init__(self, docs: List[Dict[str, Any]]):
        self.docs = copy.deepcopy(docs)

    def sort(self, key_or_list, direction=1):
        if isinstance(key_or_list, list):
            for k, d in reversed(key_or_list):
                self.docs.sort(key=lambda x: (x.get(k) is None, x.get(k)), reverse=(d == DESCENDING or d == -1))
        else:
            self.docs.sort(key=lambda x: (x.get(key_or_list) is None, x.get(key_or_list)), reverse=(direction == DESCENDING or direction == -1))
        return self

    async def to_list(self, length: Optional[int] = None) -> List[Dict[str, Any]]:
        if length is not None:
            return self.docs[:length]
        return self.docs

class InMemoryCollection:
    def __init__(self, name: str):
        self.name = name
        self.docs: List[Dict[str, Any]] = []

    def _matches(self, doc: Dict[str, Any], query: Dict[str, Any]) -> bool:
        for k, v in query.items():
            if isinstance(v, dict):
                if "$in" in v:
                    if doc.get(k) not in v["$in"]:
                        return False
            elif doc.get(k) != v:
                return False
        return True

    async def count_documents(self, query: Dict[str, Any]) -> int:
        if not query:
            return len(self.docs)
        return sum(1 for d in self.docs if self._matches(d, query))

    async def insert_one(self, doc: Dict[str, Any]):
        d = copy.deepcopy(doc)
        self.docs.append(d)
        return type("Result", (), {"inserted_id": d.get("id")})()

    async def insert_many(self, docs: List[Dict[str, Any]]):
        for d in docs:
            self.docs.append(copy.deepcopy(d))
        return type("Result", (), {"inserted_ids": [d.get("id") for d in docs]})()

    def find(self, query: Optional[Dict[str, Any]] = None):
        q = query or {}
        matched = [d for d in self.docs if self._matches(d, q)]
        return InMemoryCursor(matched)

    async def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for d in self.docs:
            if self._matches(d, query):
                return copy.deepcopy(d)
        return None

    async def find_one_and_update(self, query: Dict[str, Any], update: Dict[str, Any], return_document=None) -> Optional[Dict[str, Any]]:
        for d in self.docs:
            if self._matches(d, query):
                if "$set" in update:
                    d.update(update["$set"])
                return copy.deepcopy(d)
        return None

    async def update_one(self, query: Dict[str, Any], update: Dict[str, Any], upsert: bool = False):
        for d in self.docs:
            if self._matches(d, query):
                if "$set" in update:
                    d.update(update["$set"])
                return type("Result", (), {"modified_count": 1, "matched_count": 1})()
        if upsert:
            new_doc = copy.deepcopy(query)
            if "$set" in update:
                new_doc.update(update["$set"])
            self.docs.append(new_doc)
            return type("Result", (), {"modified_count": 0, "matched_count": 0, "upserted_id": new_doc.get("id")})()
        return type("Result", (), {"modified_count": 0, "matched_count": 0})()

    async def create_indexes(self, models):
        pass

class InMemoryDatabase:
    def __init__(self):
        self._collections: Dict[str, InMemoryCollection] = {}

    def __getitem__(self, name: str) -> InMemoryCollection:
        if name not in self._collections:
            self._collections[name] = InMemoryCollection(name)
        return self._collections[name]

    def __getattr__(self, name: str) -> InMemoryCollection:
        return self[name]

class DatabaseProxy:
    def __init__(self):
        self._mongo_client = None
        self._mongo_db = None
        self._in_memory_db = InMemoryDatabase()
        self.use_mongo = False

        if mongo_url:
            try:
                self._mongo_client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=2000)
                self._mongo_db = self._mongo_client[db_name]
                self.use_mongo = True
                logger.info("Connecting to MongoDB at %s", mongo_url)
            except Exception as e:
                logger.warning("Could not initialize MongoDB client: %s. Using in-memory store.", e)
                self.use_mongo = False
        else:
            logger.info("No MONGO_URL configured. Running with in-memory telemetry store.")

    def __getitem__(self, name: str):
        if self.use_mongo and self._mongo_db is not None:
            return self._mongo_db[name]
        return self._in_memory_db[name]

    def __getattr__(self, name: str):
        return self[name]

    def close(self):
        if self._mongo_client:
            self._mongo_client.close()

db = DatabaseProxy()
client = db

# One entry per collection: every field a route filters, sorts, or dedupes on. Applied by ensure_indexes() at startup.
INDEXES: dict[str, list[IndexModel]] = {
    "status_checks": [IndexModel([("timestamp", DESCENDING)], name="timestamp_desc")],
    "pipeline_resources": [IndexModel([("kind", ASCENDING), ("name", ASCENDING)], name="kind_name")],
    "alerts": [IndexModel([("status", ASCENDING), ("created_at", DESCENDING)], name="status_created")],
    "integrations": [IndexModel([("kind", ASCENDING)], name="kind")],
    "stream_state": [IndexModel([("id", ASCENDING)], name="id", unique=True)],
}

async def ensure_indexes() -> None:
    if not db.use_mongo:
        return
    for collection, models in INDEXES.items():
        for model in models:
            try:
                await db[collection].create_indexes([model])
            except Exception as exc:
                logger.warning("ensure_indexes(%s.%s): %s", collection, model.document["name"], exc)
