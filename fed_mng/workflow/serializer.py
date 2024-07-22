import json
import logging
import os
import re
import sqlite3
from datetime import datetime
from typing import Any
from uuid import uuid4

from SpiffWorkflow.bpmn.serializer.default.workflow import BpmnSubWorkflowConverter
from SpiffWorkflow.bpmn.serializer.workflow import BpmnWorkflowSerializer
from SpiffWorkflow.bpmn.specs.bpmn_process_spec import BpmnProcessSpec
from SpiffWorkflow.bpmn.specs.mixins.subworkflow_task import SubWorkflowTask
from SpiffWorkflow.bpmn.workflow import BpmnSubWorkflow, BpmnWorkflow
from SpiffWorkflow.spiff.serializer.config import DEFAULT_CONFIG, SPIFF_CONFIG
from sqlmodel import Session, select

from fed_mng.models import (
    Task,
    TaskData,
    TaskSpec,
    Workflow,
    WorkflowData,
    WorkflowSpec,
    WorkflowSpecDependency,
)

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
        depdir = os.path.join(dirname, "dependencies")
        if os.path.exists(depdir):
            for f in os.listdir(depdir):
                name = re.sub(r"\.json$", "", os.path.basename(f))
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
        for root, _, files in os.walk(os.path.join(self.dirname, "instance")):
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
                # '?' is active tasks -- we can't know this unless we reydrate the
                # workflow. We also have to lose the ability to filter out completed
                # workflows
                instances.append((filename, name, "-", created, updated, "-"))
        return instances


class SubworkflowConverter(BpmnSubWorkflowConverter):
    def to_dict(self, workflow):
        dct = super().to_dict(workflow)
        dct["tasks"] = list(dct["tasks"].values())
        return dct


class SqliteSerializer(BpmnWorkflowSerializer):
    def __init__(self, dbname, **kwargs):
        self.dbname = dbname
        DEFAULT_CONFIG[BpmnSubWorkflow] = SubworkflowConverter
        super().__init__(registry=super().configure(DEFAULT_CONFIG), **kwargs)

    def list_specs(self, *, name: str | None = None) -> list[tuple[str, str, str]]:
        """List workflow specifications.

        Returns:
            list[tuple[str, str, str]]: List of ID, spec name and filename.
        """
        return self.execute(self._list_specs, name=name)

    def create_workflow_spec(
        self, spec: BpmnProcessSpec, dependencies: list[BpmnProcessSpec]
    ) -> int:
        """Add the workflow specification and its dependecies to the DB.

        Args:
            spec (BpmnProcessSpec): target workflow specification
            dependencies (list[BpmnProcessSpec]): list of workflows specifications

        Returns:
            int: Workflow specification ID in the DB.
        """
        spec_id = self.execute(self._create_workflow_spec, spec)
        # if new and len(dependencies) > 0:
        #     pairs = self.get_spec_dependencies(spec_id, spec, dependencies)
        #     # This handles the case where the participant requires an event to be kicked off
        #     added = list(map(lambda p: p[1], pairs))
        #     for name, child in dependencies.items():
        #         child_id, new_child = self.execute(self._create_workflow_spec, child)
        #         if new_child:
        #             pairs |= self.get_spec_dependencies(child_id, child, dependencies)
        #         pairs.add((spec_id, child_id))
        #     self.execute(self._set_spec_dependencies, pairs)
        return spec_id

    # def get_spec_dependencies(self, parent_id, parent, dependencies):
    #     # There ought to be an option in the parser to do this
    #     pairs = set()
    #     for task_spec in filter(
    #         lambda ts: isinstance(ts, SubWorkflowTask), parent.task_specs.values()
    #     ):
    #         child = dependencies.get(task_spec.spec)
    #         child_id, new = self.execute(self._create_workflow_spec, child)
    #         pairs.add((parent_id, child_id))
    #         if new:
    #             pairs |= self.get_spec_dependencies(child_id, child, dependencies)
    #     return pairs

    def get_workflow_spec(
        self, spec_id: int, include_dependencies: bool = True
    ) -> tuple[BpmnProcessSpec, list[BpmnProcessSpec]]:
        """Return the target workflow specification.

        Args:
            spec_id (int): ID of the target workflow specification
            include_dependencies (bool, optional): Include dependencies in the returned
                object. Defaults to True.

        Returns:
            tuple[BpmnProcessSpec, list[BpmnProcessSpec]]: The first item is the target
                workflow specification, the second is the list of the sub workflow
                specifications.
        """
        return self.execute(self._get_workflow_spec, spec_id, include_dependencies)

    def delete_workflow_spec(self, spec_id: int) -> None:
        """Delete target workflow specification.

        Args:
            spec_id (int): ID of the target workflow specification.
        """
        return self.execute(self._delete_workflow_spec, spec_id)

    def create_workflow(self, workflow: BpmnWorkflow, spec_id: int) -> int:
        """Add a workflow to the DB and link it to the corresponding spec.

        Args:
            workflow (BpmnWorkflow): Workflow instance to save.
            spec_id (int): ID of the target spec.

        Returns:
            int: Workflow ID in the DB.
        """
        return self.execute(self._create_workflow, workflow, spec_id)

    def get_workflow(
        self, wf_id: int, include_dependencies: bool = True
    ) -> BpmnWorkflow:
        """Retrieve a specific workflow instance and its dependencies from the DB.

        Args:
            wf_id (int): ID of the workflow instance.
            include_dependencies (bool, optional): _description_. Defaults to True.

        Returns:
            BpmnWorkflow: the target workflow instance.
        """
        return self.execute(self._get_workflow, wf_id, include_dependencies)

    def update_workflow(self, workflow: BpmnWorkflow, wf_id: int) -> None:
        """Update workflow information.

        Args:
            workflow (BpmnWorkflow): Updated BPMN workflow
            wf_id (int): ID of the workflow instance to update.
        """
        return self.execute(self._update_workflow, workflow, wf_id)

    def list_workflows(
        self, include_completed: bool = False
    ) -> list[tuple[str, str, str, str, str, str]]:
        """List running, and optionally completed, workflow instances.

        Args:
            include_completed (bool, optional): Flag to include completed instances.
                Defaults to False.

        Returns:
            list[Workflow]: List of all instances or just running ones.
        """
        return self.execute(self._list_workflows, include_completed)

    def delete_workflow(self, wf_id: int) -> None:
        """Delete a specific workflow instance.

        Args:
            wf_id (int): ID of the workflow instance
        """
        return self.execute(self._delete_workflow, wf_id)

    def execute(self, func, *args, **kwargs):
        # TODO fix modules import
        from fed_mng.db import engine

        with Session(engine) as session:
            try:
                rv = func(session, *args, **kwargs)
            except Exception as exc:
                logger.exception(str(exc))
                session.rollback()
        return rv

    def _list_specs(
        self, session: Session, *, name: str | None = None
    ) -> list[tuple[str, str, str]]:
        """Retrieve the list of workflow specifications.

        Args:
            session (Session): Session to use to execute DB queries.

        Returns:
            list[str, str, str]: List of ID, spec name and filename.
        """
        filters = [WorkflowSpecDependency.child_id == None]  # noqa: E711
        if name is not None:
            filters.append(WorkflowSpec.name == name)
        stmt = (
            select(WorkflowSpec.id, WorkflowSpec.name, WorkflowSpec.file)
            .outerjoin(
                WorkflowSpecDependency,
                WorkflowSpec.id == WorkflowSpecDependency.child_id,
            )
            .filter(*filters)
            .distinct()
        )
        return session.exec(stmt).all()

    def _create_workflow_spec(self, session: Session, spec: BpmnProcessSpec) -> int:
        """Add workflow specification to the DB.

        Args:
            session (Session): Session to use to execute DB queries.
            spec (BpmnProcessSpec): Workflows specification to add to the DB.

        Returns:
            int: ID of the generated DB entity.
        """
        stmt = select(WorkflowSpec.id).where(
            WorkflowSpec.name == spec.name, WorkflowSpec.file == spec.file
        )
        row = session.exec(stmt).one_or_none()
        if row is None:
            dct = self.to_dict(spec)
            task_specs: dict[str, dict] = dct.pop("task_specs", {})
            workflow_spec = WorkflowSpec(**dct)
            task_specs_dict: dict[str, TaskSpec] = {}

            # Map the task spec dicts in SQL task specs
            # (do not map inputs and outputs here)
            for name, task_spec in task_specs.items():
                inputs = task_spec.pop("inputs", [])
                outputs = task_spec.pop("outputs", [])
                event_definition = json.dumps(task_spec.pop("event_definition", None))
                cond_task_specs = json.dumps(task_spec.pop("cond_task_specs", None))
                task_specs_dict[name] = TaskSpec(
                    **task_spec,
                    event_definition=event_definition,
                    cond_task_specs=cond_task_specs,
                )
                task_spec["inputs"] = inputs
                task_spec["outputs"] = outputs
                workflow_spec.task_specs.append(task_specs_dict[name])

            # Copy inputs and outputs as relationships
            for name, task_spec in task_specs.items():
                for out_task in task_spec.get("outputs", []):
                    task_specs_dict[name].outputs.append(task_specs_dict[out_task])

            session.add(workflow_spec)
            session.commit()
            return workflow_spec.id
        else:
            return row

    # def _set_spec_dependencies(self, cursor, values):
    #     cursor.executemany(
    #         "insert into _spec_dependency (parent_id, child_id) values (?, ?)", values
    #     )

    def _get_workflow_spec(
        self, session: Session, spec_id: int, include_dependencies: bool
    ) -> tuple[BpmnProcessSpec, list[BpmnProcessSpec]]:
        """Retrieve a specific workflow specification from the DB.

        Args:
            session (Session): Session to use to execute DB queries.
            spec_id (int): Workflows specification to retrieve from the DB.
            include_dependencies (bool): _description_

        Returns:
            tuple[BpmnProcessSpec, list[BpmnProcessSpec]]: The first item is the target
                workflow specification, the second is the list of the sub workflow
                specifications.
        """
        stmt = select(WorkflowSpec).where(WorkflowSpec.id == spec_id)
        row = session.exec(stmt).one_or_none()
        if row is not None:
            dct = self._recreate_workflow_spec_dict_from_db_item(row)
        spec = self.from_dict(dct)
        subprocess_specs = {}
        # if include_dependencies:
        #     subprocess_specs = self._get_subprocess_specs(cursor, spec_id)
        return spec, subprocess_specs

    # def _get_subprocess_specs(self, cursor, spec_id):
    #     subprocess_specs = {}
    #     cursor.execute(
    #         "select serialization->>'name', serialization as 'serialization [json]' from spec_dependency where root=?",
    #         (spec_id,),
    #     )
    #     for name, serialization in cursor:
    #         subprocess_specs[name] = self.from_dict(serialization)
    #     return subprocess_specs

    def _delete_workflow_spec(self, session: Session, spec_id: int) -> None:
        """Delete target workflow specification from DB.

        Args:
            session (Session): Session to use to execute DB queries.
            spec_id (int): Workflows specification to delete from the DB.
        """
        try:
            stmt = select(WorkflowSpec).where(WorkflowSpec.id == spec_id)
            item = session.exec(stmt).first()
            if item is not None:
                session.delete(item)
                session.commit()
            else:
                logger.warning("Unable to find process spec with id: %d", spec_id)
        except sqlite3.IntegrityError:
            logger.warning(
                "Unable to delete process spec %d because used by existing workflows",
                spec_id,
            )

    def _create_workflow(
        self, session: Session, bpmn_workflow: BpmnWorkflow, spec_id: int
    ) -> int:
        """Create an entry in the DB matching the target workflow.

        Args:
            session (Session): Session to use to execute DB queries.
            wf_id (int): ID of the workflow instance.
            spec_id (int): ID of the corresponding workflow specification.

        Returns:
            int: ID of the workflow instance.
        """
        dct = self.to_dict(bpmn_workflow)
        wf_data: dict[str, dict] = dct.pop("data", {})
        tasks: dict[str, dict] = dct.pop("tasks", {})
        workflow = Workflow(workflow_spec_id=spec_id, **dct)
        for k, v in wf_data:
            wd = WorkflowData(name=k, value=v)
            workflow.workflow_data.append(wd)

        active_tasks = 0
        tasks_dict: dict[str, Task] = {}
        for name, task in tasks.items():
            if task.get("state") >= 8 and task.get("state") <= 32:
                active_tasks += 1
            t_data = task.pop("data", {})
            task_spec_name = task.pop("task_spec")
            parent = task.pop("parent", None)
            children = task.pop("children", [])
            tasks_dict[name] = Task(task_spec_name=task_spec_name, **task)
            for k, v in t_data:
                td = TaskData(name=k, value=v)
                tasks_dict[name].task_data.append(td)
            task["parent"] = parent
            task["children"] = children
            workflow.tasks.append(tasks_dict[name])
        workflow.active_tasks = active_tasks

        # Copy inputs and outputs as relationships
        for name, task in tasks.items():
            for child_task in task.get("children", []):
                tasks_dict[name].children.append(tasks_dict[child_task])

        session.add(workflow)
        session.commit()
        # if len(workflow.subprocesses) > 0:
        #     cursor.execute(
        #         "select serialization->>'name', descendant from spec_dependency where root=?",
        #         (spec_id,),
        #     )
        #     dependencies = dict((name, id) for name, id in cursor)
        #     for sp_id, sp in workflow.subprocesses.items():
        #         cursor.execute(
        #             stmt, (sp_id, dependencies[sp.spec.name], self.to_dict(sp))
        #         )
        return workflow.id

    def _get_workflow(
        self, session: Session, wf_id: int, include_dependencies: bool
    ) -> BpmnWorkflow:
        """_summary_

        Args:
            session (Session): Session to use to execute DB queries.
            wf_id (int): ID of the workflow instance.
            include_dependencies (bool): _description_

        Returns:
            BpmnWorkflow: the target workflow instance.
        """
        stmt = select(Workflow).where(Workflow.id == wf_id)
        row = session.exec(stmt).one()
        dct = row.model_dump()
        dct["spec"] = self._recreate_workflow_spec_dict_from_db_item(row.workflow_spec)
        dct["tasks"] = {
            t.id: self._recreate_task_dict_from_db_item(t) for t in row.tasks
        }
        workflow = self.from_dict(dct)
        # spec_id = row.workflow_spec_id
        # if include_dependencies:
        #     workflow.subprocess_specs = self._get_subprocess_specs(cursor, spec_id)
        #     cursor.execute(
        #         "select descendant as 'id [uuid]', serialization as 'serialization [json]' from workflow_dependency where root=? order by depth",
        #         (wf_id,),
        #     )
        #     for sp_id, sp in cursor:
        #         task = workflow.get_task_from_id(sp_id)
        #         workflow.subprocesses[sp_id] = self.from_dict(
        #             sp, task=task, top_workflow=workflow
        #         )
        return workflow

    def _update_workflow(
        self, session: Session, workflow: BpmnWorkflow, wf_id: int
    ) -> None:
        # dct = self.to_dict(workflow)
        # cursor.execute(
        #     "select descendant as 'id [uuid]' from workflow_dependency where root=?",
        #     (wf_id,),
        # )
        # dependencies = [row[0] for row in cursor]
        # cursor.execute(
        #     "select serialization->>'name', descendant as 'id [uuid]' from spec_dependency where root=(select workflow_spec_id from _workflow where id=?)",
        #     (wf_id,),
        # )
        # spec_dependencies = dict((name, spec_id) for name, spec_id in cursor)
        # stmt = "update workflow set serialization=? where id=?"
        # cursor.execute(stmt, (dct, wf_id))
        # for sp_id, sp in workflow.subprocesses.items():
        #     sp_dct = self.to_dict(sp)
        #     if sp_id in dependencies:
        #         cursor.execute(stmt, (sp_dct, sp_id))
        #     else:
        #         cursor.execute(
        #             "insert into workflow (id, workflow_spec_id, serialization) values (?, ?, ?)",
        #             (sp_id, spec_dependencies[sp.spec.name], sp_dct),
        #         )

        stmt = select(Workflow).where(Workflow.id == wf_id)
        row = session.exec(stmt).one()
        db_tasks = {t.id: t for t in row.tasks}
        db_wf_data = {d.name: d for d in row.workflow_data}

        dct = self.to_dict(workflow)
        wf_data: dict[str, dict] = dct.pop("data", {})
        tasks: dict[str, dict] = dct.pop("tasks", {})

        exclude_task_data = []
        exclude_tasks = list(set(db_tasks.keys()) - set(tasks.keys()))
        exclude_data = list(set(db_wf_data.keys()) - set(wf_data.keys()))

        for k, v in wf_data:
            d = db_wf_data.get(k, None)
            if d is None:
                wd = WorkflowData(name=k, value=v)
                row.workflow_data.append(wd)
            else:
                d.value = v

        ended = True
        tasks_dict: dict[str, Task] = {}
        for name, task in tasks.items():
            if task.get("state") < 64:
                ended = False

            tasks_dict[name] = db_tasks.get(name, None)
            if tasks_dict[name] is None:
                if task.get("state") >= 8 and task.get("state") <= 32:
                    row.active_tasks += 1
                t_data = task.pop("data", {})
                parent = task.pop("parent", None)
                children = task.pop("children", [])
                task_spec_name = task.pop("task_spec")
                tasks_dict[name] = Task(task_spec_name=task_spec_name, **task)
                for k, v in t_data:
                    td = TaskData(name=k, value=v)
                    tasks_dict[name].task_data.append(td)
                task["parent"] = parent
                task["children"] = children
                row.tasks.append(tasks_dict[name])
            elif task.get("last_state_change") > tasks_dict[name].last_state_change:
                # TODO update Task attributes
                t_data: dict[str, dict] = task.pop("data", {})
                db_task_data = {d.name: d for d in tasks_dict[name].task_data}
                exclude_task_data += list(set(db_task_data.keys()) - set(t_data.keys()))
                for k, v in t_data:
                    d = db_task_data.get(k, None)
                    if d is None:
                        td = TaskData(name=k, value=v)
                        tasks_dict[name].task_data.append(td)
                    else:
                        d.value = v

        # Copy inputs and outputs as relationships
        for name, task in tasks.items():
            for child_task in task.get("children", []):
                tasks_dict[name].children.append(tasks_dict[child_task])

        # TODO update workflow attributes

        for k in exclude_tasks:
            session.delete(db_tasks.get(k))
        for k in exclude_task_data:
            session.delete(db_task_data.get(k))
        for k in exclude_data:
            session.delete(db_wf_data.get(k))
        session.commit()

    def _list_workflows(
        self, session: Session, include_completed: bool
    ) -> list[tuple[str, str, str, str, str, str]]:
        """Get the list of workflow instances.

        Args:
            session (Session): Session to use to execute DB queries.
            include_completed (bool): filter on completed instances only.

        Returns:
            list[tuple[str, str, str, str, str, str]]: List of all instances or jus
                running ones.
        """
        stmt = select(
            Workflow.id,
            WorkflowSpec.name,
            Workflow.active_tasks,
            Workflow.started,
            Workflow.updated,
            Workflow.ended,
        ).join(WorkflowSpec)
        if not include_completed:
            stmt.where(Workflow.ended is None)
        return session.exec(stmt).all()

    def _delete_workflow(self, session: Session, wf_id: int) -> None:
        """Delete a specific workflow from the DB.

        Args:
            session (Session): Session to use to execute DB queries.
            wf_id (int): ID of the workflow instance.
        """
        stmt = select(Workflow).where(Workflow.id == wf_id)
        item = session.exec(stmt).first()
        if item is not None:
            session.delete(item)
            session.commit()
        else:
            logger.warning("Unable to find workflow with id: %d", wf_id)

    def _recreate_workflow_spec_dict_from_db_item(
        self, item: WorkflowSpec
    ) -> dict[str, Any]:
        """From the DB item correctly recreate the dict to be converted.

        Args:
            item (WorkflowSpec): DB instance.

        Returns:
            dict[str, Any]: Dict with correct keys and values.
        """
        dct = item.model_dump()
        dct["task_specs"] = {}
        for t in item.task_specs:
            dct["task_specs"][t.name] = self._recreate_task_spec_dict_from_db_item(t)
        return dct

    def _recreate_task_spec_dict_from_db_item(self, item: TaskSpec) -> dict[str, Any]:
        """From the DB item correctly recreate the dict to be converted.

        Args:
            item (TaskSpec): DB instance

        Returns:
            dict[str, Any]: Dict with correct keys and values.
        """
        dct = item.model_dump()
        dct["event_definition"] = json.loads(item.event_definition)
        dct["cond_task_specs"] = json.loads(item.cond_task_specs)
        dct["inputs"] = [x.name for x in item.inputs]
        dct["outputs"] = [x.name for x in item.outputs]
        return dct

    def _recreate_task_dict_from_db_item(self, item: Task) -> dict[str, Any]:
        """From the DB item correctly recreate the dict to be converted.

        Args:
            item (Task): DB instance

        Returns:
            dict[str, Any]: Dict with correct keys and values.
        """
        dct = item.model_dump()
        dct["parent"] = item.parent.id if item.parent is not None else None
        dct["children"] = [i.id for i in item.children]
        dct["internal_data"] = {}  # TODO fix
        dct["task_spec"] = item.task_spec_name
        dct["data"] = { i.name: i.value for i in item.task_data }
        return dct
