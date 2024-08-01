import json
from logging import Logger
from typing import Any, Literal

from socketio import AsyncNamespace
from SpiffWorkflow.bpmn.specs.mixins.events.event_types import CatchingEvent
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow
from SpiffWorkflow.task import TaskState

from fed_mng.config import get_settings
from fed_mng.logger import create_logger
from fed_mng.socketio.utils import validate_auth_on_connect
from fed_mng.workflow.manager import engine as wf_engine


class SiteAdminNamespace(AsyncNamespace):
    def __init__(self, namespace=None):
        super().__init__(namespace)
        self.logger: Logger = create_logger(self.namespace)

    async def on_connect(
        self, sid: str, environ: dict[str, Any], auth: dict[Literal["token"], str]
    ):
        """When connecting evaluate user authentication."""
        self.logger.debug("Connecting to namespace")
        self.logger.debug("SID: %s", sid)
        self.logger.debug("Environment variables: %s", environ)
        validate_auth_on_connect(auth=auth, target_role=self.namespace[1:])
        self.logger.info("Connected to namespace with SID '%s'", sid)

    async def on_disconnect(self, sid):
        """Close connection

        Args:
            sid (_type_): _description_
        """
        self.logger.info("SID %s disconnected from namespace", sid)

    async def on_list_provider_federation_requests(self, sid, data):
        """List submitted requirest.

        Data contains the username or the user email to use to filter on provider
        federation requests.

        Args:
            sid (_type_): _description_
            data (_type_): _description_
        """
        self.logger.debug("Received data %s", data)
        await self.emit("list_provider_federation_requests", {"requests": [1]})
        # TODO: Retrieve list of federated providers

    async def on_submit_new_provider_federation_request(self, sid, data) -> None:
        """Submit a new provider federation request.

        Data contains the username or the user email of the issuer and the provider
        data.

        Args:
            sid (_type_): _description_
            data (_type_): _description_
        """
        self.logger.debug("Received data %s", data)

        # Retrieve workflows
        new_prov_req = "test"
        workflow_specs = wf_engine.list_specs(name=new_prov_req)
        assert (
            len(workflow_specs) > 0
        ), f"No workflow specification found with name={new_prov_req}"
        assert (
            len(workflow_specs) == 1
        ), f"Multiple workflow specifications found with name={new_prov_req}"

        # Start workflow
        wf_id = wf_engine.create_workflow(spec_id=workflow_specs[0][0])
        self.logger.info("Workflow started. ID: %s", wf_id)
        workflow = wf_engine.get_workflow(wf_id)
        await self.emit(
            "workflow_created", {"workflow": wf_engine.serializer.to_dict(workflow)}
        )

        # Start workflow
        await self._run_until_user_input_required(workflow)

    async def on_update_federated_provider(self, sid, data):
        """Submit a request to update an already federated provider.

        Data contains the updated provider data.

        Args:
            sid (_type_): _description_
            data (_type_): _description_
        """
        self.logger.debug("Received data %s", data)
        # TODO: Start a new workflow instance to update a provider

    async def on_delete_federated_provider(self, sid, data):
        """Submit a request to delete an already federated provider.

        Data contains the id of the target provider.

        Args:
            sid (_type_): _description_
            data (_type_): _description_
        """
        self.logger.debug("Received data %s", data)
        # TODO: Start a new workflow instance to delete a provider

    async def on_get_form(self, id) -> None:
        """Send a dict with the details to use to submit a new provider request."""
        settings = get_settings()
        with open(settings.NEW_PROV_FORM_JSON_SCHEMA) as f:
            data = json.load(f)

        idp_data = self._resolve_defs(
            data["properties"].pop("trusted_idps"), data["$defs"]
        )
        self.logger.debug("Identity provider section: %r", idp_data)
        provider_data = self._resolve_defs(
            data["properties"]["openstack"], data["$defs"]
        )
        self.logger.debug("Provider section: %r", provider_data)
        await self.emit("get_form", {"idp": idp_data, "provider": provider_data})

    def _resolve_defs(
        self, data: dict[str, Any], definitions: dict[str, dict]
    ) -> dict[str, dict]:
        """Convert the json schema in a more suitable dict.

        Expand $ref keys with the corresponding definitions.
        Move the required key inside the corresponding dict.

        Return the resolved dict.
        """
        resolved_data = {}

        # Expand references
        for key, value in data.items():
            if isinstance(value, dict):
                value = definitions.get(key) if value.get("$ref", None) else value
                resolved_data[key] = self._resolve_defs(value, definitions)
            else:
                resolved_data[key] = value

        # Add required flag to target item
        required_keys = resolved_data.pop("required", None)
        if required_keys is not None and isinstance(required_keys, list):
            for k in required_keys:
                resolved_data["properties"][k]["required"] = True

        if (
            resolved_data.get("type", None) == "string"
            and resolved_data.get("enum", None) is not None
        ):
            resolved_data["type"] = "select"
        return resolved_data

    async def _run_until_user_input_required(self, workflow: BpmnWorkflow):
        """"""
        task = workflow.get_next_task(state=TaskState.READY, manual=False)
        while task is not None:
            self.logger.info("Executing task %s", task.task_spec.bpmn_name)
            task.run()
            await self._run_ready_events(workflow)
            task = workflow.get_next_task(state=TaskState.READY, manual=False)
            self.logger.info(
                "Next task: %s", task.task_spec.bpmn_name if task else None
            )

    async def _run_ready_events(self, workflow: BpmnWorkflow):
        """Run all ready events."""
        workflow.refresh_waiting_tasks()
        task = workflow.get_next_task(state=TaskState.READY, spec_class=CatchingEvent)
        while task is not None:
            task.run()
            task = workflow.get_next_task(
                state=TaskState.READY, spec_class=CatchingEvent
            )
            await self.emit(
                "update_workflow_state",
                {"workflow": wf_engine.serializer.to_dict(workflow)},
            )
