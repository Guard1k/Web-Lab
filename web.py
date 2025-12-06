from flask import Flask, jsonify, request, render_template
import sqlite3
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
    conn = sqlite3.connect('db.sqlite3')
    conn.row_factory = sqlite3.Row
    return conn

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
    idempotency_key = request.headers.get("Idempotency-Key")

    if not idempotency_key:
        return {"error": "Missing Idempotency-Key"}, 400

    if not hasattr(app, "idem_cache"):
        app.idem_cache = {}

    if idempotency_key in app.idem_cache:
        return app.idem_cache[idempotency_key], 200

    data = request.get_json() or {}
    try:
        task = service.create(data)
    except ValueError as e:
        return {"error": str(e)}, 400

    app.idem_cache[idempotency_key] = task

    return jsonify(task), 201


@app.get("/health")
def health():
    return "ok", 200


# Blueprint
#app.register_blueprint(tasks_router, url_prefix="/tasks")

# RUN
if __name__ == "__main__":
    app.run(port=3000, debug=True)
