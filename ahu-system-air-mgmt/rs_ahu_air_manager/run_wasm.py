import wasmtime

# compile with
# $ cargo build --target wasm32-wasi --release

'''
NOT WORKING YET
'''

def setup_environment():
    wasi_config = wasmtime.WasiConfig()
    wasi_config.inherit_stdout()
    wasi_config.inherit_stderr()

    engine = wasmtime.Engine()
    store = wasmtime.Store(engine)
    store.set_wasi(wasi_config)

    linker = wasmtime.Linker(engine)
    linker.define_wasi()

    module_path = './target/wasm32-wasi/release/rs_ahu_air_manager.wasm'
    module = wasmtime.Module.from_file(engine, module_path)
    instance = linker.instantiate(store, module)

    return store, instance

def create_default_system_config(store, instance):
    """Retrieve the default HVAC system configuration from Rust"""
    create_func = instance.exports(store)["create_default_system_config"]
    result_ptr = create_func(store)
    
    if result_ptr == 0:
        raise ValueError("Failed to retrieve system configuration")
    
    return result_ptr

def read_string_from_memory(ptr, store, instance):
    memory = instance.exports(store)["memory"]
    data = []
    offset = 0
    memory_length = memory.data_len(store)  # Get the total length of the memory

    while True:
        # Check if the pointer+offset is within the memory bounds
        if ptr + offset >= memory_length:
            break
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
    config_ptr = create_default_system_config(store, instance)
    config_str = read_string_from_memory(config_ptr, store, instance)
    print("System Configuration Created:", config_str)

    version_func = instance.exports(store)["version"]
    version_ptr = version_func(store)
    version_str = read_string_from_memory(version_ptr, store, instance)
    print("Version:", version_str)

    # Free memory allocated for the system configuration and version string
    free_system_config(config_ptr, store, instance)
    free_func = instance.exports(store)["free_string"]
    free_func(store, version_ptr)
