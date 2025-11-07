"""Unit tests for user group dependencies in the identity providers module.

Covers:
- sla_required: ensures 404 is raised if parent_idp is None, otherwise does
    nothing.
"""

import uuid
from unittest.mock import MagicMock

import pytest

from fed_mgr.exceptions import ItemNotFoundError
from fed_mgr.v1.identity_providers.user_groups.slas.dependencies import sla_required


def test_sla_required_success():
    """Test sla_required does not raise when parent_sla is provided."""
    sla_id = uuid.uuid4()
    sla = MagicMock()  # Simulate a found user group
    assert sla_required(sla_id, sla) == sla


def test_sla_required_not_found():
    """Test sla_required raises 404 and when parent_sla is None."""
    sla_id = uuid.uuid4()
    sla = None
    with pytest.raises(
        ItemNotFoundError, match=f"SLA with ID '{sla_id!s}' does not exist"
    ):
        sla_required(sla_id, sla)
