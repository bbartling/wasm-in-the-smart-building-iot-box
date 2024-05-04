import wasmtime
import random
import matplotlib.pyplot as plt

# Initialize the WASM environment
engine = wasmtime.Engine()
store = wasmtime.Store(engine)
module = wasmtime.Module.from_file(engine, "./complete_sim.wat")
linker = wasmtime.Linker(engine)

# Define global variables for WASM based on the .wat definitions
# only points in sim to be passed from py to wasm all else
# is just default values to be set in the wat file
zone_air_temp = wasmtime.Global(
    store,
    wasmtime.GlobalType(wasmtime.ValType.f64(), mutable=True),
    wasmtime.Val.f64(68.0),
)

set_point = wasmtime.Global(
    store,
    wasmtime.GlobalType(wasmtime.ValType.f64(), mutable=True),
    wasmtime.Val.f64(72.0),
)

ahu_supply_air_temp = wasmtime.Global(
    store,
    wasmtime.GlobalType(wasmtime.ValType.f64(), mutable=True),
    wasmtime.Val.f64(61.0),
)

clg_flow_min_air_flow_setpoint = wasmtime.Global(
    store,
    wasmtime.GlobalType(wasmtime.ValType.f64(), mutable=True),
    wasmtime.Val.f64(50.0),
)

clg_flow_max_air_flow_setpoint = wasmtime.Global(
    store,
    wasmtime.GlobalType(wasmtime.ValType.f64(), mutable=True),
    wasmtime.Val.f64(1000.0),
)

satisfied_flow_min_air_flow_setpoint = wasmtime.Global(
    store,
    wasmtime.GlobalType(wasmtime.ValType.f64(), mutable=True),
    wasmtime.Val.f64(50.0),
)

htg_flow_min_air_flow_setpoint = wasmtime.Global(
    store,
    wasmtime.GlobalType(wasmtime.ValType.f64(), mutable=True),
    wasmtime.Val.f64(100.0),
)

htg_flow_max_air_flow_setpoint = wasmtime.Global(
    store,
    wasmtime.GlobalType(wasmtime.ValType.f64(), mutable=True),
    wasmtime.Val.f64(850.0),
)



# Define globals in the linker to match the module imports
linker.define(store, "env", "zone_air_temp", zone_air_temp)
linker.define(store, "env", "set_point", set_point)
linker.define(store, "env", "ahu_supply_air_temp", ahu_supply_air_temp)
linker.define(store, "env", "clg_flow_min_air_flow_setpoint", clg_flow_min_air_flow_setpoint)
linker.define(store, "env", "clg_flow_max_air_flow_setpoint", clg_flow_max_air_flow_setpoint)
linker.define(store, "env", "satisfied_flow_min_air_flow_setpoint", satisfied_flow_min_air_flow_setpoint)
linker.define(store, "env", "htg_flow_min_air_flow_setpoint", htg_flow_min_air_flow_setpoint)
linker.define(store, "env", "htg_flow_max_air_flow_setpoint", htg_flow_max_air_flow_setpoint)

# Instantiate the module with the linker
instance = linker.instantiate(store, module)

control_logic = instance.exports(store)["control_logic"]
integral_heating = instance.exports(store)["integral_heating"]
integral_cooling = instance.exports(store)["integral_cooling"]
pid_output_heating = instance.exports(store)["pid_output_heating"]
pid_output_cooling = instance.exports(store)["pid_output_cooling"]
discharge_air_temp_setpoint = instance.exports(store)["discharge_air_temp_setpoint"] 
discharge_air_flow_setpoint = instance.exports(store)["discharge_air_flow_setpoint"]
zone_air_temp_error = instance.exports(store)["zone_air_temp_error"]
mode = instance.exports(store)["mode"]


