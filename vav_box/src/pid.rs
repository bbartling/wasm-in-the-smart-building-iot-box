/// PID settings struct that holds the coefficients for PID control.
pub struct PIDSettings {
    pub kp: f32, // Proportional gain
    pub ki: f32, // Integral gain
    pub kd: f32, // Derivative gain
}

impl PIDSettings {
    pub fn new(kp: f32, ki: f32, kd: f32) -> Self {
        PIDSettings { kp, ki, kd }
    }
}

/// PIDController struct that performs PID control based on the provided settings.
pub struct PIDController {
    settings: PIDSettings,
    setpoint: f32,
    integral: f32,
    previous_error: f32,
}

impl PIDController {
    pub fn new(settings: PIDSettings, setpoint: f32) -> Self {
        PIDController {
            settings,
            setpoint,
            integral: 0.0,
            previous_error: 0.0,
        }
    }

    /// Updates the PID controller with the current measurement and calculates the control variable.
    pub fn update(&mut self, current_value: f32) -> f32 {
        let error = self.setpoint - current_value;
        self.integral += error;
        let derivative = error - self.previous_error;
        self.previous_error = error;

        (self.settings.kp * error) + (self.settings.ki * self.integral) + (self.settings.kd * derivative)
    }

    /// Sets a new setpoint for the PID controller.
    pub fn set_setpoint(&mut self, setpoint: f32) {
        self.setpoint = setpoint;
    }
}
