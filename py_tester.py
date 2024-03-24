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
vavbox_change_temp = instance.exports(store)["vavbox_change_temp"]
vavbox_get_state_code = instance.exports(store)["vavbox_get_state_code"]

# Function to print VAV box state based on the state code
def print_vav_box_state(state_code):
    state_map = {1: "Heating", 2: "Cooling", 3: "Satisfied"}
    print(f"VAV Box State Code: {state_code}")
    print(f"VAV Box State: {state_map.get(state_code, 'Unknown')}")

# Create a new VAV Box
setpoint_temp = 22.0
vav_box_ptr = vavbox_new(store, setpoint_temp)

# Scenario 1: Simulate Heating
temp_change = -5.0  # Lowering the temperature significantly
vavbox_change_temp(store, vav_box_ptr, temp_change)
state_code = vavbox_get_state_code(store, vav_box_ptr)
print("Scenario 1: Simulate Heating")
print_vav_box_state(state_code)

# Scenario 2: Simulate Cooling
temp_change = 5.0  # Increasing the temperature significantly
vavbox_change_temp(store, vav_box_ptr, temp_change)
state_code = vavbox_get_state_code(store, vav_box_ptr)
print("\nScenario 2: Simulate Cooling")
print_vav_box_state(state_code)

# Scenario 3: Simulate Satisfied
temp_change = 1.0  # Minor adjustment to simulate close to setpoint temperature
vavbox_change_temp(store, vav_box_ptr, temp_change)
state_code = vavbox_get_state_code(store, vav_box_ptr)
print("\nScenario 3: Simulate Satisfied")
print_vav_box_state(state_code)
