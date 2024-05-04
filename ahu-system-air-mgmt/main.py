import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global configuration for HVAC system
# Make up some fake stuff
system_config = {
    'zones': {
        'zone1': {'sqft': 1000, 'cfm_per_sqft': 1, 'cfm_per_person': 5, 'cfm_min': 200, 'cfm_max': 500},
        'zone2': {'sqft': 2000, 'cfm_per_sqft': 1, 'cfm_per_person': 5, 'cfm_min': 400, 'cfm_max': 1000},
        'zone3': {'sqft': 1500, 'cfm_per_sqft': 1, 'cfm_per_person': 5, 'cfm_min': 300, 'cfm_max': 750},
    },
    'ashrae_standards': {
        'Ez': 0.8,
        'co2_sf_per_person': 40,
        'people_limit_for_co2': 10,
        'area_limit_for_co2': 150,
    }
}

# Function to calculate AHU % Outside Air based on sensor readings
def calculate_ahu_percent_oa(mixed_air_temp, return_air_temp, outside_air_temp):
    if mixed_air_temp is None or return_air_temp is None or outside_air_temp is None:
        logger.error("Invalid sensor data provided.")
        return None
    if outside_air_temp != return_air_temp:
        percent_oa = (mixed_air_temp - return_air_temp) / (outside_air_temp - return_air_temp)
    else:
        percent_oa = 0
    logger.info(f"Calculated AHU % Outside Air: {percent_oa*100:.2f}%")
    return percent_oa

# Function to calculate VAV box minimum air flow setpoints
def calc_vav_flow_setpoints(occupancies, percent_oa):
    vav_flow_setpoints = {}
    for zone, occupancy in occupancies.items():
        zone_config = system_config['zones'][zone]
        standards = system_config['ashrae_standards']
        if percent_oa > 0:
            cfm_base = (zone_config['cfm_per_sqft'] * zone_config['sqft'] + zone_config['cfm_per_person'] * occupancy) / standards['Ez']
            setpoint = cfm_base / percent_oa
            vav_flow_setpoints[zone] = setpoint
        else:
            vav_flow_setpoints[zone] = None
        logger.info(f"VAV setpoint for {zone}: {vav_flow_setpoints[zone]} CFM")
    return vav_flow_setpoints

# Example usage
if __name__ == "__main__":
    # Simulated sensor readings
    mixed_air_temp = 18  # degrees Celsius
    return_air_temp = 22  # degrees Celsius
    outside_air_temp = 15  # degrees Celsius

    # Occupancy updates
    occupancies = {'zone1': 12, 'zone2': 15, 'zone3': 8}

    # Calculate AHU % OA
    percent_oa = calculate_ahu_percent_oa(mixed_air_temp, return_air_temp, outside_air_temp)
    
    # Calculate VAV box setpoints based on the AHU % OA
    vav_setpoints = calc_vav_flow_setpoints(occupancies, percent_oa)
    logger.info(f"VAV Box Setpoints: {vav_setpoints}")
