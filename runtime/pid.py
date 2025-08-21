import time

class PIDController:
    """
    A Proportional-Integral-Derivative (PID) controller.
    This implementation is adapted for controlling system resources like agent
    or task backlogs.
    """
    def __init__(
        self,
        Kp: float,
        Ki: float,
        Kd: float,
        setpoint: float,
        output_limits: tuple[float, float] = (-1.0, 1.0)
    ):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.setpoint = setpoint
        self.min_output, self.max_output = output_limits

        self._proportional = 0
        self._integral = 0
        self._derivative = 0

        self._last_error = 0
        self._last_time = time.time()

    def update(self, current_value: float) -> float:
        """
        Calculates the controller output based on the current system value.

        Args:
            current_value: The current measured value of the system (e.g., backlog size).

        Returns:
            The controller's output signal, clamped within the specified limits.
        """
        current_time = time.time()
        delta_time = current_time - self._last_time

        if delta_time == 0:
            # Avoid division by zero
            return self._clamp(self._proportional + self._integral + self._derivative)

        error = self.setpoint - current_value

        # Proportional term
        self._proportional = self.Kp * error

        # Integral term with anti-windup
        self._integral += self.Ki * error * delta_time
        self._integral = self._clamp(self._integral) # Anti-windup clamp on the integral itself

        # Derivative term
        delta_error = error - self._last_error
        self._derivative = self.Kd * (delta_error / delta_time)

        # Total output
        output = self._proportional + self._integral + self._derivative

        # Update state for next iteration
        self._last_error = error
        self._last_time = current_time

        return self._clamp(output)

    def _clamp(self, value: float) -> float:
        """Clamps a value between the output limits."""
        return max(self.min_output, min(value, self.max_output))

    def reset(self):
        """Resets the controller's internal state."""
        self._proportional = 0
        self._integral = 0
        self._derivative = 0
        self._last_error = 0
        self._last_time = time.time()
