from domain.task import Task

import uuid

class TaskService:
    def __init__(self):
        self.tasks = {}  # тимчасово — "БД у пам'яті"

    def create(self, create_request):
        if "name" not in create_request:
            raise ValueError("Name is required")

        task_id = str(uuid.uuid4())
        task = Task(task_id, create_request["name"], "pending")

        self.tasks[task_id] = task
        return task

    def get_all(self):
        return list(self.tasks.values())

    def get_by_id(self, task_id):
        if task_id not in self.tasks:
            raise KeyError("Not found")
        return self.tasks[task_id]

    def update(self, task_id, update_request):
        if task_id not in self.tasks:
            raise KeyError("Not found")

        task = self.tasks[task_id]

        if "name" in update_request:
            task.name = update_request["name"]
        if "status" in update_request:
            task.status = update_request["status"]

        return task

    def delete(self, task_id):
        if task_id not in self.tasks:
            raise KeyError("Not found")
        del self.tasks[task_id]
