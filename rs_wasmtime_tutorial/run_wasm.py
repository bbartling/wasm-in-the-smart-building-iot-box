
'''
compiled with
$ cargo build --target wasm32-wasi --release

'''

import wasmtime

def print_greet(instance, store):
    greet_func = instance.exports(store)["greet"]
    ptr = greet_func(store)
    memory = instance.exports(store)["memory"]
    data = memory.data_ptr(store)
    result = []
    i = 0
    while data[ptr + i] != 0:
        result.append(chr(data[ptr + i]))
        i += 1
    string = ''.join(result)
    print(string)
    free_func = instance.exports(store)["free_string"]
    free_func(store, ptr)

# Create the WasiConfig without redirecting stdout
wasi_config = wasmtime.WasiConfig()
wasi_config.inherit_stdout() 
#wasi_config.stdout_file = "output.txt"

# Create the engine
engine = wasmtime.Engine()

# Create the store and apply the WASI configuration
store = wasmtime.Store(engine)
store.set_wasi(wasi_config)

# Load the WASM module
module_path = './target/wasm32-wasi/release/rs_wasmtime_tutorial.wasm'
module = wasmtime.Module.from_file(engine, module_path)

# Set up the linker and define WASI
linker = wasmtime.Linker(engine)
linker.define_wasi()

# Instantiate the module
instance = linker.instantiate(store, module)

# Call the function to print the greeting
print_greet(instance, store)

# Example usage of the add function
add_func = instance.exports(store)["add"]
result = add_func(store, 5, 3)
print("5 + 3 =", result)
