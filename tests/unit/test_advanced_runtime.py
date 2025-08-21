import unittest
from unittest.mock import patch, MagicMock
import time

from runtime.scheduler import Scheduler, BugTicket
from runtime.pid import PIDController
from runtime.supervisor import Supervisor

class TestAdvancedRuntime(unittest.TestCase):

    def test_pid_controller(self):
        """Test the basic functionality of the PID controller."""
        # Test that with zero error, the output is zero (ignoring integral for a moment)
        pid = PIDController(Kp=0.1, Ki=0.01, Kd=0.0, setpoint=10)
        output = pid.update(10)
        # Initial output will have some integral component from the first error calculation
        # A better test is to check its response to a sustained error.

        # Sustained error of -5 (current is 15, setpoint is 10)
        output1 = pid.update(15)
        self.assertLess(output1, 0) # Should be negative to reduce output

        # Another update, integral term should make it more negative
        time.sleep(0.1) # Simulate time passing
        output2 = pid.update(15)
        self.assertLess(output2, output1)

    def test_scheduler_priority(self):
        """Test that the scheduler correctly prioritizes tickets."""
        scheduler = Scheduler()

        # Ticket 1: low severity, created now
        ticket1 = BugTicket(bug_id="1", severity=1, description="low sev")

        # Ticket 2: high severity, created now
        ticket2 = BugTicket(bug_id="2", severity=5, description="high sev")

        scheduler.submit_ticket(ticket1)
        scheduler.submit_ticket(ticket2)

        # The high severity ticket should come out first
        next_ticket = scheduler.get_next_ticket()
        self.assertEqual(next_ticket.bug_id, "2")

    @patch('runtime.supervisor.Coordinator')
    def test_supervisor_spawn_logic(self, mock_coordinator_class):
        """Test the spawn logic of the Supervisor's tick method."""
        supervisor = Supervisor()
        supervisor.submit_bug("test bug", severity=3)

        # 1. Test spawn-on-positive-pid
        with patch.object(supervisor.pid_controller, 'update', return_value=0.5) as mock_pid_update:
            supervisor.tick()
            mock_pid_update.assert_called_once_with(1) # Called with backlog=1
            # Assert that a coordinator was created
            self.assertEqual(len(supervisor.active_sessions), 1)

    @patch('runtime.supervisor.Coordinator')
    def test_supervisor_no_spawn_logic(self, mock_coordinator_class):
        """Test that the supervisor does not spawn when PID output is negative."""
        supervisor = Supervisor()
        supervisor.submit_bug("test bug", severity=3)

        # 2. Test no-spawn-on-negative-pid
        supervisor.active_sessions.clear() # Reset from previous test
        with patch.object(supervisor.pid_controller, 'update', return_value=-0.5) as mock_pid_update:
            supervisor.tick()
            mock_pid_update.assert_called_once_with(1)
            self.assertEqual(len(supervisor.active_sessions), 0)


if __name__ == '__main__':
    unittest.main()
