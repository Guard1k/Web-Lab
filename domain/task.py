# domain/task.py

STATUS_PENDING = "pending"
STATUS_COMPLETED = "completed"

class Task:
    """
    Доменна сутність Task (Завдання).
    не залежить від Flask, SQL чи API.
    Лише бізнес-логіка.
    """

    def __init__(self, id: int, name: str, status: str = STATUS_PENDING):
        if not name or name.strip() == "":
            raise ValueError("Task name cannot be empty")

        self.id = id
        self.name = name
        self.status = status

    def mark_as_completed(self):
        """Позначає завдання як виконане."""
        self.status = STATUS_COMPLETED

    def mark_as_pending(self):
        """Позначає завдання як невиконане."""
        self.status = STATUS_PENDING

    def is_completed(self) -> bool:
        """Перевіряє, чи виконане завдання."""
        return self.status == STATUS_COMPLETED
