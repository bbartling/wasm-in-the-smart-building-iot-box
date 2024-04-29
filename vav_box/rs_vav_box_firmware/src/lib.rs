#![no_std]

use wasm_bindgen::prelude::*;

// Static global variables for HVAC controller state
static mut ZONE_AIR_TEMP: f64 = 70.0;
static mut ZONE_AIR_TEMP_SETPOINT: f64 = 72.0;
static mut AHU_SUPPLY_AIR_TEMP: f64 = 60.0;
static mut CLG_FLOW_MIN_AIR_FLOW_SETPOINT: f64 = 500.0;
static mut CLG_FLOW_MAX_AIR_FLOW_SETPOINT: f64 = 1000.0;
static mut HTG_FLOW_MIN_AIR_FLOW_SETPOINT: f64 = 400.0;
static mut HTG_FLOW_MAX_AIR_FLOW_SETPOINT: f64 = 800.0;
static mut SATISFIED_FLOW_MIN_AIR_FLOW_SETPOINT: f64 = 450.0;
static mut MAX_DISCHARGE_AIR_TEMP: f64 = 110.0;
static mut ZONE_AIR_TEMP_DEADBAND: f64 = 5.0;

static mut KP_HEATING: f64 = 5.0;
static mut KI_HEATING: f64 = 1.0;
static mut INTEGRAL_HEATING: f64 = 0.0;
static mut KP_COOLING: f64 = 5.0;
static mut KI_COOLING: f64 = 1.0;
static mut INTEGRAL_COOLING: f64 = 0.0;
static mut PID_OUTPUT_HEATING: f64 = 0.0;
static mut PID_OUTPUT_COOLING: f64 = 0.0;
static mut MODE: i32 = 0;
static mut DISCHARGE_AIR_TEMP_SETPOINT: f64 = 0.0;
static mut DISCHARGE_AIR_FLOW_SETPOINT: f64 = 0.0;


#[wasm_bindgen]
pub fn set_zone_air_temp(value: f64) {
    unsafe {
        ZONE_AIR_TEMP = value;
    }
}

#[wasm_bindgen]
pub fn set_zone_air_temp_setpoint(value: f64) {
    unsafe {
        ZONE_AIR_TEMP_SETPOINT = value;
    }
}

#[wasm_bindgen]
pub fn set_ahu_supply_air_temp(value: f64) {
    unsafe {
        AHU_SUPPLY_AIR_TEMP = value;
    }
}

#[wasm_bindgen]
pub fn set_clg_flow_min_air_flow_setpoint(value: f64) {
    unsafe {
        CLG_FLOW_MIN_AIR_FLOW_SETPOINT = value;
    }
}

#[wasm_bindgen]
pub fn set_clg_flow_max_air_flow_setpoint(value: f64) {
    unsafe {
        CLG_FLOW_MAX_AIR_FLOW_SETPOINT = value;
    }
}

#[wasm_bindgen]
pub fn set_htg_flow_min_air_flow_setpoint(value: f64) {
    unsafe {
        HTG_FLOW_MIN_AIR_FLOW_SETPOINT = value;
    }
}

#[wasm_bindgen]
pub fn set_htg_flow_max_air_flow_setpoint(value: f64) {
    unsafe {
        HTG_FLOW_MAX_AIR_FLOW_SETPOINT = value;
    }
}

#[wasm_bindgen]
pub fn set_satisfied_flow_min_air_flow_setpoint(value: f64) {
    unsafe {
        SATISFIED_FLOW_MIN_AIR_FLOW_SETPOINT = value;
    }
}

#[wasm_bindgen]
pub fn set_max_discharge_air_temp(value: f64) {
    unsafe {
        MAX_DISCHARGE_AIR_TEMP = value;
    }
}

#[wasm_bindgen]
pub fn set_zone_air_temp_deadband(value: f64) {
    unsafe {
        ZONE_AIR_TEMP_DEADBAND = value;
    }
}

#[wasm_bindgen]
pub fn get_pid_output_heating() -> f64 {
    unsafe { PID_OUTPUT_HEATING }
}

#[wasm_bindgen]
pub fn get_pid_output_cooling() -> f64 {
    unsafe { PID_OUTPUT_COOLING }
}


#[wasm_bindgen]
pub fn calculate_pid() {
    unsafe {
        let error = ZONE_AIR_TEMP_SETPOINT - ZONE_AIR_TEMP;
        MODE = if error.abs() > ZONE_AIR_TEMP_DEADBAND / 2.0 {
            if error > 0.0 { 1 } else { 2 }
        } else {
            0
        };

        let (kp, ki, integral, pid_output) = match MODE {
            1 => (
                &mut KP_HEATING,
                &mut KI_HEATING,
                &mut INTEGRAL_HEATING,
                &mut PID_OUTPUT_HEATING,
            ),
            2 => (
                &mut KP_COOLING,
                &mut KI_COOLING,
                &mut INTEGRAL_COOLING,
                &mut PID_OUTPUT_COOLING,
            ),
            _ => return,
        };

        *integral += error; // Update integral
        let output = (*kp) * error + (*ki) * (*integral);

        // Limit output and reset integral if necessary
        let limited_output = output.min(100.0);
        if output != limited_output {
            // Prevent integral wind-up
            *integral -= error; 
        }

        match MODE {
            1 => {
                *pid_output = limited_output;
                PID_OUTPUT_COOLING = 0.0;
            }
            2 => {
                *pid_output = limited_output;
                PID_OUTPUT_HEATING = 0.0;
            }
            _ => {
                PID_OUTPUT_HEATING = 0.0;
                PID_OUTPUT_COOLING = 0.0;
            }
        }
    }
}

#[wasm_bindgen]
pub fn calculate_control_logic() {
    calculate_pid();
    calculate_discharge_air_temp_setpoint();
    calculate_discharge_air_flow_setpoint();
}

fn interpolate_output(pid_output: f64, max_val: f64, min_val: f64) -> f64 {
    let scaled_output = pid_output / 100.0;  // Scale PID output to 0-1 range
    let range_difference = max_val - min_val;
    min_val + scaled_output * range_difference 
}

pub fn calculate_discharge_air_temp_setpoint() {
    unsafe {
        match MODE {
            1 => { // Heating mode
                if PID_OUTPUT_HEATING <= 50.0 {
                    DISCHARGE_AIR_TEMP_SETPOINT = interpolate_output(
                        PID_OUTPUT_HEATING,
                        MAX_DISCHARGE_AIR_TEMP,
                        AHU_SUPPLY_AIR_TEMP,
                    );
                } else {
                    // When PID output is above 50
                    // set to max discharge air temperature
                    DISCHARGE_AIR_TEMP_SETPOINT = MAX_DISCHARGE_AIR_TEMP;
                }
            },
            2 => { // Cooling mode or other modes
                DISCHARGE_AIR_TEMP_SETPOINT = AHU_SUPPLY_AIR_TEMP;
            },
            _ => { // Satisfied mode or unknown mode
                DISCHARGE_AIR_TEMP_SETPOINT = AHU_SUPPLY_AIR_TEMP;
            },
        }
    }
}

pub fn calculate_discharge_air_flow_setpoint() {
    unsafe {
        match MODE {
            1 => { // Heating mode
                DISCHARGE_AIR_FLOW_SETPOINT = if PID_OUTPUT_HEATING > 50.0 {
                    interpolate_output(
                        PID_OUTPUT_HEATING,
                        HTG_FLOW_MAX_AIR_FLOW_SETPOINT,
                        HTG_FLOW_MIN_AIR_FLOW_SETPOINT,
                    )
                } else {
                    HTG_FLOW_MIN_AIR_FLOW_SETPOINT
                };
            },
            2 => { // Cooling mode
                DISCHARGE_AIR_FLOW_SETPOINT = interpolate_output(
                    PID_OUTPUT_COOLING,
                    CLG_FLOW_MAX_AIR_FLOW_SETPOINT,
                    CLG_FLOW_MIN_AIR_FLOW_SETPOINT,
                );
            },
            _ => { // Satisfied mode
                DISCHARGE_AIR_FLOW_SETPOINT = SATISFIED_FLOW_MIN_AIR_FLOW_SETPOINT;
            },
        }
    }
}
