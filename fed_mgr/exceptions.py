"""Custom common exceptions."""

import uuid
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse


class UnauthenticatedError(Exception):
    """Exception raised when authentication fails.

    This exception should be raised when a user or system fails to authenticate
    properly, typically due to invalid or missing credentials.

    Args:
        message (str): The error message describing the authentication failure.
        *args: Additional arguments to pass to the base Exception class.

    """

    def __init__(self, message: str, *args):
        """Initialize the exception with a custom error message.

        Args:
            message (str): The error message describing the exception.
            *args: Additional arguments to pass to the base Exception class.

        """
        self.message = message
        super().__init__(self.message, *args)


class UnauthorizedError(Exception):
    """Exception raised for unauthorized access errors.

    Attributes:
        message (str): Explanation of the error.

    Args:
        message (str): Description of the unauthorized error.
        *args: Variable length argument list to pass to the base Exception class.

    """

    def __init__(self, message: str, *args):
        """Initialize the exception with a custom error message.

        Args:
            message (str): The error message describing the exception.
            *args: Additional arguments to pass to the base Exception class.

        """
        self.message = message
        super().__init__(self.message, *args)


class NotNullError(Exception):
    """Exception raised when a None value is not acceptale during DB insertion."""

    def __init__(self, entity: str, attr: str):
        """Initialize NotNullError with a specific error message."""
        self.entity = entity
        self.attr = attr
        self.message = f"Attribute '{attr}' of {entity} can't be NULL"
        super().__init__(self.message)


class ConflictError(Exception):
    """Exception raised when there is a CONFLICT during a DB insertion."""

    def __init__(self, entity: str, attr: str, value: Any):
        """Initialize ConflictError with a specific error message."""
        self.entity = entity
        self.attr = attr
        self.value = value
        if self.value is None:
            self.message = f"{self.entity} with {self.attr} already exists"
        else:
            self.message = f"{self.entity} with {self.attr}={self.value!s} already "
            self.message += "exists"
        super().__init__(self.message)


class ProviderStateError(Exception):
    """Exception raised when the proposed state change fails."""

    def __init__(self, message: str, *args):
        """Initialize ProviderStateError with a specific error message."""
        self.message = message
        super().__init__(self.message, *args)


class ItemNotFoundError(Exception):
    """Exception raised when the target ID does not match a user in the DB."""

    def __init__(self, message: str, *args):
        """Initialize ItemNotFoundError with a specific error message."""
        self.message = message
        super().__init__(self.message, *args)


class DeleteFailedError(Exception):
    """Exception raised when the delete operations has no effect."""

    def __init__(
        self,
        entity: str,
        *,
        id: uuid.UUID | None = None,
        params: dict[str, Any] | None = None,
    ):
        """Initialize DeleteFailedError with a specific error message."""
        self.entity = entity
        self.entity_id = id
        self.entity_params = params
        if id is not None:
            self.message = f"{self.entity} with ID '{self.entity_id}' can't be deleted."
        else:
            self.message = f"{self.entity} with given key-value pairs does not exist: "
            self.message += f"{self.entity_params!s}."
        self.message += f" Check target {self.entity} has no children entities."
        super().__init__(self.message)


class BadRequestError(Exception):
    """Exception raised when input request is invalid."""

    def __init__(self, message: str):
        """Initialize BadRequest with a specific error message."""
        self.message = message
        super().__init__(self.message)


class KafkaError(Exception):
    """Exception raised when communicating with kafka."""

    def __init__(self):
        """Initialize KafkaError with a specific error message."""
        self.message = "Communication with kafka failed."
        super().__init__(self.message)


class DatabaseOperationError(Exception):
    """Generic Database erorr raised by an invalid operation."""

    def __init__(self, message: str):
        """Initialize KafkaError with a specific error message."""
        self.message = message
        super().__init__(self.message)


class ServiceUnreachableError(Exception):
    """Exception raised when a service cannot be reached.

    Attributes:
        service (str): Service name.
        message (str): Explanation of the error.
        *args: Additional arguments to pass to the base Exception class.

    """

    def __init__(self, service: str, message: str, *args):
        """Initialize error class instance.

        Args:
            service (str): Service name.
            message (str): The error message describing the issue.
            *args: Variable length argument list to pass to parent class.

        """
        self.message = f"{service}: {message}"
        super().__init__(self.message, *args)


class ServiceUnexpectedResponse(Exception):  # noqa: N818
    """Exception raised when a service returns unexpected response.

    Attributes:
        service (str): Service name.
        message (str): Explanation of the error.
        *args: Additional arguments to pass to the base Exception class.

    """

    def __init__(self, service: str, message: str, *args):
        """Initialize error class instance.

        Args:
            service (str): Service name.
            message (str): The error message describing the issue.
            *args: Variable length argument list to pass to parent class.

        """
        self.message = f"{service}: {message}"
        super().__init__(self.message, *args)


def add_exception_handlers(app: FastAPI) -> None:  # noqa: C901
    """Add exception handlers to app."""

    @app.exception_handler(UnauthenticatedError)
    def unauthenticated_exception_handler(
        request: Request, exc: UnauthenticatedError
    ) -> JSONResponse:
        """Handle UnauthenticatedError errors by returning a JSON response.

        The new object contains the exception's status code and detail.

        Args:
            request (Request): The incoming HTTP request that caused the exception.
            exc (UnauthenticatedError): The exception instance.

        Returns:
            JSONResponse: A JSON response with the status code and detail of the
                exception.

        """
        request.state.logger.error(exc.message)
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"status": status.HTTP_401_UNAUTHORIZED, "detail": exc.message},
        )

    @app.exception_handler(UnauthorizedError)
    def unauthorized_exception_handler(
        request: Request, exc: UnauthorizedError
    ) -> JSONResponse:
        """Handle UnauthorizedError errors by returning a JSON response.

        The new object contains the exception's status code and detail.

        Args:
            request (Request): The incoming HTTP request that caused the exception.
            exc (UnauthorizedError): The exception instance.

        Returns:
            JSONResponse: A JSON response with the status code and detail of the
                exception.

        """
        request.state.logger.error(exc.message)
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"status": status.HTTP_403_FORBIDDEN, "detail": exc.message},
        )

    @app.exception_handler(ItemNotFoundError)
    def item_not_found_exception_handler(
        request: Request, exc: ItemNotFoundError
    ) -> JSONResponse:
        """Handle ItemNotFoundError errors by returning a JSON response.

        The new object contains the exception's status code and detail.

        Args:
            request (Request): The incoming HTTP request that caused the exception.
            exc (ItemNotFoundError): The exception instance.

        Returns:
            JSONResponse: A JSON response with the status code and detail of the
                exception.

        """
        request.state.logger.error(exc.message)
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"status": status.HTTP_404_NOT_FOUND, "detail": exc.message},
        )

    @app.exception_handler(ConflictError)
    def conflict_exception_handler(
        request: Request, exc: ConflictError
    ) -> JSONResponse:
        """Handle ConflictError errors by returning a JSON response.

        The new object contains the exception's status code and detail.

        Args:
            request (Request): The incoming HTTP request that caused the exception.
            exc (ConflictError): The exception instance.

        Returns:
            JSONResponse: A JSON response with the status code and detail of the
                exception.

        """
        request.state.logger.error(exc.message)
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"status": status.HTTP_409_CONFLICT, "detail": exc.message},
        )

    @app.exception_handler(DeleteFailedError)
    def delete_failed_exception_handler(
        request: Request, exc: DeleteFailedError
    ) -> JSONResponse:
        """Handle DeleteFailedError errors by returning a JSON response.

        The new object contains the exception's status code and detail.

        Args:
            request (Request): The incoming HTTP request that caused the exception.
            exc (DeleteFailedError): The exception instance.

        Returns:
            JSONResponse: A JSON response with the status code and detail of the
                exception.

        """
        request.state.logger.error(exc.message)
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"status": status.HTTP_409_CONFLICT, "detail": exc.message},
        )

    @app.exception_handler(ProviderStateError)
    def flaat_unauthenticated_exception_handler(
        request: Request, exc: ProviderStateError
    ) -> JSONResponse:
        """Handle ProviderStateError errors by returning a JSON response.

        The new object contains the exception's status code and detail.

        Args:
            request (Request): The incoming HTTP request that caused the exception.
            exc (ProviderStateError): The exception instance.

        Returns:
            JSONResponse: A JSON response with the status code and detail of the
                exception.

        """
        request.state.logger.error(exc.message)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"status": status.HTTP_400_BAD_REQUEST, "detail": exc.message},
        )

    @app.exception_handler(ServiceUnreachableError)
    def service_ureachable_exception_handler(
        request: Request, exc: ServiceUnreachableError
    ) -> JSONResponse:
        """Handle ServiceUnreachableError errors by returning a JSON response.

        The new object contains the exception's status code and detail.

        Args:
            request (Request): The incoming HTTP request that caused the exception.
            exc (ServiceUnreachableError): The exception instance.

        Returns:
            JSONResponse: A JSON response with the status code and detail of the
                exception.

        """
        request.state.logger.error(exc.message)
        return JSONResponse(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            content={"status": status.HTTP_504_GATEWAY_TIMEOUT, "detail": exc.message},
        )

    @app.exception_handler(ServiceUnexpectedResponse)
    def service_unexpected_resp_exception_handler(
        request: Request, exc: ServiceUnexpectedResponse
    ) -> JSONResponse:
        """Handle ServiceUnexpectedResponse errors by returning a JSON response.

        The new object contains the exception's status code and detail.

        Args:
            request (Request): The incoming HTTP request that caused the exception.
            exc (ServiceUnexpectedResponse): The exception instance.

        Returns:
            JSONResponse: A JSON response with the status code and detail of the
                exception.

        """
        request.state.logger.error(exc.message)
        return JSONResponse(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            content={"status": status.HTTP_504_GATEWAY_TIMEOUT, "detail": exc.message},
        )

    @app.exception_handler(HTTPException)
    def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """Handle HTTPException errors by returning a JSON response.

        The new object contains the exception's status code and detail.

        Args:
            request (Request): The incoming HTTP request that caused the exception.
            exc (HTTPException): The HTTP exception instance.

        Returns:
            JSONResponse: A JSON response with the status code and detail of the
                exception.

        """
        request.state.logger.error(exc.message)
        return JSONResponse(
            status_code=exc.status_code,
            content={"status": exc.status_code, "detail": exc.detail},
        )

    @app.exception_handler(BadRequestError)
    def bad_request_handler(request: Request, exc: BadRequestError) -> JSONResponse:
        """Handle BadRequestError errors by returning a JSON response.

        The new object contains the exception's status code and detail.

        Args:
            request (Request): The incoming HTTP request that caused the exception.
            exc (BadRequestError): The exception instance.

        Returns:
            JSONResponse: A JSON response with the status code and detail of the
                exception.

        """
        request.state.logger.error(exc.message)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"status": status.HTTP_400_BAD_REQUEST, "detail": exc.message},
        )

    # @app.exception_handler(KafkaConnectionError)
    # def kafka_connection_error_handler(
    #     request: Request, exc: KafkaConnectionError
    # ) -> JSONResponse:
    #     """Handle KafkaConnectionError errors by returning a JSON response.

    #     The new object contains the exception's status code and detail.

    #     Args:
    #         request (Request): The incoming HTTP request that caused the exception.
    #         exc (KafkaConnectionError): The exception instance.

    #     Returns:
    #         JSONResponse: A JSON response with the status code and detail of the
    #             exception.

    #     """
    #     return JSONResponse(
    #         status_code=status.HTTP_504_GATEWAY_TIMEOUT,
    #         content={
    #             "status": status.HTTP_504_GATEWAY_TIMEOUT,
    #             "detail": exc.args[0],
    #         },
    #     )
