
'''
$ wasm-pack build --target no-modules --release
'''

import wasmtime

# Setup the WASM environment
engine = wasmtime.Engine()
store = wasmtime.Store(engine)
module = wasmtime.Module.from_file(engine, './pkg/rs_vav_box_firmware_bg.wasm')

# Instantiate the module
linker = wasmtime.Linker(engine)
instance = linker.instantiate(store, module)


# Access exported functions and memory
set_zone_air_temp = instance.exports(store)["set_zone_air_temp"]
set_zone_air_temp_setpoint = instance.exports(store)["set_zone_air_temp_setpoint"]
set_ahu_supply_air_temp = instance.exports(store)["set_ahu_supply_air_temp"]
set_clg_flow_min_air_flow_setpoint = instance.exports(store)["set_clg_flow_min_air_flow_setpoint"]
set_clg_flow_max_air_flow_setpoint = instance.exports(store)["set_clg_flow_max_air_flow_setpoint"]
set_htg_flow_min_air_flow_setpoint = instance.exports(store)["set_htg_flow_min_air_flow_setpoint"]
set_htg_flow_max_air_flow_setpoint = instance.exports(store)["set_htg_flow_max_air_flow_setpoint"]
set_satisfied_flow_min_air_flow_setpoint = instance.exports(store)["set_satisfied_flow_min_air_flow_setpoint"]
set_max_discharge_air_temp = instance.exports(store)["set_max_discharge_air_temp"]
set_zone_air_temp_deadband = instance.exports(store)["set_zone_air_temp_deadband"]

# Calculate control logic which internally calculates PID, and sets air temp and flow setpoints
calculate_control_logic = instance.exports(store)["calculate_control_logic"]

# Set initial conditions
set_zone_air_temp(store, 70.0)
set_zone_air_temp_setpoint(store, 72.0)
set_ahu_supply_air_temp(store, 60.0)
set_clg_flow_min_air_flow_setpoint(store, 500.0)
set_clg_flow_max_air_flow_setpoint(store, 1000.0)
set_htg_flow_min_air_flow_setpoint(store, 400.0)
set_htg_flow_max_air_flow_setpoint(store, 800.0)
set_satisfied_flow_min_air_flow_setpoint(store, 450.0)
set_max_discharge_air_temp(store, 110.0)
set_zone_air_temp_deadband(store, 5.0)

# Access exported functions
get_pid_output_heating = instance.exports(store)["get_pid_output_heating"]
get_pid_output_cooling = instance.exports(store)["get_pid_output_cooling"]

# Run the control logic
calculate_control_logic(store)

# Retrieve heating and cooling outputs
heating_output = get_pid_output_heating(store)
cooling_output = get_pid_output_cooling(store)

print("Heating output:", heating_output)
print("Cooling output:", cooling_output)
