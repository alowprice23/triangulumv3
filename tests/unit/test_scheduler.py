import time
import pytest
from unittest.mock import patch
from runtime.scheduler import Scheduler, BugTicket, calculate_priority

@pytest.fixture
def scheduler():
    return Scheduler()

def test_scheduler_submit_and_get(scheduler):
    """Test submitting a ticket and getting it back."""
    ticket = BugTicket(bug_id="BUG-001", severity=3, description="Test bug")
    scheduler.submit_ticket(ticket)
    assert len(scheduler) == 1
    assert not scheduler.is_empty()
    next_ticket = scheduler.get_next_ticket()
    assert next_ticket == ticket
    assert len(scheduler) == 0
    assert scheduler.is_empty()

def test_scheduler_priority_order(scheduler):
    """Test that the scheduler returns tickets in the correct priority order."""
    ticket1 = BugTicket(bug_id="BUG-001", severity=1, description="Low severity")
    time.sleep(0.01) # ensure different arrival times
    ticket2 = BugTicket(bug_id="BUG-002", severity=5, description="High severity")

    scheduler.submit_ticket(ticket1)
    scheduler.submit_ticket(ticket2)

    # ticket2 should have higher priority because of severity
    next_ticket = scheduler.get_next_ticket()
    assert next_ticket.bug_id == "BUG-002"

    next_ticket = scheduler.get_next_ticket()
    assert next_ticket.bug_id == "BUG-001"

@patch('time.time')
def test_calculate_priority_with_age(mock_time):
    """Test that priority increases with age."""
    # Mock time to control the age of the ticket
    mock_time.return_value = 1000.0
    ticket_new = BugTicket(bug_id="BUG-NEW", severity=3, description="New bug")

    mock_time.return_value = 1100.0 # 100 seconds later
    ticket_old = BugTicket(bug_id="BUG-OLD", severity=3, description="Old bug", arrival_time=100.0)

    priority_new = calculate_priority(ticket_new)
    priority_old = calculate_priority(ticket_old)

    assert priority_old > priority_new

@patch('time.time')
def test_scheduler_starvation_prevention(mock_time, scheduler):
    """Test that an old, low-severity ticket eventually gets picked."""
    mock_time.return_value = 1000.0
    old_low_sev_ticket = BugTicket(bug_id="BUG-OLD-LOW", severity=1, description="Old low severity", arrival_time=0.0)

    scheduler.submit_ticket(old_low_sev_ticket)

    # Submit newer, higher-severity tickets
    for i in range(5):
        mock_time.return_value = 1000.0 + i * 10
        new_high_sev_ticket = BugTicket(bug_id=f"BUG-NEW-HIGH-{i}", severity=5, description="New high severity")
        scheduler.submit_ticket(new_high_sev_ticket)

    # Let the old ticket age significantly
    mock_time.return_value = 1000.0 + 3600 * 24 # 1 day later

    # Now, the old ticket should have a higher priority than a new high-severity ticket
    new_high_sev_ticket_latest = BugTicket(bug_id="BUG-NEW-HIGH-LATEST", severity=5, description="Newest high severity")
    scheduler.submit_ticket(new_high_sev_ticket_latest)

    # The first ticket to be picked should be one of the high-severity ones
    # (depending on their exact arrival time and the effect of age)
    # but eventually the old low-severity one should be picked.

    # Let's get all tickets and see the order
    ordered_tickets = []
    while not scheduler.is_empty():
        ordered_tickets.append(scheduler.get_next_ticket())

    # We can't guarantee the exact order without knowing the exact priorities,
    # but the old ticket should not be the last one.
    # A better test is to check if its priority is now higher.

    priority_old = calculate_priority(old_low_sev_ticket)
    priority_new_high = calculate_priority(new_high_sev_ticket_latest)

    assert priority_old > priority_new_high
