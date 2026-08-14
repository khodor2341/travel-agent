import sqlite3
import json
from datetime import datetime

DB_FILE = "trips.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            destination TEXT,
            duration INTEGER,
            budget INTEGER,
            currency TEXT,
            preferences TEXT,
            itinerary TEXT,
            created_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_trip(destination, duration, budget, currency, preferences, itinerary):
    init_db()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO trips (destination, duration, budget, currency, preferences, itinerary, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (destination, duration, budget, currency, preferences, itinerary, datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    trip_id = c.lastrowid
    conn.close()
    return trip_id

def get_all_trips():
    init_db()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT id, destination, duration, budget, currency, created_at FROM trips ORDER BY created_at DESC')
    trips = c.fetchall()
    conn.close()
    return trips

def get_trip(trip_id):
    init_db()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT * FROM trips WHERE id = ?', (trip_id,))
    trip = c.fetchone()
    conn.close()
    return trip

def delete_trip(trip_id):
    init_db()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('DELETE FROM trips WHERE id = ?', (trip_id,))
    conn.commit()
    conn.close()