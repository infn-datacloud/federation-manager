"""Unit tests for v1 common schemas.

Covers:
- ItemID default UUID generation
- ErrorMessage field assignment
- CreationQuery and UpdateQuery datetime fields
- PaginationQuery default values
- Pagination total_pages calculation
- PageNavigation field types and navigation logic
- PaginatedList computed properties (page and links)
"""

import uuid
from datetime import datetime

from pydantic import AnyHttpUrl

from fed_mgr.v1.schemas import (
    CreationQuery,
    ErrorMessage,
    ItemID,
    PageNavigation,
    PaginatedList,
    Pagination,
    PaginationQuery,
    SortQuery,
    UpdateQuery,
)


def test_itemid_default_id():
    """Generate ItemID with a valid UUID by default."""
    item = ItemID()
    assert isinstance(item.id, uuid.UUID)


def test_error_message_fields():
    """Set detail in ErrorMessage."""
    err = ErrorMessage(detail="Something went wrong")
    assert err.detail == "Something went wrong"


def test_creation_query_fields():
    """Set created_before and created_after in CreationQuery."""
    now = datetime.now()
    cq = CreationQuery(created_before=now, created_after=now)
    assert cq.created_before == now
    assert cq.created_after == now


def test_update_query_fields():
    """Set updated_before and updated_after in UpdateQuery."""
    now = datetime.now()
    uq = UpdateQuery(updated_before=now, updated_after=now)
    assert uq.updated_before == now
    assert uq.updated_after == now


def test_pagination_query_defaults():
    """Check PaginationQuery default values."""
    pq = PaginationQuery()
    assert pq.size == 5
    assert pq.page == 1


def test_sort_query_defaults():
    """Check SortQuery default values."""
    pq = SortQuery()
    assert pq.sort == "-created_at"


def test_pagination_total_pages():
    """Compute total_pages in Pagination for various cases."""
    p = Pagination(size=5, number=1, total_elements=0)
    assert p.total_pages == 1
    p = Pagination(size=5, number=1, total_elements=12)
    assert p.total_pages == 3
    p = Pagination(size=5, number=1, total_elements=5)
    assert p.total_pages == 1


def test_page_navigation_fields():
    """Set all fields in PageNavigation and check types."""
    url1 = AnyHttpUrl("http://test/1")
    url2 = AnyHttpUrl("http://test/2")
    nav = PageNavigation(first=url1, prev=url2, next=None, last=url1)
    assert nav.first == url1
    assert nav.prev == url2
    assert nav.next is None
    assert nav.last == url1


def test_paginated_list_page_and_links_properties():
    """Test PaginatedList computed properties: page and links."""
    # Prepare test data
    url = AnyHttpUrl("http://test/resource")
    page_number = 2
    page_size = 5
    tot_items = 12

    paginated = PaginatedList(
        page_number=page_number,
        page_size=page_size,
        tot_items=tot_items,
        resource_url=url,
    )

    # Test page property
    page = paginated.page
    assert page.number == page_number
    assert page.size == page_size
    assert page.total_elements == tot_items
    assert page.total_pages == 3

    # Test links property
    links = paginated.links
    assert isinstance(links, PageNavigation)
    assert links.first == AnyHttpUrl("http://test/resource?page=1")
    assert links.last == AnyHttpUrl("http://test/resource?page=3")
    assert links.prev == AnyHttpUrl("http://test/resource?page=1")
    assert links.next == AnyHttpUrl("http://test/resource?page=3")

    # Test edge cases: first page (no prev)
    paginated_first = PaginatedList(
        page_number=1,
        page_size=page_size,
        tot_items=tot_items,
        resource_url=url,
    )
    links_first = paginated_first.links
    assert links_first.prev is None
    assert links_first.next == AnyHttpUrl("http://test/resource?page=2")

    # Test edge cases: last page (no next)
    paginated_last = PaginatedList(
        page_number=3,
        page_size=page_size,
        tot_items=tot_items,
        resource_url=url,
    )
    links_last = paginated_last.links
    assert links_last.next is None
    assert links_last.prev == AnyHttpUrl("http://test/resource?page=2")
