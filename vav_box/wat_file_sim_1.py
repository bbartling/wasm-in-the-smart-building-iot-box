import wasmtime

# Load the WASM module.
engine = wasmtime.Engine()
store = wasmtime.Store(engine)
module = wasmtime.Module.from_file(engine, './wat/pi_block.wasm')

# Create a linking environment
linker = wasmtime.Linker(engine)

# Create global types for sensor value, set point, and other parameters
sensor_value_type = wasmtime.GlobalType(wasmtime.ValType.f64(), mutable=True)
set_point_type = wasmtime.GlobalType(wasmtime.ValType.f64(), mutable=False)
kp_type = wasmtime.GlobalType(wasmtime.ValType.f64(), mutable=False)
ki_type = wasmtime.GlobalType(wasmtime.ValType.f64(), mutable=False)
accumulated_error_type = wasmtime.GlobalType(wasmtime.ValType.f64(), mutable=True)

# Define necessary global variables using their respective types
sensor_value = wasmtime.Global(store, sensor_value_type, wasmtime.Val.f64(0.0))
set_point = wasmtime.Global(store, set_point_type, wasmtime.Val.f64(0.0))
kp = wasmtime.Global(store, kp_type, wasmtime.Val.f64(0.1))  # Assume these are the PID constants
ki = wasmtime.Global(store, ki_type, wasmtime.Val.f64(0.01))
accumulated_error = wasmtime.Global(store, accumulated_error_type, wasmtime.Val.f64(0.0))

# Define these globals in the linker to match the module imports
linker.define(store, "env", "sensorValue", sensor_value)
linker.define(store, "env", "setPoint", set_point)
linker.define(store, "env", "Kp", kp)
linker.define(store, "env", "Ki", ki)
linker.define(store, "env", "accumulatedError", accumulated_error)

# Instantiate the module with the linker
instance = linker.instantiate(store, module)

# Now you can call the exported function
calculate_output = instance.exports(store)["calculateOutput"]
output = calculate_output(store)
print("PI Controller Output:", output)

