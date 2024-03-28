from wasmtime import Engine, Store, Module, Instance

def load_wasm_module(filepath):
    with open(filepath, 'rb') as file:
        return file.read()

wasm_bytes = load_wasm_module('target/wasm32-unknown-unknown/debug/wasm_vav_control.wasm')
engine = Engine()
store = Store(engine)
module = Module(engine, wasm_bytes)
instance = Instance(store, module, [])

vavbox_new = instance.exports(store)["vavbox_new"]
vavbox_update_temperature = instance.exports(store)["vavbox_update_temperature"]
vavbox_get_state_code = instance.exports(store)["vavbox_get_state_code"]

def print_vav_box_state(state_code):
    state_map = {1: "Heating", 2: "Cooling", 3: "Satisfied"}
    print(f"VAV Box State Code: {state_code}")
    print(f"VAV Box State: {state_map.get(state_code, 'Unknown')}")

# Create a new VAV Box with a setpoint temperature
setpoint_temp = 22.0
vav_box_ptr = vavbox_new(store, setpoint_temp)

# Scenario 1: Update current temperature to simulate a new reading for heating
new_temp = 17.0  # New current temperature
vavbox_update_temperature(store, vav_box_ptr, new_temp)
state_code = vavbox_get_state_code(store, vav_box_ptr)
print("Scenario 1: Simulate Heating")
print_vav_box_state(state_code)


# Scenario 2: Simulate Cooling
new_temp = 33.0  # New current temperature
vavbox_update_temperature(store, vav_box_ptr, new_temp)
state_code = vavbox_get_state_code(store, vav_box_ptr)
print("Scenario 1: Simulate Cooling")
print_vav_box_state(state_code)

# Scenario 3: Simulate Satisfied
new_temp = 21.5  # New current temperature
vavbox_update_temperature(store, vav_box_ptr, new_temp)
state_code = vavbox_get_state_code(store, vav_box_ptr)
print("Scenario 1: Simulate Satisfied")
print_vav_box_state(state_code)
