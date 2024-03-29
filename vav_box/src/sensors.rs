

pub struct TemperatureSensor {
    pub last_reading: f32,
}

impl TemperatureSensor {
    pub fn new(initial_reading: f32) -> Self {
        TemperatureSensor {
            last_reading: initial_reading,
        }
    }

    // Methods to update/read sensor data
}
