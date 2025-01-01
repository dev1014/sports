import hashlib
import sqlite3
from datetime import datetime, timedelta
import os

def hash_password(password: str) -> str:
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000
    )
    return salt.hex() + ':' + key.hex()

def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt_str, key_str = stored_hash.split(':')
        salt = bytes.fromhex(salt_str)
        stored_key = bytes.fromhex(key_str)
        new_key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000
        )
        return stored_key == new_key
    except:
        return False

def create_user(conn, username: str, password: str) -> bool:
    try:
        c = conn.cursor()
        hashed = hash_password(password)
        c.execute('INSERT INTO users (username, password) VALUES (?, ?)',
                 (username, hashed))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def get_user(conn, username: str, password: str):
    c = conn.cursor()
    c.execute('SELECT id, password FROM users WHERE username = ?', (username,))
    result = c.fetchone()
    if result and verify_password(password, result[1]):
        return result[0]
    return None

def save_user_prop(conn, user_id: int, prop_data: dict) -> bool:
    try:
        c = conn.cursor()
        c.execute('INSERT INTO saved_props (user_id, prop_data) VALUES (?, ?)',
                 (user_id, str(prop_data)))
        conn.commit()
        return True
    except:
        return False
