"""
Flask Task API - Demo app for Claude Code CI/CD session.
Intentional issues are present for demo purposes (marked with # BUG).
"""
from flask import Flask, jsonify, request
from models import Task, db
import logging

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tasks.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.route("/tasks", methods=["GET"])
def get_tasks():
    """Return all tasks."""
    tasks = Task.query.all()
    return jsonify([t.to_dict() for t in tasks]), 200


@app.route("/tasks", methods=["POST"])
def create_task():
    """Create a new task."""
    data = request.get_json()

    # BUG 1: No input validation — title could be None or empty string
    title = data.get("title")
    title = data.get("title") or ""  # empty string silently accepted
    description = data.get("description", "")

    # BUG 2: No check for duplicate titles
    task = Task(title=title, description=description)
    db.session.add(task)
    db.session.commit()

    logger.info(f"Created task: {task.id}")
    return jsonify(task.to_dict()), 201


@app.route("/tasks/<int:task_id>", methods=["GET"])
def get_task(task_id):
    """Return a single task by ID."""
    # BUG 3: Using .first() instead of .get() or 404 — returns None silently
    task = Task.query.filter_by(id=task_id).first()
    if not task:
        return jsonify({"error": "Task not found"}), 404
    return jsonify(task.to_dict()), 200


@app.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    """Update an existing task."""
    task = Task.query.get_or_404(task_id)
    data = request.get_json()

    # BUG 4: Allows setting title to empty string / None with no validation
    if "title" in data:
        task.title = data["title"]
    if "description" in data:
        task.description = data["description"]
    if "completed" in data:
        task.completed = data["completed"]

    db.session.commit()
    return jsonify(task.to_dict()), 200


@app.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    """Delete a task."""
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return jsonify({"message": "Task deleted"}), 200


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
