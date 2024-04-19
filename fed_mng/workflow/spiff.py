import datetime
import time

from SpiffWorkflow.bpmn.script_engine import PythonScriptEngine, TaskDataEnvironment
from SpiffWorkflow.spiff.parser.process import SpiffBpmnParser, BpmnValidator
from SpiffWorkflow.spiff.specs.defaults import NoneTask, UserTask
from SpiffWorkflow.util.task import TaskState

from fed_mng.config import get_settings
from fed_mng.workflow.engine import BpmnEngine
from fed_mng.workflow.serializer import FileSerializer
from fed_mng.workflow.task_handlers import NoneTaskHandler, UserTaskHandler

# Setup
settings = get_settings()
serializer = FileSerializer(dirname=settings.WORKFLOW_DIR)

parser = SpiffBpmnParser(validator=BpmnValidator())

script_env = TaskDataEnvironment({"datetime": datetime})
script_engine = PythonScriptEngine(environment=script_env)

handlers = {
    UserTask: UserTaskHandler,
    # ManualTask: ManualTaskHandler,
    NoneTask: NoneTaskHandler,
}

engine = BpmnEngine(
    parser=parser, serializer=serializer, handlers=handlers, script_engine=script_engine
)

# Run

print("Load WorkflowSpecs")
spec_id = engine.add_spec("test", ["processes/test.bpmn"])
print(f"Loaded workflowSpec with id {spec_id}")
# engine.list_specs())

print("Clear previous workflow instances")
for i in engine.list_workflows():
    engine.delete_workflow(i[0])

print("Initialize a new workflow instance")
wf_id = engine.start_workflow(spec_id)
print(f"Instantiated workflow with id {wf_id}")
# engine.list_workflows()
wf = engine.get_workflow(wf_id)
for k, v in wf.tasks.items():
    print(
        f"Task id: {k}, BPMN task name: {v.task_spec.bpmn_name}, \
BPMN task id: {v.task_spec.bpmn_id}, \
Manual: {v.task_spec.manual}, \
State: {TaskState._names[TaskState._values.index(v.state)]}"
    )

time.sleep(1)
print("Start and run until user input is required")
engine.run_until_user_input_required(wf)
next_task = wf.get_next_task(state=TaskState.READY, manual=True)
while next_task is not None:
    print(f"There is a manual task `{next_task.task_spec.bpmn_name}`")
    task = engine.handler(next_task)
    if isinstance(task, UserTaskHandler):
        results = input("Waiting for user input: ")
        task.on_complete({"my_text": results})
    elif isinstance(task, NoneTaskHandler):
        task.on_complete()
    print("Continue running until user input is required")
    engine.run_until_user_input_required(wf)
    next_task = wf.get_next_task(state=TaskState.READY, manual=True)

print("Completed")
for k, v in wf.tasks.items():
    print(
        f"Task id: {k}, BPMN task name: {v.task_spec.bpmn_name}, \
Manual: {v.task_spec.manual}, \
State: {TaskState._names[TaskState._values.index(v.state)]}"
    )
print(list(filter(lambda x: x[0] == wf_id, engine.list_workflows())))
