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
    let config_str = unsafe { 
        assert!(!config_json.is_null());
        match CStr::from_ptr(config_json).to_str() {
            Ok(str) => str,
            Err(_) => return std::ptr::null_mut()  // Handle invalid UTF-8 gracefully
        }
    };
    let system_config: SystemConfig = match serde_json::from_str(config_str) {
        Ok(config) => config,
        Err(_) => return std::ptr::null_mut()  // Handle JSON parsing errors
    };
    println!("System configuration created with {} zones.", system_config.zones.len());
    let config_json = match serde_json::to_string(&system_config) {
        Ok(json) => json,
        Err(_) => return std::ptr::null_mut()  // Handle serialization errors
    };
    let c_string = CString::new(config_json).unwrap_or_else(|_| CString::new("").unwrap()); // Handle NUL errors in JSON
    let ptr = c_string.into_raw();
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


#[cfg(test)]
mod tests {
    use super::*;
    use std::ffi::{CString, CStr};

    #[test]
    fn test_create_system_config_valid() {
        let input = r#"{
            "zones": {
                "zone1": {"az_sqft": 1000, "ra_cfm_per_sqft": 1.0, "rp_cfm_per_person": 5.0, "cfm_min": 200, "cfm_max": 500}
            },
            "ashrae_standards": {"ez": 0.8, "co2_sf_per_person": 40, "people_limit_for_co2": 10, "area_limit_for_co2": 150}
        }"#;
        let c_input = CString::new(input).unwrap();
        let ptr = create_system_config(c_input.as_ptr());

        unsafe {
            assert!(!ptr.is_null());
            let output = CStr::from_ptr(ptr).to_str().unwrap();
            println!("Output JSON: {}", output);
            assert!(output.contains("zone1"));
            free_system_config(ptr);
        }
    }

    #[test]
    fn test_create_system_config_invalid_json() {
        let input = r#"{"zones": {"zone1": {"az_sqft": "not an integer"}}}"#;
        let c_input = CString::new(input).unwrap();
        let ptr = create_system_config(c_input.as_ptr());

        assert!(ptr.is_null());
    }

    #[test]
    fn test_version() {
        let ptr = version();
        unsafe {
            assert!(!ptr.is_null());
            let version_info = CStr::from_ptr(ptr).to_str().unwrap();
            assert_eq!(version_info, "Version 1.0 of HVAC System Configurations");
            free_string(ptr);
        }
    }
}
