from SpiffWorkflow.task import Task


class TaskHandler:
    def __init__(self, task: Task) -> None:
        self.task = task

    def on_complete(self) -> None:
        self.task.run()


class ManualTaskHandler:
    pass


class UserTaskHandler(TaskHandler):
    def on_complete(self, results: dict | None = None) -> None:
        self.task.set_data(**results)
        super().on_complete()


class NoneTaskHandler(TaskHandler):
    ...
