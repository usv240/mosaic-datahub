import pytest

from mosaic.engine import assess_demo
from mosaic.writeback import (
    ApprovalRequiredError,
    InMemoryCatalog,
    build_proposal,
    publish_proposal,
)


def test_writeback_refuses_without_approval() -> None:
    with pytest.raises(ApprovalRequiredError):
        publish_proposal(InMemoryCatalog(), build_proposal(assess_demo()), approved=False)


def test_approved_writeback_is_reread() -> None:
    result = publish_proposal(InMemoryCatalog(), build_proposal(assess_demo()), approved=True)
    assert result["status"] == "published"
    assert result["reread_verified"] is True
