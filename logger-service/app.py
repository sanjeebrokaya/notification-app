from flask import Flask, request, jsonify
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask_cors import CORS

app = Flask(__name__)
# Allow requests from any origin (including file://)
CORS(app, resources={r"/*": {"origins": "*"}})

DB_HOST = os.getenv('POSTGRES_HOST', 'postgres')
DB_DB   = os.getenv('POSTGRES_DB', 'logs_db')
DB_USER = os.getenv('POSTGRES_USER', 'user')
DB_PASS = os.getenv('POSTGRES_PASSWORD', 'password')

def get_conn():
    return psycopg2.connect(
        host=DB_HOST, dbname=DB_DB, user=DB_USER, password=DB_PASS
    )

def ensure_table():
    sql = '''
    CREATE TABLE IF NOT EXISTS logs (
        id SERIAL PRIMARY KEY,
        message TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    '''
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            conn.commit()

@app.get('/')
def health():
    try:
        ensure_table()
        return jsonify(status='ok', service='logger-service')
    except Exception as e:
        return jsonify(status='error', message=str(e)), 500

@app.post('/log')
def write_log():
    ensure_table()
    data = request.get_json(silent=True) or {}
    msg = data.get('message', '').strip()
    if not msg:
        return jsonify(status='error', message='message is required'), 400
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute('INSERT INTO logs (message) VALUES (%s) RETURNING id, created_at', (msg,))
                row = cur.fetchone()
                conn.commit()
        return jsonify(status='ok', id=row[0], created_at=str(row[1]))
    except Exception as e:
        return jsonify(status='error', message='db insert failed', details=str(e)), 500

@app.get('/logs')
def read_logs():
    ensure_table()
    try:
        with get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute('SELECT id, message, created_at FROM logs ORDER BY id DESC LIMIT 50')
                rows = cur.fetchall()
        return jsonify(rows)
    except Exception as e:
        return jsonify(status='error', message='db read failed', details=str(e)), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081)
