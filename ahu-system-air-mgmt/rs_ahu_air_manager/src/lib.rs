use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::ffi::{CStr, CString};
use std::os::raw::c_char;

#[derive(Debug, Clone, Serialize, Deserialize)]
struct ZoneConfig {
    az_sqft: i32,
    ra_cfm_per_sqft: f32,
    rp_cfm_per_person: f32,
    cfm_min: i32,
    cfm_max: i32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct AshraeStandards {
    ez: f32,
    co2_sf_per_person: i32,
    people_limit_for_co2: i32,
    area_limit_for_co2: i32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct SystemConfig {
    zones: HashMap<String, ZoneConfig>,
    ashrae_standards: AshraeStandards,
}

#[no_mangle]
pub extern "C" fn create_system_config(config_json: *const c_char) -> *mut c_char {
    let config_str = unsafe { CStr::from_ptr(config_json).to_str().unwrap() };
    let system_config: SystemConfig = serde_json::from_str(config_str).unwrap();
    println!("System configuration created with {} zones.", system_config.zones.len());
    let config_json = serde_json::to_string(&system_config).unwrap();
    let c_string = CString::new(config_json).expect("CString::new failed");
    let ptr = c_string.into_raw();
    println!("SystemConfig JSON allocated at pointer {:?}", ptr);
    ptr
}

#[no_mangle]
pub extern "C" fn free_system_config(ptr: *mut c_char) {
    unsafe {
        if !ptr.is_null() {
            println!("Freeing SystemConfig at pointer {:?}", ptr);
            let _ = CString::from_raw(ptr);
        } else {
            println!("Received null pointer, no action taken.");
        }
    }
}

#[no_mangle]
pub extern "C" fn version() -> *mut c_char {
    let version_info = "Version 1.0 of HVAC System Configurations";
    println!("Providing version info: {}", version_info);
    let c_string = CString::new(version_info).expect("CString::new failed");
    let ptr = c_string.into_raw();
    println!("Version info allocated at pointer {:?}", ptr);
    ptr
}

#[no_mangle]
pub extern "C" fn free_string(s: *mut c_char) {
    unsafe {
        if !s.is_null() {
            println!("Freeing memory at pointer {:?}", s);
            let _ = CString::from_raw(s);
        } else {
            println!("Received null pointer, no action taken.");
        }
    }
}
