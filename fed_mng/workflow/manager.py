import datetime

from SpiffWorkflow.bpmn.script_engine import PythonScriptEngine, TaskDataEnvironment
from SpiffWorkflow.spiff.parser.process import BpmnValidator, SpiffBpmnParser
from SpiffWorkflow.spiff.specs.defaults import NoneTask, UserTask

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
