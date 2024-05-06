

# Global configuration for HVAC system
system_config = {
    'zones': {
        'zone1': {'Az_sqft': 1000, 'Ra_cfm_per_sqft': 1, 'Rp_cfm_per_person': 5, 'cfm_min': 200, 'cfm_max': 500},
        'zone2': {'Az_sqft': 2000, 'Ra_cfm_per_sqft': 1, 'Rp_cfm_per_person': 5, 'cfm_min': 400, 'cfm_max': 1000},
        'zone3': {'Az_sqft': 1500, 'Ra_cfm_per_sqft': 1, 'Rp_cfm_per_person': 5, 'cfm_min': 300, 'cfm_max': 750},
    },
    'ashrae_standards': {
        'Ez': 0.8, 
        'co2_sf_per_person': 40,
        'people_limit_for_co2': 10,
        'area_limit_for_co2': 150,
    }
}

# Function to calculate AHU % Outside Air based on sensor readings
def calculate_ahu_percent_oa(mixed_air_temp, return_air_temp, outside_air_temp, ahu_outside_air_damper_cmd):
    if mixed_air_temp is None or return_air_temp is None or outside_air_temp is None:
        print("Invalid sensor data provided.")
        return None
    if outside_air_temp != return_air_temp:
        percent_oa = (mixed_air_temp - return_air_temp) / (outside_air_temp - return_air_temp)
    else:
        percent_oa = 0

    print(f" percent_oa calculated is: {percent_oa}")
        
    ahu_oa_dpr_cmd_as_percent = ahu_outside_air_damper_cmd / 100
    if ahu_oa_dpr_cmd_as_percent > percent_oa:
        print(f" ahu_oa_dpr_cmd_as_percent > percent_oa!")
        percent_oa = ahu_oa_dpr_cmd_as_percent
        print(f" percent_oa is now {percent_oa}")

    print(f"Calculated AHU % Outside Air: {percent_oa*100:.2f}%")
    return percent_oa

# Function to calculate VAV box minimum air flow setpoints based on ASHRAE 62.1 Equation 6-1
def calc_vav_flow_setpoints(Pz, percent_oa):
    '''
    Vbz calculation that incorporates zone population (Pz) 
    and AHU percent OA and Zone Air Distribution Effectiveness (Ez).
    TODO see if Ez can be revised for dynamic calc?
    Vbz = (Rp * Pz + Ra * Az) / Ez / percent_oa
    '''
    vav_flow_setpoints = {}
    for zone, occupancy in Pz.items():
        config = system_config['zones'][zone]
        standards = system_config['ashrae_standards']
        if percent_oa > 0:
            Vbz = (config['Rp_cfm_per_person'] * occupancy + config['Ra_cfm_per_sqft'] * config['Az_sqft']) / standards['Ez']
            setpoint = Vbz / percent_oa
            vav_flow_setpoints[zone] = setpoint
        else:
            vav_flow_setpoints[zone] = None
        print(f"VAV setpoint for {zone}: {vav_flow_setpoints[zone]} CFM")
    return vav_flow_setpoints

# Example usage
if __name__ == "__main__":
    # Simulated sensor readings and conditions
    mixed_air_temp = 60.0  # degrees F
    return_air_temp = 72.1  # degrees F
    outside_air_temp = 40.2  # degrees F
    ahu_outside_air_damper_cmd = 55.5 # percent command

    # Occupancy People Counts
    Pz = {'zone1': 12, 'zone2': 15, 'zone3': 8}

    # Calculate AHU % OA
    percent_oa = calculate_ahu_percent_oa(mixed_air_temp, return_air_temp, outside_air_temp, ahu_outside_air_damper_cmd)
    
    # Calculate VAV box setpoints based on the AHU % OA
    vav_setpoints = calc_vav_flow_setpoints(Pz, percent_oa)
    print(f"VAV Box Setpoints: {vav_setpoints}")
