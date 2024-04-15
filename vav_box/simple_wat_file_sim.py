import wasmtime

# Initialize sim constants for the PI block
INITIAL_SETPOINT = 72.0
INITIAL_ZONE_TEMP = 68.0
KP = 5.0
KI = 1.0

# Load the WASM module.
engine = wasmtime.Engine()
store = wasmtime.Store(engine)
module = wasmtime.Module.from_file(engine, './wat/simple_sim.wat')

# Create a linking environment
linker = wasmtime.Linker(engine)

# Create global types for sensor value, set point, and other parameters
sensor_value_type = wasmtime.GlobalType(wasmtime.ValType.f64(), mutable=True)
set_point_type = wasmtime.GlobalType(wasmtime.ValType.f64(), mutable=False)
kp_type = wasmtime.GlobalType(wasmtime.ValType.f64(), mutable=False)
ki_type = wasmtime.GlobalType(wasmtime.ValType.f64(), mutable=False)
accumulated_error_type = wasmtime.GlobalType(wasmtime.ValType.f64(), mutable=True)

# Define necessary global variables using their respective types
sensor_value = wasmtime.Global(store, sensor_value_type, wasmtime.Val.f64(INITIAL_ZONE_TEMP))
set_point = wasmtime.Global(store, set_point_type, wasmtime.Val.f64(INITIAL_SETPOINT))
kp = wasmtime.Global(store, kp_type, wasmtime.Val.f64(KP))
ki = wasmtime.Global(store, ki_type, wasmtime.Val.f64(KI))
accumulated_error = wasmtime.Global(store, accumulated_error_type, wasmtime.Val.f64(0.0))

# Define these globals in the linker to match the module imports
linker.define(store, "env", "sensorValue", sensor_value)
linker.define(store, "env", "setPoint", set_point)
linker.define(store, "env", "Kp", kp)
linker.define(store, "env", "Ki", ki)
linker.define(store, "env", "accumulatedError", accumulated_error)

# Instantiate the module with the linker
instance = linker.instantiate(store, module)

def simulate_with_wasm():
    steps = 10
    print(f"Initial Temp = {sensor_value.value(store)}F, Set Point = {set_point.value(store)}F")

    for step in range(steps):
        # Call the WebAssembly function to calculate the PID output for heating
        calculate_output = instance.exports(store)["calculateOutput"]
        output = calculate_output(store)
        print(f"Step {step + 1}: Current Temp = {sensor_value.value(store):.2f}F, Heating Output = {output:.2f}%")

simulate_with_wasm()
