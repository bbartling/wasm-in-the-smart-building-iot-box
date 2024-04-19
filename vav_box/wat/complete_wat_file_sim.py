import wasmtime
import random

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


# Define globals in the linker to match the module imports
linker.define(store, "env", "zone_air_temp", zone_air_temp)
linker.define(store, "env", "set_point", set_point)
linker.define(store, "env", "ahu_supply_air_temp", ahu_supply_air_temp)

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

# Simulation parameters
satisfied_zone_temp = 73.0
constant_heating_zone_temp = 66.0
constant_cooling_zone_temp = 78.0

satisfied_ahu_discharge_temp = 60.0
cooling_ahu_discharge_temp = 55.0
heating_ahu_discharge_temp = 65.0


def gradual_transition(start_temp, end_temp, start_ahu_temp, end_ahu_temp, steps):
    """Generate lists of temperatures for a smooth transition for both space temp and AHU discharge temp."""
    zone_air_temps = [start_temp + (end_temp - start_temp) * i / (steps - 1) for i in range(steps)]
    ahu_temps = [start_ahu_temp + (end_ahu_temp - start_ahu_temp) * i / (steps - 1) for i in range(steps)]
    return list(zip(zone_air_temps, ahu_temps))

def simulate_with_ahu_transitions():
    control_logic = instance.exports(store)["control_logic"]
    mode_desc = {0: 'Satisfied', 1: 'Heating', 2: 'Cooling'}
    
    # Define transitions including small random fluctuations around the target AHU temperatures
    heating_transition = gradual_transition(73.0, 66.0, 60.0, 65.0, 20)  # From satisfied to heating
    cooling_transition = gradual_transition(66.0, 78.0, 65.0, 55.0, 20)  # From heating to cooling

    # Run simulation for each transition
    for zone_air_temp_value, ahu_temp_value in heating_transition + cooling_transition:
        fluctuated_ahu_temp = ahu_temp_value + random.uniform(-1.0, 1.0)  # Adding random fluctuation
        zone_air_temp.set_value(store, wasmtime.Val.f64(zone_air_temp_value))
        ahu_supply_air_temp.set_value(store, wasmtime.Val.f64(fluctuated_ahu_temp))
        control_logic(store)  # Set values in the WASM file

        print(f" ***************** ***************** ***************** ***************** ***************** ")
        print(f"Zone Temp = {zone_air_temp.value(store):.2f}F, Zone Temp Set Point = {set_point.value(store)}F")
        print(f"Space Temp Error = {zone_air_temp_error.value(store):.2f}F, Mode = {mode_desc[mode.value(store)]}")
        print(f"Heating PI % Output = {pid_output_heating.value(store):.2f}%, Cooling PI % Output = {pid_output_cooling.value(store):.2f}%")
        print(f"Heating Integral = {integral_heating.value(store):.2f}, Cooling Integral = {integral_cooling.value(store):.2f}")
        print(f"Calculated Discharge Air Temp Spt = {discharge_air_temp_setpoint.value(store):.2f}F, Calculated Discharge Air Flow Spt = {discharge_air_flow_setpoint.value(store):.2f} CFM")


simulate_with_ahu_transitions()

