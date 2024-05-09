import wasmtime

def custom_print_greet(instance, store, input_str):
    memory = instance.exports(store)["memory"]
    greet_func = instance.exports(store)["custom_greet"]

    # Encode the input string to bytes
    input_bytes = input_str.encode('utf-8')

    # Get available memory length and calculate the position to write the input bytes
    memory_length = memory.data_len(store)
    input_ptr = memory_length - len(input_bytes) - 1

    print(f"Writing to memory: Input string bytes = {input_bytes}")
    print(f"Memory data length = {memory_length}, Input pointer = {input_ptr}")

    # Write the input bytes to memory
    if input_ptr + len(input_bytes) > memory_length:
        raise Exception("Not enough space in memory to write the input bytes")
    
    memory.write(store, input_bytes, start=input_ptr)
    print("String written to WASM memory at pointer", input_ptr)

    # Call the custom greet function with the pointer to the input string
    ptr = greet_func(store, input_ptr)
    print(f"Received pointer from custom_greet: {ptr}")

    # Read the result string from WASM memory
    result_bytes = []
    offset = 0
    while True:
        byte = memory.read(store, start=ptr + offset, stop=ptr + offset + 1)[0]
        if byte == 0:
            break
        result_bytes.append(byte)
        offset += 1
    string = bytes(result_bytes).decode('utf-8')
    print(f"Resulting string: {string}")

    # Free the allocated string in WASM
    free_func = instance.exports(store)["free_string"]
    free_func(store, ptr)
    print("Freed memory at pointer:", ptr)

# Configuration and module loading
wasi_config = wasmtime.WasiConfig()
wasi_config.inherit_stdout()

engine = wasmtime.Engine()
store = wasmtime.Store(engine)
store.set_wasi(wasi_config)

module_path = './target/wasm32-wasi/release/rs_wasmtime_tutorial.wasm'
module = wasmtime.Module.from_file(engine, module_path)

linker = wasmtime.Linker(engine)
linker.define_wasi()

instance = linker.instantiate(store, module)

# Pass a custom string and print the greeting
custom_print_greet(instance, store, "World")

# Example usage of the add function
add_func = instance.exports(store)["add"]
result = add_func(store, 5, 3)
print("5 + 3 =", result)
