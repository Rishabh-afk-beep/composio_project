import sqlite3
import json
import os
from typing import Optional, Dict, Any

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "composio_radar.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # Table for HTTP request cache
    c.execute('''
        CREATE TABLE IF NOT EXISTS http_cache (
            url TEXT PRIMARY KEY,
            response TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Table for app research results
    c.execute('''
        CREATE TABLE IF NOT EXISTS app_research (
            app_name TEXT PRIMARY KEY,
            data JSON,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def get_cached_request(url: str) -> Optional[str]:
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT response FROM http_cache WHERE url = ?', (url,))
    row = c.fetchone()
    conn.close()
    if row:
        return row['response']
    return None

def set_cached_request(url: str, response: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO http_cache (url, response, timestamp)
        VALUES (?, ?, CURRENT_TIMESTAMP)
    ''', (url, response))
    conn.commit()
    conn.close()

def save_app_research(app_name: str, data: Dict[str, Any]):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO app_research (app_name, data, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
    ''', (app_name, json.dumps(data)))
    conn.commit()
    conn.close()

def get_app_research(app_name: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT data FROM app_research WHERE app_name = ?', (app_name,))
    row = c.fetchone()
    conn.close()
    if row:
        return json.loads(row['data'])
    return None
