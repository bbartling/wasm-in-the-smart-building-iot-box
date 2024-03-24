// lib.rs
// $ cargo new --lib wasm_vav_control
// cargo build --target wasm32-unknown-unknown


use std::os::raw::c_char;

#[repr(u32)]
#[derive(Debug, PartialEq, Eq)]
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
            current_temp: 21.9,
            setpoint_temp: setpoint,
            state: VavState::Satisfied,
        }
    }

    fn update_state(&mut self) {
        let deviation = self.setpoint_temp - self.current_temp;
        println!("Deviation: {}", deviation);
    
        self.state = if deviation.abs() < 0.5 {
            // Condition for being satisfied
            VavState::Satisfied
        } else if deviation > 0.0 {
            // If current temperature is below setpoint, consider heating
            VavState::Heating
        } else {
            // If current temperature is above setpoint, consider cooling
            VavState::Cooling
        };
    }    
    

    fn change_temp(&mut self, temp_change: f32) {
        println!("Before change: {}", self.current_temp);
        self.current_temp += temp_change;
        println!("After change: {}", self.current_temp);
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
        match self.state {
            VavState::Heating => 1,
            VavState::Cooling => 2,
            VavState::Satisfied => 3,
        }
    }
}

// Extern FFI function for py
#[no_mangle]
pub extern "C" fn vavbox_get_state_code(vav_box_ptr: *mut VavBox) -> u32 {
    let vav_box = unsafe {
        assert!(!vav_box_ptr.is_null());
        &mut *vav_box_ptr
    };
    vav_box.get_state_code()
}

// Extern FFI function for py
#[no_mangle]
pub extern "C" fn vavbox_new(setpoint: f32) -> *mut VavBox {
    Box::into_raw(Box::new(VavBox::new(setpoint)))
}

// Extern FFI function for py
#[no_mangle]
pub extern "C" fn vavbox_change_temp(vav_box_ptr: *mut VavBox, temp_change: f32) {
    let vav_box = unsafe {
        assert!(!vav_box_ptr.is_null());
        &mut *vav_box_ptr
    };

    vav_box.change_temp(temp_change);
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_heating() {
        let mut vav = VavBox::new(22.0);
        // Simulate a significant decrease in temperature
        vav.change_temp(-5.0);
        assert_eq!(vav.state, VavState::Heating);
    }

    #[test]
    fn test_cooling() {
        let mut vav = VavBox::new(22.0);
        // Simulate a significant increase in temperature
        vav.change_temp(5.0);
        assert_eq!(vav.state, VavState::Cooling);
    }

    #[test]
    fn test_satisfied() {
        let mut vav = VavBox::new(22.0);
        // Simulate a minor temperature change within the satisfied threshold
        vav.change_temp(0.4);
        assert_eq!(vav.state, VavState::Satisfied);
    }
}



fn main() {
    let mut vav = VavBox::new(22.0); // Setpoint temperature
    vav.change_temp(-3.0); // Simulate a temperature change
    
    println!("Current state: {:?}", vav.state);
    println!("Control signal: {}", vav.control_signal());
    
    // Since `get_state_code` returns a `u32`, you can print it directly.
    println!("VAV State Code: {}", vav.get_state_code());
}
