"""
Simple SQLite-backed key-value cache for persistent storage
"""

import os
import sqlite3
import json
import time
from typing import Optional, Any

from src.config import CACHE_DB_PATH


def _ensure_db() -> None:
    os.makedirs(os.path.dirname(CACHE_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(CACHE_DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS kv_cache (
                k TEXT PRIMARY KEY,
                v TEXT NOT NULL,
                ts REAL NOT NULL
            )
            """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_kv_ts ON kv_cache (ts)")
        conn.commit()
    finally:
        conn.close()


def cache_get(key: str) -> Optional[Any]:
    _ensure_db()
    conn = sqlite3.connect(CACHE_DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute("SELECT v FROM kv_cache WHERE k = ?", (key,))
        row = cur.fetchone()
        if not row:
            return None
        try:
            return json.loads(row[0])
        except Exception:
            return None
    finally:
        conn.close()


def cache_set(key: str, value: Any) -> None:
    _ensure_db()
    conn = sqlite3.connect(CACHE_DB_PATH)
    try:
        cur = conn.cursor()
        payload = json.dumps(value, ensure_ascii=False)
        cur.execute(
            "INSERT OR REPLACE INTO kv_cache (k, v, ts) VALUES (?, ?, ?)",
            (key, payload, float(time.time())),
        )
        conn.commit()
    finally:
        conn.close()


