from fastapi import status
from pytest_cases import case
from requests.exceptions import ConnectionError, Timeout


class CaseRoles:
    @case(tags="valid")
    def case_no_roles(self) -> dict:
        return {}

    @case(tags="valid")
    def case_single_role(self) -> dict[str, list[str]]:
        return {"result": ["role1"]}

    @case(tags="valid")
    def case_multi_roles(self) -> dict[str, list[str]]:
        return {"result": ["role1", "role2"]}

    @case(tags="http_exc")
    def case_bad_req(self) -> int:
        return status.HTTP_400_BAD_REQUEST

    @case(tags="http_exc")
    def case_server_err(self) -> int:
        return status.HTTP_500_INTERNAL_SERVER_ERROR

    @case(tags="conn_err")
    def case_timeout(self) -> type[Timeout]:
        return Timeout

    @case(tags="conn_err")
    def case_conn_err(self) -> type[ConnectionError]:
        return ConnectionError
