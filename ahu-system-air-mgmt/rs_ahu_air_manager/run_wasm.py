import json
import wasmtime

#help(wasmtime.Memory.write)


# Define system configuration
system_config = {
    'zones': {
        'zone1': {'az_sqft': 1000, 'ra_cfm_per_sqft': 1.0, 'rp_cfm_per_person': 5.0, 'cfm_min': 200, 'cfm_max': 500},
        'zone2': {'az_sqft': 2000, 'ra_cfm_per_sqft': 1.0, 'rp_cfm_per_person': 5.0, 'cfm_min': 400, 'cfm_max': 1000},
        'zone3': {'az_sqft': 1500, 'ra_cfm_per_sqft': 1.0, 'rp_cfm_per_person': 5.0, 'cfm_min': 300, 'cfm_max': 750},
    },
    'ashrae_standards': {'ez': 0.8, 'co2_sf_per_person': 40, 'people_limit_for_co2': 10, 'area_limit_for_co2': 150},
}


def create_system_config(config_json, store, instance):
    """ Create the HVAC system configuration in Rust from JSON """
    memory = instance.exports(store)["memory"]
    config_bytes = bytearray(config_json.encode('utf-8'))  # Ensure it's a bytearray
    
    # Allocate memory for the config
    memory_length = memory.data_len(store)
    config_ptr = memory_length - len(config_bytes) - 1

    # Check if there's enough space to write the data
    if config_ptr < 0 or config_ptr + len(config_bytes) > memory_length:
        raise Exception("Not enough memory to write the configuration data")

    # Correct usage of the write method
    try:
        bytes_written = memory.write(store, config_bytes, config_ptr)
        print(f"Bytes written: {bytes_written}")
    except IndexError as e:
        raise Exception(f"Memory write error: {str(e)}")

    create_func = instance.exports(store)["create_system_config"]
    result_ptr = create_func(store, config_ptr)
    
    if result_ptr == 0:
        raise ValueError("Failed to create system configuration")
    
    return result_ptr


def read_string_from_memory(ptr, store, instance):
    """ Read a null-terminated string from memory """
    memory = instance.exports(store)["memory"]
    data = []
    offset = 0
    while True:
        byte = memory.read(store, ptr + offset, 1)[0]
        if byte == 0:
            break
        data.append(byte)
        offset += 1
    return bytes(data).decode('utf-8')

def free_system_config(ptr, store, instance):
    """ Free the memory allocated by Rust for the configuration """
    free_func = instance.exports(store)["free_system_config"]
    free_func(store, ptr)

# Setup the WASM environment
engine = wasmtime.Engine()
store = wasmtime.Store(engine)
linker = wasmtime.Linker(engine)
linker.define_wasi()
module_path = './target/wasm32-wasi/release/rs_ahu_air_manager.wasm'
module = wasmtime.Module.from_file(engine, module_path)
instance = linker.instantiate(store, module)

# Serialize system configuration to JSON
config_json = json.dumps(system_config)

# Create system configuration in Rust and get pointer to the result
config_ptr = create_system_config(config_json, store, instance)
config_str = read_string_from_memory(config_ptr, store, instance)
print("System Configuration Created:", config_str)

# Optionally, retrieve version information
version_func = instance.exports(store)["version"]
version_ptr = version_func(store)
version_str = read_string_from_memory(version_ptr, store, instance)
print("Version:", version_str)

# Free memory allocated for the system configuration and version string
free_system_config(config_ptr, store, instance)
free_func = instance.exports(store)["free_string"]
free_func(store, version_ptr)
