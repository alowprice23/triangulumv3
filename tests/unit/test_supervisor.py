import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

from runtime.supervisor import Supervisor
from runtime.scheduler import BugTicket

class TestSupervisor(unittest.TestCase):

    def setUp(self):
        """Set up a mock environment for testing the Supervisor."""
        self.repo_root = Path("/fake/repo")

        # We patch the dependencies of the Supervisor so we can test it in isolation.
        self.mock_allocator = MagicMock()
        self.mock_executor = MagicMock()
        self.mock_scheduler = MagicMock()
        self.mock_pid_controller = MagicMock()

        # Patch the classes in the supervisor module
        patcher_allocator = patch('runtime.supervisor.Allocator', return_value=self.mock_allocator)
        patcher_executor = patch('runtime.supervisor.ParallelExecutor', return_value=self.mock_executor)
        patcher_scheduler = patch('runtime.supervisor.Scheduler', return_value=self.mock_scheduler)
        patcher_pid = patch('runtime.supervisor.PIDController', return_value=self.mock_pid_controller)

        self.addCleanup(patcher_allocator.stop)
        self.addCleanup(patcher_executor.stop)
        self.addCleanup(patcher_scheduler.stop)
        self.addCleanup(patcher_pid.stop)

        patcher_allocator.start()
        patcher_executor.start()
        patcher_scheduler.start()
        patcher_pid.start()

        self.supervisor = Supervisor(max_concurrent_sessions=3, repo_root=self.repo_root)

    def test_submit_bug(self):
        """Test that submitting a bug adds a ticket to the scheduler."""
        self.supervisor.submit_bug("Test bug", 5)
        self.mock_scheduler.submit_ticket.assert_called_once()
        call_args = self.mock_scheduler.submit_ticket.call_args[0]
        self.assertIsInstance(call_args[0], BugTicket)
        self.assertEqual(call_args[0].description, "Test bug")

    def test_tick_spawns_new_session_when_conditions_met(self):
        """Test that a new session is spawned when there is capacity and demand."""
        # Arrange: PID says spawn, scheduler has a ticket, not at capacity
        self.mock_pid_controller.update.return_value = 0.5
        self.mock_scheduler.is_empty.return_value = False
        self.mock_scheduler.get_next_ticket.return_value = BugTicket("1", 5, "desc")
        self.mock_executor.get_active_session_count.return_value = 1
        self.mock_executor.launch_session.return_value = True

        # Act
        self.supervisor.tick()

        # Assert
        self.mock_executor.launch_session.assert_called_once()

    def test_tick_does_not_spawn_when_at_capacity(self):
        """Test that a new session is not spawned when at max capacity."""
        # Arrange: PID says spawn, scheduler has a ticket, but at capacity
        self.mock_pid_controller.update.return_value = 0.5
        self.mock_scheduler.is_empty.return_value = False
        self.mock_executor.get_active_session_count.return_value = 3 # At capacity

        # Act
        self.supervisor.tick()

        # Assert
        self.mock_executor.launch_session.assert_not_called()

    def test_tick_does_not_spawn_when_pid_is_low(self):
        """Test that a new session is not spawned when PID output is low."""
        # Arrange: PID says wait, scheduler has a ticket, not at capacity
        self.mock_pid_controller.update.return_value = 0.1 # Too low
        self.mock_scheduler.is_empty.return_value = False
        self.mock_executor.get_active_session_count.return_value = 1

        # Act
        self.supervisor.tick()

        # Assert
        self.mock_executor.launch_session.assert_not_called()

    def test_tick_handles_completed_sessions(self):
        """Test that the supervisor checks for and handles completed sessions."""
        # Arrange: Executor reports one completed session
        self.mock_executor.check_completed_sessions.return_value = [
            ("BUG-001", {"status": "success"})
        ]
        self.mock_pid_controller.update.return_value = 0.0 # Set a return value

        # Act
        self.supervisor.tick()

        # Assert
        self.mock_executor.check_completed_sessions.assert_called_once()

    def test_run_loop_stops(self):
        """Test that the main run loop can be stopped."""
        # Arrange
        self.mock_pid_controller.update.return_value = 0.0 # Set a return value

        # Act: Short duration to test the loop exit
        self.supervisor.run(duration_seconds=0.1)

        # Assert
        self.assertFalse(self.supervisor.is_running)
        self.mock_executor.shutdown.assert_called_once()

if __name__ == '__main__':
    unittest.main()
