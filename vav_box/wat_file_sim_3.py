import wasmtime


# Initialize the WASM environment
engine = wasmtime.Engine()
store = wasmtime.Store(engine)
module = wasmtime.Module.from_file(engine, "./wat/pi_block_3.wat")
linker = wasmtime.Linker(engine)

# Define global variables for WASM based on the .wat definitions
space_temp = wasmtime.Global(
    store,
    wasmtime.GlobalType(wasmtime.ValType.f64(), mutable=True),
    wasmtime.Val.f64(68.0),
)

set_point = wasmtime.Global(
    store,
    wasmtime.GlobalType(wasmtime.ValType.f64(), mutable=False),
    wasmtime.Val.f64(72.0),
)

kp_heating = wasmtime.Global(
    store,
    wasmtime.GlobalType(wasmtime.ValType.f64(), mutable=False),
    wasmtime.Val.f64(5.0),
)

ki_heating = wasmtime.Global(
    store,
    wasmtime.GlobalType(wasmtime.ValType.f64(), mutable=False),
    wasmtime.Val.f64(1.0),
)

kd_heating = wasmtime.Global(
    store,
    wasmtime.GlobalType(wasmtime.ValType.f64(), mutable=False),
    wasmtime.Val.f64(0.0),
)
integral_heating = wasmtime.Global(
    store,
    wasmtime.GlobalType(wasmtime.ValType.f64(), mutable=True),
    wasmtime.Val.f64(0.0),
)

prev_error_heating = wasmtime.Global(
    store,
    wasmtime.GlobalType(wasmtime.ValType.f64(), mutable=True),
    wasmtime.Val.f64(0.0),
)

kp_cooling = wasmtime.Global(
    store,
    wasmtime.GlobalType(wasmtime.ValType.f64(), mutable=False),
    wasmtime.Val.f64(5.0),
)
ki_cooling = wasmtime.Global(
    store,
    wasmtime.GlobalType(wasmtime.ValType.f64(), mutable=False),
    wasmtime.Val.f64(1.0),
)

kd_cooling = wasmtime.Global(
    store,
    wasmtime.GlobalType(wasmtime.ValType.f64(), mutable=False),
    wasmtime.Val.f64(0.0),
)
integral_cooling = wasmtime.Global(
    store,
    wasmtime.GlobalType(wasmtime.ValType.f64(), mutable=True),
    wasmtime.Val.f64(0.0),
)

prev_error_cooling = wasmtime.Global(
    store,
    wasmtime.GlobalType(wasmtime.ValType.f64(), mutable=True),
    wasmtime.Val.f64(0.0),
)

# Define globals in the linker to match the module imports
linker.define(store, "env", "space_temp", space_temp)
linker.define(store, "env", "setPoint", set_point)
linker.define(store, "env", "Kp_heating", kp_heating)
linker.define(store, "env", "Ki_heating", ki_heating)
linker.define(store, "env", "Kd_heating", kd_heating)
linker.define(store, "env", "integral_heating", integral_heating)
linker.define(store, "env", "prev_error_heating", prev_error_heating)
linker.define(store, "env", "Kp_cooling", kp_cooling)
linker.define(store, "env", "Ki_cooling", ki_cooling)
linker.define(store, "env", "Kd_cooling", kd_cooling)
linker.define(store, "env", "integral_cooling", integral_cooling)
linker.define(store, "env", "prev_error_cooling", prev_error_cooling)

# Instantiate the module with the linker
instance = linker.instantiate(store, module)
calculate_output = instance.exports(store)["control_logic"]


def simulate_with_wasm():

    # Simulation parameters
    satisfied_temp = 73.0
    constant_cooling_temp = 76.0
    constant_heating_temp = 68.0
    steps = 30

    print(
        f"Initial Temp = {space_temp.value(store)}F, Set Point = {set_point.value(store)}F"
    )

    print("\nTesting Heating Demand with Constant Temperature outside Deadband")
    for step in range(10):
        print("Type of satisfied_temp:", type(satisfied_temp))  # Debugging type
        space_temp.set_value(store, wasmtime.Val.f64(satisfied_temp))

        output = calculate_output(store)
        print(f"************* STEP: {step+1} *************")
        print(
            f"Current Temp = {space_temp.value(store):.2f}F, Heating Output = {output:.2f}%"
        )

    print("\nTesting Satisfied Mode within Deadband")
    for step in range(5):
        space_temp.set_value(store, wasmtime.Val.f64(constant_heating_temp))
        output = calculate_output(store)
        print(f"************* STEP: {step+1} *************")
        print(
            f"Current Temp = {space_temp.value(store):.2f}F, Satisfied Output = {output:.2f}%"
        )

    print("\nTesting Cooling Demand with Constant Temperature outside Deadband")
    for step in range(5, steps):
        space_temp.set_value(store, wasmtime.Val.f64(constant_cooling_temp))
        output = calculate_output(store)
        print(f"************* STEP: {step+1} *************")
        print(
            f"Current Temp = {space_temp.value(store):.2f}F, Cooling Output = {output:.2f}%"
        )


simulate_with_wasm()
