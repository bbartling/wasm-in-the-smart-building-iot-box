use lazy_static::lazy_static;
use std::collections::HashMap;
use std::ffi::{c_char, CStr, CString};
use std::sync::Mutex;

// compile with
// $ cargo build --target wasm32-wasi --release

// run tests with prints
// $ cargo test -- --nocapture

#[derive(Debug, Clone)]
struct Zone {
    az_sqft: i32,
    ra_cfm_per_sqft: f32,
    rp_cfm_per_person: f32,
    cfm_min: i32,
    cfm_max: i32,
    people_count: i32,
}

#[derive(Debug, Clone)]
struct AshraeStandards {
    ez: f32,
    co2_sf_per_person: f32,
    people_limit_for_co2: i32,
    area_limit_for_co2: i32,
}

#[derive(Debug, Clone)]
struct SystemConfig {
    zones: HashMap<String, Zone>,
    ashrae_standards: AshraeStandards,
}

lazy_static! {
    static ref ZONES: Mutex<HashMap<String, Zone>> = Mutex::new(HashMap::new());
    static ref SYSTEM_CONFIG: Mutex<SystemConfig> = Mutex::new(SystemConfig {
        zones: HashMap::new(),
        ashrae_standards: AshraeStandards {
            ez: 0.8,
            co2_sf_per_person: 40.0,
            people_limit_for_co2: 10,
            area_limit_for_co2: 150,
        },
    });
}

fn calculate_ahu_percent_oa(
    mixed_air_temp: f32,
    return_air_temp: f32,
    outside_air_temp: f32,
    ahu_outside_air_damper_cmd: f32,
) -> f32 {
    if outside_air_temp == return_air_temp {
        return 0.0;
    }
    let percent_oa = (mixed_air_temp - return_air_temp) / (outside_air_temp - return_air_temp);
    let ahu_oa_dpr_cmd_as_percent = ahu_outside_air_damper_cmd / 100.0;
    if ahu_oa_dpr_cmd_as_percent > percent_oa {
        ahu_oa_dpr_cmd_as_percent
    } else {
        percent_oa
    }
}

fn calculate_vav_flow_setpoints(percent_oa: f32) -> HashMap<String, Option<f32>> {
    let config = SYSTEM_CONFIG.lock().unwrap();
    let mut vav_flow_setpoints = HashMap::new();
    for (zone_name, zone) in config.zones.iter() {
        let vbz = (zone.rp_cfm_per_person * zone.people_count as f32
            + zone.ra_cfm_per_sqft * zone.az_sqft as f32)
            / config.ashrae_standards.ez;
        let setpoint = vbz / percent_oa;
        vav_flow_setpoints.insert(zone_name.clone(), Some(setpoint));
    }
    vav_flow_setpoints
}

#[no_mangle]
pub extern "C" fn add_zone(
    zone_name: *const c_char,
    az_sqft: i32,
    ra_cfm_per_sqft: f32,
    rp_cfm_per_person: f32,
    cfm_min: i32,
    cfm_max: i32,
    people_count: i32,
) -> *mut c_char {
    let zone_name = unsafe { CStr::from_ptr(zone_name).to_str().unwrap().to_owned() };
    let zone = Zone {
        az_sqft,
        ra_cfm_per_sqft,
        rp_cfm_per_person,
        cfm_min,
        cfm_max,
        people_count,
    };
    let mut zones = ZONES.lock().unwrap();
    zones.insert(zone_name, zone);
    CString::new("Zone added successfully").unwrap().into_raw()
}

#[no_mangle]
pub extern "C" fn calculate_vav_flow_setpoints_extern() -> *mut c_char {
    let percent_oa = calculate_ahu_percent_oa(60.0, 72.1, 40.2, 55.5); // Example values
    let vav_flow_setpoints = calculate_vav_flow_setpoints(percent_oa);
    let output = format!("{:?}", vav_flow_setpoints);
    CString::new(output)
        .expect("CString::new failed")
        .into_raw()
}

#[no_mangle]
pub extern "C" fn update_people_count(zone_name: *const c_char, new_count: i32) -> *mut c_char {
    // Convert C string to Rust string
    let zone_name = unsafe {
        if zone_name.is_null() {
            return CString::new("Error: null pointer for zone name")
                .unwrap()
                .into_raw();
        }
        match CStr::from_ptr(zone_name).to_str() {
            Ok(str) => str,
            Err(_) => {
                return CString::new("Error: invalid UTF-8 string")
                    .unwrap()
                    .into_raw()
            }
        }
    };

    // Access the global SYSTEM_CONFIG to update the people count
    let mut system_config = SYSTEM_CONFIG.lock().unwrap();
    if let Some(zone) = system_config.zones.get_mut(zone_name) {
        println!(
            "Updating people count for {} from {} to {}",
            zone_name, zone.people_count, new_count
        );
        zone.people_count = new_count;
        CString::new("Update successful").unwrap().into_raw()
    } else {
        CString::new(format!("Error: Zone {} not found", zone_name))
            .unwrap()
            .into_raw()
    }
}

#[no_mangle]
pub extern "C" fn version() -> *mut c_char {
    let version_info = "Version 1.0 of HVAC System Configurations";
    CString::new(version_info)
        .expect("CString::new failed")
        .into_raw()
}

#[no_mangle]
pub extern "C" fn free_string(s: *mut c_char) {
    unsafe {
        if !s.is_null() {
            CString::from_raw(s);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::ffi::{CStr, CString};

    fn setup_default_system_config() {
        // Setup the default system configuration without returning a pointer
        let mut config = SYSTEM_CONFIG.lock().unwrap();
        config.zones.insert(
            "zone1".to_string(),
            Zone {
                az_sqft: 1000,
                ra_cfm_per_sqft: 1.0,
                rp_cfm_per_person: 5.0,
                cfm_min: 200,
                cfm_max: 500,
                people_count: 12,
            },
        );
        config.zones.insert(
            "zone2".to_string(),
            Zone {
                az_sqft: 2000,
                ra_cfm_per_sqft: 1.0,
                rp_cfm_per_person: 5.0,
                cfm_min: 400,
                cfm_max: 1000,
                people_count: 15,
            },
        );
        config.zones.insert(
            "zone3".to_string(),
            Zone {
                az_sqft: 1500,
                ra_cfm_per_sqft: 1.0,
                rp_cfm_per_person: 5.0,
                cfm_min: 300,
                cfm_max: 750,
                people_count: 8,
            },
        );
    }

    #[test]
    fn test_update_people_count_and_calculate_flow_setpoints() {
        // Setup initial configuration
        setup_default_system_config();

        // Zone to update
        let zone_name = CString::new("zone1").unwrap();
        let new_people_count = 20;

        // Update people count
        let update_result = update_people_count(zone_name.as_ptr(), new_people_count);
        unsafe {
            let update_message = CStr::from_ptr(update_result).to_str().unwrap();
            assert_eq!(update_message, "Update successful");
            free_string(update_result);
        }

        // Calculate VAV flow setpoints after update
        let percent_oa = calculate_ahu_percent_oa(60.0, 72.1, 40.2, 55.5); // Assume sensor values
        let setpoints = calculate_vav_flow_setpoints(percent_oa);

        // Check the updated people count impact
        let updated_setpoint = setpoints.get("zone1").unwrap().unwrap();
        println!("Updated VAV Setpoint for zone1: {}", updated_setpoint);
        assert!(updated_setpoint > 0.0); // Specific value depends on initial conditions and formula
    }

    #[test]
    fn test_calculate_ahu_percent_oa() {
        let mixed_air_temp = 60.0;
        let return_air_temp = 72.1;
        let outside_air_temp = 40.2;
        let ahu_outside_air_damper_cmd = 55.5;
        let percent_oa = calculate_ahu_percent_oa(
            mixed_air_temp,
            return_air_temp,
            outside_air_temp,
            ahu_outside_air_damper_cmd,
        );
        assert!(percent_oa > 0.0);
    }

    #[test]
    fn test_calculate_vav_flow_setpoints() {
        setup_default_system_config();
        let percent_oa = calculate_ahu_percent_oa(60.0, 72.1, 40.2, 55.5);
        let setpoints = calculate_vav_flow_setpoints(percent_oa);
        assert!(!setpoints.is_empty());
        assert!(setpoints.get("zone1").unwrap().is_some());
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
