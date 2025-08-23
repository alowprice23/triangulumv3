import unittest
from unittest.mock import patch, MagicMock
import time

from runtime.scheduler import Scheduler, BugTicket
from runtime.pid import PIDController
from runtime.supervisor import Supervisor

@patch('runtime.supervisor.RecoveryManager')
class TestAdvancedRuntime(unittest.TestCase):

    def test_pid_controller(self, mock_recovery_manager):
        """Test the basic functionality of the PID controller."""
        pid = PIDController(Kp=0.1, Ki=0.01, Kd=0.0, setpoint=10)

        output1 = pid.update(15)
        self.assertLess(output1, 0)

        time.sleep(0.1)
        output2 = pid.update(15)
        self.assertLess(output2, output1)

    def test_scheduler_priority(self, mock_recovery_manager):
        """Test that the scheduler correctly prioritizes tickets."""
        scheduler = Scheduler()
        ticket1 = BugTicket(bug_id="1", severity=1, description="low sev")
        ticket2 = BugTicket(bug_id="2", severity=5, description="high sev")
        scheduler.submit_ticket(ticket1)
        scheduler.submit_ticket(ticket2)
        next_ticket = scheduler.get_next_ticket()
        self.assertEqual(next_ticket.bug_id, "2")

    @patch('runtime.supervisor.ParallelExecutor')
    def test_supervisor_spawn_logic(self, mock_executor_class, mock_recovery_manager):
        """Test the spawn logic of the Supervisor's tick method."""
        mock_executor_instance = MagicMock()
        mock_executor_class.return_value = mock_executor_instance
        mock_recovery_manager.return_value.recover_state.return_value = {"scheduler_tickets": [], "active_sessions": {}}

        supervisor = Supervisor()
        supervisor.submit_bug("test bug", severity=3)

        mock_executor_instance.get_active_session_count.return_value = 0
        with patch.object(supervisor.pid_controller, 'update', return_value=0.5):
            supervisor.tick()
            mock_executor_instance.launch_session.assert_called_once()

    @patch('runtime.supervisor.ParallelExecutor')
    def test_supervisor_no_spawn_logic(self, mock_executor_class, mock_recovery_manager):
        """Test that the supervisor does not spawn when PID output is negative."""
        mock_executor_instance = MagicMock()
        mock_executor_class.return_value = mock_executor_instance
        mock_recovery_manager.return_value.recover_state.return_value = {"scheduler_tickets": [], "active_sessions": {}}

        supervisor = Supervisor()
        supervisor.submit_bug("test bug", severity=3)

        mock_executor_instance.get_active_session_count.return_value = 0
        with patch.object(supervisor.pid_controller, 'update', return_value=-0.5):
            supervisor.tick()
            mock_executor_instance.launch_session.assert_not_called()

if __name__ == '__main__':
    unittest.main()
