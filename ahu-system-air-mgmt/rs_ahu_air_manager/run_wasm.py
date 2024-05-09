import json
import wasmtime

def create_system_config(config_json, store, instance):
    """ Create the HVAC system configuration in Rust from JSON """
    memory = instance.exports(store)["memory"]
    
    # Convert JSON string to bytes
    config_json_bytes = config_json.encode('utf-8')

    # Ensure there is enough memory in the WASM instance
    current_memory_pages = memory.size(store)
    needed_memory_pages = (len(config_json_bytes) + memory.data_len(store) - 1) // 65536 + 1
    if needed_memory_pages > current_memory_pages:
        memory.grow(store, needed_memory_pages - current_memory_pages)

    # Write JSON bytes into WASM memory at an offset (e.g., at the start)
    memory.write(store, 0, config_json_bytes)  # Correct usage
    #memory.write(store, 0, config_json_bytes, len(config_json_bytes))

    # Assuming create_system_config in Rust takes a pointer (offset) and length
    create_func = instance.exports(store)["create_system_config"]
    ptr = create_func(store, 0, len(config_json_bytes))
    return ptr

def free_system_config(ptr, store, instance):
    """ Free the memory allocated by Rust for the configuration """
    free_func = instance.exports(store)["free_system_config"]
    free_func(store, ptr)

def calculate_percent_oa(store, instance, sensor_data):
    """ Calculate the percentage of outside air based on sensor readings """
    memory = instance.exports(store)["memory"]
    sensor_data_json = json.dumps(sensor_data)
    sensor_data_bytes = sensor_data_json.encode('utf-8')

    # Ensure memory is sufficient
    current_memory_pages = memory.size(store)
    needed_memory_pages = (len(sensor_data_bytes) + memory.data_len(store) - 1) // 65536 + 1
    if needed_memory_pages > current_memory_pages:
        memory.grow(store, needed_memory_pages - current_memory_pages)

    # Write sensor data into WASM memory
    memory.write(store, 0, sensor_data_bytes)  # Assuming we write at position 0 for simplicity

    # Call the Rust function with offset and length
    calc_func = instance.exports(store)["calculate_percent_oa"]
    result = calc_func(store, 0, len(sensor_data_bytes))
    return result

# Setup the WASM environment
engine = wasmtime.Engine()
store = wasmtime.Store(engine)
linker = wasmtime.Linker(engine)
linker.define_wasi()
module_path = './target/wasm32-wasi/release/rs_ahu_air_manager.wasm'
module = wasmtime.Module.from_file(engine, module_path)
instance = linker.instantiate(store, module)

# Define system configuration
system_config = {
    'zones': {
        'zone1': {'Az_sqft': 1000, 'Ra_cfm_per_sqft': 1, 'Rp_cfm_per_person': 5, 'cfm_min': 200, 'cfm_max': 500},
        'zone2': {'Az_sqft': 2000, 'Ra_cfm_per_sqft': 1, 'Rp_cfm_per_person': 5, 'cfm_min': 400, 'cfm_max': 1000},
        'zone3': {'Az_sqft': 1500, 'Ra_cfm_per_sqft': 1, 'Rp_cfm_per_person': 5, 'cfm_min': 300, 'cfm_max': 750},
    },
    'ashrae_standards': {'Ez': 0.8, 'co2_sf_per_person': 40, 'people_limit_for_co2': 10, 'area_limit_for_co2': 150},
}
config_json = json.dumps(system_config)
config_ptr = create_system_config(config_json, store, instance)

# Example sensor data for the HVAC system
sensor_data = [60.0, 72.1, 40.2, 55.5]  # Mixed air temp, return air temp, outside air temp, damper command
percent_oa = calculate_percent_oa(store, instance, sensor_data)
print(f"Calculated AHU % Outside Air: {percent_oa*100:.2f}%")

# Clean up by freeing the system configuration
free_system_config(config_ptr, store, instance)
