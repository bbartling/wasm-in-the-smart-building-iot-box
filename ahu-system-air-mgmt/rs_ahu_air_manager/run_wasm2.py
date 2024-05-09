import wasmtime
import json

# Define the HVAC system configuration
system_config = {
    'zones': {
        'zone1': {'az_sqft': 1000, 'ra_cfm_per_sqft': 1.0, 'rp_cfm_per_person': 5.0, 'cfm_min': 200, 'cfm_max': 500},
        'zone2': {'az_sqft': 2000, 'ra_cfm_per_sqft': 1.0, 'rp_cfm_per_person': 5.0, 'cfm_min': 400, 'cfm_max': 1000},
        'zone3': {'az_sqft': 1500, 'ra_cfm_per_sqft': 1.0, 'rp_cfm_per_person': 5.0, 'cfm_min': 300, 'cfm_max': 750},
    },
    'ashrae_standards': {'ez': 0.8, 'co2_sf_per_person': 40, 'people_limit_for_co2': 10, 'area_limit_for_co2': 150},
}

def setup_environment():
    # Create a WASI configuration and set up the environment
    wasi_config = wasmtime.WasiConfig()
    wasi_config.inherit_stdout()
    wasi_config.inherit_stderr()

    engine = wasmtime.Engine()
    store = wasmtime.Store(engine)
    store.set_wasi(wasi_config)

    linker = wasmtime.Linker(engine)
    linker.define_wasi()

    # Load the compiled WebAssembly module
    module_path = './target/wasm32-wasi/release/rs_ahu_air_manager.wasm'
    module = wasmtime.Module.from_file(engine, module_path)
    instance = linker.instantiate(store, module)

    return store, instance

def create_system_config(config_json, store, instance):
    """ Create the HVAC system configuration in Rust from JSON """
    memory = instance.exports(store)["memory"]
    config_bytes = bytearray(config_json.encode('utf-8'))
    
    memory_length = memory.data_len(store)
    config_ptr = memory_length - len(config_bytes) - 1

    if config_ptr < 0 or config_ptr + len(config_bytes) > memory_length:
        raise Exception("Not enough memory to write the configuration data")

    memory.write(store, config_bytes, config_ptr)

    create_func = instance.exports(store)["create_system_config"]
    result_ptr = create_func(store, config_ptr)
    
    if result_ptr == 0:
        raise ValueError("Failed to create system configuration")
    
    return result_ptr

def read_string_from_memory(ptr, store, instance):
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
    free_func = instance.exports(store)["free_system_config"]
    free_func(store, ptr)

# Main execution
if __name__ == "__main__":
    store, instance = setup_environment()
    config_json = json.dumps(system_config)
    config_ptr = create_system_config(config_json, store, instance)
    config_str = read_string_from_memory(config_ptr, store, instance)
    print("System Configuration Created:", config_str)

    version_func = instance.exports(store)["version"]
    version_ptr = version_func(store)
    version_str = read_string_from_memory(version_ptr, store, instance)
    print("Version:", version_str)

    free_system_config(config_ptr, store, instance)
    free_func = instance.exports(store)["free_string"]
    free_func(store, version_ptr)
