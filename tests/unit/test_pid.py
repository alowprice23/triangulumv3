import unittest
import time
from unittest.mock import patch

from runtime.pid import PIDController

class TestPIDController(unittest.TestCase):
    def test_proportional_term(self):
        pid = PIDController(Kp=0.5, Ki=0, Kd=0, setpoint=10, output_limits=(-10, 10))
        output = pid.update(5)
        self.assertAlmostEqual(output, 2.5) # 0.5 * (10 - 5)

    def test_integral_term_accumulation(self):
        pid = PIDController(Kp=0, Ki=0.5, Kd=0, setpoint=10, output_limits=(-10, 10))

        with patch('time.time') as mock_time:
            # First update
            mock_time.return_value = 1000
            pid._last_time = 1000 # Set initial time

            mock_time.return_value = 1001
            output1 = pid.update(5)
            self.assertAlmostEqual(pid._integral, 2.5)
            self.assertAlmostEqual(output1, 2.5)

            # Second update
            mock_time.return_value = 1002
            output2 = pid.update(5)
            self.assertAlmostEqual(pid._integral, 5.0)
            self.assertAlmostEqual(output2, 5.0)

    def test_derivative_term(self):
        pid = PIDController(Kp=0, Ki=0, Kd=0.5, setpoint=10)
        with patch('time.time', side_effect=[1000, 1001]):
            pid.update(5) # Initial error is 5
        with patch('time.time', side_effect=[1001, 1002]):
            output = pid.update(7) # Error is now 3, delta_error is -2
            self.assertAlmostEqual(output, -1.0) # 0.5 * (-2 / 1)

    def test_output_clamping(self):
        pid = PIDController(Kp=10, Ki=0, Kd=0, setpoint=10, output_limits=(-1, 1))
        output = pid.update(0)
        self.assertEqual(output, 1)
        output = pid.update(20)
        self.assertEqual(output, -1)

    def test_anti_windup(self):
        pid = PIDController(Kp=1, Ki=1, Kd=0, setpoint=10, output_limits=(-5, 5))
        with patch('time.time') as mock_time:
            mock_time.return_value = 1000
            # Saturate the output
            for _ in range(10):
                mock_time.return_value += 1
                pid.update(0)
            # The integral term should be clamped
            self.assertLessEqual(pid._integral, 5)

    def test_reset(self):
        pid = PIDController(Kp=1, Ki=1, Kd=1, setpoint=10)
        pid.update(5)
        pid.reset()
        self.assertEqual(pid._proportional, 0)
        self.assertEqual(pid._integral, 0)
        self.assertEqual(pid._derivative, 0)
        self.assertEqual(pid._last_error, 0)

if __name__ == '__main__':
    unittest.main()
