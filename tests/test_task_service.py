import pytest
from service.task_service import TaskService

# Ізольований тестовий сервіс (без основної БД)
def get_test_service():
    service = TaskService()
    # замінюємо БД на in-memory SQLite для тестів
    service.conn = __import__("sqlite3").connect(":memory:")
    service.conn.execute("""
        CREATE TABLE tasks (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)
    return service


def test_create_task_success():
    service = get_test_service()

    task = service.create({"name": "Test Task"})

    assert task is not None
    assert task.name == "Test Task"
    assert task.status == "pending"


def test_create_validation_error():
    service = get_test_service()

    with pytest.raises(ValueError) as exc:
        service.create({"name": ""})

    assert "Task name cannot be empty" in str(exc.value)
