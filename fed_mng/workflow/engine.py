import logging

from SpiffWorkflow.bpmn.parser.ValidationException import ValidationException
from SpiffWorkflow.bpmn.script_engine import PythonScriptEngine
from SpiffWorkflow.bpmn.specs.mixins.events.event_types import CatchingEvent
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow
from SpiffWorkflow.spiff.parser.process import SpiffBpmnParser
from SpiffWorkflow.task import TaskState

from fed_mng.workflow.serializer import FileSerializer

logger = logging.getLogger("spiff_engine")


class BpmnEngine:
    def __init__(
        self,
        *,
        parser: SpiffBpmnParser,
        serializer: FileSerializer,
        handlers=None,
        script_engine: PythonScriptEngine | None = None,
    ) -> None:
        self.parser = parser
        self.serializer = serializer
        self._script_engine = script_engine or PythonScriptEngine()
        self._handlers = handlers or {}

    def handler(self, task):
        handler = self._handlers.get(task.task_spec.__class__)
        if handler is not None:
            return handler(task)

    def add_spec(
        self,
        process_id: str,
        bpmn_files: list[str] | None,
        dmn_files: list[str] | None = None,
        force: bool = False,
    ) -> str:
        self.add_files(bpmn_files=bpmn_files, dmn_files=dmn_files)
        try:
            spec = self.parser.get_spec(process_id)
            dependencies = self.parser.get_subprocess_specs(process_id)
        except ValidationException as exc:
            # Clear the process parsers so the files can be re-added
            # There's probably plenty of other stuff that should be here
            # However, our parser makes me mad so not investigating further at this time
            self.parser.process_parsers = {}
            raise exc
        spec_id = self.serializer.create_workflow_spec(spec, dependencies, force=force)
        logger.info("Added %s with id %s", process_id, spec_id)
        return spec_id

    def add_collaboration(
        self,
        collaboration_id: str,
        bpmn_files: list[str],
        dmn_files: list[str] | None = None,
        force: bool = False,
    ) -> str:
        self.add_files(bpmn_files=bpmn_files, dmn_files=dmn_files)
        try:
            spec, dependencies = self.parser.get_collaboration(collaboration_id)
        except ValidationException as exc:
            self.parser.process_parsers = {}
            raise exc
        spec_id = self.serializer.create_workflow_spec(spec, dependencies, force=force)
        logger.info("Added %s with id %s", collaboration_id, spec_id)
        return spec_id

    def add_files(
        self, *, bpmn_files: list[str], dmn_files: list[str] | None = None
    ) -> None:
        logger.info("Adding BPMN files %s", bpmn_files)
        self.parser.add_bpmn_files(bpmn_files)
        if dmn_files is not None:
            logger.info("Adding DMN files %s", dmn_files)
            self.parser.add_dmn_files(dmn_files)

    def list_specs(self) -> list[tuple[str, str, str]]:
        return self.serializer.list_specs()

    def delete_workflow_spec(self, spec_id) -> None:
        self.serializer.delete_workflow_spec(spec_id)
        logger.info("Deleted workflow spec with id %s", spec_id)

    def start_workflow(self, spec_id) -> str:
        spec, sp_specs = self.serializer.get_workflow_spec(spec_id)
        wf = BpmnWorkflow(spec, sp_specs, script_engine=self._script_engine)
        wf_id = self.serializer.create_workflow(wf, spec_id)
        logger.info("Created workflow with id %s", wf_id)
        return wf_id

    def get_workflow(self, wf_id) -> BpmnWorkflow:
        wf = self.serializer.get_workflow(wf_id)
        wf.script_engine = self._script_engine
        return wf

    def update_workflow(self, workflow, wf_id):
        logger.info("Saved workflow %s", wf_id)
        self.serializer.update_workflow(workflow, wf_id)

    def list_workflows(
        self, include_completed=False
    ) -> list[tuple[str, str, str, str, str, str]]:
        return self.serializer.list_workflows(include_completed)

    def delete_workflow(self, wf_id) -> None:
        self.serializer.delete_workflow(wf_id)
        logger.info("Deleted workflow with id %s", wf_id)

    def run_until_user_input_required(self, workflow: BpmnWorkflow):
        task = workflow.get_next_task(state=TaskState.READY, manual=False)
        while task is not None:
            logger.info("Executing task %s", task.task_spec.bpmn_name)
            task.run()
            self.run_ready_events(workflow)
            task = workflow.get_next_task(state=TaskState.READY, manual=False)
            logger.info("Next task: %s", task.task_spec.bpmn_name if task else None)

    def run_ready_events(self, workflow: BpmnWorkflow):
        workflow.refresh_waiting_tasks()
        task = workflow.get_next_task(state=TaskState.READY, spec_class=CatchingEvent)
        while task is not None:
            task.run()
            task = workflow.get_next_task(
                state=TaskState.READY, spec_class=CatchingEvent
            )
