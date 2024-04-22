import json
import logging
import os
import re
from datetime import datetime
from uuid import uuid4

from SpiffWorkflow.bpmn.serializer.workflow import BpmnWorkflowSerializer
from SpiffWorkflow.bpmn.specs.bpmn_process_spec import BpmnProcessSpec
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow
from SpiffWorkflow.spiff.serializer.config import SPIFF_CONFIG

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
