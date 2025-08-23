import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

from runtime.supervisor import Supervisor
from runtime.scheduler import BugTicket
from storage.wal import LogEntryType

class TestSupervisor(unittest.TestCase):

    def setUp(self):
        """Set up a mock environment for testing the Supervisor."""
        self.repo_root = Path("/fake/repo")
        self.state_dir = Path("/tmp/fake_state") # Give a fake dir

        # We patch the storage and recovery components at a high level
        # to prevent the Supervisor's __init__ from actually doing recovery.
        self.mock_recovery_manager = MagicMock()
        self.mock_recovery_manager.recover_state.return_value = {
            "scheduler_tickets": [],
            "active_sessions": {},
        }

        # Patch the classes in the supervisor module
        patcher_recovery = patch('runtime.supervisor.RecoveryManager', return_value=self.mock_recovery_manager)
        self.patcher_executor = patch('runtime.supervisor.ParallelExecutor')

        # We don't need to patch WAL and SnapshotManager if we patch RecoveryManager,
        # as it's the only thing that uses them in __init__.
        self.addCleanup(patcher_recovery.stop)
        self.addCleanup(self.patcher_executor.stop)

        patcher_recovery.start()
        self.mock_executor_class = self.patcher_executor.start()
        self.mock_executor_instance = self.mock_executor_class.return_value

        self.supervisor = Supervisor(max_concurrent_sessions=3, repo_root=self.repo_root, state_dir=self.state_dir)

        # Also mock the WAL on the instance for tests that call log_event
        self.supervisor.wal = MagicMock()


    def test_submit_bug(self):
        """Test that submitting a bug adds a ticket to the scheduler and logs it."""
        ticket = self.supervisor.submit_bug("Test bug", 5)
        self.assertIsInstance(ticket, BugTicket)
        self.supervisor.wal.log_event.assert_called_once()
        self.assertEqual(len(self.supervisor.scheduler), 1)

    def test_tick_spawns_new_session_when_conditions_met(self):
        """Test that a new session is spawned when there is capacity and demand."""
        self.supervisor.scheduler.submit_ticket(BugTicket("1", 5, "desc"))
        with patch.object(self.supervisor.pid_controller, 'update', return_value=0.5):
            self.mock_executor_instance.get_active_session_count.return_value = 1
            self.mock_executor_instance.launch_session.return_value = True

            self.supervisor.tick()

            self.mock_executor_instance.launch_session.assert_called_once()
            self.supervisor.wal.log_event.assert_called_once_with(LogEntryType.SESSION_LAUNCHED, unittest.mock.ANY)

    def test_tick_does_not_spawn_when_at_capacity(self):
        """Test that a new session is not spawned when at max capacity."""
        self.supervisor.scheduler.submit_ticket(BugTicket("1", 5, "desc"))
        with patch.object(self.supervisor.pid_controller, 'update', return_value=0.5):
            self.mock_executor_instance.get_active_session_count.return_value = 3 # At capacity

            self.supervisor.tick()

            self.mock_executor_instance.launch_session.assert_not_called()

    def test_tick_does_not_spawn_when_pid_is_low(self):
        """Test that a new session is not spawned when PID output is low."""
        self.supervisor.scheduler.submit_ticket(BugTicket("1", 5, "desc"))
        with patch.object(self.supervisor.pid_controller, 'update', return_value=0.1): # Too low
            self.mock_executor_instance.get_active_session_count.return_value = 1

            self.supervisor.tick()

            self.mock_executor_instance.launch_session.assert_not_called()

    def test_tick_handles_completed_sessions(self):
        """Test that the supervisor checks for and handles completed sessions."""
        self.mock_executor_instance.check_completed_sessions.return_value = [
            ("BUG-001", {"status": "success"})
        ]
        with patch.object(self.supervisor.pid_controller, 'update', return_value=0.0):
            self.supervisor.tick()

            self.mock_executor_instance.check_completed_sessions.assert_called_once()
            self.supervisor.wal.log_event.assert_called_once_with(LogEntryType.SESSION_COMPLETED, unittest.mock.ANY)

    def test_run_loop_stops(self):
        """Test that the main run loop can be stopped."""
        self.supervisor.stop = MagicMock(wraps=self.supervisor.stop)
        with patch.object(self.supervisor.pid_controller, 'update', return_value=0.0):
            self.supervisor.run(duration_seconds=0.1)

            self.supervisor.stop.assert_called_once()
            self.mock_executor_instance.shutdown.assert_called_once()

if __name__ == '__main__':
    unittest.main()
