import unittest
from unittest.mock import MagicMock, patch, ANY
from pathlib import Path
import time
from concurrent.futures import Future

from runtime.parallel_executor import ParallelExecutor
from runtime.scheduler import BugTicket
from runtime.allocator import Allocator

class TestParallelExecutor(unittest.TestCase):

    def setUp(self):
        self.mock_allocator = MagicMock(spec=Allocator)
        # Mock the ThreadPoolExecutor to control thread execution manually
        self.mock_thread_pool = MagicMock()

        patcher = patch('runtime.parallel_executor.ThreadPoolExecutor', return_value=self.mock_thread_pool)
        self.addCleanup(patcher.stop)
        patcher.start()

        self.executor = ParallelExecutor(max_workers=3, allocator=self.mock_allocator)

    def test_launch_session_success(self):
        """Test that a session is launched successfully when resources are available."""
        self.mock_allocator.allocate.return_value = True
        ticket = BugTicket("BUG-001", 5, "Test bug")
        repo_root = Path("/fake/repo")

        # Mock the Coordinator class within the executor's scope
        with patch('runtime.parallel_executor.Coordinator') as mock_coordinator_class:
            mock_coordinator_instance = MagicMock()
            mock_coordinator_class.return_value = mock_coordinator_instance

            launched = self.executor.launch_session(ticket, repo_root)

            self.assertTrue(launched)
            self.mock_allocator.allocate.assert_called_once_with("BUG-001")
            mock_coordinator_class.assert_called_once_with(repo_root=repo_root)
            self.mock_thread_pool.submit.assert_called_once_with(
                mock_coordinator_instance.run_debugging_cycle,
                bug_description="Test bug",
                code_graph=None
            )
            self.assertEqual(self.executor.get_active_session_count(), 1)

    def test_launch_session_fails_when_at_capacity(self):
        """Test that a session is not launched when the executor is at capacity."""
        # Manually set the number of active sessions to be at capacity
        self.executor._active_sessions = {"1": MagicMock(), "2": MagicMock(), "3": MagicMock()}

        ticket = BugTicket("BUG-004", 5, "Another bug")
        repo_root = Path("/fake/repo")

        launched = self.executor.launch_session(ticket, repo_root)

        self.assertFalse(launched)
        self.mock_allocator.allocate.assert_not_called()
        self.mock_thread_pool.submit.assert_not_called()

    def test_launch_session_fails_when_no_agents(self):
        """Test that a session is not launched when the allocator fails."""
        self.mock_allocator.allocate.return_value = False
        ticket = BugTicket("BUG-001", 5, "Test bug")
        repo_root = Path("/fake/repo")

        launched = self.executor.launch_session(ticket, repo_root)

        self.assertFalse(launched)
        self.mock_allocator.allocate.assert_called_once_with("BUG-001")
        self.mock_thread_pool.submit.assert_not_called()

    def test_check_completed_sessions(self):
        """Test that completed sessions are correctly identified and processed."""
        # Create a mock session with a future that is 'done'
        done_future = Future()
        done_future.set_result({"status": "success"})

        mock_session = MagicMock()
        mock_session.bug_id = "BUG-001"
        mock_session.future = done_future

        self.executor._active_sessions = {"BUG-001": mock_session}

        completed = self.executor.check_completed_sessions()

        self.assertEqual(len(completed), 1)
        self.assertEqual(completed[0], ("BUG-001", {"status": "success"}))
        self.mock_allocator.release.assert_called_once_with("BUG-001")
        self.assertEqual(self.executor.get_active_session_count(), 0)

    def test_shutdown_is_called(self):
        """Test that the executor's shutdown method calls the thread pool's shutdown."""
        self.executor.shutdown()
        self.mock_thread_pool.shutdown.assert_called_once_with(wait=True)

if __name__ == '__main__':
    unittest.main()
