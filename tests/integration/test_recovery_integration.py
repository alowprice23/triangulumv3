import unittest
import time
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from runtime.supervisor import Supervisor
from runtime.scheduler import BugTicket

class TestRecoveryIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.state_dir = Path(self.test_dir) / "state"

        self.sleep_patcher = patch('time.sleep', return_value=None)
        self.sleep_patcher.start()

    def tearDown(self):
        shutil.rmtree(self.test_dir)
        self.sleep_patcher.stop()

    @patch('runtime.supervisor.ParallelExecutor')
    def test_crash_and_recover_scenario(self, mock_executor_class):
        """
        Simulates a full crash-and-recover cycle to ensure state is persisted
        and restored correctly.
        """
        # --- Phase 1: Normal Operation and Crash ---

        with patch('runtime.supervisor.PIDController') as mock_pid_class:
            mock_pid_class.return_value.update.return_value = 1.0

            supervisor1 = Supervisor(repo_root=Path(self.test_dir), state_dir=self.state_dir)

            mock_executor = mock_executor_class.return_value
            mock_executor.check_completed_sessions.return_value = []
            mock_executor.get_active_session_count.return_value = 0

            # Submit and launch Bug A
            ticket_a = supervisor1.submit_bug("bug_A", 1)
            supervisor1.tick()

            # Create a mock session object that looks like the real one
            from runtime.parallel_executor import Session
            mock_future = MagicMock()
            mock_session = Session(ticket=ticket_a, future=mock_future)
            mock_executor._active_sessions = {ticket_a.bug_id: mock_session}

            # Submit Bug B
            ticket_b = supervisor1.submit_bug("bug_B", 2)

            # Create Snapshot
            supervisor1.snapshot_manager.create_snapshot(supervisor1._get_current_state())

            # Submit Bug C (after snapshot)
            ticket_c = supervisor1.submit_bug("bug_C", 3)

            del supervisor1

        # --- Phase 2: Recovery ---
        supervisor2 = Supervisor(repo_root=Path(self.test_dir), state_dir=self.state_dir)

        # --- Phase 3: Verification ---
        recovered_bug_ids = {t.item.bug_id for t in supervisor2.scheduler._queue}
        expected_bug_ids = {ticket_a.bug_id, ticket_b.bug_id, ticket_c.bug_id}

        self.assertSetEqual(recovered_bug_ids, expected_bug_ids)
        self.assertEqual(len(recovered_bug_ids), 3)

if __name__ == '__main__':
    unittest.main()
