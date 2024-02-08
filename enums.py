from enum import Enum


class RequestType(Enum):
    PROVIDER_FEDERATION: str = "provider_federation"
    RESOURCE_USAGE: str = "resource_usage"
    SLA_NEGOTIATION: str = "sla_negotiation"


class ProviderFederationStatus(Enum):
    SUBMITTED: str = "submitted"
    ASSIGNED: str = "assigned"
    FAILED: str = "failed"
    ACCEPTED: str = "accepted"


class ProviderFederationType(Enum):
    CREATE: str = "create"
    UPDATE: str = "update"
    DELETE: str = "delete"


class ResourceUsageStatus(Enum):
    SUBMITTED: str = "submitted"
    REJECTED: str = "rejected"
    NEGOTIATION: str = "negotiation"
    VALIDATION: str = "validation"
    READY: str = "ready"
    COMPLETED: str = "completed"


class SLANegotiationStatus(Enum):
    SUBMITTED: str = "submitted"
    REJECTED: str = "rejected"
    ACCEPTED: str = "accepted"


class SLAStatus(Enum):
    DISCUSSING: str = "discussing"
    CANCELED: str = "canceled"
    CREATED: str = "created"
    ACCEPTED: str = "accepted"
    VALIDATED: str = "validated"
    COMPLETED: str = "completed"
