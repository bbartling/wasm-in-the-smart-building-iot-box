// lib.rs
// $ cargo new --lib wasm_vav_control
// cargo build --target wasm32-unknown-unknown


use std::os::raw::c_char;

#[repr(u32)]
#[derive(Debug, PartialEq, Eq, Copy, Clone)] // Added Copy and Clone here
pub enum VavState {
    Heating = 1,
    Cooling = 2,
    Satisfied = 3,
}


struct VavBox {
    current_temp: f32,
    setpoint_temp: f32,
    state: VavState,
}

impl VavBox {
    fn new(setpoint: f32) -> VavBox {
        VavBox {
            current_temp: 21.9, // Initial current temperature
            setpoint_temp: setpoint,
            state: VavState::Satisfied,
        }
    }

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

    fn update_temperature(&mut self, new_temp: f32) {
        self.current_temp = new_temp;
        self.update_state();
    }

    fn control_signal(&self) -> f32 {
        match self.state {
            VavState::Heating => 1.0,
            VavState::Cooling => -1.0,
            VavState::Satisfied => 0.0,
        }
    }
    
    pub fn get_state_code(&self) -> u32 {
        self.state as u32
    }
}

#[no_mangle]
pub extern "C" fn vavbox_get_state_code(vav_box_ptr: *mut VavBox) -> u32 {
    unsafe {
        assert!(!vav_box_ptr.is_null());
        (&*vav_box_ptr).get_state_code()
    }
}

#[no_mangle]
pub extern "C" fn vavbox_new(setpoint: f32) -> *mut VavBox {
    Box::into_raw(Box::new(VavBox::new(setpoint)))
}

#[no_mangle]
pub extern "C" fn vavbox_update_temperature(vav_box_ptr: *mut VavBox, new_temp: f32) {
    unsafe {
        assert!(!vav_box_ptr.is_null());
        (&mut *vav_box_ptr).update_temperature(new_temp);
    }
}


#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_heating() {
        let mut vav = VavBox::new(22.0);
        // Simulate a new current temperature that would require heating
        vav.update_temperature(17.0); // New temperature is 17.0°C
        assert_eq!(vav.state, VavState::Heating);
    }

    #[test]
    fn test_cooling() {
        let mut vav = VavBox::new(22.0);
        // Simulate a new current temperature that would require cooling
        vav.update_temperature(27.0); // New temperature is 27.0°C
        assert_eq!(vav.state, VavState::Cooling);
    }

    #[test]
    fn test_satisfied() {
        let mut vav = VavBox::new(22.0);
        // Simulate a new current temperature within the satisfied threshold
        vav.update_temperature(22.4); // New temperature is 22.4°C
        assert_eq!(vav.state, VavState::Satisfied);
    }
}




fn main() {
    let mut vav = VavBox::new(22.0); // Setpoint temperature
    vav.update_temperature(19.0); // Update to simulate a new current temperature

    println!("Current state: {:?}", vav.state);
    println!("Control signal: {}", vav.control_signal());
    
    println!("VAV State Code: {}", vav.get_state_code());
}
