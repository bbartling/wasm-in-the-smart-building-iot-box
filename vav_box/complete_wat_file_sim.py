import wasmtime


# Initialize the WASM environment
engine = wasmtime.Engine()
store = wasmtime.Store(engine)
module = wasmtime.Module.from_file(engine, "./wat/complete_sim.wat")
linker = wasmtime.Linker(engine)

# Define global variables for WASM based on the .wat definitions
# only points in sim to be passed from py to wasm all else
# is just default values to be set in the wat file
space_temp = wasmtime.Global(
    store,
    wasmtime.GlobalType(wasmtime.ValType.f64(), mutable=True),
    wasmtime.Val.f64(68.0),
)

set_point = wasmtime.Global(
    store,
    wasmtime.GlobalType(wasmtime.ValType.f64(), mutable=True),
    wasmtime.Val.f64(72.0),
)


# Define globals in the linker to match the module imports
linker.define(store, "env", "space_temp", space_temp)
linker.define(store, "env", "setPoint", set_point)

# Instantiate the module with the linker
instance = linker.instantiate(store, module)
calculate_output = instance.exports(store)["control_logic"]
integral_heating = instance.exports(store)["integral_heating"]
integral_cooling = instance.exports(store)["integral_cooling"]
control_mode = instance.exports(store)["control_mode"]

def simulate_with_wasm():

    # Simulation parameters
    satisfied_temp = 73.0
    constant_cooling_temp = 78.0
    constant_heating_temp = 66.0
    steps = 30

    print(f"Initial Temp = {space_temp.value(store)}F, Set Point = {set_point.value(store)}F")

    print("\nTesting Heating Demand with Constant Temperature outside Deadband")
    for step in range(10):
        space_temp.set_value(store, wasmtime.Val.f64(constant_heating_temp)) 

        output = calculate_output(store)
        mode = calculate_output(store)
        mode_desc = {0: 'Satisfied', 1: 'Heating', 2: 'Cooling'}
        print(f"************* STEP: {step+1} *************")
        print(f"Current Temp = {space_temp.value(store):.2f}F, Mode = {mode_desc[mode]}, PI % Output = {output:.2f}%")
        print(f"Heating Integral = {integral_heating.value(store):.2f}, Cooling Integral = {integral_cooling.value(store):.2f}")


    print("\nTesting Satisfied Mode within Deadband")
    for step in range(5):
        space_temp.set_value(store, wasmtime.Val.f64(satisfied_temp))

        output = calculate_output(store)
        mode = calculate_output(store)
        mode_desc = {0: 'Satisfied', 1: 'Heating', 2: 'Cooling'}
        print(f"************* STEP: {step+1} *************")
        print(f"Current Temp = {space_temp.value(store):.2f}F, Mode = {mode_desc[mode]}, PI % Output = {output:.2f}%")
        print(f"Heating Integral = {integral_heating.value(store):.2f}, Cooling Integral = {integral_cooling.value(store):.2f}")

    print("\nTesting Cooling Demand with Constant Temperature outside Deadband")
    for step in range(5, steps):
        space_temp.set_value(store, wasmtime.Val.f64(constant_cooling_temp))

        output = calculate_output(store)
        mode = calculate_output(store)
        mode_desc = {0: 'Satisfied', 1: 'Heating', 2: 'Cooling'}
        print(f"************* STEP: {step+1} *************")
        print(f"Current Temp = {space_temp.value(store):.2f}F, Mode = {mode_desc[mode]}, PI % Output = {output:.2f}%")
        print(f"Heating Integral = {integral_heating.value(store):.2f}, Cooling Integral = {integral_cooling.value(store):.2f}")


simulate_with_wasm()