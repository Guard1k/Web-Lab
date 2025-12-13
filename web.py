from flask import Flask, jsonify, request, render_template
import psycopg2
import os
import time
import uuid
import random

from api.tasks_api import router as tasks_router
import service
from store import idempotency_store, rate_limit_store

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# DB
def get_db_connection():
    db_url = os.environ.get("DB_URL")
    print("Connecting to:", db_url)  # тимчасово, щоб перевірити
    return psycopg2.connect(db_url)

#    conn = psycopg2.connect(
#        dbname=os.getenv("POSTGRES_DB", "todo_db"),
#        user=os.getenv("POSTGRES_USER", "postgres"),
#        password=os.getenv("POSTGRES_PASSWORD", "password"),
#        host=os.getenv("POSTGRES_HOST", "localhost"),
#        port=os.getenv("POSTGRES_PORT", 5432)
#    )
#    return conn
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            status TEXT DEFAULT 'pending'
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

# MIDDLEWARE
@app.before_request
def assign_request_id():
    req_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
    request.req_id = req_id


@app.after_request
def add_request_id_header(response):
    response.headers["X-Request-Id"] = request.req_id
    return response


@app.before_request
def rate_limiter():
    ip = request.remote_addr or "local"
    now = time.time()

    window = 10
    limit = 5

    record = rate_limit_store.get(ip)

    if not record or now - record["start"] > window:
        record = {"count": 0, "start": now}

    record["count"] += 1
    rate_limit_store[ip] = record

    if record["count"] > limit:
        response = jsonify({"error": "Too Many Requests", "requestId": request.req_id})
        response.status_code = 429
        response.headers["Retry-After"] = "2"
        return response

@app.before_request
def check_idempotency():
    if request.method == "POST" and request.path == "/tasks":
        key = request.headers.get("Idempotency-Key")

        if key and key in idempotency_store:
            cached = idempotency_store[key]
            response = jsonify(cached)
            response.status_code = 201
            response.headers["X-Idempotent-Cache"] = "true"
            return response

        request.idempotency_key = key


@app.before_request
def chaos_monkey():
    chance = random.random()

    if chance < 0.15:
        time.sleep(2)

    if chance > 0.90:
        response = jsonify({"error": "Service Unavailable", "requestId": request.req_id})
        response.status_code = 503
        return response


# ROUTES
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/tasks", methods=["GET"])
def get_tasks():
    conn = get_db_connection()
    tasks = conn.execute('SELECT * FROM tasks').fetchall()
    conn.close()
    return jsonify([dict(t) for t in tasks])


@app.route("/tasks", methods=["POST"])
def create_task():
    data = request.get_json() or {}
    name = data.get("name")
    if not name:
        return {"error": "Name is required"}, 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO tasks (name, status) VALUES (%s, 'pending') RETURNING id, name, status;",
        (name,)
    )
    task = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"id": task[0], "name": task[1], "status": task[2]}), 201


@app.get("/health")
def health():
    return "ok", 200


# Blueprint
#app.register_blueprint(tasks_router, url_prefix="/tasks")

# RUN
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=3000, debug=True)
