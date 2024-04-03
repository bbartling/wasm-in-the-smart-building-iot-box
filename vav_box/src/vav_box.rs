//use crate::control_signals::ControlSignal;
use crate::pid::{PIDController, PIDSettings};
use crate::sensors::TemperatureSensor;

#[derive(Debug, PartialEq)]
pub enum VavState {
    Heating,
    Cooling,
    Satisfied,
}

pub struct VavBox {
    pub current_temp: f32,
    pub setpoint_temp: f32,
    pub state: VavState,
    pub heating_pid: PIDController,
    pub cooling_pid: PIDController,
    // Example: Adding a temperature sensor directly, could be expanded to more sensors
    pub temp_sensor: TemperatureSensor,
}

impl VavBox {
    pub fn new(
        setpoint: f32,
        heating_pid_settings: PIDSettings,
        cooling_pid_settings: PIDSettings,
    ) -> Self {
        VavBox {
            current_temp: 21.9,
            setpoint_temp: setpoint,
            state: VavState::Satisfied,
            temp_sensor: TemperatureSensor::new(21.9), // Initialized with some default value
            heating_pid: PIDController::new(heating_pid_settings, 22.0),
            cooling_pid: PIDController::new(cooling_pid_settings, 25.0), // Added setpoint argument
                                                                         // other fields...
        }
    }

    // Method to update the VavBox's current temperature and recalculate its state
    pub fn update_temperature(&mut self, new_temp: f32) {
        self.current_temp = new_temp;

        // Recalculate the state based on the new temperature
        self.update_state();
    }

    // Method to update the state of the VavBox based on the current temperature and setpoint
    fn update_state(&mut self) {
        let deviation = self.setpoint_temp - self.current_temp;

        self.state = if deviation.abs() < 0.5 {
            VavState::Satisfied
        } else if deviation > 0.0 {
            VavState::Heating
        } else {
            VavState::Cooling
        };
    }

    pub fn get_state_code(&self) -> u32 {
        match self.state {
            VavState::Heating => 1,
            VavState::Cooling => 2,
            VavState::Satisfied => 3,
        }
    }
}

#[no_mangle]
pub extern "C" fn vavbox_new(setpoint: f32) -> *mut VavBox {
    let heating_pid_settings = PIDSettings::new(1.0, 0.01, 0.001); // Example settings
    let cooling_pid_settings = PIDSettings::new(1.2, 0.02, 0.002); // Example settings

    Box::into_raw(Box::new(VavBox::new(
        setpoint,
        heating_pid_settings,
        cooling_pid_settings,
    )))
}

// Assuming this is in `vav_box.rs` or appropriately included in `lib.rs`
#[no_mangle]
pub extern "C" fn vavbox_update_temperature(vav_box_ptr: *mut VavBox, new_temp: f32) {
    let vav_box = unsafe {
        assert!(!vav_box_ptr.is_null());
        &mut *vav_box_ptr
    };
    vav_box.update_temperature(new_temp);
}

#[no_mangle]
pub extern "C" fn vavbox_get_state_code(vav_box_ptr: *mut VavBox) -> u32 {
    unsafe {
        assert!(!vav_box_ptr.is_null());
        (&*vav_box_ptr).get_state_code()
    }
}
