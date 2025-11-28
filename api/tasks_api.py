from flask import Blueprint, request, jsonify
from service.task_service import TaskService

router = Blueprint("tasks", __name__)
service = TaskService()

@router.post("/")
def create_task():
    try:
        task = service.create(request.json)
        return jsonify(task.to_dict()), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@router.get("/")
def get_all():
    tasks = service.get_all()
    return jsonify([t.to_dict() for t in tasks]), 200

@router.get("/<task_id>")
def get_by_id(task_id):
    try:
        task = service.get_by_id(task_id)
        return jsonify(task.to_dict()), 200
    except KeyError:
        return jsonify({"error": "Not Found"}), 404

@router.put("/<task_id>")
def update(task_id):
    try:
        task = service.update(task_id, request.json)
        return jsonify(task.to_dict()), 200
    except KeyError:
        return jsonify({"error": "Not Found"}), 404

@router.delete("/<task_id>")
def delete(task_id):
    try:
        service.delete(task_id)
        return "", 204
    except KeyError:
        return jsonify({"error": "Not Found"}), 404
