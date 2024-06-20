import json
import logging
import os
import re
import sqlite3
from datetime import datetime
from uuid import UUID, uuid4

from SpiffWorkflow.bpmn.serializer.default.process_spec import BpmnProcessSpecConverter
from SpiffWorkflow.bpmn.serializer.default.workflow import (
    BpmnSubWorkflowConverter,
    BpmnWorkflowConverter,
)
from SpiffWorkflow.bpmn.serializer.workflow import BpmnWorkflowSerializer
from SpiffWorkflow.bpmn.specs.bpmn_process_spec import BpmnProcessSpec
from SpiffWorkflow.bpmn.specs.mixins.subworkflow_task import SubWorkflowTask
from SpiffWorkflow.bpmn.workflow import BpmnSubWorkflow, BpmnWorkflow
from SpiffWorkflow.spiff.serializer.config import DEFAULT_CONFIG, SPIFF_CONFIG
from sqlmodel import Session, select

from fed_mng.models import WorkflowSpec

logger = logging.getLogger(__name__)


class FileSerializer(BpmnWorkflowSerializer):
    def __init__(self, *, dirname: str, **kwargs) -> None:
        self.fmt = {"indent": 2, "separators": [", ", ": "]}
        self.__initialize_dir__(dirname)
        super().__init__(registry=super().configure(SPIFF_CONFIG), **kwargs)

    def __initialize_dir__(self, dirname: str) -> None:
        self.dirname = dirname
        os.makedirs(os.path.join(self.dirname, "spec"), exist_ok=True)
        os.makedirs(os.path.join(self.dirname, "instance"), exist_ok=True)

    def create_workflow_spec(
        self, spec: BpmnProcessSpec, dependencies: dict, force: bool = False
    ) -> str:
        spec_dir = os.path.join(self.dirname, "spec")
        if spec.file is not None:
            dirname = os.path.join(spec_dir, os.path.dirname(spec.file), spec.name)
        else:
            dirname = os.path.join(spec_dir, spec.name)
        filename = os.path.join(dirname, f"{spec.name}.json")
        try:
            os.makedirs(dirname, exist_ok=True)
            with open(filename, "w" if force else "x") as fh:
                fh.write(json.dumps(self.to_dict(spec), **self.fmt))
            if len(dependencies) > 0:
                os.mkdir(os.path.join(dirname, "dependencies"))
                for name, sp in dependencies.items():
                    with open(
                        os.path.join(dirname, "dependencies", f"{name}.json"), "w"
                    ) as fh:
                        fh.write(json.dumps(self.to_dict(sp), **self.fmt))
        except FileExistsError:
            pass
        return filename

    def delete_workflow_spec(self, filename) -> None:
        try:
            os.remove(filename)
        except FileNotFoundError:
            pass

    def get_workflow_spec(self, filename, **kwargs):
        dirname = os.path.dirname(filename)
        with open(filename) as fh:
            spec = self.from_dict(json.loads(fh.read()))
        subprocess_specs = {}
        depdir = os.path.join(os.path.dirname(filename), "dependencies")
        if os.path.exists(depdir):
            for f in os.listdir(depdir):
                name = re.sub("\.json$", "", os.path.basename(f))
                with open(os.path.join(depdir, f)) as fh:
                    subprocess_specs[name] = self.from_dict(json.loads(fh.read()))
        return spec, subprocess_specs

    def list_specs(self) -> list[tuple[str, str, str]]:
        library = []
        for root, _dirs, files in os.walk(os.path.join(self.dirname, "spec")):
            if "dependencies" not in root:
                for f in files:
                    filename = os.path.join(root, f)
                    name = re.sub(r"\.json$", "", os.path.basename(f))
                    path = re.sub(
                        os.path.join(self.dirname, "spec"), "", filename
                    ).lstrip("/")
                    library.append((filename, name, path))
        return library

    def create_workflow(self, workflow, spec_id) -> str:
        name = re.sub(r"\.json$", "", os.path.basename(spec_id))
        dirname = os.path.join(self.dirname, "instance", name)
        os.makedirs(dirname, exist_ok=True)
        wf_id = uuid4()
        with open(os.path.join(dirname, f"{wf_id}.json"), "w") as fh:
            fh.write(json.dumps(self.to_dict(workflow), **self.fmt))
        return os.path.join(dirname, f"{wf_id}.json")

    def get_workflow(self, filename, **kwargs) -> BpmnWorkflow:
        with open(filename) as fh:
            return self.from_dict(json.loads(fh.read()))

    def update_workflow(self, workflow, filename):
        with open(filename, "w") as fh:
            fh.write(json.dumps(self.to_dict(workflow), **self.fmt))

    def delete_workflow(self, filename) -> None:
        try:
            os.remove(filename)
        except FileNotFoundError:
            pass

    def list_workflows(
        self, include_completed
    ) -> list[tuple[str, str, str, str, str, str]]:
        instances = []
        for root, dirs, files in os.walk(os.path.join(self.dirname, "instance")):
            for f in files:
                filename = os.path.join(root, f)
                name = os.path.split(os.path.dirname(filename))[-1]
                stat = os.lstat(filename)
                created = datetime.fromtimestamp(stat.st_ctime).strftime(
                    "%Y-%^m-%d %H:%M:%S"
                )
                updated = datetime.fromtimestamp(stat.st_mtime).strftime(
                    "%Y-%^m-%d %H:%M:%S"
                )
                # '?' is active tasks -- we can't know this unless we reydrate the workflow
                # We also have to lose the ability to filter out completed workflows
                instances.append((filename, name, "-", created, updated, "-"))
        return instances


class WorkflowConverter(BpmnWorkflowConverter):
    def to_dict(self, workflow):
        dct = super(BpmnWorkflowConverter, self).to_dict(workflow)
        dct["bpmn_events"] = self.registry.convert(workflow.bpmn_events)
        dct["subprocesses"] = {}
        dct["tasks"] = list(dct["tasks"].values())
        return dct


class SubworkflowConverter(BpmnSubWorkflowConverter):
    def to_dict(self, workflow):
        dct = super().to_dict(workflow)
        dct["tasks"] = list(dct["tasks"].values())
        return dct


class WorkflowSpecConverter(BpmnProcessSpecConverter):
    def to_dict(self, spec):
        dct = super().to_dict(spec)
        dct["task_specs"] = list(dct["task_specs"].values())
        return dct


class SqliteSerializer(BpmnWorkflowSerializer):
    def __init__(self, dbname, **kwargs):
        self.dbname = dbname
        DEFAULT_CONFIG[BpmnWorkflow] = WorkflowConverter
        DEFAULT_CONFIG[BpmnSubWorkflow] = SubworkflowConverter
        DEFAULT_CONFIG[BpmnProcessSpec] = WorkflowSpecConverter
        super().__init__(registry=super().configure(DEFAULT_CONFIG), **kwargs)

    def create_workflow_spec(self, spec, dependencies):
        spec_id, new = self.execute(self._create_workflow_spec, spec)
        if new and len(dependencies) > 0:
            pairs = self.get_spec_dependencies(spec_id, spec, dependencies)
            # This handles the case where the participant requires an event to be kicked off
            added = list(map(lambda p: p[1], pairs))
            for name, child in dependencies.items():
                child_id, new_child = self.execute(self._create_workflow_spec, child)
                if new_child:
                    pairs |= self.get_spec_dependencies(child_id, child, dependencies)
                pairs.add((spec_id, child_id))
            self.execute(self._set_spec_dependencies, pairs)
        return spec_id

    def get_spec_dependencies(self, parent_id, parent, dependencies):
        # There ought to be an option in the parser to do this
        pairs = set()
        for task_spec in filter(
            lambda ts: isinstance(ts, SubWorkflowTask), parent.task_specs.values()
        ):
            child = dependencies.get(task_spec.spec)
            child_id, new = self.execute(self._create_workflow_spec, child)
            pairs.add((parent_id, child_id))
            if new:
                pairs |= self.get_spec_dependencies(child_id, child, dependencies)
        return pairs

    def get_workflow_spec(self, spec_id, include_dependencies=True):
        return self.execute(self._get_workflow_spec, spec_id, include_dependencies)

    def list_specs(self):
        return self.execute(self._list_specs)

    def delete_workflow_spec(self, spec_id):
        return self.execute(self._delete_workflow_spec, spec_id)

    def create_workflow(self, workflow, spec_id):
        return self.execute(self._create_workflow, workflow, spec_id)

    def get_workflow(self, wf_id, include_dependencies=True):
        return self.execute(self._get_workflow, wf_id, include_dependencies)

    def update_workflow(self, workflow, wf_id):
        return self.execute(self._update_workflow, workflow, wf_id)

    def list_workflows(self, include_completed=False):
        return self.execute(self._list_workflows, include_completed)

    def delete_workflow(self, wf_id):
        return self.execute(self._delete_workflow, wf_id)

    def _create_workflow_spec(self, session: Session, spec: BpmnProcessSpec):
        stmt = select(WorkflowSpec.id)
        row = session.exec(stmt).one_or_none()
        if row is None:
            dct = self.to_dict(spec)
            spec_id = uuid4()
            cursor.execute(
                "insert into workflow_specs (id, serialization) values (?, ?)",
                (spec_id, dct),
            )
            return spec_id, True
        else:
            return row

    def _set_spec_dependencies(self, cursor, values):
        cursor.executemany(
            "insert into _spec_dependency (parent_id, child_id) values (?, ?)", values
        )

    def _get_workflow_spec(self, cursor, spec_id, include_dependencies):
        cursor.execute(
            "select serialization as 'serialization [json]' from workflow_specs where id=?",
            (spec_id,),
        )
        spec = self.from_dict(cursor.fetchone()[0])
        subprocess_specs = {}
        if include_dependencies:
            subprocess_specs = self._get_subprocess_specs(cursor, spec_id)
        return spec, subprocess_specs

    def _get_subprocess_specs(self, cursor, spec_id):
        subprocess_specs = {}
        cursor.execute(
            "select serialization->>'name', serialization as 'serialization [json]' from spec_dependency where root=?",
            (spec_id,),
        )
        for name, serialization in cursor:
            subprocess_specs[name] = self.from_dict(serialization)
        return subprocess_specs

    def _list_specs(self, cursor):
        cursor.execute("select id, name, filename from spec_library")
        return cursor.fetchall()

    def _delete_workflow_spec(self, cursor, spec_id):
        try:
            cursor.execute("delete from workflow_specs where id=?", (spec_id,))
        except sqlite3.IntegrityError:
            logger.warning(
                f"Unable to delete spec {spec_id} because it is used by existing workflows"
            )

    def _create_workflow(self, cursor, workflow, spec_id):
        dct = super().to_dict(workflow)
        wf_id = uuid4()
        stmt = "insert into workflow (id, workflow_spec_id, serialization) values (?, ?, ?)"
        cursor.execute(stmt, (wf_id, spec_id, dct))
        if len(workflow.subprocesses) > 0:
            cursor.execute(
                "select serialization->>'name', descendant from spec_dependency where root=?",
                (spec_id,),
            )
            dependencies = dict((name, id) for name, id in cursor)
            for sp_id, sp in workflow.subprocesses.items():
                cursor.execute(
                    stmt, (sp_id, dependencies[sp.spec.name], self.to_dict(sp))
                )
        return wf_id

    def _get_workflow(self, cursor, wf_id, include_dependencies):
        cursor.execute(
            "select workflow_spec_id, serialization as 'serialization [json]' from workflow where id=?",
            (wf_id,),
        )
        row = cursor.fetchone()
        spec_id, workflow = row[0], self.from_dict(row[1])
        if include_dependencies:
            workflow.subprocess_specs = self._get_subprocess_specs(cursor, spec_id)
            cursor.execute(
                "select descendant as 'id [uuid]', serialization as 'serialization [json]' from workflow_dependency where root=? order by depth",
                (wf_id,),
            )
            for sp_id, sp in cursor:
                task = workflow.get_task_from_id(sp_id)
                workflow.subprocesses[sp_id] = self.from_dict(
                    sp, task=task, top_workflow=workflow
                )
        return workflow

    def _update_workflow(self, cursor, workflow, wf_id):
        dct = self.to_dict(workflow)
        cursor.execute(
            "select descendant as 'id [uuid]' from workflow_dependency where root=?",
            (wf_id,),
        )
        dependencies = [row[0] for row in cursor]
        cursor.execute(
            "select serialization->>'name', descendant as 'id [uuid]' from spec_dependency where root=(select workflow_spec_id from _workflow where id=?)",
            (wf_id,),
        )
        spec_dependencies = dict((name, spec_id) for name, spec_id in cursor)
        stmt = "update workflow set serialization=? where id=?"
        cursor.execute(stmt, (dct, wf_id))
        for sp_id, sp in workflow.subprocesses.items():
            sp_dct = self.to_dict(sp)
            if sp_id in dependencies:
                cursor.execute(stmt, (sp_dct, sp_id))
            else:
                cursor.execute(
                    "insert into workflow (id, workflow_spec_id, serialization) values (?, ?, ?)",
                    (sp_id, spec_dependencies[sp.spec.name], sp_dct),
                )

    def _list_workflows(self, cursor, include_completed):
        if include_completed:
            query = "select id, spec_name, active_tasks, started, updated, ended from instance"
        else:
            query = "select id, spec_name, active_tasks, started, updated, ended from instance where ended is null"
        cursor.execute(query)
        return cursor.fetchall()

    def _delete_workflow(self, cursor, wf_id):
        cursor.execute("delete from workflow where id=?", (wf_id,))

    def execute(self, func, *args, **kwargs):
        from fed_mng.db import engine
        with Session(engine) as session:
            #try:
                rv = func(session, *args, **kwargs)
                #conn.commit()
            #except Exception as exc:
            #    logger.error(str(exc), exc_info=True)
                #conn.rollback()
            # finally:
            #     cursor.close()
            #     conn.close()
        return rv
