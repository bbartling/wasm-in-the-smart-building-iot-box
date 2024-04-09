import wasmtime


# https://dev.to/ajeetraina/using-webassembly-with-python-o61

# Load the compiled WebAssembly module
wasm_module = "./c/vav_controller.wasm"

# Create an instance of the module
instance = wasmtime.Instance(wasm_module)

# Get a reference to the exported function
square_func = instance.exports.square

# Call the function and print the result
result = square_func(5)
print("Square of 5:", result)
